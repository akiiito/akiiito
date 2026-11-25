"""スマホ版（claude.ai アーティファクト）用に、問題・論点・試験回データを1つの JSON にまとめる。

  python scripts/build_artifact_data.py   # → artifact/data.json
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "artifact" / "data.json"

SKILL = ROOT / ".claude" / "skills" / "sharoshi-advisor" / "SKILL.md"


def advisor_prompt() -> str:
    """sharoshi-advisor スキルの本文から、ページの「Claudeに相談」で送る指示文を作る（同じ内容に保つ）。"""
    text = SKILL.read_text(encoding="utf-8").split("---", 2)[2]
    keep = []
    for sec in text.split("\n## ")[1:]:
        title = sec.split("\n", 1)[0]
        if title.startswith(("社労士試験の前提", "分析の観点", "書き方", "出力形式")):
            keep.append("## " + sec.strip())
    head = ("あなたは社会保険労務士試験の専門家で、1人の受験生専属の家庭教師です（sharoshi-advisor スキル）。"
            "下の演習ログ（JSON）を分析し、次に何をすべきかを助言してください。"
            "一般的な勉強法ではなく、このログから読み取れることだけを書きます。")
    tail = ("返答は、出力形式の score-advice と同じ形の JSON オブジェクトだけにしてください"
            "（キーは summary / focus / actions の3つ）。")
    return head + "\n\n" + "\n\n".join(keep) + "\n\n" + tail


KEEP = ["id", "format", "number", "branch", "subject", "topic", "stem", "text", "choices", "answer",
        "also_correct", "options", "blanks", "ox", "explanation", "law_check", "law_note"]


def main() -> None:
    topics = json.loads((DATA / "topics.json").read_text(encoding="utf-8"))["groups"]
    meta = {k: v for k, v in json.loads((DATA / "exams.json").read_text(encoding="utf-8")).items()
            if not k.startswith("_")}
    exams, questions = [], []
    for path in sorted((DATA / "questions").glob("*.json")):
        d = json.loads(path.read_text(encoding="utf-8"))
        qs = d["questions"]
        fmts = sorted({q["format"] for q in qs})
        exams.append({"exam": d["exam"], "year": d["year_num"], "count": len(qs), "formats": fmts,
                      "pass": meta.get(d["exam"], {}).get("pass")})
        for q in qs:
            o = {k: q[k] for k in KEEP if k in q and q[k] not in (None, "", [])}
            o["exam"] = d["exam"]
            if "choices" in o:
                o["choices"] = [{"label": c["label"], "text": c["text"], "explanation": c["explanation"]}
                                for c in o["choices"]]
            questions.append(o)
    exams.sort(key=lambda e: e["year"], reverse=True)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"topics": topics, "exams": exams, "questions": questions, "advisor_prompt": advisor_prompt()},
                              ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{OUT}: {len(questions)}問, {OUT.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
