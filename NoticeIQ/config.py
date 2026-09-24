"""
Configuration for NoticeIQ.

Reads database credentials from environment variables so that no real
password is ever hard-coded into the source. Sensible defaults are provided
for easy local development (except the password, which defaults to empty).
"""
import os


def _load_dotenv():
    """Tiny .env loader (no external dependency). Loads KEY=VALUE lines."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

# --- Database configuration -------------------------------------------------
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")   # no real password in source
DB_NAME = os.environ.get("DB_NAME", "noticeiq")

# --- Flask configuration ----------------------------------------------------
SECRET_KEY = os.environ.get("SECRET_KEY", "noticeiq-dev-secret-key-change-me")
PORT = int(os.environ.get("PORT", "5000"))
