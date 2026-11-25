"""Claude API による学習アドバイス生成（専属の家庭教師）。"""
from __future__ import annotations

import json
import os
from collections import defaultdict

import anthropic

from . import db
from .exam import SUBJECTS, TARGET_SECONDS, Store
from .stats import latest_by_question, overview, subject_stats, topic_stats

MODEL = os.environ.get("SHAROSHI_MODEL", "claude-opus-5-5")

SYSTEM_PROMPT = """あなたは社会保険労務士試験の専門家で、1人の受験生専属の家庭教師です。
受験生の演習ログ（正誤・回答時間・科目別/論点別の成績・模試結果）を分析し、次に何をすべきかを具体的に助言します。

社労士試験の前提知識:
- 選択式（8問・各5空欄・80分、1空欄1点・科目5点満点・計40点）と択一式（70問・5肢択一・210分、科目10点満点・計70点）。
- 合格には総得点の基準に加えて、全科目で基準点（選択式は原則各3点、択一式は原則各4点、年度により補正）を満たす必要がある。1科目でも足切りに掛かれば不合格になるため、「得意科目を伸ばす」より「どの科目も基準点を割らない」ことが優先される。
- 選択式は条文・判例・白書の穴埋めで、1科目で2点以下を取る事故が最大のリスク。特に労一・社一の一般常識は対策しにくい。
- 択一式の一般常識は労一と社一の合算10点で基準点判定される。
- 年金2法（国年・厚年）は相互に関連し、配点も大きい。徴収法は労災・雇用の択一式各3問程度に含まれる。
- 法改正点と統計・白書は直前期に重点化される。

助言の方針:
- データに基づいて書く。数字（正答率・回答数・残り日数）を根拠として示す。
- 回答数が少ない科目・論点は「まだ判断材料が少ない」と明記し、断定しない。
- 試験までの残り日数に応じて優先順位を変える（例: 直前期は新しい範囲に手を広げず誤答の見直しを優先）。
- 足切りリスクのある科目を最優先で指摘する。
- 回答時間が目安（択一1問約3分、選択1問約10分）から大きく外れていれば触れる。
- 一般論の勉強法ではなく、この受験生のログから読み取れることだけを書く。
- 日本語で、簡潔に。summary は4〜6文程度。"""

ADVICE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string", "description": "全体の状況と最優先事項の要約（4〜6文）"},
        "focus": {
            "type": "array",
            "description": "重点項目（優先度順、3〜5件）",
            "items": {
                "type": "object",
                "properties": {
                    "topic_id": {"type": "string", "description": "論点ID（入力の topics にあるもの。科目全体なら空文字）"},
                    "title": {"type": "string"},
                    "subject": {"type": "string", "description": "科目名（例: 健保）"},
                    "reason": {"type": "string"},
                },
                "required": ["topic_id", "title", "subject", "reason"],
                "additionalProperties": False,
            },
        },
        "actions": {
            "type": "array",
            "description": "次の学習セッションでやること（具体的に、2〜4件）",
            "items": {"type": "string"},
        },
    },
    "required": ["summary", "focus", "actions"],
    "additionalProperties": False,
}


def api_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def build_context(store: Store, settings: dict, mock_results: list[dict]) -> dict:
    answers = [a for a in db.all_answers() if a["question_id"] in store.questions]
    done = [a for a in answers if not a["skipped"]]

    # 形式別の平均回答時間
    times = defaultdict(list)
    for a in done:
        if a["time_ms"]:
            times[store.questions[a["question_id"]]["format"]].append(a["time_ms"] / 1000)
    avg_time = {f: {"avg_sec": round(sum(v) / len(v)), "target_sec": TARGET_SECONDS[f], "n": len(v)}
                for f, v in times.items()}

    # 形式×科目
    fs = defaultdict(lambda: [0, 0])
    for a in done:
        q = store.questions[a["question_id"]]
        k = f'{q["format"]}/{SUBJECTS[q["subject"]]}'
        fs[k][0] += a["correct_units"]
        fs[k][1] += a["total_units"]

    # 論点別（回答のあるもの）
    tstats = topic_stats(store)
    topics = []
    for tid, v in sorted(tstats.items(), key=lambda kv: (kv[1]["pct"] or 0)):
        t = store.topics.get(tid)
        topics.append({"topic_id": tid, "name": t.name if t else tid,
                       "subject": SUBJECTS.get(t.subject, "") if t else "",
                       "correct": v["cu"], "total": v["tu"], "answers": v["n"], "pct": v["pct"]})

    # 現在誤答のままの問題（論点別件数）
    wrong_topics = defaultdict(int)
    for qid, a in latest_by_question(answers).items():
        if a["correct_units"] < a["total_units"]:
            wrong_topics[store.topic_name(store.questions[qid]["topic"])] += 1

    return {
        "overview": overview(store, settings),
        "subjects": [{k: r[k] for k in ("name", "pct", "cu", "tu", "touched", "total")}
                     for r in subject_stats(store, settings)],
        "format_subject": {k: {"correct": v[0], "total": v[1]} for k, v in fs.items()},
        "topics": topics,
        "still_wrong_by_topic": dict(wrong_topics),
        "avg_time": avg_time,
        "mock_results": mock_results,
        "pass_criteria": {
            "sentaku_total": settings["pass_sentaku_total"], "sentaku_each": settings["pass_sentaku_each"],
            "takuitsu_total": settings["pass_takuitsu_total"], "takuitsu_each": settings["pass_takuitsu_each"],
        },
        "exam_date": settings["exam_date"],
    }


def generate_advice(context: dict, focus_note: str = "") -> dict:
    """アドバイスを生成して dict を返す。失敗時は例外を投げる。"""
    client = anthropic.Anthropic()
    user = "以下は私の演習ログの集計です。分析して学習方針をアドバイスしてください。\n"
    if focus_note:
        user += f"\n特に注目してほしい点: {focus_note}\n"
    user += "\n```json\n" + json.dumps(context, ensure_ascii=False, indent=1) + "\n```"

    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user}],
        output_config={
            "effort": "medium",
            "format": {"type": "json_schema", "schema": ADVICE_SCHEMA},
        },
        # 安全分類器による辞退時はサーバー側で別モデルに自動フォールバック
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("モデルが応答を辞退しました。時間をおいて再生成してください。")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("出力が上限に達しました。再生成してください。")
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)
