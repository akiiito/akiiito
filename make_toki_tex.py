"""make_toki_tex.py ― 第1話の小道具の絵（報告書・新聞・時計の文字盤）。架空の会社・架空の見出し"""
import os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "toki_tex"); os.makedirs(D, exist_ok=True)
G = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
M = "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf"
if not os.path.exists(M): M = G
f = lambda p, s: ImageFont.truetype(p, s)
rnd = random.Random(4)
def paper(w, h, base=(232, 220, 190)):
    im = Image.new("RGB", (w, h), base); px = im.load()
    for _ in range(w * h // 6):
        x, y = rnd.randrange(w), rnd.randrange(h); c = px[x, y]; k = rnd.randint(-14, 8); px[x, y] = tuple(max(0, min(255, v + k)) for v in c)
    d = ImageDraw.Draw(im)
    for _ in range(6):                                        # しみ
        x, y, r = rnd.randrange(w), rnd.randrange(h), rnd.randint(20, 70)
        d.ellipse((x - r, y - r, x + r, y + r), fill=tuple(v - 18 for v in base))
    return im.filter(ImageFilter.GaussianBlur(1.2))
# 報告書
im = paper(840, 1200); d = ImageDraw.Draw(im)
d.text((420, 90), "社外秘", font=f(G, 64), fill=(150, 20, 20), anchor="mm")
d.rectangle((300, 50, 540, 130), outline=(150, 20, 20), width=6)
d.text((420, 230), "文字盤工員 健康調査 報告書", font=f(M, 54), fill=(30, 25, 20), anchor="mm")
d.line((90, 290, 750, 290), fill=(30, 25, 20), width=3)
for i, s in enumerate(["一、工員の多数に 歯・あごの異常を認む", "二、原因は 夜光塗料の口中摂取と推定", "三、作業方法の 即時変更を要す", "", "結論：重大な健康被害のおそれあり"]):
    d.text((100, 360 + i * 90), s, font=f(M, 40), fill=(40, 32, 26))
for i in range(5): d.line((100, 860 + i * 52, 740 - rnd.randint(0, 200), 860 + i * 52), fill=(120, 110, 95), width=4)
st = Image.new("RGBA", (420, 220), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
sd.rounded_rectangle((10, 10, 410, 210), 20, outline=(200, 20, 30, 230), width=14); sd.text((210, 112), "危険", font=f(G, 140), fill=(200, 20, 30, 230), anchor="mm")
st = st.rotate(-12, expand=True, resample=Image.BICUBIC); im.paste(st, (380, 820), st)
im.save(os.path.join(D, "report.png"))
# 新聞
im = paper(1000, 1400, (225, 218, 200)); d = ImageDraw.Draw(im)
d.text((500, 70), "夜光新報", font=f(M, 90), fill=(20, 18, 16), anchor="mm")
d.line((40, 135, 960, 135), fill=(20, 18, 16), width=6); d.line((40, 150, 960, 150), fill=(20, 18, 16), width=2)
d.text((500, 290), "時計工場", font=f(G, 170), fill=(15, 12, 10), anchor="mm")
d.text((500, 480), "危険を隠ぺい", font=f(G, 150), fill=(160, 20, 20), anchor="mm")
d.text((500, 620), "工員の少女たち、被害を訴え", font=f(M, 62), fill=(20, 18, 16), anchor="mm")
d.line((40, 680, 960, 680), fill=(20, 18, 16), width=3)
for c in range(4):
    for r in range(13):
        x0 = 60 + c * 230; y = 720 + r * 50
        d.line((x0, y, x0 + 200 - rnd.randint(0, 60), y), fill=(90, 85, 75), width=6)
im.save(os.path.join(D, "news.png"))
# 時計の文字盤（夜光の数字）
im = Image.new("RGB", (512, 512), (20, 26, 22)); d = ImageDraw.Draw(im)
import math
d.ellipse((16, 16, 496, 496), fill=(28, 34, 30), outline=(120, 120, 110), width=10)
for k in range(12):
    a = math.radians(k * 30); x, y = 256 + 190 * math.sin(a), 256 - 190 * math.cos(a)
    d.text((x, y), str(k or 12), font=f(G, 58), fill=(150, 255, 120), anchor="mm")
im.save(os.path.join(D, "dial.png"))
mk = Image.new("L", (512, 512), 0); dm = ImageDraw.Draw(mk)
for k in range(12):
    a = math.radians(k * 30); x, y = 256 + 190 * math.sin(a), 256 - 190 * math.cos(a)
    dm.text((x, y), str(k or 12), font=f(G, 58), fill=255, anchor="mm")
mk.save(os.path.join(D, "dial_mask.png"))
print("ok")
