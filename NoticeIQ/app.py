"""
app.py
======
NoticeIQ – Flask application (routes, session auth, page rendering).

Run locally with:
    pip install -r requirements.txt
    python app.py
"""
import json
from datetime import datetime
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify)
from werkzeug.security import check_password_hash

import config
import database
import analyzer
import scoring
import seed

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# --- form option lists (also used by the analyzer output editor) ------------
BRANCHES = ["Computer Engineering", "Information Technology", "Mechanical Engineering",
            "Electronics Engineering", "Electrical Engineering", "Civil Engineering"]
YEARS = ["FE", "SE", "TE", "BE"]
DIVISIONS = ["A", "B", "C", "D"]
SUBJECTS = ["IIS", "TOC", "Computer Graphics", "Microprocessor", "Data Structures",
            "Java", "Python", "Artificial Intelligence", "Machine Learning",
            "Thermodynamics", "Manufacturing", "Robotics", "Design"]
INTERESTS = ["Artificial Intelligence", "Machine Learning", "Internships", "Hackathons",
             "Design", "Robotics", "Placements", "Cultural", "Sports"]
CATEGORIES = ["Academic", "Examination", "Assignment", "Event", "Placement",
              "Internship", "Workshop", "Administrative", "Scholarship", "Fee", "General"]


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _loads(value, default):
    try:
        return json.loads(value) if value else default
    except (ValueError, TypeError):
        return default


def user_from_row(row):
    if not row:
        return None
    return {
        "id": row["id"], "name": row["name"], "email": row["email"],
        "role": row["role"], "branch": row["branch"], "year": row["year"],
        "division": row["division"],
        "subjects": _loads(row["subjects_json"], []),
        "interests": _loads(row["interests_json"], []),
    }


