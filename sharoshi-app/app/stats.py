"""成績集計・出題選択・模試採点。"""
from __future__ import annotations

import random
from collections import defaultdict
from datetime import date, datetime, timedelta

from . import db
from .exam import SUBJECTS, TAKUITSU_GROUP_NAMES, TAKUITSU_GROUPS, Store


def _pct(c: int, t: int) -> int | None:
    return round(100 * c / t) if t else None


def eligible_questions(store: Store, settings: dict, *, for_mock: bool = False) -> list[dict]:
    """分野別演習で出してよい問題。模試用の試験回・法改正で使えない問題を除く。"""
    mock = settings.get("mock_exam", "")
    include_uncertain = settings.get("include_uncertain", "1") == "1"
    out = []
    for q in store.questions.values():
        if q.get("law_check") == "revised":
            continue
        if q.get("law_check") == "uncertain" and not include_uncertain:
            continue
        if not for_mock and mock and q["exam"] == mock:
            continue
        out.append(q)
    return out


def latest_by_question(answers: list[dict]) -> dict[str, dict]:
    latest: dict[str, dict] = {}
    for a in answers:
        if a["skipped"]:
            continue
        latest[a["question_id"]] = a
    return latest


def select_questions(store: Store, settings: dict, *, subject: str = "", topic: str = "",
                     fmt: str = "", order: str = "smart", count: int = 10) -> list[str]:
    pool = eligible_questions(store, settings)
    if subject:
        pool = [q for q in pool if q["subject"] == subject]
    if topic:
        pool = [q for q in pool if q["topic"] == topic]
    if fmt:
        pool = [q for q in pool if q["format"] == fmt]
    latest = latest_by_question(db.all_answers())

    def is_wrong(q):
        a = latest.get(q["id"])
        return a is not None and a["correct_units"] < a["total_units"]

    random.shuffle(pool)
    if order == "wrong":
        pool = [q for q in pool if is_wrong(q)]
    elif order == "new":
        pool = [q for q in pool if q["id"] not in latest]
    elif order == "smart":
        # 誤答 → 未着手 → 正解済み(古い順)
        def key(q):
            a = latest.get(q["id"])
            if a is None:
                return (1, "")
            if a["correct_units"] < a["total_units"]:
                return (0, a["answered_at"])
            return (2, a["answered_at"])
        pool.sort(key=key)
    return [q["id"] for q in pool[:count]]


def subject_stats(store: Store, settings: dict) -> list[dict]:
    answers = [a for a in db.all_answers() if not a["skipped"] and a["question_id"] in store.questions]
    pool = eligible_questions(store, settings)
    total_q = defaultdict(int)
    for q in pool:
        total_q[q["subject"]] += 1
    agg = defaultdict(lambda: {"cu": 0, "tu": 0, "n": 0, "qs": set()})
    for a in answers:
        q = store.questions[a["question_id"]]
        g = agg[q["subject"]]
        g["cu"] += a["correct_units"]
        g["tu"] += a["total_units"]
        g["n"] += 1
        g["qs"].add(q["id"])
    rows = []
    for sid, name in SUBJECTS.items():
        g = agg[sid]
        rows.append({
            "id": sid, "name": name, "pct": _pct(g["cu"], g["tu"]),
            "cu": g["cu"], "tu": g["tu"], "n": g["n"],
            "touched": len(g["qs"]), "total": total_q[sid],
        })
    return rows


def topic_stats(store: Store) -> dict[str, dict]:
    answers = [a for a in db.all_answers() if not a["skipped"] and a["question_id"] in store.questions]
    agg = defaultdict(lambda: {"cu": 0, "tu": 0, "n": 0})
    for a in answers:
        t = store.questions[a["question_id"]]["topic"]
        agg[t]["cu"] += a["correct_units"]
        agg[t]["tu"] += a["total_units"]
        agg[t]["n"] += 1
    return {t: {**v, "pct": _pct(v["cu"], v["tu"])} for t, v in agg.items()}


def overview(store: Store, settings: dict) -> dict:
    answers = [a for a in db.all_answers() if a["question_id"] in store.questions]
    done = [a for a in answers if not a["skipped"]]
    cu = sum(a["correct_units"] for a in done)
    tu = sum(a["total_units"] for a in done)
    today = date.today().isoformat()
    today_n = sum(1 for a in answers if a["answered_at"].startswith(today))
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    recent = [a for a in done if a["answered_at"] >= week_ago]
    rcu = sum(a["correct_units"] for a in recent)
    rtu = sum(a["total_units"] for a in recent)
    pool = eligible_questions(store, settings)
    touched = {a["question_id"] for a in done}
    try:
        days_left = (date.fromisoformat(settings["exam_date"]) - date.today()).days
    except ValueError:
        days_left = None
    wrong_now = sum(1 for a in latest_by_question(answers).values() if a["correct_units"] < a["total_units"])
    return {
        "answers": len(done), "pct": _pct(cu, tu), "recent_pct": _pct(rcu, rtu), "recent_n": len(recent),
        "today": today_n, "pool": len(pool), "touched": len(touched & {q["id"] for q in pool}),
        "days_left": days_left, "wrong_now": wrong_now,
    }


def score_mock(store: Store, settings: dict, qids: list[str], answers: dict[int, dict]) -> dict:
    """模試の採点。選択式は空欄1つ1点（科目5点満点）、択一式は1問1点（科目10点満点）。"""
    sen = defaultdict(lambda: [0, 0])
    tak = defaultdict(lambda: [0, 0])
    for i, qid in enumerate(qids):
        q = store.questions.get(qid)
        if not q:
            continue
        a = answers.get(i)
        cu = a["correct_units"] if a and not a["skipped"] else 0
        if q["format"] == "選択式":
            sen[q["subject"]][0] += cu
            sen[q["subject"]][1] += len(q["blanks"])
        else:
            grp = next(g for g, subs in TAKUITSU_GROUPS.items() if q["subject"] in subs)
            tak[grp][0] += cu
            tak[grp][1] += 1
    s_each = int(settings.get("pass_sentaku_each", 3))
    t_each = int(settings.get("pass_takuitsu_each", 4))
    s_rows = [{"name": SUBJECTS[k], "score": v[0], "max": v[1], "ok": v[0] >= s_each}
              for k, v in sen.items()]
    t_rows = [{"name": TAKUITSU_GROUP_NAMES[k], "score": v[0], "max": v[1], "ok": v[0] >= t_each}
              for k, v in tak.items()]
    s_total = sum(r["score"] for r in s_rows)
    t_total = sum(r["score"] for r in t_rows)
    s_need = int(settings.get("pass_sentaku_total", 25))
    t_need = int(settings.get("pass_takuitsu_total", 44))
    full = sum(r["max"] for r in s_rows) == 40 and sum(r["max"] for r in t_rows) == 70
    passed = (s_total >= s_need and t_total >= t_need
              and all(r["ok"] for r in s_rows) and all(r["ok"] for r in t_rows)) if full else None
    return {
        "sentaku": s_rows, "takuitsu": t_rows,
        "sentaku_total": s_total, "sentaku_max": sum(r["max"] for r in s_rows), "sentaku_need": s_need,
        "takuitsu_total": t_total, "takuitsu_max": sum(r["max"] for r in t_rows), "takuitsu_need": t_need,
        "sentaku_each": s_each, "takuitsu_each": t_each, "full": full, "passed": passed,
    }
