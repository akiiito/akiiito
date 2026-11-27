"""第3話：はがした名札の下（白石 蓮）と、出席簿の見開き（13番だけ黒い枠）"""
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
F = "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"
M = F
f = lambda s, p=F: ImageFont.truetype(p, s)
# はがした名札の下：元の名札がそのまま残っている
W, H = 800, 300
im = Image.new("RGB", (W, H), (240, 236, 224)); d = ImageDraw.Draw(im)
d.rectangle((6, 6, W - 7, H - 7), outline=(120, 110, 100), width=6)
d.text((30, 22), "2年B組　出席番号", font=f(44), fill=(60, 60, 60))
d.text((60, 120), "13", font=f(150), fill=(30, 30, 30))
d.text((330, 128), "白石 蓮", font=f(130, M), fill=(20, 20, 24))
rnd = random.Random(2)                                   # テープのはがし跡
for k in range(14):
    x = rnd.uniform(20, W - 60); y = rnd.choice((rnd.uniform(70, 100), rnd.uniform(270, 290)))
    d.line([(x, y), (x + rnd.uniform(20, 70), y + rnd.uniform(-3, 3))], fill=(180, 172, 160), width=rnd.randint(3, 7))
im.save("s3_assets/gk_nameplate_clean.png")
# 出席簿の見開き
W, H = 1200, 820
im = Image.new("RGB", (W, H), (244, 240, 228)); d = ImageDraw.Draw(im)
d.line([(W // 2, 0), (W // 2, H)], fill=(170, 160, 145), width=6)
names = [(9, "小松 美緒"), (10, "斉藤 玲奈"), (11, "佐々木 拓真"), (12, "佐藤 優"), (13, "白石 蓮"), (14, "杉本 沙恵"), (15, "鈴木 明莉"), (16, "高田 悠斗"),
         (17, "竹内 陽向"), (18, "田中 ひなた"), (19, "千葉 颯"), (20, "土屋 結衣"), (21, "中島 湊"), (22, "西村 葵"), (23, "野口 蒼"), (24, "橋本 凛")]
d.text((40, 30), "2年B組　出席簿", font=f(52), fill=(40, 40, 50))
d.text((660, 40), "11月", font=f(44), fill=(40, 40, 50))
rnd = random.Random(7)
for k, (no, nm) in enumerate(names):
    px = 40 if k < 8 else 640; y = 140 + (k % 8) * 84
    d.line([(px, y + 76), (px + 520, y + 76)], fill=(185, 180, 170), width=2)
    d.text((px + 6, y + 14), "%d" % no, font=f(44), fill=(50, 50, 60))
    d.text((px + 80, y + 10), nm, font=f(50, M), fill=(25, 25, 30))
    if no == 13:                                              # 13番だけ黒い枠（喪の印）、出欠の印なし
        d.rectangle((px - 6, y - 2, px + 530, y + 80), outline=(8, 8, 10), width=11)
    else:
        for j in range(4):
            d.ellipse((px + 360 + j * 42, y + 26, px + 388 + j * 42, y + 54), outline=(60, 70, 120), width=4)
im = im.filter(ImageFilter.GaussianBlur(0.6))
im.save("s3_assets/gk_rollbook.png")
print("ok")
