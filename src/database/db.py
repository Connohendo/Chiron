"""SQLite database layer for Chiron – stores jobs and email config locally."""

import sqlite3
from pathlib import Path

DB_DIR = Path.home() / ".chiron"
DB_PATH = DB_DIR / "chiron.db"


def _ensure_dir():
    DB_DIR.mkdir(parents=True, exist_ok=True)


def get_connection():
    """Return a connection with Row factory enabled."""
    _ensure_dir()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            company         TEXT    NOT NULL,
            position        TEXT    DEFAULT '',
            status          TEXT    DEFAULT 'open',
            email_subject   TEXT    DEFAULT '',
            email_from      TEXT    DEFAULT '',
            email_snippet   TEXT    DEFAULT '',
            date_detected   TEXT    DEFAULT (datetime('now', 'localtime')),
            date_updated    TEXT    DEFAULT (datetime('now', 'localtime')),
            notes           TEXT    DEFAULT ''
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS email_config (
            id              INTEGER PRIMARY KEY CHECK (id = 1),
            email_address   TEXT    NOT NULL,
            imap_server     TEXT    NOT NULL,
            imap_port       INTEGER DEFAULT 993,
            app_password    TEXT    NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key     TEXT PRIMARY KEY,
            value   TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS processed_emails (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id      TEXT    UNIQUE NOT NULL,
            processed_at    TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.commit()
    conn.close()


# ── App settings (key-value) ──────────────────────────────────────────────────

def get_setting(key: str) -> str | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT value FROM app_settings WHERE key = ?", (key,)
    ).fetchone()
    conn.close()
    return row["value"] if row else None


def save_setting(key: str, value: str):
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
        (key, value),
    )
    conn.commit()
    conn.close()


# ── Email config ─────────────────────────────────────────────────────────────

def get_email_config():
    conn = get_connection()
    row = conn.execute("SELECT * FROM email_config WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else None


def save_email_config(email_address, imap_server, imap_port, app_password):
    conn = get_connection()
    conn.execute(
        """INSERT OR REPLACE INTO email_config
           (id, email_address, imap_server, imap_port, app_password)
           VALUES (1, ?, ?, ?, ?)""",
        (email_address, imap_server, imap_port, app_password),
    )
    conn.commit()
    conn.close()


# ── Jobs ─────────────────────────────────────────────────────────────────────

def add_job(company, position, status, email_subject, email_from, email_snippet):
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO jobs
           (company, position, status, email_subject, email_from, email_snippet)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (company, position, status, email_subject, email_from, email_snippet),
    )
    conn.commit()
    job_id = cur.lastrowid
    conn.close()
    return job_id


def update_job_status(job_id, new_status):
    conn = get_connection()
    conn.execute(
        "UPDATE jobs SET status = ?, date_updated = datetime('now','localtime') WHERE id = ?",
        (new_status, job_id),
    )
    conn.commit()
    conn.close()


def get_all_jobs():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM jobs ORDER BY date_updated DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def find_job_by_company(company):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM jobs WHERE LOWER(company) = LOWER(?) ORDER BY date_updated DESC LIMIT 1",
        (company,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_job(job_id):
    conn = get_connection()
    conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()


# ── Processed-email deduplication ────────────────────────────────────────────

def is_email_processed(message_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM processed_emails WHERE message_id = ?", (message_id,)
    ).fetchone()
    conn.close()
    return row is not None


def mark_email_processed(message_id):
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO processed_emails (message_id) VALUES (?)",
        (message_id,),
    )
    conn.commit()
    conn.close()
