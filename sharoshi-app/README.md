# Score — 自分専用 社労士学習アプリ

スマホから使う、自分専用の社会保険労務士試験の学習Webアプリです。
宅建用の学習アプリを自作したnote記事の作り方を、社労士試験向けに置き換えています。

| 記事（宅建） | このアプリ（社労士） |
|---|---|
| 学習：YouTube 2チャンネルの動画に論点ラベルを付け、論点から動画へ飛べる | **学習タブ**：社労士の論点（約60個）ごとに動画を並べる。Claude Code のスキルで動画タイトルに論点を付ける |
| 演習：過去問PDFをAIで構造化し、肢ごとの解説・論点タグ・法改正チェックを付ける | **演習タブ**：Claude Code のスキルで過去問PDFを取り込み、肢ごと／空欄ごとの解説・論点タグ・法改正チェックを付ける。択一式（5肢）と選択式（空欄5つ・語群20個）の両方に対応 |
| 最新年度は模試用に取っておく | 設定で「模試用に取っておく試験回」を選ぶと、普段の分野別演習には出なくなる。試験回モードでは選択式と択一式それぞれの**科目別基準点（足切り）**を判定する |
| フィードバック：選んだ肢・正誤・回答時間を記録し、Claude API で傾向分析とアドバイスを作る | **履歴タブ**：同じ情報を記録し、**APIを使わず**スキル経由で Claude に渡す。Claude は「足切りされそうな科目」を最優先に、重点論点と次にやることを提案し、その結果をアプリに取り込む |
| FastAPI + Jinja2 + SQLite を自宅サーバーで動かし、Tailscale でスマホから使う | 同じ構成。ホーム画面に追加してアプリのように使える（PWA） |

## 画面

- **ホーム**：試験までの残り日数、今日の回答数、累計正答率、おまかせ演習、誤答の復習
- **演習**：科目・論点・形式・出題順（おまかせ／誤答のみ／未着手／ランダム）を選んで解く。試験回（模試）もここから
- **学習**：論点ごとの動画一覧と、その論点の正答率
- **履歴**：科目別の成績、AIアドバイス、最近のセッション
- **設定**：本試験日、模試用の試験回、法令基準日、合格基準（目安）、データの再読み込み

## AIアドバイスの流れ（API不要・追加料金なし）

アプリは Claude API を呼びません。普段使っている Claude（アプリ／Claude Code）に、スキル経由でアドバイスさせます。

### スマホ（Claudeアプリ）で

1. アプリの **履歴** か **結果画面** で「Claudeに相談」を押す
2. 「コピーしてClaudeを開く」を押す → Claude の新しいチャットに貼り付けて送信
3. Claude の返答を最後まで全部コピー → アプリに戻って貼り付け →「取り込む」
4. ホームと履歴にアドバイスが表示され、重点論点からそのまま演習・動画へ移れる

精度を上げるため、claude.ai に **sharoshi-advisor スキル** を入れておきます（初回のみ）。
`skills-dist/sharoshi-advisor.zip` を、claude.ai の 設定 → 機能（Capabilities）→ スキル でアップロードしてください。
スキルが無くても、貼り付けるテキストに指示と出力形式が含まれているので動きます。

### PC（Claude Code）で

アプリを動かしているPCで `sharoshi-app` を開いて Claude Code を起動し、

```
/sharoshi-advisor
```

と打つだけです。Claude がログを読んで分析し、アドバイスをアプリに直接書き込みます（コピペ不要）。

## セットアップ（自宅PC / Mac / Linux）

```bash
cd sharoshi-app
python3 -m venv .venv
source .venv/bin/activate          # Windows は .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

PCのブラウザで http://localhost:8000 を開くと使えます。

### スマホから使う（Tailscale）

1. PCとスマホの両方に [Tailscale](https://tailscale.com/) を入れ、同じアカウントでログインする
2. PCで `tailscale serve --bg 8000` を実行する（Tailscale内だけで使える https のURLが発行される）
3. 表示された `https://<PC名>.<tailnet名>.ts.net` をスマホのブラウザで開く
4. 共有メニューの「ホーム画面に追加」で、アプリのように起動できる

https で開くと、「クリップボードから貼り付け」と「共有メニューで送る」ボタンが使えます。http のままでもコピーと手動の貼り付けは使えます。
インターネットには公開されません。念のためパスワードを掛けたい場合は、`APP_PASSWORD=好きな文字列` を設定して起動してください。

