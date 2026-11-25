"""学習アドバイスの受け渡し（API不使用）。

アプリは演習ログを「Claudeに渡すテキスト」に書き出し、Claude（チャット or Claude Code）が
sharoshi-advisor スキルで分析した結果（score-advice 形式のJSON）を取り込むだけ。
"""
from __future__ import annotations

import json
import re
from collections import defaultdict

from . import db
from .exam import SUBJECTS, TARGET_SECONDS, Store
from .stats import latest_by_question, overview, score_mock, subject_stats, topic_stats

EXPORT_HEADER = "【Score学習ログ】"

# Claudeに渡すテキストの冒頭。スキル未導入でも動くよう出力形式も書いておく。
EXPORT_INSTRUCTIONS = """sharoshi-advisor スキルで、以下の社労士試験の演習ログを分析して学習アドバイスをください。
（スキルが無い場合: 社労士試験の専門家として、足切り(科目別基準点)リスクを最優先に、ログの数字を根拠に助言し、
最後に必ず次の形式のコードブロックを付けてください）
```score-advice
{"summary": "4〜6文の要約", "focus": [{"topic_id": "論点ID or 空文字", "title": "", "subject": "科目名", "reason": ""}], "actions": ["次にやること"]}
```"""


def build_context(store: Store, settings: dict, session_id: int | None = None) -> dict:
    answers = [a for a in db.all_answers() if a["question_id"] in store.questions]
    done = [a for a in answers if not a["skipped"]]

    times = defaultdict(list)
    for a in done:
        if a["time_ms"]:
            times[store.questions[a["question_id"]]["format"]].append(a["time_ms"] / 1000)
    avg_time = {f: {"avg_sec": round(sum(v) / len(v)), "target_sec": TARGET_SECONDS[f], "n": len(v)}
                for f, v in times.items()}

    fs = defaultdict(lambda: [0, 0])
    for a in done:
        q = store.questions[a["question_id"]]
        k = f'{q["format"]}/{SUBJECTS[q["subject"]]}'
        fs[k][0] += a["correct_units"]
        fs[k][1] += a["total_units"]

    tstats = topic_stats(store)
    topics = []
    for tid, v in sorted(tstats.items(), key=lambda kv: (kv[1]["pct"] or 0)):
        t = store.topics.get(tid)
        topics.append({"topic_id": tid, "name": t.name if t else tid,
                       "subject": SUBJECTS.get(t.subject, "") if t else "",
                       "correct": v["cu"], "total": v["tu"], "pct": v["pct"]})

    wrong_topics = defaultdict(int)
    for qid, a in latest_by_question(answers).items():
        if a["correct_units"] < a["total_units"]:
            wrong_topics[store.questions[qid]["topic"]] += 1

    ctx = {
        "overview": overview(store, settings),
        "subjects": [{k: r[k] for k in ("name", "pct", "cu", "tu", "touched", "total")}
                     for r in subject_stats(store, settings)],
        "format_subject": {k: f"{v[0]}/{v[1]}" for k, v in fs.items()},
        "topics": topics,
        "still_wrong_by_topic": dict(wrong_topics),
        "avg_time": avg_time,
        "mock_results": mock_results(store, settings),
        "pass_criteria": {
            "sentaku": f'総得点{settings["pass_sentaku_total"]}・各{settings["pass_sentaku_each"]}',
            "takuitsu": f'総得点{settings["pass_takuitsu_total"]}・各{settings["pass_takuitsu_each"]}',
        },
        "exam_date": settings["exam_date"],
    }
    if session_id is not None:
        ctx["focus_session"] = session_detail(store, session_id)
    return ctx


def mock_results(store: Store, settings: dict) -> list[dict]:
    out = []
    for s in db.recent_sessions(50):
        if s["mode"] != "mock":
            continue
        sess = db.get_session(s["id"])
        sc = score_mock(store, settings, sess["question_ids"], db.session_answers(s["id"]))
        out.append({"title": s["title"], "date": s["started_at"][:10],
                    "sentaku": f'{sc["sentaku_total"]}/{sc["sentaku_max"]}',
                    "takuitsu": f'{sc["takuitsu_total"]}/{sc["takuitsu_max"]}',
                    "below_base": [r["name"] + "(選択)" for r in sc["sentaku"] if not r["ok"]]
                                  + [r["name"] + "(択一)" for r in sc["takuitsu"] if not r["ok"]]})
    return out


def session_detail(store: Store, sid: int) -> dict | None:
    sess = db.get_session(sid)
    if not sess:
        return None
    ans = db.session_answers(sid)
    items = []
    for i, qid in enumerate(sess["question_ids"]):
        q = store.questions.get(qid)
        a = ans.get(i)
        if not q:
            continue
        items.append({
            "q": f'{q["exam"]} {q["format"]}問{q["number"]}', "topic": q["topic"],
            "result": "skip" if not a or a["skipped"] else f'{a["correct_units"]}/{a["total_units"]}',
            "sec": round(a["time_ms"] / 1000) if a and a["time_ms"] else None,
        })
    return {"title": sess["title"], "mode": sess["mode"], "items": items}


def export_text(ctx: dict, scope: str) -> str:
    return (f"{EXPORT_HEADER} scope={scope}\n{EXPORT_INSTRUCTIONS}\n\n```json\n"
            + json.dumps(ctx, ensure_ascii=False, separators=(",", ":")) + "\n```")


class AdviceParseError(ValueError):
    pass


def parse_advice(text: str) -> dict:
    """Claudeの返答（全文コピーでも可）から score-advice JSON を取り出して検証する。"""
    candidates = re.findall(r"```(?:score-advice|json)?\s*\n(.*?)```", text, flags=re.S)
    if not candidates:
        m = re.search(r"\{.*\}", text, flags=re.S)
        candidates = [m.group(0)] if m else []
    for c in reversed(candidates):  # 最後のブロックを優先
        try:
            data = json.loads(c)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and "summary" in data:
            return _validate(data)
    raise AdviceParseError("score-advice 形式のJSONが見つかりませんでした。Claudeの返答を最後まで全部コピーして貼り付けてください。")


def _validate(d: dict) -> dict:
    if not isinstance(d.get("summary"), str) or not d["summary"].strip():
        raise AdviceParseError("summary がありません")
    focus = []
    for f in d.get("focus") or []:
        if isinstance(f, dict) and f.get("title"):
            focus.append({k: str(f.get(k) or "") for k in ("topic_id", "title", "subject", "reason")})
    actions = [str(a) for a in (d.get("actions") or []) if a]
    return {"summary": d["summary"].strip(), "focus": focus, "actions": actions}
