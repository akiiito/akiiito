---
name: sharoshi-label-videos
description: 社労士講座の YouTube 動画に論点ラベルを付けて Score アプリの data/videos.json に登録する。「このチャンネルの動画を登録して」「/sharoshi-label-videos <URL>」などと言われたときに使う。API は使わない。
---

# YouTube講座動画の論点ラベル付け

`sharoshi-app/` で作業する。

## 手順

1. 動画一覧を取得する。
   - URLがある場合：`python scripts/fetch_videos.py "<URL>" > /tmp/videos_raw.json`
     - yt-dlp がなければ `pip install yt-dlp`。
   - CSVやタイトル一覧が渡された場合：それを使う。
   - チャンネル名（アプリでの表示名）が分からなければ、受験生に聞く。
2. `python scripts/advice_io.py topics` で論点ID一覧を得る。
3. 各動画のタイトルから、最も関連する論点IDを1つ選ぶ。
   - 特定の論点に当てはまらない動画（勉強法・雑談・全体まとめ等）は登録しない。
   - kind の付け方：通常の解説は「講義」、直前対策・法改正・白書・総まとめは「直前期」、過去問の解説は「過去問解説」。
4. `data/videos.json` に追記する（`{"videos": [...]}`）。
   - 各要素：`{"id": 動画ID, "channel": 表示名, "title", "url", "topic", "kind", "minutes", "published": null}`
   - 同じURLが既にあれば置き換える。
   - 他チャンネルの登録は消さない。
   - 数百本ある場合は、スクリプト（Python）で取得結果とラベルを結合して書き込んでよい。
5. `python scripts/validate_data.py data/videos.json` で NG がないことを確認する。
6. 受験生に報告する：登録本数、論点ごとの本数の偏り、登録しなかった本数。
   - アプリの「設定 → データを再読み込み」で反映されることも伝える。
