"""
analyzer.py
===========
Rule-based information extraction for college notices.

This is a deliberately simple and explainable component. Given the raw text of
a notice, analyze_notice() extracts structured metadata using keyword matching,
dictionaries and regular expressions. No machine learning, no external APIs.

AI technique: rule-based inference (keyword matching + heuristic extraction).
"""
import re
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# DICTIONARIES  (kept together and visible so they are easy to explain / edit)
# ---------------------------------------------------------------------------

# Category -> list of keywords. Order matters: earlier categories win ties.
CATEGORY_KEYWORDS = [
    ("Examination", ["exam", "examination", "semester exam", "mid-sem", "end-sem", "viva", "practical exam"]),
    ("Placement",   ["placement", "aptitude", "campus drive", "campus recruitment", "recruitment", "interview"]),
    ("Internship",  ["internship", "intern ", "interns"]),
    ("Workshop",    ["workshop", "seminar", "technical session", "webinar", "guest lecture", "industry session", "bootcamp"]),
    ("Placement2",  []),  # placeholder to keep numbering clear (unused)
    ("Scholarship", ["scholarship", "financial aid", "stipend", "freeship"]),
    ("Fee",         ["fee", "fees", "payment", "tuition", "dues"]),
    ("Event",       ["fest", "cultural", "sports event", "sports", "annual day", "competition", "hackathon"]),
    ("Assignment",  ["assignment", "journal", "term work", "termwork", "tutorial", "experiment", "lab manual"]),
    ("Academic",    ["submission", "submit", "syllabus", "lecture", "class", "attendance", "course", "academic"]),
    ("Administrative", ["notice", "circular", "office", "administrative", "id card", "bonafide", "certificate"]),
]

# Branch -> aliases used inside notice text.
BRANCH_KEYWORDS = {
    "Computer Engineering": ["computer engineering", "computer science", "computer", "cse", "comp ", "c.e.", "ce "],
    "Information Technology": ["information technology", " it ", "i.t."],
    "Mechanical Engineering": ["mechanical engineering", "mechanical", "mech"],
    "Electronics Engineering": ["electronics and telecommunication", "electronics", "entc", "e&tc", "extc"],
    "Electrical Engineering": ["electrical engineering", "electrical"],
    "Civil Engineering": ["civil engineering", "civil"],
}

# Year aliases -> normalized code.
YEAR_KEYWORDS = {
    "FE": ["f.e.", "fe ", "first year", "first-year", "1st year"],
    "SE": ["s.e.", "se ", "second year", "second-year", "2nd year"],
    "TE": ["t.e.", "te ", "third year", "third-year", "3rd year"],
    "BE": ["b.e.", "be ", "final year", "fourth year", "4th year"],
}

# Subject / topic dictionary. Canonical name -> aliases.
SUBJECT_KEYWORDS = {
    "IIS": ["iis", "intelligent systems", "introduction to intelligent systems"],
    "TOC": ["toc", "theory of computation"],
    "Computer Graphics": ["computer graphics", "graphics"],
    "Microprocessor": ["microprocessor", "microprocessors"],
    "Data Structures": ["data structures", "dsa"],
    "Java": ["java"],
    "Python": ["python"],
    "Artificial Intelligence": ["artificial intelligence", "ai/ml", " ai ", "a.i."],
    "Machine Learning": ["machine learning", "ml"],
    "Thermodynamics": ["thermodynamics", "thermo"],
    "Manufacturing": ["manufacturing", "production"],
    "Robotics": ["robotics", "robot"],
    "Design": ["design engineering", "cad", "design "],
}

# Interest / keyword dictionary (used for interest matching).
INTEREST_KEYWORDS = {
    "Artificial Intelligence": ["artificial intelligence", "ai/ml", " ai ", "a.i."],
    "Machine Learning": ["machine learning", "ml"],
    "Internships": ["internship", "intern"],
    "Hackathons": ["hackathon", "coding competition", "codeathon"],
    "Design": ["design", "cad"],
    "Robotics": ["robotics", "robot"],
    "Placements": ["placement", "campus drive", "recruitment"],
    "Cultural": ["cultural", "fest", "dance", "music"],
    "Sports": ["sports", "athletics", "tournament"],
}

ACTION_WORDS = ["submit", "register", "attend", "fill", "complete", "pay",
                "report", "download", "apply", "bring", "collect", "enroll"]

