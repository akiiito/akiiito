"""make_gk_tex.py ― 学園デスゲームの小物の絵（python3）：16:44で止まった時計、黒板のチョーク文字"""
import math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(HERE, "s3_assets")
F = "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"
# 時計（16:44）
S = 512; im = Image.new("RGB", (S, S), (240, 238, 230)); d = ImageDraw.Draw(im); c = S / 2
d.ellipse([6, 6, S - 6, S - 6], outline=(40, 40, 40), width=18)
for k in range(60):
    a = k / 60 * 2 * math.pi; r0 = 210 if k % 5 else 185
    d.line([(c + r0 * math.sin(a), c - r0 * math.cos(a)), (c + 228 * math.sin(a), c - 228 * math.cos(a))], fill=(30, 30, 30), width=10 if k % 5 == 0 else 3)
f = ImageFont.truetype(F, 44)
for h in range(1, 13):
    a = h / 12 * 2 * math.pi; d.text((c + 150 * math.sin(a), c - 150 * math.cos(a)), str(h), font=f, fill=(30, 30, 30), anchor="mm")
def hand(frac, ln, w, col):
    a = frac * 2 * math.pi; d.line([(c - 20 * math.sin(a), c + 20 * math.cos(a)), (c + ln * math.sin(a), c - ln * math.cos(a))], fill=col, width=w)
hand((4 + 44 / 60) / 12, 120, 16, (20, 20, 20)); hand(44 / 60, 190, 10, (20, 20, 20)); hand(0.0 / 60, 200, 4, (190, 30, 30))
d.ellipse([c - 14, c - 14, c + 14, c + 14], fill=(20, 20, 20))
im.save(os.path.join(A, "gk_clock.png"))
# 黒板のチョーク文字（透明背景）
Wb, Hb = 2200, 550; im = Image.new("RGBA", (Wb, Hb), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
ch = (235, 235, 225, 230)
d.text((60, 40), "11月25日（水）", font=ImageFont.truetype(F, 86), fill=ch)
d.text((Wb - 60, 40), "日直", font=ImageFont.truetype(F, 80), fill=ch, anchor="ra")
d.text((Wb - 60, 150), "13番", font=ImageFont.truetype(F, 120), fill=ch, anchor="ra")
d.text((Wb / 2, Hb / 2 + 40), "放課後　教室に残ること", font=ImageFont.truetype(F, 96), fill=(235, 235, 225, 120), anchor="mm")
im = im.filter(ImageFilter.GaussianBlur(1.2)); im.save(os.path.join(A, "gk_board.png"))
print("ok")
