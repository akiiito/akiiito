"""Claude Code から学習ログを読み、アドバイスをアプリに書き込むための入出力（API不使用）。

  python scripts/advice_io.py export                 # 全体の学習ログ(JSON)を表示
  python scripts/advice_io.py export --last-session  # 直近のセッションも詳しく含める
  python scripts/advice_io.py import advice.json     # score-advice を取り込む（"-" で標準入力）
  python scripts/advice_io.py topics                 # 論点IDの一覧
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import advisor, db  # noqa: E402
from app.exam import load_store  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    ex = sub.add_parser("export")
    ex.add_argument("--last-session", action="store_true")
    ex.add_argument("--session", type=int)
    im = sub.add_parser("import")
    im.add_argument("file")
    im.add_argument("--scope", default="overall")
    sub.add_parser("topics")
    args = ap.parse_args()

    db.init_db()
    store = load_store()
    if args.cmd == "export":
        sid = args.session
        if args.last_session and sid is None:
            recent = db.recent_sessions(1)
            sid = recent[0]["id"] if recent else None
        ctx = advisor.build_context(store, db.get_settings(), sid)
        print(json.dumps(ctx, ensure_ascii=False, indent=1))
    elif args.cmd == "import":
        text = sys.stdin.read() if args.file == "-" else Path(args.file).read_text(encoding="utf-8")
        try:
            advice = advisor.parse_advice(text)
        except advisor.AdviceParseError as e:
            sys.exit(f"取り込み失敗: {e}")
        unknown = [f["topic_id"] for f in advice["focus"] if f["topic_id"] and f["topic_id"] not in store.topics]
        if unknown:
            sys.exit(f"取り込み失敗: 未知の topic_id {unknown}（topics コマンドで確認）")
        db.save_advice(args.scope, advice)
        if args.scope != "overall":
            db.save_advice("overall", advice)
        print(f"取り込みました（重点{len(advice['focus'])}件・アクション{len(advice['actions'])}件）。アプリをリロードすると表示されます。")
    elif args.cmd == "topics":
        for t in store.topics.values():
            print(f"{t.id}\t{t.group} / {t.name}")


if __name__ == "__main__":
    main()
