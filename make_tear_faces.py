"""make_tear_faces.py ― めいの顔に涙をのせた表情を作る（ハナ用：tearsad / tearsadtalk / tearsmile / tearsmiletalk / tearblink）"""
import os
from PIL import Image, ImageDraw, ImageFilter
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "s3_assets")
SRC = {"tearsad": "sad", "tearsadtalk": "sadtalk", "tearsmile": "blushsmile", "tearsmiletalk": "smiletalk", "tearblink": "sadblink"}
for new, base in SRC.items():
    im = Image.open(os.path.join(A, "face_mei_%s.png" % base)).convert("RGBA")
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    eyes_open = "blink" not in base and "smile" not in base
    for cx in (352, 672):
        if eyes_open:                                     # 目にたまった涙（下のふちに光る帯）
            d.ellipse((cx - 82, 440, cx + 82, 512), fill=(200, 235, 255, 120))
            d.ellipse((cx - 50, 470, cx - 10, 490), fill=(255, 255, 255, 230))
        # ほおを伝う涙のすじ
        x0 = cx - 55 if cx < 512 else cx + 55
        for k in range(26):
            y = 505 + k * 6; w = 13 - k * 0.25
            d.ellipse((x0 - w, y - w, x0 + w, y + w), fill=(170, 220, 255, 210))
        d.ellipse((x0 - 16, 655, x0 + 16, 695), fill=(170, 220, 255, 230))
        d.ellipse((x0 - 6, 662, x0 + 2, 676), fill=(255, 255, 255, 240))
    lay = lay.filter(ImageFilter.GaussianBlur(1.2))
    im.alpha_composite(lay); im.save(os.path.join(A, "face_mei_%s.png" % new)); print(new)