## 過去問を取り込む（Claude Code のスキル）

### 収録済み

| 試験回 | 問題数 | 法改正で除外 | 要確認 | 備考 |
|---|---|---|---|---|
| 令和8年度（第58回） | 78 | 1 | 8 | 初期設定で模試用に取っておく（分野別演習には出ない）。選択式の一部は空欄ごとに4択の新形式 |
| 令和7年度（第57回） | 78 | 0 | 9 | |
| 令和6年度（第56回） | 78 | 1 | 7 | |

- 問題・正答は試験センター公式サイトのPDFから取り込みました。正答は公式の正答表と全問照合済みです。
- 公式に正答が2つとされた問題（令和6年度 労災問6、令和8年度 一般常識問9）は、どちらを選んでも正解になります。
- 試験回ごとの公式合格基準（科目別の補正を含む）は `data/exams.json` にあり、模試の判定に使います。
- 公式サイトで公開されているのは直近3年分だけです。それより前の年度を入れたい場合は、PDFを入手して下の手順で取り込んでください。

### 追加で取り込む

社労士試験の過去問（問題・正答）は、社会保険労務士試験オフィシャルサイト（試験センター）で、直近の年度分がPDFで公開されています。

1. 選択式の問題・択一式の問題・正答のPDFを `sharoshi-app/inbox/` に置く
2. Claude Code で `/sharoshi-import-exam 令和7年度` と頼む
3. Claude が PDF を読み、肢ごとの解説・論点タグ・法改正チェック付きで `data/questions/R07.json` を作り、`scripts/validate_data.py` で形式を検証する
4. アプリの **設定 → データを再読み込み** で反映

- `law_check` の値で出題を制御します。
  - `revised`（法改正で正答が変わる・公式に正答なし）：出題しません
  - `uncertain`（改正の可能性あり、統計・白書のように年度で変わるもの）：設定で出題するかどうかを選べます
- **AIの解説と法改正の判定は誤ることがあります。** 気になる問題は条文やテキストで確認し、JSONを直接直してください。
- 年度を分割して作った場合は、`inbox/parts/R05_*.json` に置いて `python scripts/merge_parts.py R05` で1ファイルにまとめられます。

## YouTube講座を論点に紐づける（Claude Code のスキル）

```
/sharoshi-label-videos https://www.youtube.com/@xxxx/videos
```

`scripts/fetch_videos.py`（yt-dlp）で動画一覧を取り、Claude がタイトルから論点と種別（講義／直前期／過去問解説）を付けて、`data/videos.json` に追記します。
動画が未登録の論点では、YouTube の検索リンクを表示します。

## ファイル構成

```
sharoshi-app/
  app/
    main.py        画面とルーティング（FastAPI）
    exam.py        試験の構造（科目・択一の一般常識合算）とデータ読み込み
    stats.py       集計・出題の選び方・模試の採点
    advisor.py     学習ログの書き出しと、Claudeの返答（score-advice）の読み取り
    db.py          SQLite（回答ログ・セッション・アドバイス・設定）
    templates/     画面（Jinja2）
    static/        CSS・アイコン・manifest
  .claude/skills/
    sharoshi-advisor/       学習アドバイス（Claudeアプリ / Claude Code 共通）
    sharoshi-import-exam/   過去問PDFの取り込み
    sharoshi-label-videos/  動画への論点ラベル付け
  skills-dist/sharoshi-advisor.zip   claude.ai にアップロードする用
  data/
    topics.json         論点の一覧（自由に編集してよい）
    questions/*.json    問題データ（R06〜R08）
    exams.json          試験回ごとの公式合格基準
    videos.json         動画データ
    app.db              学習記録（自動作成・Git管理外）
  inbox/                過去問PDFの置き場（Git管理外）
  scripts/
    advice_io.py        Claude Code 用：ログの書き出し・アドバイスの取り込み
    validate_data.py    問題・動画JSONの形式チェック
    fetch_videos.py     YouTube動画一覧の取得（yt-dlp）
    merge_parts.py      分割して作った問題データの結合
```

## メモ

- Claude API は使いません。Claude のサブスクリプション（Claudeアプリ・Claude Code）の範囲で動きます。
- 合格基準（選択式25点・各3点、択一式44点・各4点）は目安の初期値です。毎年補正されるので、設定で調整してください。
- 本試験日の初期値（2027-08-22）は例年の日程から推定した仮の日付です。公式発表を確認して設定してください。
