#!/usr/bin/env python3
"""
Memory utilities for agents (SQLite-backed persistence).

Provides small, focused helpers to persist agent state without introducing heavy
dependencies. Safe to import from agents.
"""

import os
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional


class SoloLevelingDB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS user_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    level INTEGER NOT NULL,
                    xp INTEGER NOT NULL,
                    streak INTEGER NOT NULL,
                    last_active_date TEXT
                )
                """
            )
            # Seed single row if empty
            c.execute("SELECT COUNT(*) FROM user_state")
            if c.fetchone()[0] == 0:
                c.execute(
                    "INSERT INTO user_state (id, level, xp, streak, last_active_date) VALUES (1, ?, ?, ?, ?)",
                    (1, 0, 0, None),
                )
            conn.commit()

    def get_user_state(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT level, xp, streak, last_active_date FROM user_state WHERE id = 1")
            row = c.fetchone()
            if not row:
                return {"level": 1, "xp": 0, "streak": 0, "last_active_date": None}
            return {"level": row[0], "xp": row[1], "streak": row[2], "last_active_date": row[3]}

    def save_user_state(self, level: int, xp: int, streak: int, last_active_date: Optional[str]):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                "UPDATE user_state SET level = ?, xp = ?, streak = ?, last_active_date = ? WHERE id = 1",
                (level, xp, streak, last_active_date),
            )
            conn.commit()


class TraderMemoryDB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS momentum_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    signal_strength TEXT,
                    momentum_6h_pct REAL,
                    momentum_24h_pct REAL,
                    current_price REAL,
                    inserted_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def log_momentum_signals(self, signals: Dict[str, Any]):
        if not isinstance(signals, dict):
            return
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            for symbol, data in signals.items():
                c.execute(
                    """
                    INSERT INTO momentum_signals (symbol, signal_strength, momentum_6h_pct, momentum_24h_pct, current_price, inserted_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        symbol,
                        data.get("signal_strength"),
                        float(data.get("momentum_6h_pct", 0) or 0),
                        float(data.get("momentum_24h_pct", 0) or 0),
                        float(data.get("current_price", 0) or 0),
                        now,
                    ),
                )
            conn.commit()


