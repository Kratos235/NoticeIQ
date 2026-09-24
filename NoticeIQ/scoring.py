"""
scoring.py
==========
Core AI logic for NoticeIQ: personalized relevance and priority.

Everything here is transparent, weighted, rule-based reasoning:
  * calculate_relevance(user, notice)  -> 0..100 + human-readable reasons
  * calculate_priority(...)            -> 0..100 + level (HIGH/MEDIUM/LOW)
  * generate_explanation(...)          -> a single sentence summary

Relevance and priority are NEVER stored. They are computed on demand from the
student profile + notice, so editing a profile instantly changes results.
"""
from datetime import date

import analyzer

# --- weights (kept visible for the viva) ------------------------------------
W_BRANCH = 30
W_YEAR = 20
W_DIVISION = 10          # audience total = 60
W_SUBJECT = 25
W_INTEREST = 15          # content total = 40  -> grand total 100

PRIORITY_W_RELEVANCE = 0.60
PRIORITY_W_URGENCY = 0.25
PRIORITY_W_ACTION = 0.15

LOW_RELEVANCE_CAP = 25   # below this a near deadline cannot make a notice HIGH


# ---------------------------------------------------------------------------
# DEADLINE HELPERS
# ---------------------------------------------------------------------------

def days_until(deadline):
    """Return integer days from today to deadline (negative => overdue)."""
    if not deadline:
        return None
    if isinstance(deadline, str):
        try:
            deadline = date.fromisoformat(deadline)
        except ValueError:
            return None
    return (deadline - date.today()).days


def deadline_label(deadline):
    """Human friendly countdown text."""
    d = days_until(deadline)
    if d is None:
        return "No deadline"
    if d < 0:
        return "Overdue"
    if d == 0:
        return "Due Today"
    if d == 1:
        return "Due Tomorrow"
    if d <= 14:
        return f"{d} days left"
    return f"{d} days left"


def urgency_score(deadline):
    """Convert a deadline into a 0..100 urgency score."""
    d = days_until(deadline)
    if d is None:
        return 10
    if d <= 1:            # overdue or 0-1 day
        return 100
    if d <= 3:
        return 85
    if d <= 7:
        return 65
    if d <= 14:
        return 40
    return 20


# ---------------------------------------------------------------------------
# RELEVANCE
# ---------------------------------------------------------------------------

def _get_interests_of_notice(notice):
    """Detected interests: stored on notice or derived from its body."""
    if notice.get("interests"):
        return notice["interests"]
    return analyzer.detect_interests(notice.get("body", ""))


def calculate_relevance(user, notice):
    """
    Return (relevance_score, reasons, breakdown).

    reasons   : list of {"ok": bool, "text": str}
    breakdown : dict with audience/subject/interest sub-scores
    """
    reasons = []

    branches = notice.get("target_branches") or []
    years = notice.get("target_years") or []
    divisions = notice.get("target_divisions") or []
    topics = notice.get("topics") or []
    notice_interests = _get_interests_of_notice(notice)

    # --- Branch (30) ---
    if not branches:
        branch_score = W_BRANCH
        reasons.append({"ok": True, "text": "Notice applies to all branches"})
    elif user.get("branch") in branches:
        branch_score = W_BRANCH
        reasons.append({"ok": True, "text": f"Your branch matches {user['branch']}"})
    else:
        branch_score = 0
        reasons.append({"ok": False, "text": f"Notice targets {', '.join(branches)}"})

    # --- Year (20) ---
    if not years:
        year_score = W_YEAR
        reasons.append({"ok": True, "text": "Notice applies to all years"})
    elif user.get("year") in years:
        year_score = W_YEAR
        reasons.append({"ok": True, "text": f"Your year matches {user['year']}"})
    else:
        year_score = 0
        reasons.append({"ok": False, "text": f"Notice targets {', '.join(years)} students"})

    # --- Division (10) ---
    if not divisions:
        division_score = W_DIVISION
        reasons.append({"ok": True, "text": "Notice applies to all divisions"})
    elif user.get("division") in divisions:
        division_score = W_DIVISION
        reasons.append({"ok": True, "text": f"Your division matches {user['division']}"})
    else:
        division_score = 0
        reasons.append({"ok": False, "text": f"Notice targets division {', '.join(divisions)}"})

    audience_score = branch_score + year_score + division_score

    # --- Subject / topic (25) ---
    user_subjects = user.get("subjects") or []
    if not topics:
        subject_score = W_SUBJECT
        reasons.append({"ok": True, "text": "Notice is not restricted to a specific subject"})
    else:
        matched = [t for t in topics if t in user_subjects]
        if matched:
            subject_score = W_SUBJECT
            reasons.append({"ok": True, "text": f"{', '.join(matched)} is in your subject profile"})
        else:
            subject_score = 0
            reasons.append({"ok": False, "text": f"Notice topic ({', '.join(topics)}) is not in your subjects"})

    # --- Interest (15) ---
    user_interests = user.get("interests") or []
    interest_score = 0
    if notice_interests:
        matched_i = [i for i in notice_interests if i in user_interests]
        if matched_i:
            interest_score = W_INTEREST
            reasons.append({"ok": True, "text": f"Matches your interest in {', '.join(matched_i)}"})

    relevance = min(100, audience_score + subject_score + interest_score)

    breakdown = {
        "branch_score": branch_score,
        "year_score": year_score,
        "division_score": division_score,
        "audience_score": audience_score,
        "audience_max": W_BRANCH + W_YEAR + W_DIVISION,
        "subject_score": subject_score,
        "subject_max": W_SUBJECT,
        "interest_score": interest_score,
        "interest_max": W_INTEREST,
        "relevance": relevance,
    }
    return relevance, reasons, breakdown