def notice_from_row(row):
    deadline = row["deadline"]
    if deadline is not None and not isinstance(deadline, str):
        deadline = deadline.isoformat()
    return {
        "id": row["id"], "title": row["title"], "body": row["body"],
        "category": row["category"], "source": row["source"],
        "target_branches": _loads(row["target_branches_json"], []),
        "target_years": _loads(row["target_years_json"], []),
        "target_divisions": _loads(row["target_divisions_json"], []),
        "topics": _loads(row["topics_json"], []),
        "deadline": deadline,
        "action_required": bool(row["action_required"]),
        "mandatory": bool(row["mandatory"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return user_from_row(database.query_one("SELECT * FROM users WHERE id=%s", (uid,)))


def login_required(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return redirect(url_for("login"))
            if role and user["role"] != role:
                flash("You are not authorised to view that page.", "error")
                return redirect(url_for("index"))
            return fn(user, *args, **kwargs)
        return wrapper
    return decorator


def get_notice_state(user_id, notice_id):
    row = database.query_one(
        "SELECT is_read, is_saved FROM notice_states WHERE user_id=%s AND notice_id=%s",
        (user_id, notice_id))
    if not row:
        return {"is_read": False, "is_saved": False}
    return {"is_read": bool(row["is_read"]), "is_saved": bool(row["is_saved"])}


def all_notices():
    return [notice_from_row(r) for r in
            database.query_all("SELECT * FROM notices ORDER BY created_at DESC")]


def scored_notices_for(user):
    """Return every notice scored + state for the given student."""
    result = []
    for n in all_notices():
        scored = scoring.score_notice_for_user(user, n)
        state = get_notice_state(user["id"], n["id"])
        scored.update(state)
        result.append(scored)
    return result


def _sort_key_priority(n):
    dl = n["days_left"]
    dl = dl if dl is not None else 10 ** 6
    return (-n["priority_score"], dl)


@app.context_processor
def inject_globals():
    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")
    return {"app_name": "NoticeIQ", "subtitle": "Personalized College Notice Intelligence",
            "current_year": datetime.now().year, "greeting_word": greeting}


# ---------------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        row = database.query_one("SELECT * FROM users WHERE email=%s", (email,))
        if row and check_password_hash(row["password_hash"], password):
            session["user_id"] = row["id"]
            flash(f"Welcome back, {row['name'].split()[0]}!", "success")
            return redirect(url_for("index"))
        flash("Invalid email or password. Please try again.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# ROOT -> role based dashboard
# ---------------------------------------------------------------------------

@app.route("/")
@login_required()
def index(user):
    if user["role"] == "admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("student_dashboard"))


# ---------------------------------------------------------------------------
# STUDENT
# ---------------------------------------------------------------------------

@app.route("/dashboard")
@login_required(role="student")
def student_dashboard(user):
    notices = scored_notices_for(user)

    high = [n for n in notices if n["priority_level"] == "HIGH"]
    relevant = [n for n in notices if n["relevance"] >= 50]
    due_soon = [n for n in notices if n["days_left"] is not None and 0 <= n["days_left"] <= 3]

    important = sorted(notices, key=_sort_key_priority)
    important = [n for n in important if n["relevance"] >= 40][:6]

    upcoming = [n for n in notices if n["days_left"] is not None and n["days_left"] >= 0]
    upcoming = sorted(upcoming, key=lambda n: n["days_left"])[:5]

    summary = {
        "high": len(high), "relevant": len(relevant),
        "due_soon": len(due_soon), "total": len(notices),
    }
    return render_template("student_dashboard.html", user=user, summary=summary,
                           important=important, upcoming=upcoming)


@app.route("/notices/my")
@login_required(role="student")
def my_notices(user):
    notices = scored_notices_for(user)
    # personalized feed => hide the barely-relevant ones
    notices = [n for n in notices if n["relevance"] >= 25]
    return render_template("notices.html", user=user, notices=notices,
                           title="My Notices", scope="my")


@app.route("/notices/all")
@login_required(role="student")
def all_notices_view(user):
    notices = scored_notices_for(user)
    return render_template("notices.html", user=user, notices=notices,
                           title="All Notices", scope="all")


@app.route("/notice/<int:notice_id>")
@login_required(role="student")
def notice_detail(user, notice_id):
    row = database.query_one("SELECT * FROM notices WHERE id=%s", (notice_id,))
    if not row:
        flash("Notice not found.", "error")
        return redirect(url_for("student_dashboard"))
    scored = scoring.score_notice_for_user(user, notice_from_row(row))
    scored.update(get_notice_state(user["id"], notice_id))
    _mark_read(user["id"], notice_id)
    scored["is_read"] = True
    return render_template("notice_detail.html", user=user, n=scored)


def _upsert_state(user_id, notice_id, **fields):
    existing = database.query_one(
        "SELECT id FROM notice_states WHERE user_id=%s AND notice_id=%s",
        (user_id, notice_id))
    if existing:
        sets = ", ".join(f"{k}=%s" for k in fields)
        database.execute(
            f"UPDATE notice_states SET {sets} WHERE user_id=%s AND notice_id=%s",
            (*fields.values(), user_id, notice_id))
    else:
        cols = ", ".join(["user_id", "notice_id", *fields.keys()])
        ph = ", ".join(["%s"] * (2 + len(fields)))
        database.execute(
            f"INSERT INTO notice_states ({cols}) VALUES ({ph})",
            (user_id, notice_id, *fields.values()))


def _mark_read(user_id, notice_id):
    _upsert_state(user_id, notice_id, is_read=True)


@app.route("/notice/<int:notice_id>/read", methods=["POST"])
@login_required(role="student")
def mark_read(user, notice_id):
    _mark_read(user["id"], notice_id)
    return jsonify({"ok": True, "is_read": True})


@app.route("/notice/<int:notice_id>/save", methods=["POST"])
@login_required(role="student")
def toggle_save(user, notice_id):
    state = get_notice_state(user["id"], notice_id)
    new_val = not state["is_saved"]
    _upsert_state(user["id"], notice_id, is_saved=new_val)
    return jsonify({"ok": True, "is_saved": new_val})


@app.route("/profile", methods=["GET", "POST"])
@login_required(role="student")
def profile(user):
    if request.method == "POST":
        name = request.form.get("name", "").strip() or user["name"]
        branch = request.form.get("branch", "").strip()
        year = request.form.get("year", "").strip()
        division = request.form.get("division", "").strip()
        subjects = request.form.getlist("subjects")
        interests = request.form.getlist("interests")
        database.execute(
            """UPDATE users SET name=%s, branch=%s, year=%s, division=%s,
               subjects_json=%s, interests_json=%s WHERE id=%s""",
            (name, branch, year, division, json.dumps(subjects),
             json.dumps(interests), user["id"]))
        flash("Profile updated. Your personalized scores have been recalculated.", "success")
        return redirect(url_for("profile"))
    return render_template("profile.html", user=user, branches=BRANCHES, years=YEARS,
                           divisions=DIVISIONS, all_subjects=SUBJECTS, all_interests=INTERESTS)


# ---------------------------------------------------------------------------
# ADMIN
# ---------------------------------------------------------------------------

@app.route("/admin")
@login_required(role="admin")
def admin_dashboard(user):
    notices = all_notices()
    students = database.query_all("SELECT id FROM users WHERE role='student'")
    from datetime import timedelta
    week_ago = datetime.now() - timedelta(days=7)

    def _created(n):
        c = n["created_at"]
        return c if isinstance(c, datetime) else datetime.strptime(str(c), "%Y-%m-%d %H:%M:%S")

    this_week = [n for n in notices if _created(n) >= week_ago]
    summary = {
        "total": len(notices), "published": len(notices),
        "this_week": len(this_week), "students": len(students),
    }
    recent = notices[:8]
    return render_template("admin_dashboard.html", user=user, summary=summary, recent=recent)


@app.route("/admin/add", methods=["GET"])
@login_required(role="admin")
def admin_add(user):
    return render_template("admin_add_notice.html", user=user, analysis=None,
                           branches=BRANCHES, years=YEARS, divisions=DIVISIONS,
                           categories=CATEGORIES, subjects=SUBJECTS, form={})


@app.route("/admin/analyze", methods=["POST"])
@login_required(role="admin")
def admin_analyze(user):
    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    source = request.form.get("source", "").strip()
    manual_category = request.form.get("category", "").strip() or None

    if not title or not body:
        flash("Please provide both a notice title and body before analyzing.", "error")
        return render_template("admin_add_notice.html", user=user, analysis=None,
                               branches=BRANCHES, years=YEARS, divisions=DIVISIONS,
                               categories=CATEGORIES, subjects=SUBJECTS,
                               form={"title": title, "body": body, "source": source})

    analysis = analyzer.analyze_notice(f"{title}. {body}", manual_category)
    form = {"title": title, "body": body, "source": source}
    return render_template("admin_add_notice.html", user=user, analysis=analysis,
                           branches=BRANCHES, years=YEARS, divisions=DIVISIONS,
                           categories=CATEGORIES, subjects=SUBJECTS, form=form)


def _parse_notice_form():
    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    source = request.form.get("source", "").strip()
    category = request.form.get("category", "General").strip() or "General"
    branches = request.form.getlist("branches")
    years = request.form.getlist("years")
    divisions = request.form.getlist("divisions")
    topics = [t.strip() for t in request.form.get("topics", "").split(",") if t.strip()]
    deadline = request.form.get("deadline", "").strip() or None
    action = request.form.get("action_required") == "on"
    mandatory = request.form.get("mandatory") == "on"
    return dict(title=title, body=body, source=source, category=category,
                branches=branches, years=years, divisions=divisions, topics=topics,
                deadline=deadline, action=action, mandatory=mandatory)


@app.route("/admin/publish", methods=["POST"])
@login_required(role="admin")
def admin_publish(user):
    f = _parse_notice_form()
    if not f["title"] or not f["body"]:
        flash("A notice needs a title and body.", "error")
        return redirect(url_for("admin_add"))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    database.execute(
        """INSERT INTO notices
           (title, body, category, source, target_branches_json, target_years_json,
            target_divisions_json, topics_json, deadline, action_required, mandatory,
            created_at, updated_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (f["title"], f["body"], f["category"], f["source"],
         json.dumps(f["branches"]), json.dumps(f["years"]), json.dumps(f["divisions"]),
         json.dumps(f["topics"]), f["deadline"], f["action"], f["mandatory"], now, now))
    flash("Notice published! It is now visible to students.", "success")
    return redirect(url_for("admin_manage"))


@app.route("/admin/manage")
@login_required(role="admin")
def admin_manage(user):
    notices = all_notices()
    for n in notices:
        n["deadline_label"] = scoring.deadline_label(n["deadline"])
    return render_template("admin_manage_notices.html", user=user, notices=notices)


@app.route("/admin/edit/<int:notice_id>", methods=["GET", "POST"])
@login_required(role="admin")
def admin_edit(user, notice_id):
    row = database.query_one("SELECT * FROM notices WHERE id=%s", (notice_id,))
    if not row:
        flash("Notice not found.", "error")
        return redirect(url_for("admin_manage"))
    if request.method == "POST":
        f = _parse_notice_form()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        database.execute(
            """UPDATE notices SET title=%s, body=%s, category=%s, source=%s,
               target_branches_json=%s, target_years_json=%s, target_divisions_json=%s,
               topics_json=%s, deadline=%s, action_required=%s, mandatory=%s, updated_at=%s
               WHERE id=%s""",
            (f["title"], f["body"], f["category"], f["source"],
             json.dumps(f["branches"]), json.dumps(f["years"]), json.dumps(f["divisions"]),
             json.dumps(f["topics"]), f["deadline"], f["action"], f["mandatory"], now, notice_id))
        flash("Notice updated.", "success")
        return redirect(url_for("admin_manage"))
    notice = notice_from_row(row)
    return render_template("admin_add_notice.html", user=user, analysis=notice,
                           branches=BRANCHES, years=YEARS, divisions=DIVISIONS,
                           categories=CATEGORIES, subjects=SUBJECTS,
                           form={"title": notice["title"], "body": notice["body"],
                                 "source": notice["source"]},
                           edit_id=notice_id, edit_mode=True)


@app.route("/admin/delete/<int:notice_id>", methods=["POST"])
@login_required(role="admin")
def admin_delete(user, notice_id):
    database.execute("DELETE FROM notices WHERE id=%s", (notice_id,))
    flash("Notice deleted.", "success")
    return redirect(url_for("admin_manage"))


# ---------------------------------------------------------------------------
# STARTUP
# ---------------------------------------------------------------------------

def bootstrap():
    database.init_db()
    seed.seed()


bootstrap()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT, debug=True)
