"""
db_utils.py
SQLite-backed persistence for ARIA's Web App conversation sessions.

Why this exists: the Flask app previously kept `sessions: dict[str, AriaChatbot]`
purely in memory. That's fine while the Flask process itself keeps running,
but any process restart (a crash, gunicorn recycling a worker, `python app.py`
being stopped and started again locally) wiped every active conversation and
session setting (persona, RAG toggle). SQLite gives us an on-disk store that
survives all of that.

Scope note: this protects against the *process* restarting while the
container/machine stays the same. On free tiers of platforms like Render or
Railway, a full redeploy usually wipes the container's disk entirely (unless
you've attached a persistent volume, which is typically a paid feature) — so
this doesn't make chat history survive a redeploy on those free tiers. It's
still a real improvement for local development and for crash recovery.
"""

import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.environ.get("ARIA_DB_PATH", "aria_chat.db")


@contextmanager
def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _init_db():
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session
            ON messages (session_id)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS session_settings (
                session_id TEXT PRIMARY KEY,
                persona_key TEXT NOT NULL DEFAULT 'default',
                custom_prompt TEXT,
                rag_enabled INTEGER NOT NULL DEFAULT 0,
                tools_enabled INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL
            )
        """)
        # Older databases created before tools_enabled existed won't have the
        # column — add it on the fly rather than forcing a manual migration.
        try:
            conn.execute("ALTER TABLE session_settings ADD COLUMN tools_enabled INTEGER NOT NULL DEFAULT 1")
        except sqlite3.OperationalError:
            pass  # column already exists


_init_db()  # runs once at import time, creates the DB file/tables if missing


# ---------- Conversation history ----------

def load_messages(session_id: str) -> list:
    """Return this session's conversation history as [{"role", "content"}, ...], oldest first."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,)
        ).fetchall()
    return [{"role": role, "content": content} for role, content in rows]


def append_message(session_id: str, role: str, content: str):
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, datetime.now().isoformat(timespec="seconds"))
        )


def clear_messages(session_id: str):
    with _get_conn() as conn:
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))


# ---------- Per-session settings (persona, RAG toggle) ----------

def load_settings(session_id: str) -> dict:
    """Return {"persona_key", "custom_prompt", "rag_enabled", "tools_enabled"} — sensible defaults if nothing saved yet."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT persona_key, custom_prompt, rag_enabled, tools_enabled FROM session_settings WHERE session_id = ?",
            (session_id,)
        ).fetchone()
    if row is None:
        return {"persona_key": "default", "custom_prompt": None, "rag_enabled": False, "tools_enabled": True}
    return {
        "persona_key": row[0],
        "custom_prompt": row[1],
        "rag_enabled": bool(row[2]),
        "tools_enabled": bool(row[3]),
    }


def save_settings(session_id: str, persona_key: str, custom_prompt: str, rag_enabled: bool, tools_enabled: bool = True):
    with _get_conn() as conn:
        conn.execute("""
            INSERT INTO session_settings (session_id, persona_key, custom_prompt, rag_enabled, tools_enabled, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                persona_key = excluded.persona_key,
                custom_prompt = excluded.custom_prompt,
                rag_enabled = excluded.rag_enabled,
                tools_enabled = excluded.tools_enabled,
                updated_at = excluded.updated_at
        """, (session_id, persona_key, custom_prompt, int(rag_enabled), int(tools_enabled),
              datetime.now().isoformat(timespec="seconds")))