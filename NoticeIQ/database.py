"""
Database layer for NoticeIQ.

Uses mysql-connector-python with direct SQL queries (no ORM) so the database
logic stays simple and easy to explain during a viva.
"""
import mysql.connector

import config


def _server_connection():
    """Connect to the MySQL server (without selecting a database)."""
    return mysql.connector.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
    )


def get_connection():
    """Return a connection to the noticeiq database."""
    return mysql.connector.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
    )


def init_db():
    """Create the database and all tables if they do not already exist."""
    # 1. Ensure the database exists.
    conn = _server_connection()
    cur = conn.cursor()
    cur.execute(
        f"CREATE DATABASE IF NOT EXISTS {config.DB_NAME} "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    conn.commit()
    cur.close()
    conn.close()

    # 2. Ensure tables exist.
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(120) NOT NULL,
            email VARCHAR(160) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'student',
            branch VARCHAR(120),
            year VARCHAR(20),
            division VARCHAR(10),
            subjects_json TEXT,
            interests_json TEXT,
            created_at DATETIME
        ) ENGINE=InnoDB
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS notices (
            id INT PRIMARY KEY AUTO_INCREMENT,
            title VARCHAR(255) NOT NULL,
            body TEXT NOT NULL,
            category VARCHAR(60),
            source VARCHAR(160),
            target_branches_json TEXT,
            target_years_json TEXT,
            target_divisions_json TEXT,
            topics_json TEXT,
            deadline DATE NULL,
            action_required BOOLEAN DEFAULT FALSE,
            mandatory BOOLEAN DEFAULT FALSE,
            created_at DATETIME,
            updated_at DATETIME
        ) ENGINE=InnoDB
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS notice_states (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            notice_id INT NOT NULL,
            is_read BOOLEAN DEFAULT FALSE,
            is_saved BOOLEAN DEFAULT FALSE,
            UNIQUE KEY uniq_user_notice (user_id, notice_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (notice_id) REFERENCES notices(id) ON DELETE CASCADE
        ) ENGINE=InnoDB
        """
    )

    conn.commit()
    cur.close()
    conn.close()


# --- Small query helpers ----------------------------------------------------

def query_all(sql, params=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def query_one(sql, params=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params or ())
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def execute(sql, params=None):
    """Run an INSERT/UPDATE/DELETE and return the last row id."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    conn.commit()
    last_id = cur.lastrowid
    cur.close()
    conn.close()
    return last_id
