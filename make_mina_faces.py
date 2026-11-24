"""make_mina_faces.py ― ミナ（狙撃手の少女）の顔。涙つきの表情も作る"""
import os
from PIL import Image, ImageDraw
import s3_face as F
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "s3_assets")
for e in F.COMBO: F.face(os.path.join(A, "face_mina_%s.png" % e), ((60, 30, 80), (170, 110, 220)), e, girl=True)
for new, base in {"tearsad": "sad", "tearsadtalk": "sadtalk"}.items():
    im = Image.open(os.path.join(A, "face_mina_%s.png" % base)).convert("RGBA")
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for cx in (352, 672):
        d.ellipse((cx - 82, 440, cx + 82, 512), fill=(200, 235, 255, 120))
        x0 = cx - 55 if cx < 512 else cx + 55
        for k in range(26):
            y = 505 + k * 6; w = 13 - k * 0.25; d.ellipse((x0 - w, y - w, x0 + w, y + w), fill=(170, 220, 255, 210))
    Image.alpha_composite(im, lay).save(os.path.join(A, "face_mina_%s.png" % new))
print("ok")
