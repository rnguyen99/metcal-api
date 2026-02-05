"""Initialize the SQLite database with required tables and seed data."""
from __future__ import annotations

import sqlite3

from auth import get_password_hash
from config import get_settings
from logger import configure_logging, get_logger

configure_logging()
LOGGER = get_logger("init_db")
SETTINGS = get_settings()

ASSET_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS asset (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
"""

USER_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);
"""


def ensure_tables(connection: sqlite3.Connection) -> None:
    connection.execute(ASSET_TABLE_SQL)
    connection.execute(USER_TABLE_SQL)
    connection.commit()


def seed_admin_user(connection: sqlite3.Connection) -> None:
    cur = connection.execute("SELECT COUNT(1) AS count FROM user")
    count = cur.fetchone()["count"]
    if count:
        LOGGER.info("User table already populated; skipping admin seed")
        return
    hashed_password = get_password_hash("password")
    connection.execute(
        "INSERT INTO user (username, password) VALUES (?, ?)",
        ("admin", hashed_password),
    )
    connection.commit()
    LOGGER.info("Seeded default admin user with username 'admin'")


def main() -> None:
    LOGGER.info("Initializing database at %s", SETTINGS.database_path)
    conn = sqlite3.connect(SETTINGS.database_path)
    conn.row_factory = sqlite3.Row
    try:
        ensure_tables(conn)
        seed_admin_user(conn)
    finally:
        conn.close()
    LOGGER.info("Database initialization complete")


if __name__ == "__main__":
    main()
