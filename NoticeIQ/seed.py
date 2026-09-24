"""
seed.py
=======
Seeds demo accounts and realistic sample notices so the app looks complete on
first run. Idempotent: running it again will not create duplicates.

Deadlines are seeded RELATIVE TO TODAY (today + N days) so the personalized
feed always shows realistic "Due Today / 2 days left / Overdue" states.
"""
import json
from datetime import date, datetime, timedelta

from werkzeug.security import generate_password_hash

import database


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _seed_users():
    users = [
        {
            "name": "Admin", "email": "admin@noticeiq.local", "password": "admin123",
            "role": "admin", "branch": None, "year": None, "division": None,
            "subjects": [], "interests": [],
        },
        {
            "name": "Aarav Mehta", "email": "student@noticeiq.local", "password": "student123",
            "role": "student", "branch": "Computer Engineering", "year": "TE", "division": "A",
            "subjects": ["IIS", "TOC", "Computer Graphics", "Microprocessor"],
            "interests": ["Artificial Intelligence", "Machine Learning", "Internships", "Hackathons"],
        },
        {
            "name": "Riya Sharma", "email": "student2@noticeiq.local", "password": "student123",
            "role": "student", "branch": "Mechanical Engineering", "year": "SE", "division": "B",
            "subjects": ["Thermodynamics", "Manufacturing"],
            "interests": ["Design", "Robotics"],
        },
    ]
    for u in users:
        exists = database.query_one("SELECT id FROM users WHERE email=%s", (u["email"],))
        if exists:
            continue
        database.execute(
            """INSERT INTO users
               (name, email, password_hash, role, branch, year, division,
                subjects_json, interests_json, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (u["name"], u["email"], generate_password_hash(u["password"]), u["role"],
             u["branch"], u["year"], u["division"],
             json.dumps(u["subjects"]), json.dumps(u["interests"]), _now()),
        )


def _d(offset_days):
    """Deadline helper: today + offset (may be negative for 'overdue')."""
    return (date.today() + timedelta(days=offset_days)).isoformat()


def _seed_notices():
    # Only seed once (if no notices exist yet).
    existing = database.query_one("SELECT COUNT(*) AS c FROM notices")
    if existing and existing["c"] > 0:
        return

    notices = [
        {
            "title": "IIS Journal Submission – T.E. Computer Engineering",
            "body": ("All T.E. Computer Engineering students are required to submit their "
                     "IIS (Introduction to Intelligent Systems / Artificial Intelligence) "
                     "journal by the given deadline before 4:00 PM. Submission is mandatory."),
            "category": "Academic", "source": "Computer Engineering Department",
            "branches": ["Computer Engineering"], "years": ["TE"], "divisions": [],
            "topics": ["IIS"], "deadline": _d(2), "action": True, "mandatory": True,
        },
        {
            "title": "Computer Graphics Experiment 7 Submission",
            "body": ("T.E. Computer Engineering students must submit Computer Graphics "
                     "Experiment 7 in the lab. Please complete and submit your journal."),
            "category": "Assignment", "source": "CG Lab",
            "branches": ["Computer Engineering"], "years": ["TE"], "divisions": [],
            "topics": ["Computer Graphics"], "deadline": _d(1), "action": True, "mandatory": True,
        },
        {
            "title": "Placement Cell Aptitude Test Registration",
            "body": ("All B.E. students interested in campus placements must register for the "
                     "aptitude test conducted by the Placement Cell. Registration is required."),
            "category": "Placement", "source": "Training & Placement Cell",
            "branches": [], "years": ["BE"], "divisions": [],
            "topics": [], "deadline": _d(5), "action": True, "mandatory": False,
        },
        {
            "title": "College Cultural Fest Registration",
            "body": ("All students are invited to register for the annual cultural fest. "
                     "Participate in music, dance and cultural events. Register early!"),
            "category": "Event", "source": "Student Council",
            "branches": [], "years": [], "divisions": [],
            "topics": [], "deadline": _d(9), "action": True, "mandatory": False,
        },
        {
            "title": "Mechanical Engineering Workshop",
            "body": ("S.E. Mechanical Engineering students should attend a hands-on workshop on "
                     "manufacturing processes. Attendance is recommended."),
            "category": "Workshop", "source": "Mechanical Department",
            "branches": ["Mechanical Engineering"], "years": ["SE"], "divisions": [],
            "topics": ["Manufacturing"], "deadline": _d(12), "action": True, "mandatory": False,
        },
        {
            "title": "TOC Tutorial Submission",
            "body": ("All T.E. Computer Engineering students must submit the Theory of Computation "
                     "(TOC) tutorial. Submission is compulsory."),
            "category": "Academic", "source": "Computer Engineering Department",
            "branches": ["Computer Engineering"], "years": ["TE"], "divisions": [],
            "topics": ["TOC"], "deadline": _d(-1), "action": True, "mandatory": True,
        },
        {
            "title": "Scholarship Renewal Notice",
            "body": ("All eligible students receiving scholarships must apply for renewal and "
                     "submit the required documents to the accounts office."),
            "category": "Scholarship", "source": "Accounts Office",
            "branches": [], "years": [], "divisions": [],
            "topics": [], "deadline": _d(14), "action": True, "mandatory": False,
        },
        {
            "title": "AI/ML Industry Session",
            "body": ("An industry session on Artificial Intelligence and Machine Learning will be "
                     "held for all interested students. Attend to learn about AI/ML careers."),
            "category": "Workshop", "source": "Department of Computer Engineering",
            "branches": [], "years": [], "divisions": [],
            "topics": ["Artificial Intelligence", "Machine Learning"], "deadline": _d(4),
            "action": True, "mandatory": False,
        },
    ]

    for n in notices:
        database.execute(
            """INSERT INTO notices
               (title, body, category, source, target_branches_json, target_years_json,
                target_divisions_json, topics_json, deadline, action_required, mandatory,
                created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (n["title"], n["body"], n["category"], n["source"],
             json.dumps(n["branches"]), json.dumps(n["years"]),
             json.dumps(n["divisions"]), json.dumps(n["topics"]),
             n["deadline"], n["action"], n["mandatory"], _now(), _now()),
        )


def seed():
    _seed_users()
    _seed_notices()


if __name__ == "__main__":
    database.init_db()
    seed()
    print("Seed complete.")
