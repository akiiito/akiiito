# 一問一答データ作成タスク（平成29〜令和5年度 択一式）

作業ディレクトリ: /home/user/akiiito/sharoshi-app
Python: /home/user/akiiito/.venv/bin/python

## 入力

`inbox/lab/<PREFIX>_<PART>.json`

- 試験センター公表の択一式問題を、肢ごと（A〜E）に分けた文章。
- 出典は社労士過去問ラボ。設問の柱書（「正しいものはどれか」等）は含まれていない。
- 各 item の中身：
  - `number`：通し番号 1〜70
  - `branch`：A〜E
  - `text`：肢の文章（試験センター原文）
  - `lab_ox`：社労士過去問ラボのAIが付けた○×
    - 未検証で、公式照合の結果、約8%誤っていた。
    - 問題単位で○×が丸ごと反転している誤りが多い。
  - `lab_pattern`：問題内の○の数が1か4なら `standard`、それ以外は `irregular`
    - irregular は、個数問題・組合せ問題、またはラボの誤り。
  - `lab_subject`、`lab_law_status`：参考情報。

## やること（各肢）

1. **ox（出題当時の法令で、その肢の記述が正しいか）を自分で判定する。**
   - lab_ox は参考にとどめる。
   - 判定が lab_ox と食い違ったら、条文・通達・判例を思い出してよく検討する。
   - 1問5肢の整合も確認する。通常の問題なら、5肢のうち1つだけが他と異なることが多い。
   - 最終判断を ox に入れ、`ox_check` を次のどちらかにする。
     - `"agree"`：lab_ox と一致した。
     - `"disagree"`：lab_ox と食い違った。この場合 law_check を最低でも `uncertain` にし、law_note に「○×の判定に食い違いあり（理由）」を書く。
2. **explanation を自分の言葉で書く。**
   - 1〜3文。正誤と根拠（条文番号・通達・判例）を書く。
   - 誤りの肢は「正しくは何か」を明示する。
   - 社労士過去問ラボの解説は見ていない前提で、独自に書くこと（コピー禁止）。
3. **topic を選ぶ。** `python scripts/advice_io.py topics` の論点IDから1つ選ぶ。
4. **subject を決める。** 番号で決める。
   - 1-10：roki、11-20：rosai、21-30：koyo
   - 31-40：roippan か shaippan（内容で判断）
   - 41-50：kenpo、51-60：konen、61-70：kokunen
5. **law_check を付ける。** 基準日 2027-04-16 時点の現行法で判定する。
   - `ok`：今もそのまま○×が成り立つ。
   - `revised`：改正で○×が変わった、または前提の制度がなくなった。law_note に何の改正かを書く。
   - `uncertain`：自信がない、統計・白書・年度の金額に依存する、ox_check が disagree。law_note に理由を書く。

## 出力

`inbox/parts/<PREFIX>_O<PART>.json`

```json
{"exam": "<入力の exam>", "year_num": <入力の year_num>, "questions": [
  {"id": "<PREFIX>-T07C", "format": "一問一答", "number": 7, "branch": "C",
   "subject": "roki", "topic": "lb_wage", "stem": "<text を一字一句そのまま>",
   "ox": true, "ox_check": "agree", "explanation": "...",
   "law_check": "ok", "law_note": ""}
]}
```

- id は `<PREFIX>-T<2桁番号><枝>`。
- 入力の全肢を出力する（欠けさせない）。
- 量が多いので、10問（50肢）ずつ Python スクリプトでファイルに追記するなど、確実に書き出すこと。

## 検証

`/home/user/akiiito/.venv/bin/python scripts/validate_data.py inbox/parts/<PREFIX>_O<PART>.json` を実行し、OK になるまで直す。

最後に次を報告する。

- 肢数
- 検証結果
- disagree の件数と主な例
- revised の件数と主な例
