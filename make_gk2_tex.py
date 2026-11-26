"""第2話：塗りつぶされた名札（下から「13」が透けて見える）"""
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
F = "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"
W, H = 800, 300
im = Image.new("RGB", (W, H), (236, 232, 220)); d = ImageDraw.Draw(im)
d.rectangle((6, 6, W - 7, H - 7), outline=(120, 110, 100), width=6)
d.text((30, 22), "2年B組　出席番号", font=ImageFont.truetype(F, 44), fill=(60, 60, 60))
d.text((60, 120), "13", font=ImageFont.truetype(F, 150), fill=(40, 40, 40))
d.text((330, 140), "（名前）", font=ImageFont.truetype(F, 110), fill=(40, 40, 40))
# 黒いマーカーで塗りつぶし（13 がうっすら透ける）
ov = Image.new("L", (W, H), 0); od = ImageDraw.Draw(ov); rnd = random.Random(4)
for k in range(46):
    y = 90 + k * 4.4 + rnd.uniform(-3, 3)
    od.line([(20 + rnd.uniform(0, 30), y), (W - 20 - rnd.uniform(0, 30), y + rnd.uniform(-10, 10))], fill=rnd.randint(248, 255), width=22)
ov = ov.filter(ImageFilter.GaussianBlur(2))
ink = Image.new("RGB", (W, H), (14, 14, 18))
im = Image.composite(ink, im, ov)
# 13 の部分だけ塗りが薄い（インクがかすれている）
thin = Image.new("L", (W, H), 0); ImageDraw.Draw(thin).text((60, 120), "13", font=ImageFont.truetype(F, 150), fill=95)
im = Image.composite(Image.new("RGB", (W, H), (120, 116, 110)), im, thin.filter(ImageFilter.GaussianBlur(1.5)))
im.save("s3_assets/gk_nameplate.png")
