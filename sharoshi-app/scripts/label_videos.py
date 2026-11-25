"""YouTube講座動画に論点ラベルを付けて data/videos.json に登録する。

使い方（どちらか）:
  # 1) 再生リスト/チャンネルURLから一覧を取得（要: pip install yt-dlp、YouTubeに接続できる環境）
  python scripts/label_videos.py --channel "〇〇の社労士講座" --url "https://www.youtube.com/@xxxx/videos"

  # 2) CSVから（列: title,url[,minutes,published]）
  python scripts/label_videos.py --channel "〇〇の社労士講座" --csv videos.csv

タイトルから Claude が論点ID と種別（講義/直前期/過去問解説/その他）を付けます。
同じURLの動画は上書き、別チャンネルの登録はそのまま残ります。
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import anthropic

from common import DATA, call_json, load_topics, topics_text

KINDS = ["講義", "直前期", "過去問解説", "その他"]
BATCH = 80


def fetch_with_ytdlp(url: str) -> list[dict]:
    try:
        import yt_dlp  # type: ignore
    except ImportError:
        sys.exit("yt-dlp が必要です: pip install yt-dlp")
    opts = {"extract_flat": True, "quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    out = []
    for e in info.get("entries") or []:
        if not e or not e.get("id"):
            continue
        dur = e.get("duration")
        out.append({"title": e.get("title", ""), "url": f'https://www.youtube.com/watch?v={e["id"]}',
                    "minutes": round(dur / 60) if dur else None, "published": None})
    return out


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return [{"title": r["title"], "url": r["url"],
             "minutes": int(r["minutes"]) if r.get("minutes") else None,
             "published": r.get("published") or None} for r in rows]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--channel", required=True, help="チャンネル名（アプリでの表示名）")
    ap.add_argument("--url", help="YouTubeの再生リスト/チャンネル動画一覧URL")
    ap.add_argument("--csv", type=Path, help="title,url[,minutes,published] のCSV")
    args = ap.parse_args()
    if not (args.url or args.csv):
        sys.exit("--url か --csv を指定してください")

    videos = fetch_with_ytdlp(args.url) if args.url else read_csv(args.csv)
    print(f"{len(videos)}本を取得")
    topics = load_topics()
    topic_ids = [t["id"] for t in topics] + ["none"]
    schema = {
        "type": "object",
        "properties": {"items": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "index": {"type": "integer"},
                "topic_id": {"type": "string", "enum": topic_ids},
                "kind": {"type": "string", "enum": KINDS},
            },
            "required": ["index", "topic_id", "kind"],
            "additionalProperties": False,
        }}},
        "required": ["items"],
        "additionalProperties": False,
    }
    system = ("社労士試験の講座動画のタイトルから、最も関連する論点IDを1つ選びます。"
              "特定の論点に当てはまらない動画（勉強法、雑談、全科目まとめ等）は topic_id を none にします。"
              "kind は、通常の解説=講義、直前対策・法改正・白書・総まとめ=直前期、過去問の解説=過去問解説。")

    client = anthropic.Anthropic()
    labeled = []
    for start in range(0, len(videos), BATCH):
        chunk = videos[start:start + BATCH]
        lines = "\n".join(f"{i}: {v['title']}" for i, v in enumerate(chunk))
        print(f"[run] {start + 1}〜{start + len(chunk)}本目")
        res = call_json(client, system=system, effort="low", schema=schema, content=[{
            "type": "text",
            "text": f"論点IDリスト:\n{topics_text(topics)}\n\n動画タイトル一覧（index: title）:\n{lines}",
        }])
        for it in res["items"]:
            if 0 <= it["index"] < len(chunk) and it["topic_id"] != "none":
                v = chunk[it["index"]]
                labeled.append({**v, "channel": args.channel, "topic": it["topic_id"], "kind": it["kind"],
                                "id": v["url"].rsplit("=", 1)[-1]})

    vpath = DATA / "videos.json"
    existing = json.loads(vpath.read_text(encoding="utf-8")).get("videos", []) if vpath.exists() else []
    by_url = {v["url"]: v for v in existing}
    for v in labeled:
        by_url[v["url"]] = v
    vpath.write_text(json.dumps({"videos": list(by_url.values())}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"保存: {vpath}（今回 {len(labeled)}本 / 合計 {len(by_url)}本）")


if __name__ == "__main__":
    main()
