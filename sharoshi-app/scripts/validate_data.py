"""問題データ・動画データの形式チェック（Claude Code のスキルが書いたJSONの検証用）。

  python scripts/validate_data.py                         # data/ 以下をすべて検証
  python scripts/validate_data.py data/questions/R07.json # 指定ファイルだけ
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SUBJECTS = {"roki", "rosai", "koyo", "roippan", "shaippan", "kenpo", "konen", "kokunen"}
LABELS = ["A", "B", "C", "D", "E"]
TAKUITSU_SUBJECT = [(1, 10, {"roki"}), (11, 20, {"rosai"}), (21, 30, {"koyo"}), (31, 40, {"roippan", "shaippan"}),
                    (41, 50, {"kenpo"}), (51, 60, {"konen"}), (61, 70, {"kokunen"})]
SENTAKU_SUBJECT = ["roki", "rosai", "koyo", "roippan", "shaippan", "kenpo", "konen", "kokunen"]


def topic_ids() -> set[str]:
    data = json.loads((DATA / "topics.json").read_text(encoding="utf-8"))
    return {t["id"] for g in data["groups"] for t in g["topics"]}


def check_questions(path: Path, topics: set[str]) -> list[str]:
    errs: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    for k in ("exam", "year_num", "questions"):
        if k not in data:
            errs.append(f"トップレベルに {k} がありません")
    ids = set()
    is_sample = data.get("exam") == "サンプル"
    for q in data.get("questions", []):
        w = f'{q.get("id", "?")}: '
        if q.get("id") in ids:
            errs.append(w + "id が重複")
        ids.add(q.get("id"))
        if q.get("subject") not in SUBJECTS:
            errs.append(w + f'subject が不正 {q.get("subject")}')
        if q.get("topic") not in topics:
            errs.append(w + f'topic が不明 {q.get("topic")}')
        if q.get("law_check", "ok") not in ("ok", "uncertain", "revised"):
            errs.append(w + "law_check が不正")
        if q.get("law_check") in ("uncertain", "revised") and not q.get("law_note"):
            errs.append(w + "law_note が空")
        if not q.get("stem"):
            errs.append(w + "stem が空")
        n = q.get("number")
        if q.get("format") == "択一式":
            ch = q.get("choices") or []
            if [c.get("label") for c in ch] != LABELS:
                errs.append(w + "choices は A〜E の5つが必要")
            if q.get("answer") not in LABELS:
                errs.append(w + "answer が A〜E ではない")
            if sum(bool(c.get("correct")) for c in ch) != 1 or not any(
                    c.get("correct") and c.get("label") == q.get("answer") for c in ch):
                errs.append(w + "correct フラグと answer が一致しない")
            for c in ch:
                if not c.get("text") or not c.get("explanation"):
                    errs.append(w + f'肢{c.get("label")} の text/explanation が空')
            if not is_sample and isinstance(n, int):
                exp = next((s for a, b, s in TAKUITSU_SUBJECT if a <= n <= b), None)
                if exp and q.get("subject") not in exp:
                    errs.append(w + f"問{n} の subject は {sorted(exp)} のはず")
        elif q.get("format") == "選択式":
            opts = q.get("options") or []
            if len(opts) != 20:
                errs.append(w + f"options は20個（現在{len(opts)}）")
            bl = q.get("blanks") or []
            if [b.get("label") for b in bl] != LABELS:
                errs.append(w + "blanks は A〜E の5つが必要")
            text = q.get("text", "")
            for b in bl:
                if f'［{b.get("label")}］' not in text:
                    errs.append(w + f'本文に ［{b.get("label")}］ がない')
                if not isinstance(b.get("answer"), int) or not 1 <= b["answer"] <= len(opts):
                    errs.append(w + f'空欄{b.get("label")} の answer が範囲外')
                if not b.get("explanation"):
                    errs.append(w + f'空欄{b.get("label")} の explanation が空')
            if not is_sample and isinstance(n, int) and 1 <= n <= 8 and q.get("subject") != SENTAKU_SUBJECT[n - 1]:
                errs.append(w + f"選択式問{n} の subject は {SENTAKU_SUBJECT[n - 1]} のはず")
        else:
            errs.append(w + "format は 択一式 / 選択式")
    return errs


def check_videos(path: Path, topics: set[str]) -> list[str]:
    errs = []
    seen = set()
    for v in json.loads(path.read_text(encoding="utf-8")).get("videos", []):
        w = f'{v.get("url", "?")}: '
        for k in ("id", "channel", "title", "url", "topic"):
            if not v.get(k):
                errs.append(w + f"{k} が空")
        if v.get("topic") and v["topic"] not in topics:
            errs.append(w + f'topic が不明 {v["topic"]}')
        if v.get("kind") not in (None, "講義", "直前期", "過去問解説", "その他"):
            errs.append(w + "kind が不正")
        if v.get("url") in seen:
            errs.append(w + "url が重複")
        seen.add(v.get("url"))
    return errs


def main() -> None:
    topics = topic_ids()
    paths = [Path(p) for p in sys.argv[1:]] or sorted((DATA / "questions").glob("*.json")) + (
        [DATA / "videos.json"] if (DATA / "videos.json").exists() else [])
    total = 0
    for p in paths:
        if p.name.endswith(".partial.json"):
            continue
        errs = check_videos(p, topics) if p.name == "videos.json" else check_questions(p, topics)
        total += len(errs)
        print(f"{'OK ' if not errs else 'NG '} {p}" + (f"（{len(errs)}件）" if errs else ""))
        for e in errs[:50]:
            print("   -", e)
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
