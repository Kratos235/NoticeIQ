# NoticeIQ — AI-Based Personalized College Notice Relevance & Priority Detection

> **Subtitle:** Personalized College Notice Intelligence

NoticeIQ is a web-based intelligent system that reads college notices, extracts
their key information, and computes **how relevant and how important** each
notice is **for an individual student**. The same notice can be *very high*
priority for one student and *very low* for another.

---

## 1. Project Title
**NoticeIQ – AI-Based Personalized College Notice Relevance and Priority Detection System**

## 2. Problem Statement
College students receive a flood of notices (academic, exams, placements,
events, scholarships…). Most are irrelevant to any given student, and important
deadlines get lost. A plain notice board / CRUD system cannot tell a student
*what matters to them*.

## 3. Objective
Build an **explainable intelligent system** that:
1. Understands a notice's content,
2. Extracts structured information (branch, year, subject, deadline, actions…),
3. Matches it against the student's profile,
4. Produces a **personalized relevance score** and a **personalized priority level**,
5. Explains *why* — in plain language.

## 4. Key Features
- 🔐 Session-based login (Admin + Students) with hashed passwords
- 🧠 Rule-based notice analyzer (category, branch, year, division, topics, deadline, action, mandatory)
- 🎯 Personalized **relevance** (0–100%) and **priority** (HIGH / MEDIUM / LOW) per student
- 📝 Human-readable reasoning + full score breakdown
- 🧑‍💼 Admin: paste a raw notice → **Analyze** → edit extracted fields → **Publish**
- 🎓 Student: dashboard, my/all notices, search, filters, sort, read/save, editable profile
- 📅 Dynamic deadline countdown (Due Today / 2 days left / Overdue…)
- 📱 Responsive, polished dashboard UI (no external CDN — works fully offline)

## 5. AI Technique Used
**Rule-based inference + heuristic scoring for personalized relevance and priority detection.**

No machine learning is used, and none is claimed.

## 6. Why Rule-Based Reasoning?
The project is for the *Introduction to Intelligent Systems* subject, where the
decision process must be **transparent and explainable during a viva**. A
rule-based expert-system style approach lets every score be traced back to a
concrete rule (branch match, subject match, deadline urgency, mandatory flag…),
unlike a black-box ML model.

## 7. System Architecture
```
College Notice (pasted by admin)
      ↓  analyzer.analyze_notice()        → extract category/branch/year/div/topics/deadline/action/mandatory
      ↓  (admin reviews & edits)          → stored in MySQL
      ↓  scoring.calculate_relevance()    → personalized relevance (0–100) + reasons
      ↓  scoring.calculate_priority()     → urgency + action → priority (HIGH/MEDIUM/LOW)
      ↓  scoring.generate_explanation()   → plain-language recommendation
      ↓  Flask + Jinja templates          → personalized student feed
```
Files: `app.py` (routes), `database.py` (MySQL), `analyzer.py` (extraction),
`scoring.py` (AI logic), `seed.py` (demo data), `config.py` (env config).

## 8. Relevance Scoring Formula (max 100)
```
AUDIENCE MATCH  = 60   Branch 30 · Year 20 · Division 10
CONTENT  MATCH  = 40   Subject/topic 25 · Interest 15
```
If a notice does not restrict a field (e.g. no branch specified), that criterion
is treated as universally applicable and earns full points.

## 9. Priority Scoring Formula
```
priority = 0.60 * relevance + 0.25 * urgency + 0.15 * action
```
**Urgency:** ≤1 day/overdue = 100 · 2–3 = 85 · 4–7 = 65 · 8–14 = 40 · >14 = 20 · none = 10
**Action:** mandatory = 100 · action required = 70 · informational = 20
**Levels:** 75–100 HIGH · 50–74 MEDIUM · 0–49 LOW
**Safeguard:** if relevance < 25, priority is capped to LOW (a near deadline
cannot make an irrelevant notice HIGH).

## 10. Database Design (MySQL, auto-created)
- `users` — id, name, email, password_hash, role, branch, year, division, subjects_json, interests_json, created_at
- `notices` — id, title, body, category, source, target_*_json, topics_json, deadline, action_required, mandatory, timestamps
- `notice_states` — id, user_id → users, notice_id → notices, is_read, is_saved (unique per user+notice)

Relevance/priority are **never stored** — they are computed on demand from
*profile + notice*, so editing a profile instantly changes the results.

## 11. Technology Stack
Python · Flask · Jinja2 · MySQL (`mysql-connector-python`) · HTML · CSS · Vanilla JS.
No React, no Node, no ORM, no external APIs.

## 12. How Notices Enter the System
The **admin pastes/writes a raw notice**. There is no scraping and no external
source. Sample notices are seeded automatically on first run.

## 13. How Personalization Works
Each notice is scored against the logged-in student's branch, year, division,
subjects and interests, combined with the notice's deadline urgency and required
actions. Change the profile → scores recalculate immediately.

## 14. Demo Workflow
1. Login as **Aarav (student@noticeiq.local)** → open *IIS Journal Submission* → Relevance ~100%, Priority **HIGH**.
2. Logout, login as **Riya (student2@noticeiq.local)** → open the **same** notice → Relevance very low, Priority **LOW**.
3. Login as **Admin** → *Add Notice* → paste text → **Analyze** → edit → **Publish** → visible instantly to students.

## 15. Installation
### a. Install MySQL
- Ubuntu: `sudo apt install mariadb-server` (MariaDB is fully compatible) or MySQL Server.
- Windows/Mac: install MySQL Community Server / XAMPP.

### b. Create the database/user (optional — app auto-creates the DB)
```sql
CREATE DATABASE IF NOT EXISTS noticeiq;
-- optionally a dedicated user:
CREATE USER 'noticeiq'@'localhost' IDENTIFIED BY 'yourpassword';
GRANT ALL PRIVILEGES ON noticeiq.* TO 'noticeiq'@'localhost';
```

### c. Configure credentials
Copy `.env.example` to `.env` and edit:
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=          # your MySQL password (empty by default)
DB_NAME=noticeiq
```
No real password is hard-coded in the source.

### d. Install dependencies & run
```bash
pip install -r requirements.txt
python app.py
```
The app creates tables and seeds demo data automatically, then serves at
`http://localhost:5000` (set `PORT` in `.env` to change).

## 16. Demo Credentials
| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@noticeiq.local` | `admin123` |
| Student (Aarav — TE Computer) | `student@noticeiq.local` | `student123` |
| Student (Riya — SE Mechanical) | `student2@noticeiq.local` | `student123` |

## 17. Future Scope
- More notice sources (email/upload) and richer topic dictionaries
- Student-configurable rule weights
- Optional statistical ranking layer on top of the rule base

## 18. Limitations
- Rule-based extraction is intentionally simple; the admin can correct any field.
- Deadline parsing covers common formats only.
- No ML → it will not "learn" patterns beyond the written rules.

## Testing
```bash
python -m compileall .
python -m unittest test_noticeiq.py
```

---
**The system is designed as an explainable rule-based intelligent system rather than a machine-learning model.**
