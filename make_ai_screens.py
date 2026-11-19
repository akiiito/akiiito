"""make_ai_screens.py ― AI動画のパソコン画面（800x500）を作る → ai_screens/*.png（架空の画面。実在のサービスの見た目は使わない）"""
import os
from PIL import Image, ImageDraw, ImageFont
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_screens"); os.makedirs(OUT, exist_ok=True)
F = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
def f(s): return ImageFont.truetype(F, s)
W, H = 800, 500
def base(dark=False, title=""):
    im = Image.new("RGB", (W, H), (30, 34, 44) if dark else (246, 247, 250)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 44), fill=(52, 58, 74) if dark else (220, 226, 236))
    d.text((18, 10), title, font=f(22), fill=(230, 235, 245) if dark else (40, 50, 70))
    return im, d
def save(im, name): im.save(os.path.join(OUT, name + ".png"))
# ログイン（朝）
im, d = base(False, "デスクトップ"); d.text((230, 200), "おはようございます", font=f(40), fill=(60, 70, 90)); save(im, "login")
# AIで下書き（3段階）
for k in range(1, 4):
    im, d = base(True, "アシスタント")
    d.rounded_rectangle((30, 64, 770, 120), 12, fill=(60, 70, 96)); d.text((48, 78), "取引先10社へのお礼メールを下書きして", font=f(24), fill=(240, 240, 250))
    n = {1: 3, 2: 7, 3: 10}[k]
    for i in range(n):
        y = 140 + i * 34; d.text((48, y), "✓ メール%02d　株式会社サンプル%d 様　お礼と次回のご提案" % (i + 1, i + 1), font=f(20), fill=(140, 230, 170))
    if k == 3: d.text((620, 8), "10/10 完了", font=f(26), fill=(255, 220, 120))
    save(im, "ai_mail%d" % k)
# 手で書く（3段階）
body = ["件名：先日のお打ち合わせのお礼", "株式会社サンプル1 様", "", "いつもお世話になっております。", "先日はお忙しいところ、お時間を", "いただきありがとうございました。", "つきましては、次回の"]
for k in range(1, 4):
    im, d = base(False, "メール作成（1通目）")
    n = {1: 3, 2: 5, 3: 7}[k]
    for i, line in enumerate(body[:n]): d.text((40, 70 + i * 40), line, font=f(26), fill=(40, 40, 50))
    d.rectangle((40 + 26 * len(body[n - 1]), 70 + (n - 1) * 40, 43 + 26 * len(body[n - 1]), 98 + (n - 1) * 40), fill=(40, 90, 220))
    d.text((560, 460), "残り 9通…", font=f(24), fill=(200, 80, 60)); save(im, "hand_mail%d" % k)
# 学ぶ（コード＋アシスタント）
for k in range(1, 3):
    im, d = base(True, "学習ノート")
    code = ["def 売上を集計(データ):", "    合計 = 0", "    for 行 in データ:", "        合計 += 行.金額", "    return 合計"]
    for i, c in enumerate(code): d.text((40, 70 + i * 34), c, font=f(22), fill=(150, 210, 255) if i == 0 else (220, 225, 235))
    d.rounded_rectangle((420, 260, 780, 380), 12, fill=(60, 70, 96))
    d.text((436, 272), "ここは、なぜ0から？", font=f(20), fill=(240, 240, 250)); d.text((436, 306), "→ 足し算の出発点だからです", font=f(20), fill=(170, 230, 190))
    if k == 2: d.text((40, 420), "自作ツール 完成！", font=f(40), fill=(255, 220, 120))
    save(im, "learn%d" % k)
# 表計算（同じ作業）
for k, tag in ((1, ""), (2, "✓ 確認済み")):
    im, d = base(False, "売上表")
    for r in range(9):
        for c in range(5):
            x, y = 30 + c * 150, 60 + r * 46
            d.rectangle((x, y, x + 150, y + 46), outline=(190, 196, 210))
            d.text((x + 10, y + 12), ["月", "店舗", "売上", "前年", "差"][c] if r == 0 else ("%d月" % r if c == 0 else "%d" % ((r * 37 + c * 13) % 90 * 1000)), font=f(20), fill=(50, 50, 60))
    if tag: d.text((560, 462), tag, font=f(26), fill=(40, 160, 90))
    save(im, "sheet%d" % k)
# ミス発覚
im, d = base(False, "送信済み")
d.text((40, 80), "件名：今期の売上報告", font=f(26), fill=(40, 40, 50)); d.text((40, 140), "今期の売上は 3億円 でした。", font=f(32), fill=(40, 40, 50))
d.rectangle((0, 330, W, 430), fill=(220, 50, 50)); d.text((40, 352), "！ 誤り：正しくは 3千万円", font=f(40), fill=(255, 255, 255)); save(im, "error")
# AIの下書き＋自分で確認
im, d = base(True, "提案書")
for i, line in enumerate(["AIの下書き", "・市場は前年より伸びている", "・数字：3千万円（出典：社内売上表）", "・次の一手：既存客への再提案"]):
    d.text((40, 70 + i * 50), line, font=f(28 if i == 0 else 24), fill=(255, 220, 120) if i == 0 else (220, 225, 235))
for i, mark in enumerate(["✓ 出典を確認", "✓ 数字を確認", "✓ 自分の言葉で直した"]):
    d.text((470, 300 + i * 40), mark, font=f(24), fill=(140, 230, 170))
save(im, "check")
# 使わなかった人もAIを使い始める
im, d = base(False, "アシスタント（はじめて）")
d.rounded_rectangle((30, 64, 770, 120), 12, fill=(225, 232, 245)); d.text((48, 78), "この表の数字、前年と比べて変なところある？", font=f(24), fill=(40, 50, 70))
d.text((48, 150), "→ 3月の「差」の計算がずれています", font=f(24), fill=(40, 120, 70))
d.text((48, 200), "（元の表で確かめる：…本当だ）", font=f(24), fill=(90, 90, 110)); save(im, "b_ai")
im, d = base(False, ""); save(im, "blank")
print(sorted(os.listdir(OUT)))
