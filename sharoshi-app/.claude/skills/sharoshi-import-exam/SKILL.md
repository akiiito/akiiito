---
name: sharoshi-import-exam
description: 社労士試験の過去問PDF（問題・正答）を読み、Score アプリ用の問題JSON（肢ごとの解説・論点タグ・法改正チェック付き）を作る。「過去問を取り込んで」「/sharoshi-import-exam 令和7年度」などと言われたときに使う。API は使わず、Claude Code 自身が PDF を読んで書く。
---

# 過去問PDFの取り込み

`sharoshi-app/` で作業する。

## 入力

- `inbox/` に置かれたPDF：選択式の問題、択一式の問題、正答。
  - ファイル名から判断できなければ、受験生に確認する。
- 試験回の表示名（例：令和7年度）、西暦（例：2025）、ID接頭辞（例：R07）。
  - 指定がなければ、表示名から決める。
- 法改正チェックの基準日：`data/app.db` の設定 `law_baseline`。
  - 取得できなければ `2027-04-16`。

## 手順

1. `python scripts/advice_io.py topics` で論点ID一覧を得る。
2. PDFを Read で読む。
   - 長いPDFは `pages` で分ける（1回20ページまで）。
   - 正答は必ず正答PDFに従う。自分の判断で正答を変えない。
3. 次の順に、少しずつ `data/questions/<ID接頭辞>.json` に書き足す。
   - 選択式8問 → 択一式 問1〜10 → 問11〜20 → … → 問61〜70。
   - 1度に全部書かない（出力が長くなりすぎるため）。
4. 書き終えたら `python scripts/validate_data.py data/questions/<ID接頭辞>.json` を実行する。
   - NG がなくなるまで直す。
5. 受験生に次を報告する。
   - 問題数、`revised` と `uncertain` の件数と主な理由。
   - アプリの「設定 → データを再読み込み」で反映されること。

## JSON形式

```json
{"exam": "令和7年度", "year_num": 2025, "questions": [ ... ]}
```

### 択一式

```json
{"id": "R07-T01", "format": "択一式", "number": 1, "subject": "roki", "topic": "lb_dismissal",
 "stem": "設問文（原文どおり）",
 "choices": [{"label": "A", "text": "肢の本文（原文どおり）", "correct": false, "explanation": "正誤と根拠"}, ...A〜E],
 "answer": "C", "law_check": "ok", "law_note": ""}
```

- `subject` は問題番号で決まる。
  - 1〜10：roki、11〜20：rosai、21〜30：koyo、31〜40：roippan か shaippan（内容で判断）。
  - 41〜50：kenpo、51〜60：konen、61〜70：kokunen。
- 徴収法の問題（労災・雇用の後半3問程度）は、topic に `lc_*` を使う。
- 組合せ問題（「アとイ」など）や個数問題も、A〜E の肢にそのまま書き起こす。
  - 各肢の explanation で、ア〜オそれぞれの正誤にも触れる。

### 選択式

```json
{"id": "R07-S01", "format": "選択式", "number": 1, "subject": "roki", "topic": "lb_wage",
 "stem": "次の文中の［　］の部分を…",
 "text": "本文。空欄は［A］〜［E］で表記。段落は\n",
 "options": ["語群1", ... 20個（番号は除く）],
 "blanks": [{"label": "A", "answer": 7, "explanation": "根拠と紛らわしい語との違い"}, ...A〜E],
 "law_check": "ok", "law_note": ""}
```

- `subject` は問1〜8の順に、roki, rosai, koyo, roippan, shaippan, kenpo, konen, kokunen。
- `answer` は語群の番号（1始まり）。

## 書き起こしと解説のルール

- 問題文・肢は**原文どおり**。要約・言い換えはしない。
- 解説には根拠（条文番号・通達・最高裁判例・白書）を簡潔に書く。
  - 誤りの肢は「どこが誤りで、正しくは何か」を明示する。
- `law_check` の付け方：
  - `ok`：基準日時点の法令で、正答どおりに成立する。
  - `uncertain`：改正の可能性があり確信が持てないもの、統計・白書など年度で変わるもの。
  - `revised`：改正で正誤や数値が変わるもの、公式に「全員正解」「正答なし」となったもの。
  - `uncertain` と `revised` は、`law_note` に理由（どの改正か）を書く。
- 自信のない解説は、推測で断定しない。explanation に「要確認」と書く。
