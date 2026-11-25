"""SQLite: 回答ログ・セッション・アドバイス・設定。"""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from .exam import DATA_DIR

DB_PATH = Path(os.environ.get("SHAROSHI_DB", DATA_DIR / "app.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mode TEXT NOT NULL,            -- practice / review / mock
    title TEXT NOT NULL,
    question_ids TEXT NOT NULL,    -- JSON array
    started_at TEXT NOT NULL,
    finished_at TEXT
);
CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    question_id TEXT NOT NULL,
    idx INTEGER NOT NULL,
    selected TEXT,                 -- 択一: "C" / 選択: JSON {"A":3,...} / スキップ: NULL
    skipped INTEGER NOT NULL DEFAULT 0,
    correct_units INTEGER NOT NULL,  -- 択一: 0/1, 選択: 正解した空欄数
    total_units INTEGER NOT NULL,    -- 択一: 1,   選択: 5
    time_ms INTEGER,
    answered_at TEXT NOT NULL,
    UNIQUE(session_id, idx)
);
CREATE INDEX IF NOT EXISTS idx_answers_q ON answers(question_id);
CREATE TABLE IF NOT EXISTS advice (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL,           -- overall / session:<id>
    content TEXT NOT NULL,         -- JSON
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

DEFAULT_SETTINGS = {
    "exam_date": "2027-08-22",       # 例年8月第4日曜。公式発表で要確認
    "mock_exam": "令和8年度",        # 模試用に分野別演習から除外する試験回（最新年度を取っておく）
    "law_baseline": "2027-04-16",    # 法令基準日（例年4月中旬施行のものまで）
    "per_session": "10",
    "include_uncertain": "1",        # 法改正「要確認」の問題も出題する
    "pass_sentaku_total": "25",
    "pass_sentaku_each": "3",
    "pass_takuitsu_total": "44",
    "pass_takuitsu_each": "4",
}


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@contextmanager
def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with conn() as c:
        c.executescript(SCHEMA)
        for k, v in DEFAULT_SETTINGS.items():
            c.execute("INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)", (k, v))


def get_settings() -> dict[str, str]:
    with conn() as c:
        return {r["key"]: r["value"] for r in c.execute("SELECT key, value FROM settings")}


def save_settings(values: dict[str, str]) -> None:
    with conn() as c:
        for k, v in values.items():
            if k in DEFAULT_SETTINGS:
                c.execute("INSERT OR REPLACE INTO settings(key, value) VALUES (?, ?)", (k, v))


def create_session(mode: str, title: str, qids: list[str]) -> int:
    with conn() as c:
        cur = c.execute(
            "INSERT INTO sessions(mode, title, question_ids, started_at) VALUES (?, ?, ?, ?)",
            (mode, title, json.dumps(qids), now()),
        )
        return cur.lastrowid


def get_session(sid: int) -> dict | None:
    with conn() as c:
        r = c.execute("SELECT * FROM sessions WHERE id = ?", (sid,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["question_ids"] = json.loads(d["question_ids"])
    return d


def finish_session(sid: int) -> None:
    with conn() as c:
        c.execute("UPDATE sessions SET finished_at = COALESCE(finished_at, ?) WHERE id = ?", (now(), sid))


def recent_sessions(limit: int = 10) -> list[dict]:
    with conn() as c:
        rows = c.execute(
            """SELECT s.*, COUNT(a.id) AS n_answered,
                      COALESCE(SUM(a.correct_units),0) AS cu, COALESCE(SUM(a.total_units),0) AS tu
               FROM sessions s LEFT JOIN answers a ON a.session_id = s.id
               GROUP BY s.id ORDER BY s.id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def record_answer(sid: int, idx: int, qid: str, selected, skipped: bool,
                  correct_units: int, total_units: int, time_ms: int | None) -> None:
    sel = None if selected is None else (selected if isinstance(selected, str) else json.dumps(selected))
    with conn() as c:
        c.execute(
            """INSERT OR REPLACE INTO answers
               (session_id, question_id, idx, selected, skipped, correct_units, total_units, time_ms, answered_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sid, qid, idx, sel, int(skipped), correct_units, total_units, time_ms, now()),
        )


def session_answers(sid: int) -> dict[int, dict]:
    with conn() as c:
        rows = c.execute("SELECT * FROM answers WHERE session_id = ? ORDER BY idx", (sid,)).fetchall()
    out = {}
    for r in rows:
        d = dict(r)
        if d["selected"] and d["selected"].startswith("{"):
            d["selected"] = json.loads(d["selected"])
        out[d["idx"]] = d
    return out


def all_answers() -> list[dict]:
    with conn() as c:
        rows = c.execute(
            """SELECT a.*, s.mode FROM answers a JOIN sessions s ON s.id = a.session_id
               ORDER BY a.id"""
        ).fetchall()
    return [dict(r) for r in rows]


def save_advice(scope: str, content: dict) -> None:
    with conn() as c:
        c.execute("INSERT INTO advice(scope, content, created_at) VALUES (?, ?, ?)",
                  (scope, json.dumps(content, ensure_ascii=False), now()))


def latest_advice(scope: str) -> dict | None:
    with conn() as c:
        r = c.execute("SELECT * FROM advice WHERE scope = ? ORDER BY id DESC LIMIT 1", (scope,)).fetchone()
    if not r:
        return None
    d = json.loads(r["content"])
    d["created_at"] = r["created_at"]
    return d