# ---------------------------------------------------------------------------
# PRIORITY
# ---------------------------------------------------------------------------

def action_score(action_required, mandatory):
    if mandatory:
        return 100
    if action_required:
        return 70
    return 20


def calculate_priority(relevance_score, deadline, action_required, mandatory):
    """Return (priority_score, level, breakdown)."""
    urg = urgency_score(deadline)
    act = action_score(action_required, mandatory)

    score = round(
        PRIORITY_W_RELEVANCE * relevance_score
        + PRIORITY_W_URGENCY * urg
        + PRIORITY_W_ACTION * act
    )

    capped = False
    # A barely-relevant notice must not become HIGH just due to a near deadline.
    if relevance_score < LOW_RELEVANCE_CAP:
        score = min(score, 49)
        capped = True

    if score >= 75:
        level = "HIGH"
    elif score >= 50:
        level = "MEDIUM"
    else:
        level = "LOW"

    breakdown = {
        "relevance": relevance_score,
        "urgency": urg,
        "action": act,
        "priority": score,
        "capped": capped,
    }
    return score, level, breakdown


# ---------------------------------------------------------------------------
# EXPLANATION
# ---------------------------------------------------------------------------

def generate_explanation(level, reasons, deadline, action_required, mandatory):
    """Build a single human-readable sentence from the matched rules."""
    positives = [r["text"].replace("✓ ", "") for r in reasons if r["ok"]]
    negatives = [r["text"] for r in reasons if not r["ok"]]

    dl = deadline_label(deadline)
    urgent = dl in ("Overdue", "Due Today", "Due Tomorrow") or dl.endswith("days left") and dl[0] in "123"

    if level == "HIGH":
        parts = "; ".join(positives[:3]) if positives else "it targets your profile"
        tail = " and requires action before an approaching deadline" if (action_required or mandatory) else ""
        return f"This notice is highly relevant because {parts}{tail}."
    if level == "MEDIUM":
        if positives:
            return (f"This notice is relevant to you ({positives[0].lower()}), "
                    f"but is less urgent for your profile.")
        return "This notice has moderate relevance to your profile."
    # LOW
    if negatives:
        return f"This notice has limited relevance because {negatives[0].lower()}."
    return "This notice has limited relevance to your current profile."


# ---------------------------------------------------------------------------
# CONVENIENCE: score a notice for a user in one call
# ---------------------------------------------------------------------------

def score_notice_for_user(user, notice):
    """Attach relevance/priority/reasons/labels to a copy of the notice dict."""
    relevance, reasons, rel_breakdown = calculate_relevance(user, notice)
    priority, level, pri_breakdown = calculate_priority(
        relevance,
        notice.get("deadline"),
        notice.get("action_required"),
        notice.get("mandatory"),
    )
    explanation = generate_explanation(
        level, reasons, notice.get("deadline"),
        notice.get("action_required"), notice.get("mandatory"),
    )
    result = dict(notice)
    result.update({
        "relevance": relevance,
        "priority_score": priority,
        "priority_level": level,
        "reasons": reasons,
        "relevance_breakdown": rel_breakdown,
        "priority_breakdown": pri_breakdown,
        "explanation": explanation,
        "deadline_label": deadline_label(notice.get("deadline")),
        "days_left": days_until(notice.get("deadline")),
    })
    return result
