"""make_toki2_faces.py ― 第2話の顔（sae：マッチ工場の少女／owner：工場主。殴られ顔 hurt・目を回す dizzy も）"""
import os, math
from PIL import Image, ImageDraw
import s3_face as F
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "s3_assets")
for who, iris, girl in (("sae", ((40, 50, 70), (120, 150, 200)), True), ("owner", ((40, 28, 20), (110, 75, 50)), False)):
    for e in F.COMBO: F.face(os.path.join(A, "face_%s_%s.png" % (who, e)), iris, e, girl=girl)
for new, base in {"tearsad": "sad", "tearsadtalk": "sadtalk", "tearsmile": "blushsmile", "tearsmiletalk": "smiletalk"}.items():
    im = Image.open(os.path.join(A, "face_sae_%s.png" % base)).convert("RGBA")
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for cx in (352, 672):
        x0 = cx - 55 if cx < 512 else cx + 55
        for k in range(26):
            y = 505 + k * 6; w = 13 - k * 0.25; d.ellipse((x0 - w, y - w, x0 + w, y + w), fill=(170, 220, 255, 210))
    Image.alpha_composite(im, lay).save(os.path.join(A, "face_sae_%s.png" % new))
def noeyes(src):
    im = Image.open(os.path.join(A, src)).convert("RGBA"); px = im.load()
    for x in range(im.size[0]):
        for y in range(250, 540):
            if abs(x - 352) < 130 or abs(x - 672) < 130: px[x, y] = (0, 0, 0, 0)
    return im
im = noeyes("face_owner_shock.png"); d = ImageDraw.Draw(im)         # ＞＜
for cx, s in ((352, 1), (672, -1)):
    d.line([(cx - 60 * s, 340), (cx + 50 * s, 400), (cx - 60 * s, 460)], fill=(30, 20, 20, 255), width=26, joint="curve")
for k in range(3): d.line([(250 + k * 40, 560), (270 + k * 40, 600)], fill=(200, 60, 60, 160), width=10)
im.save(os.path.join(A, "face_owner_hurt.png"))
im = noeyes("face_owner_shock.png"); d = ImageDraw.Draw(im)         # ぐるぐる目
for cx in (352, 672):
    pts = [(cx + 6 * a * math.cos(a), 400 + 6 * a * math.sin(a)) for a in [i * 0.2 for i in range(60)]]
    d.line(pts, fill=(30, 20, 20, 255), width=12)
im.save(os.path.join(A, "face_owner_dizzy.png"))
print("ok")
