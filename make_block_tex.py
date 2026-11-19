"""make_block_tex.py ― ブロック世界のオリジナル16x16ドット絵テクスチャ（色も模様も自作）→ blk_tex/*.png"""
import os, random
from PIL import Image
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blk_tex"); os.makedirs(OUT, exist_ok=True)
def tile(name, base, var, pattern=None, seed=1):
    r = random.Random(seed); im = Image.new("RGB", (16, 16))
    for y in range(16):
        for x in range(16):
            c = pattern(x, y, r) if pattern else None
            if c is None:
                k = r.uniform(-var, var); c = tuple(max(0, min(255, int(v * (1 + k)))) for v in base)
            im.putpixel((x, y), c)
    im.save(os.path.join(OUT, name + ".png"))
# このブロック世界の色：ミント色の草・ラベンダー色の土・白い樹皮・桜色の葉・空色の板（よく知られたゲームと見分けがつく配色）
tile("grass_top", (128, 214, 178), 0.1, lambda x, y, r: (255, 255, 240) if r.random() < 0.03 else None, 2)
tile("grass_side", (164, 134, 176), 0.1, lambda x, y, r: (tuple(int(v * r.uniform(0.9, 1.08)) for v in (128, 214, 178)) if y < 5 - (x % 4 == 1) else None), 3)
tile("dirt", (164, 134, 176), 0.12, None, 4)
tile("stone", (120, 128, 150), 0.08, lambda x, y, r: (150, 160, 185) if (x * 5 + y) % 13 == 0 else None, 5)
tile("log_side", (232, 228, 220), 0.04, lambda x, y, r: (60, 56, 64) if (y % 6 == 2 and 3 < x < 9) or (y % 7 == 5 and x > 10) else None, 6)
tile("log_top", (214, 196, 170), 0.05, lambda x, y, r: (232, 228, 220) if max(abs(x - 7.5), abs(y - 7.5)) > 6 else None, 7)
tile("leaves", (246, 176, 200), 0.12, lambda x, y, r: (222, 130, 170) if r.random() < 0.2 else ((255, 236, 244) if r.random() < 0.08 else None), 8)
tile("planks", (150, 196, 228), 0.05, lambda x, y, r: (96, 140, 186) if x % 8 == 0 or (y == 7 and x % 8 < 7) else None, 9)
tile("shadow", (70, 14, 24), 0.2, lambda x, y, r: (30, 4, 10) if r.random() < 0.25 else None, 10)
print(sorted(os.listdir(OUT)))
