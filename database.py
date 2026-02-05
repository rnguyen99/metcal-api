"""SQLite helper utilities."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Generator, Iterable, Optional

from config import get_settings

_SETTINGS = get_settings()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_SETTINGS.database_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


def fetch_user_by_username(conn: sqlite3.Connection, username: str) -> Optional[sqlite3.Row]:
    cur = conn.execute("SELECT id, username, password FROM user WHERE username = ?", (username,))
    return cur.fetchone()


def fetch_user_by_id(conn: sqlite3.Connection, user_id: int) -> Optional[sqlite3.Row]:
    cur = conn.execute("SELECT id, username FROM user WHERE id = ?", (user_id,))
    return cur.fetchone()


def fetch_asset_by_id(conn: sqlite3.Connection, asset_id: int) -> Optional[sqlite3.Row]:
    cur = conn.execute("SELECT id, name FROM asset WHERE id = ?", (asset_id,))
    return cur.fetchone()


def fetch_all_assets(conn: sqlite3.Connection) -> Iterable[sqlite3.Row]:
    cur = conn.execute("SELECT id, name FROM asset ORDER BY id ASC")
    return cur.fetchall()


def create_asset(conn: sqlite3.Connection, name: str) -> int:
    cur = conn.execute("INSERT INTO asset (name) VALUES (?)", (name,))
    conn.commit()
    return cur.lastrowid


def update_asset(conn: sqlite3.Connection, asset_id: int, name: str) -> bool:
    cur = conn.execute("UPDATE asset SET name = ? WHERE id = ?", (name, asset_id))
    conn.commit()
    return cur.rowcount > 0