MANDATORY_WORDS = ["mandatory", "compulsory", "strictly", "must ",
                   "are required", "is required", "required to",
                   "all students are required", "not optional"]

MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}


# ---------------------------------------------------------------------------
# EXTRACTION HELPERS
# ---------------------------------------------------------------------------

def _padded(text):
    """Lowercase and pad with spaces so ' it ' style aliases match at edges."""
    return " " + re.sub(r"\s+", " ", text.lower()) + " "


def detect_category(text, manual_category=None):
    if manual_category:
        return manual_category
    padded = _padded(text)
    for category, keywords in CATEGORY_KEYWORDS:
        if not keywords:
            continue
        for kw in keywords:
            if kw in padded:
                return category
    return "General"


def detect_branches(text):
    padded = _padded(text)
    found = []
    for branch, aliases in BRANCH_KEYWORDS.items():
        if any(alias in padded for alias in aliases):
            found.append(branch)
    return found  # empty => applies to all branches


def detect_years(text):
    padded = _padded(text)
    found = []
    for year, aliases in YEAR_KEYWORDS.items():
        if any(alias in padded for alias in aliases):
            found.append(year)
    return found  # empty => all years


def detect_divisions(text):
    padded = _padded(text)
    found = []
    # Patterns like "division a", "div a", "a division"
    for div in ["A", "B", "C", "D"]:
        d = div.lower()
        patterns = [f"division {d}", f"div {d}", f"div-{d}", f"{d} division"]
        if any(p in padded for p in patterns):
            found.append(div)
    return found  # empty => all divisions


def detect_topics(text):
    padded = _padded(text)
    found = []
    for subject, aliases in SUBJECT_KEYWORDS.items():
        if any(alias in padded for alias in aliases):
            found.append(subject)
    return found


def detect_interests(text):
    padded = _padded(text)
    found = []
    for interest, aliases in INTEREST_KEYWORDS.items():
        if any(alias in padded for alias in aliases):
            found.append(interest)
    return found


def detect_action_required(text):
    padded = _padded(text)
    return any(word in padded for word in ACTION_WORDS)


def detect_mandatory(text):
    padded = _padded(text)
    return any(word in padded for word in MANDATORY_WORDS)


def detect_deadline(text):
    """Return a datetime.date or None. Supports many common formats."""
    lower = text.lower()

    # Relative words first.
    if re.search(r"\btoday\b", lower):
        return date.today()
    if re.search(r"\btomorrow\b", lower):
        return date.today() + timedelta(days=1)

    # Numeric formats: 30/09/2026, 30-09-2026, 30.09.2026
    m = re.search(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\b", text)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        try:
            return date(y, mo, d)
        except ValueError:
            pass

    # Textual: 30 September 2026 / 30 Sep 2026 (year optional)
    m = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([a-zA-Z]+)\.?\s*(\d{4})?\b", text)
    if m:
        d = int(m.group(1))
        mon_name = m.group(2).lower()[:4]
        # normalize month lookup (try full then 3-letter)
        month = MONTHS.get(m.group(2).lower()) or MONTHS.get(m.group(2).lower()[:3])
        if month:
            y = int(m.group(3)) if m.group(3) else _infer_year(month, d)
            try:
                return date(y, month, d)
            except ValueError:
                pass
    return None


def _infer_year(month, day):
    """If no year is given, pick the next occurrence (this or next year)."""
    today = date.today()
    try:
        candidate = date(today.year, month, day)
    except ValueError:
        return today.year
    if candidate < today:
        return today.year + 1
    return today.year


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------

def analyze_notice(text, manual_category=None):
    """
    Analyze raw notice text and return a structured dictionary.

    Never raises on unusual input: missing fields simply return empty lists /
    None so that the admin can fill them in manually before publishing.
    """
    text = (text or "").strip()

    deadline = detect_deadline(text)
    return {
        "category": detect_category(text, manual_category),
        "target_branches": detect_branches(text),
        "target_years": detect_years(text),
        "target_divisions": detect_divisions(text),
        "topics": detect_topics(text),
        "interests": detect_interests(text),
        "deadline": deadline.isoformat() if deadline else None,
        "action_required": detect_action_required(text),
        "mandatory": detect_mandatory(text),
    }
