"""スマホ版（claude.ai アーティファクト）用に、問題・論点・試験回データを1つの JSON にまとめる。

  python scripts/build_artifact_data.py   # → artifact/data.json
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "artifact" / "data.json"

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
    OUT.write_text(json.dumps({"topics": topics, "exams": exams, "questions": questions},
                              ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{OUT}: {len(questions)}問, {OUT.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
