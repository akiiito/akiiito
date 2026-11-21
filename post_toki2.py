"""
post_toki2.py ― 第2話の仕上げ（frames_TOKI2 → frames_TOKI2_post）
  第1話の仕上げ ＋ 当たった瞬間の「衝撃コマ」（白黒反転ぎみ・集中線）＋ 踏みこみ・吹っ飛びの集中線
"""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import post_toki1 as P1
import post_block5 as P5
HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SRC = os.path.join(HERE, arg("--src", "frames_TOKI2")); DST = os.path.join(HERE, arg("--dst", "frames_TOKI2_post"))
ONLY = [x for x in arg("--only", "").split(",") if x]
W_, H_ = P5.W_, P5.H_
os.makedirs(DST, exist_ok=True)

def speed_lines(cx, cy, seed, n=90, inner=0.28):
    """画面の端から中心(cx,cy)へ向かう集中線（白）のマスク 0..1"""
    rng = np.random.default_rng(seed)
    im = Image.new("L", (W_, H_), 0); d = ImageDraw.Draw(im)
    R = math.hypot(W_, H_)
    for k in range(n):
        a = rng.uniform(0, 2 * math.pi); w = rng.uniform(0.004, 0.018)
        r0 = R * rng.uniform(inner, inner + 0.18)
        p0 = (cx + math.cos(a) * r0, cy + math.sin(a) * r0)
        p1 = (cx + math.cos(a - w) * R, cy + math.sin(a - w) * R); p2 = (cx + math.cos(a + w) * R, cy + math.sin(a + w) * R)
        d.polygon([p0, p1, p2], fill=255)
    return np.asarray(im.filter(ImageFilter.GaussianBlur(1.2)), np.float32)[..., None] / 255

def process(name):
    m = json.load(open(os.path.join(SRC, name[:-4] + ".json")))
    P1.SRC, P1.DST = SRC, DST
    P1.process(name)                                                     # 第1話と同じ仕上げ（ブルーム・光の筋・時止めの色）
    im = Image.open(os.path.join(DST, name)).convert("RGB")
    a = np.asarray(im, np.float32) / 255
    iv = m.get("impact", 0.0); dash = m.get("dash", 0.0); fr = int(name[:4])
    cx, cy = W_ / 2, H_ * 0.45
    if "imp" in m and m["imp"][2] > 0: cx, cy = m["imp"][0] * W_, (1 - m["imp"][1]) * H_
    if iv > 0.75:                                                        # 衝撃コマ：ネガ反転ぎみの白黒＋赤み
        lum = a @ np.array([0.2126, 0.7152, 0.0722])
        neg = np.clip(1.0 - (lum - 0.15) * 1.6, 0, 1)[..., None] * np.array([1.0, 0.92, 0.88])
        k = min(1.0, (iv - 0.75) / 0.25)
        a = a * (1 - k) + neg * k
        a = a * (1 - speed_lines(cx, cy, fr) * 0.9 * k) + speed_lines(cx, cy, fr + 7, 60) * 0.0
    elif iv > 0.05:                                                      # 余韻：中心へ白い集中線
        L = speed_lines(cx, cy, fr, 70, 0.32)
        a = a + L * 0.55 * min(1.0, iv * 1.8)
    if dash > 0.05:
        L = speed_lines(W_ / 2, H_ * 0.45, fr + 3, 80, 0.36)
        a = a + L * 0.4 * dash
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(DST, name))

if __name__ == "__main__":
    names = sorted(f for f in os.listdir(SRC) if f.endswith(".png") and "_tmp" not in f)
    if ONLY: names = [n for n in names if n[:4] in ONLY]
    todo = [n for n in names if ONLY or not os.path.exists(os.path.join(DST, n))]
    for i, n in enumerate(todo):
        process(n)
        if i % 50 == 0: print("post", n, "%d/%d" % (i + 1, len(todo)), flush=True)
    print("done", len(todo))
