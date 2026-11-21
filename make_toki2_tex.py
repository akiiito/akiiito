"""make_toki2_tex.py ― 第2話の小道具（罰金表・マッチ箱のラベル・金貨）。架空の会社"""
import os, random, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import make_toki_tex as T1
D = T1.D; f = T1.f; G = T1.G; M = T1.M
im = T1.paper(800, 1100, (225, 210, 175)); d = ImageDraw.Draw(im)
d.text((400, 110), "罰 金 表", font=f(M, 110), fill=(120, 15, 15), anchor="mm")
d.line((80, 190, 720, 190), fill=(40, 30, 25), width=5)
for i, (a, b) in enumerate([("おしゃべり", "3ペンス"), ("遅刻", "半日分"), ("マッチを落とす", "1ペンス"), ("手を止める", "3ペンス"), ("床が汚い", "3ペンス")]):
    y = 280 + i * 120
    d.text((90, y), a, font=f(M, 56), fill=(30, 24, 20), anchor="lm"); d.text((710, y), b, font=f(M, 56), fill=(120, 15, 15), anchor="rm")
    d.line((90, y + 50, 710, y + 50), fill=(150, 130, 100), width=2)
d.text((400, 950), "― 工場主 ―", font=f(M, 50), fill=(40, 30, 25), anchor="mm")
im.save(os.path.join(D, "fines.png"))
im = Image.new("RGB", (512, 256), (180, 40, 35)); d = ImageDraw.Draw(im)
d.rectangle((14, 14, 498, 242), outline=(240, 210, 120), width=10)
d.text((256, 100), "黄燐マッチ", font=f(G, 70), fill=(250, 230, 160), anchor="mm")
d.text((256, 190), "SAFETY? MATCHES", font=f(G, 34), fill=(250, 230, 160), anchor="mm")
im.save(os.path.join(D, "matchbox.png"))
im = Image.new("RGB", (256, 256), (200, 150, 40)); d = ImageDraw.Draw(im)
d.ellipse((6, 6, 250, 250), fill=(235, 185, 60), outline=(150, 100, 20), width=10); d.ellipse((40, 40, 216, 216), outline=(170, 120, 30), width=6)
d.text((128, 128), "1", font=f(G, 120), fill=(170, 120, 30), anchor="mm")
im.save(os.path.join(D, "coin.png"))
print("ok")
