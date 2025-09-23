"""
SQLite-backed memory for conversations and long-term notes.

Schema:
- messages(id INTEGER PRIMARY KEY, role TEXT, text TEXT, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
- memories(id INTEGER PRIMARY KEY, tag TEXT, content TEXT, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

APIs:
- save_message(role, text)
- recent_messages(n=20)
- save_memory(tag, content)
- search_memories(query, limit=10)
- summarize_thread(): summarize last 50 messages via llm and store as memory(tag="summary")
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import List, Tuple

from .config import load_config
from .llm import generate


def _ensure_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            role TEXT NOT NULL,
            text TEXT NOT NULL,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY,
            tag TEXT NOT NULL,
            content TEXT NOT NULL,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


@contextmanager
def _get_conn():
    cfg = load_config()
    conn = sqlite3.connect(str(cfg.memory_db_path))
    try:
        _ensure_schema(conn)
        yield conn
    finally:
        conn.close()


def save_message(role: str, text: str) -> None:
    with _get_conn() as conn:
        conn.execute("INSERT INTO messages(role, text) VALUES(?, ?)", (role, text))
        conn.commit()


def recent_messages(n: int = 20) -> List[Tuple[int, str, str, str]]:
    with _get_conn() as conn:
        cur = conn.execute(
            "SELECT id, role, text, ts FROM messages ORDER BY id DESC LIMIT ?",
            (n,),
        )
        rows = cur.fetchall()
    return list(reversed(rows))  # chronological order


def save_memory(tag: str, content: str) -> None:
    with _get_conn() as conn:
        conn.execute("INSERT INTO memories(tag, content) VALUES(?, ?)", (tag, content))
        conn.commit()


def search_memories(query: str, limit: int = 10) -> List[Tuple[int, str, str, str]]:
    like = f"%{query}%"
    with _get_conn() as conn:
        cur = conn.execute(
            "SELECT id, tag, content, ts FROM memories WHERE content LIKE ? OR tag LIKE ? ORDER BY id DESC LIMIT ?",
            (like, like, limit),
        )
        rows = cur.fetchall()
    return rows


def _all_message_texts(limit: int = 50) -> str:
    rows = recent_messages(limit)
    lines = []
    for _id, role, text, _ts in rows:
        prefix = "User" if role == "user" else "Assistant"
        lines.append(f"{prefix}: {text}")
    return "\n".join(lines)


def summarize_thread() -> str:
    """Summarize the last 50 messages and store as a memory with tag='summary'."""
    convo = _all_message_texts(50)
    if not convo.strip():
        return ""
    system = (
        "You are Jarvis. Summarize the recent conversation in 5-8 concise bullets. "
        "Capture goals, decisions, follow-ups, and specific entities. Be brief."
    )
    user = f"Conversation to summarize:\n\n{convo}\n\nReturn only the summary bullets."
    summary = generate(system, user)
    if summary and summary.strip():
        save_memory("summary", summary.strip())
    return summary.strip()

