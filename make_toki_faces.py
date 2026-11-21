"""make_toki_faces.py ― 「その罪、時効にさせない」の顔（hana：工員の少女／toki：時の裁判官／boss：工場長）"""
import os
from PIL import Image, ImageDraw
import s3_face as F
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "s3_assets")
IRIS = {"hana": ((40, 55, 35), (120, 160, 100)), "toki": ((110, 70, 10), (255, 205, 90)), "boss": ((35, 25, 20), (95, 70, 55))}
for who, iris in IRIS.items():
    for e in F.COMBO:
        F.face(os.path.join(A, "face_%s_%s.png" % (who, e)), iris, e, girl=(who != "boss"))
for new, base in {"tearsad": "sad", "tearsadtalk": "sadtalk", "tearsmile": "blushsmile", "tearsmiletalk": "smiletalk"}.items():
    im = Image.open(os.path.join(A, "face_hana_%s.png" % base)).convert("RGBA")
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for cx in (352, 672):
        if "smile" not in base:
            d.ellipse((cx - 82, 440, cx + 82, 512), fill=(200, 235, 255, 120)); d.ellipse((cx - 50, 470, cx - 10, 490), fill=(255, 255, 255, 230))
        x0 = cx - 55 if cx < 512 else cx + 55
        for k in range(26):
            y = 505 + k * 6; w = 13 - k * 0.25; d.ellipse((x0 - w, y - w, x0 + w, y + w), fill=(170, 220, 255, 210))
    Image.alpha_composite(im, lay).save(os.path.join(A, "face_hana_%s.png" % new))
print("ok")
