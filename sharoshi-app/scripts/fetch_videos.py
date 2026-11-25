"""YouTube の再生リスト/チャンネル動画一覧を取得して JSON で出力する（要: pip install yt-dlp）。

  python scripts/fetch_videos.py "https://www.youtube.com/@xxxx/videos" > /tmp/videos_raw.json

出力: [{"id", "title", "url", "minutes"}]。論点の付与は sharoshi-label-videos スキルで行う。
"""
from __future__ import annotations

import json
import sys


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    try:
        import yt_dlp  # type: ignore
    except ImportError:
        sys.exit("yt-dlp が必要です: pip install yt-dlp")
    with yt_dlp.YoutubeDL({"extract_flat": True, "quiet": True, "skip_download": True}) as ydl:
        info = ydl.extract_info(sys.argv[1], download=False)
    out = []
    for e in info.get("entries") or []:
        if e and e.get("id"):
            dur = e.get("duration")
            out.append({"id": e["id"], "title": e.get("title", ""),
                        "url": f'https://www.youtube.com/watch?v={e["id"]}',
                        "minutes": round(dur / 60) if dur else None})
    print(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"{len(out)}本", file=sys.stderr)


if __name__ == "__main__":
    main()
