# NoticeIQ — Personalized College Notice Intelligence

NoticeIQ helps college students identify which notices are relevant and urgent for them. An administrator enters a notice, the system extracts structured information, and an explainable rule-based engine scores it against each student's academic profile and interests.

The same notice can have a different relevance and priority for different students. NoticeIQ uses deterministic rules and heuristic scoring; **it does not use a trained machine-learning model**.

## Why NoticeIQ?

Students receive notices about academics, examinations, assignments, events, internships, placements and administration. A conventional notice board shows the same feed to everyone. NoticeIQ adds a personal relevance layer so students can focus on notices that match their branch, year, division, subjects and interests.

## Main features

### Student
- Session-based student login.
- Personalised dashboard with relevant, high-priority and soon-due notice summaries.
- Separate **My Notices** and **All Notices** views.
- Notice search, filtering and sorting.
- Per-notice relevance score, priority level and explanation.
- Read and save states.
- Editable profile with branch, year, division, subjects and interests.
- Deadline countdown and overdue indicators.

### Administrator
- Separate administrator access and dashboard.
- Create notices by entering or pasting their text.
- Analyse notice text to extract category, target audience, topics, deadline and action requirements.
- Review and edit extracted fields before publishing.
- Manage published notices.

### Explainable prioritisation
- Relevance score from 0–100, based on audience and content matches.
- Priority classification: HIGH, MEDIUM or LOW.
- Human-readable scoring reasons and breakdown.
- Scores are calculated against the active student's profile and the notice, rather than stored as fixed notice properties.

## How it works

```text
Admin enters a notice
        |
        v
analyzer.analyze_notice()
        |
        v
Admin reviews and edits extracted fields
        |
        v
Notice is stored in MySQL
        |
        v
scoring.score_notice_for_user(student, notice)
        |
        +--> Relevance score
        +--> Urgency score
        +--> Action score
        |
        v
Priority level + explanation
        |
        v
Personalised student dashboard
```

### Relevance formula

```text
Audience match (60 points)
  Branch       30
  Year         20
  Division     10

Content match (40 points)
  Subject/topic match  25
  Interest match       15
```

### Priority formula

```text
priority = 0.60 * relevance
         + 0.25 * urgency
         + 0.15 * action
```

| Priority score | Level |
|---:|---|
| 75–100 | HIGH |
| 50–74 | MEDIUM |
| 0–49 | LOW |

A safeguard caps a very low-relevance notice at LOW priority, even when its deadline is close.

## Technology stack

| Layer | Technologies |
|---|---|
| Main application | Python, Flask |
| Server-rendered UI | Jinja2, HTML, CSS, Vanilla JavaScript |
| Database | MySQL |
| Database access | mysql-connector-python |
| Authentication | Flask sessions, Werkzeug password-hash verification |
| Tests | Python `unittest` |

## Architecture and repository layout

The main NoticeIQ product implementation is the Flask application in `NoticeIQ/`.

```text
NoticeIQ/
├── NoticeIQ/
│   ├── app.py             # Flask routes, sessions and page rendering
│   ├── analyzer.py        # Rule-based notice extraction
│   ├── scoring.py         # Personalised relevance and priority scoring
│   ├── database.py        # MySQL schema setup and query helpers
│   ├── seed.py            # Local demo data
│   ├── config.py          # Environment-based configuration
│   ├── templates/         # Jinja2 templates
│   ├── static/            # CSS and JavaScript assets
│   └── test_noticeiq.py   # Analyzer and scoring unit tests
├── backend/               # Separate FastAPI scaffold
├── frontend/              # Separate React scaffold
└── README.md
```

**Repository note:** The top-level `backend/` and `frontend/` folders are a separate FastAPI/React scaffold. They are not the implementation of the NoticeIQ Flask features described above. Start the Flask app from the `NoticeIQ/` subdirectory.

## Database

The Flask application initialises its MySQL database and creates three principal tables:

- `users` — account details, role, password hash and student profile attributes.
- `notices` — notice text, category, target audience, topics, deadline and action/mandatory flags.
- `notice_states` — per-user read and saved state for each notice.

Relevance and priority are calculated on demand. Updating a student's profile therefore changes how notices are ranked for that student.

## Requirements

- Python 3
- MySQL Server
- pip

## Setup and run

### 1. Create the database (optional)

The application creates the database if it does not exist, provided the configured MySQL user has permission. You can also create it manually:

```sql
CREATE DATABASE noticeiq;
```

### 2. Configure environment variables

Create a `.env` file inside `NoticeIQ/` (beside `app.py` and `config.py`):

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=noticeiq
SECRET_KEY=replace_with_a_long_random_secret
PORT=5000
```

The development configuration defaults to `localhost:3306`, user `root`, database `noticeiq`, an empty database password and port `5000`. Set a strong `SECRET_KEY` for any environment beyond local testing.

### 3. Install dependencies and start the app

```bash
cd NoticeIQ
pip install -r requirements.txt
python app.py
```

Open [http://localhost:5000](http://localhost:5000).

The seed module provides local demo data. Demo accounts documented in `NoticeIQ/README.md` are intended for local development only; change or remove them before deployment.

## Tests

From the `NoticeIQ/` directory:

```bash
python -m compileall .
python -m unittest test_noticeiq.py
```

The unit tests cover notice field extraction (including branch, year, division and deadline parsing) and scoring behaviour (including different scores for different students). Run the tests locally with your configured Python environment before relying on the results.

## Limitations

- Notice analysis is rule-based and intentionally limited; administrators can review and correct extracted fields before publication.
- Deadline parsing supports common formats, not every date expression.
- There is no model training or automatic learning from student behaviour.
- Notices are entered by administrators; the application does not scrape college websites or email systems.
- The FastAPI/React scaffold is separate from the main Flask implementation.

## Future improvements

- PDF/image notice upload with validated text extraction.
- More robust date parsing and multilingual notice analysis.
- Configurable scoring weights and richer topic matching.
- Email or calendar reminders for important notices.
- More automated tests for access control, database workflows and parser edge cases.
- Production deployment configuration and secret management.

---

NoticeIQ is an explainable intelligent-system project that applies rule-based reasoning and personalised heuristic scoring to improve how students discover important college notices.
