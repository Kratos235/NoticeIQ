# Running NoticeIQ locally

The full app already exists at `/app/NoticeIQ` (Flask + MySQL). To run it on your own
machine, these are the only steps you need.

## Prerequisites
- Python 3.9+ installed
- MySQL Server **or** MariaDB installed and running

## Steps

### 1. Get the project
Copy the `NoticeIQ/` folder onto your machine (or download the code).

### 2. Install & start MySQL
- Windows: install MySQL Community Server (or XAMPP and start MySQL).
- macOS: `brew install mysql` then `brew services start mysql`.
- Ubuntu/Debian: `sudo apt install mariadb-server` then `sudo service mariadb start`.

You do **not** need to create the `noticeiq` database by hand — the app creates it
automatically. (Optionally you can: `CREATE DATABASE noticeiq;`)

### 3. Configure database credentials
In the `NoticeIQ` folder, copy `.env.example` to `.env` and set your MySQL details:
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password   # leave blank if your root has no password
DB_NAME=noticeiq
PORT=5000
```
> Note: if your MySQL `root` uses socket auth (common on Linux), either set a password
> for root, or create a dedicated user and put it in `.env`.

### 4. Install Python dependencies
```
cd NoticeIQ
pip install -r requirements.txt
```
(`requirements.txt` = Flask + mysql-connector-python only.)

### 5. Run the app
```
python app.py
```
On first run it auto-creates the tables and seeds demo data (3 users + 8 notices).

### 6. Open in browser
Go to **http://localhost:5000**

## Demo logins
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@noticeiq.local | admin123 |
| Student (Aarav, TE Computer) | student@noticeiq.local | student123 |
| Student (Riya, SE Mechanical) | student2@noticeiq.local | student123 |

## Optional: run the tests
```
python -m compileall .
python -m unittest test_noticeiq.py
```

## Common issues
- **"Access denied for user 'root'"** → your root needs a password (put it in `.env`)
  or root uses socket auth; create a MySQL user with a password and use it in `.env`.
- **"Can't connect to MySQL server"** → MySQL isn't running; start the service.
- **Port 5000 busy** → change `PORT` in `.env` (e.g. `PORT=8000`).
