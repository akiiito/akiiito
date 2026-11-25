"""社労士試験の過去問PDF（問題・正答）を取り込み、解説・論点タグ・法改正チェック付きJSONにする。

使い方:
  python scripts/import_pdf.py --exam 令和7年度 --year 2025 --prefix R07 \
      --sentaku 選択式.pdf --takuitsu 択一式.pdf --answers 正答.pdf

  - 問題PDF・正答PDFは試験センター（社会保険労務士試験オフィシャルサイト）で公開されているもの。
  - 出力: data/questions/<prefix>.json（途中結果は .partial.json に保存され、再実行で続きから）
  - 法改正チェックは --baseline の日付時点の法令で行う（既定はアプリ設定の法令基準日と同じ想定）。
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

import anthropic

from common import DATA, call_json, load_topics, topics_text

TAKUITSU_RANGES = [  # (開始, 終了, 科目候補)
    (1, 10, ["roki"]), (11, 20, ["rosai"]), (21, 30, ["koyo"]), (31, 40, ["roippan", "shaippan"]),
    (41, 50, ["kenpo"]), (51, 60, ["konen"]), (61, 70, ["kokunen"]),
]
SENTAKU_SUBJECTS = ["roki", "rosai", "koyo", "roippan", "shaippan", "kenpo", "konen", "kokunen"]

LAW = {
    "law_check": {"type": "string", "enum": ["ok", "uncertain", "revised"],
                  "description": "ok=基準日時点の法令でそのまま正しく解ける / uncertain=改正の可能性がある・統計白書など年度依存 / revised=改正等で正答が変わる・成立しない・公式に正答なし(全員正解等)"},
    "law_note": {"type": "string", "description": "uncertain/revised の理由（どの改正か）。ok なら空文字"},
}

TAKUITSU_SCHEMA = {
    "type": "object",
    "properties": {"questions": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "number": {"type": "integer"},
            "subject": {"type": "string", "enum": SENTAKU_SUBJECTS},
            "topic": {"type": "string"},
            "stem": {"type": "string", "description": "問題文（設問部分）。原文どおり"},
            "choices": {"type": "array", "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "enum": ["A", "B", "C", "D", "E"]},
                    "text": {"type": "string", "description": "選択肢の本文。原文どおり"},
                    "correct": {"type": "boolean", "description": "この肢が設問の求める答え（正答）か"},
                    "explanation": {"type": "string", "description": "正誤とその根拠（条文番号・通達・判例など）を簡潔に"},
                },
                "required": ["label", "text", "correct", "explanation"],
                "additionalProperties": False,
            }},
            "answer": {"type": "string", "enum": ["A", "B", "C", "D", "E"]},
            **LAW,
        },
        "required": ["number", "subject", "topic", "stem", "choices", "answer", "law_check", "law_note"],
        "additionalProperties": False,
    }}},
    "required": ["questions"],
    "additionalProperties": False,
}

SENTAKU_SCHEMA = {
    "type": "object",
    "properties": {"questions": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "number": {"type": "integer"},
            "subject": {"type": "string", "enum": SENTAKU_SUBJECTS},
            "topic": {"type": "string"},
            "stem": {"type": "string"},
            "text": {"type": "string", "description": "本文。空欄は［A］〜［E］の形で表記。段落は改行(\\n)"},
            "options": {"type": "array", "items": {"type": "string"}, "description": "選択肢の語群（①〜⑳の順、番号は除く）"},
            "blanks": {"type": "array", "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "enum": ["A", "B", "C", "D", "E"]},
                    "answer": {"type": "integer", "description": "正解の語群番号（1始まり）"},
                    "explanation": {"type": "string", "description": "根拠（条文・判例・白書等）と紛らわしい選択肢との違い"},
                },
                "required": ["label", "answer", "explanation"],
                "additionalProperties": False,
            }},
            **LAW,
        },
        "required": ["number", "subject", "topic", "stem", "text", "options", "blanks", "law_check", "law_note"],
        "additionalProperties": False,
    }}},
    "required": ["questions"],
    "additionalProperties": False,
}

SYSTEM = """あなたは社会保険労務士試験の過去問を、学習アプリ用の構造化データに変換する専門家です。
- 問題文・選択肢は PDF の原文どおりに書き起こす（要約・言い換えをしない）。
- 正答は必ず正答PDFに従う。自分の判断で正答を変えない。
- 解説は、各肢（各空欄）の正誤と根拠（法令の条文番号、通達、最高裁判例、白書等）を簡潔に書く。誤りの肢は「どこが誤りか・正しくは何か」を明示する。
- 論点(topic)は与えられた論点IDリストから最も適切なものを1つ選ぶ。徴収法の問題は徴収法の論点を選ぶ。
- 法改正チェック: 基準日時点の法令で、その問題が正答どおりに成立するかを判定する。改正で正誤が変わる・数値が変わるものは revised、確信が持てないもの・統計/白書など年度依存のものは uncertain とし、law_note に理由を書く。公式発表で「全員正解」「正答なし」等になった問題も revised とする。"""


def pdf_block(path: Path, cache: bool = False) -> dict:
    data = base64.standard_b64encode(path.read_bytes()).decode()
    block = {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": data},
             "title": path.name}
    if cache:
        block["cache_control"] = {"type": "ephemeral"}
    return block


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exam", required=True, help="試験回の表示名 例: 令和7年度")
    ap.add_argument("--year", type=int, required=True, help="西暦 例: 2025")
    ap.add_argument("--prefix", required=True, help="問題IDの接頭辞 例: R07")
    ap.add_argument("--sentaku", type=Path, help="選択式の問題PDF")
    ap.add_argument("--takuitsu", type=Path, help="択一式の問題PDF")
    ap.add_argument("--answers", type=Path, required=True, help="正答PDF")
    ap.add_argument("--baseline", default="2027-04-16", help="法改正チェックの基準日")
    ap.add_argument("--only", help="一部だけ処理 例: S / T1-10")
    args = ap.parse_args()
    if not (args.sentaku or args.takuitsu):
        sys.exit("--sentaku か --takuitsu の少なくとも一方を指定してください")

    topics = load_topics()
    topic_ids = {t["id"] for t in topics}
    out_path = DATA / "questions" / f"{args.prefix}.json"
    partial_path = out_path.with_suffix(".partial.json")
    done: dict[str, list] = json.loads(partial_path.read_text(encoding="utf-8")) if partial_path.exists() else {}

    jobs = []
    if args.sentaku:
        jobs.append(("S", "選択式", "選択式 問1〜問8 のすべて", SENTAKU_SCHEMA, args.sentaku))
    if args.takuitsu:
        for a, b, subs in TAKUITSU_RANGES:
            jobs.append((f"T{a}-{b}", "択一式", f"択一式 問{a}〜問{b}（科目: {', '.join(subs)}）",
                         TAKUITSU_SCHEMA, args.takuitsu))

    client = anthropic.Anthropic()
    for key, fmt, scope, schema, qpdf in jobs:
        if args.only and args.only != key:
            continue
        if key in done:
            print(f"[skip] {key}（取り込み済み）")
            continue
        print(f"[run] {scope}")
        content = [
            pdf_block(qpdf),
            pdf_block(args.answers, cache=True),  # 同じPDFを繰り返し送るのでキャッシュ
            {"type": "text", "text": (
                f"{args.exam}（{args.year}年実施）の社労士試験です。1つ目のPDFが{fmt}の問題、2つ目が正答です。\n"
                f"{scope} を変換してください。\n"
                f"法改正チェックの基準日: {args.baseline}\n\n論点IDリスト:\n{topics_text(topics)}"
            )},
        ]
        result = call_json(client, system=SYSTEM, content=content, schema=schema)
        qs = result["questions"]
        for q in qs:
            if q["topic"] not in topic_ids:
                print(f"  ! 問{q['number']}: 未知の論点 {q['topic']}", file=sys.stderr)
        done[key] = qs
        partial_path.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  -> {len(qs)}問")

    questions = []
    for key, qs in done.items():
        for q in qs:
            fmt = "選択式" if key == "S" else "択一式"
            q = {"id": f'{args.prefix}-{"S" if fmt == "選択式" else "T"}{q["number"]:02d}', "format": fmt, **q}
            if fmt == "択一式":
                # 正答PDFとの整合: correct フラグを answer に合わせる
                for c in q["choices"]:
                    c["correct"] = c["label"] == q["answer"]
            questions.append(q)
    questions.sort(key=lambda q: (q["format"] != "選択式", q["number"]))
    out_path.write_text(json.dumps({"exam": args.exam, "year_num": args.year, "questions": questions},
                                   ensure_ascii=False, indent=1), encoding="utf-8")
    n_rev = sum(q["law_check"] == "revised" for q in questions)
    n_unc = sum(q["law_check"] == "uncertain" for q in questions)
    print(f"保存: {out_path}（{len(questions)}問 / 法改正で除外 {n_rev} / 要確認 {n_unc}）")
    if len(questions) == (8 if args.sentaku else 0) + (70 if args.takuitsu else 0):
        partial_path.unlink(missing_ok=True)
    print("アプリの 設定 → データを再読み込み で反映されます。")


if __name__ == "__main__":
    main()
