"""inbox/parts/<prefix>_*.json（分割して作った問題データ）を data/questions/<prefix>.json にまとめる。

  python scripts/merge_parts.py R07
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    prefix = sys.argv[1]
    parts = sorted((ROOT / "inbox" / "parts").glob(f"{prefix}_*.json"))
    if not parts:
        sys.exit(f"inbox/parts/{prefix}_*.json がありません")
    exam = year = None
    by_id: dict[str, dict] = {}
    for p in parts:
        d = json.loads(p.read_text(encoding="utf-8"))
        exam, year = d["exam"], d["year_num"]
        for q in d["questions"]:
            by_id[q["id"]] = q
    qs = sorted(by_id.values(), key=lambda q: (q["format"] != "選択式", q["number"]))
    out = ROOT / "data" / "questions" / f"{prefix}.json"
    out.write_text(json.dumps({"exam": exam, "year_num": year, "questions": qs}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    n_s = sum(q["format"] == "選択式" for q in qs)
    n_t = len(qs) - n_s
    print(f"{out}: 選択式{n_s}問 / 択一式{n_t}問" + ("" if (n_s, n_t) == (8, 70) else "  ※不足あり"))


if __name__ == "__main__":
    main()
