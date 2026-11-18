"""
s3_face.py ― アニメ顔のパーツ（目・眉・口・ほお）を透明PNGで描く（顔に貼るデカール）
  python3 s3_face.py → s3_assets/face_<who>_<expr>.png
expr: base（口とじ）, talk（口あき）, blink（目とじ）, smile, shock, blush
"""
import os
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1024, 768

def eye(d, cx, cy, iris, s=1.0, closed=False, happy=False, wide=False, lash=(30, 22, 28)):
    w, h = 150 * s, 190 * s * (1.12 if wide else 1.0)
    if closed or happy:
        # 閉じた目（下向きの弧）／笑い目（上向きの弧）
        box = [cx - w / 2, cy - h * 0.15, cx + w / 2, cy + h * 0.35]
        if happy:
            d.arc([cx - w / 2, cy - h * 0.05, cx + w / 2, cy + h * 0.55], 200, 340, fill=lash, width=int(16 * s))
        else:
            d.arc(box, 20, 160, fill=lash, width=int(16 * s))
        return
    # 白目
    d.ellipse([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], fill=(255, 255, 255, 255))
    # 虹彩（上が暗く下が明るいグラデーション）
    iw, ih = w * 0.78, h * 0.86
    top, bot = iris
    for k in range(int(ih)):
        t = k / ih
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        y = cy - ih / 2 + k + h * 0.05
        half = (iw / 2) * (1 - (2 * t - 1) ** 2) ** 0.5
        d.line([cx - half, y, cx + half, y], fill=c + (255,))
    d.ellipse([cx - iw * 0.22, cy - ih * 0.12, cx + iw * 0.22, cy + ih * 0.25], fill=(20, 12, 18, 255))      # 瞳孔
    d.ellipse([cx - iw * 0.36, cy - ih * 0.36, cx - iw * 0.02, cy - ih * 0.06], fill=(255, 255, 255, 255))  # ハイライト大
    d.ellipse([cx + iw * 0.12, cy + ih * 0.18, cx + iw * 0.3, cy + ih * 0.32], fill=(255, 255, 255, 230))   # ハイライト小
    # 上まつげ（太い弧）と目尻
    d.arc([cx - w * 0.62, cy - h * 0.62, cx + w * 0.62, cy + h * 0.5], 195, 345, fill=lash, width=int(20 * s))
    d.line([cx + w * 0.5, cy - h * 0.18, cx + w * 0.66, cy - h * 0.3], fill=lash, width=int(12 * s))
    d.arc([cx - w * 0.4, cy + h * 0.2, cx + w * 0.4, cy + h * 0.56], 60, 120, fill=lash, width=int(5 * s))   # 下まつげ

COMBO = {  # 表情名: (目, 口, 照れ)
    "base": ("base", "base", False), "talk": ("base", "talk", False), "blink": ("blink", "base", False),
    "smile": ("smile", "smile", False), "smiletalk": ("smile", "talk", False), "shock": ("shock", "shock", False),
    "shockc": ("shock", "base", False), "blush": ("base", "base", True), "blushtalk": ("base", "talk", True),
    "blushsmile": ("smile", "smile", True)}

def face(path, iris, expr="base", girl=True):
    eyes, mouth, blush = COMBO[expr]
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    lash = (40, 26, 30) if girl else (45, 32, 28)
    s = 1.3 if girl else 1.08
    ey = 380
    sleepy = not girl
    # ほお
    if girl or blush:
        bl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(bl)
        a = 150 if blush else 70
        for cx in (290, 734):
            bd.ellipse([cx - 80, 510, cx + 80, 570], fill=(255, 120, 130, a))
        if blush:
            for cx in (290, 734):
                for k in range(3):
                    bd.line([cx - 40 + k * 30, 520, cx - 55 + k * 30, 560], fill=(230, 80, 100, 200), width=5)
        im.alpha_composite(bl.filter(ImageFilter.GaussianBlur(10)))
        d = ImageDraw.Draw(im)
    for side, cx in ((-1, 352), (1, 672)):
        if eyes == "blink":
            eye(d, cx, ey, iris, s, closed=True, lash=lash)
        elif eyes == "smile":
            eye(d, cx, ey, iris, s, happy=True, lash=lash)
        else:
            eye(d, cx, ey, iris, s, wide=(eyes == "shock"), lash=lash)
            if sleepy and eyes != "shock":                       # 眠そうなまぶた
                d.rectangle([cx - 100, ey - 140, cx + 100, ey - 48], fill=(0, 0, 0, 0))
                d.line([cx - 92, ey - 48, cx + 92, ey - 48], fill=lash, width=16)
        # 眉
        by = ey - int((150 if eyes == "shock" else 130) * s)
        d.arc([cx - 70 * s, by, cx + 70 * s, by + 60 * s], 200 if side < 0 else 200, 340, fill=lash, width=8)
    # 口
    mx, my = 512, 600
    if mouth in ("talk", "shock"):
        r = 34 if mouth == "talk" else 46
        d.ellipse([mx - r * 0.9, my - r * 0.55, mx + r * 0.9, my + r * 0.75], fill=(150, 50, 60, 255), outline=(60, 20, 25, 255), width=5)
        d.ellipse([mx - r * 0.5, my + r * 0.15, mx + r * 0.5, my + r * 0.7], fill=(235, 120, 130, 255))
    elif mouth == "smile":
        d.arc([mx - 40, my - 30, mx + 40, my + 20], 20, 160, fill=(60, 20, 25, 255), width=7)
    else:
        d.arc([mx - 22, my - 14, mx + 22, my + 8], 30, 150, fill=(60, 20, 25, 255), width=6)
    im.save(path)

if __name__ == "__main__":
    out = os.path.join(HERE, "s3_assets")
    for e in COMBO:
        face(os.path.join(out, "face_mei_%s.png" % e), ((70, 30, 50), (210, 110, 120)), e, girl=True)
        face(os.path.join(out, "face_yota_%s.png" % e), ((60, 40, 25), (170, 120, 70)), e, girl=False)
    print("ok")
