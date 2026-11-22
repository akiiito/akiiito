"""
post_block6.py ― 完結編の仕上げ（frames_BLK6 → frames_BLK6_post）
  ブルーム・光の筋（post_block5）＋ 当たった瞬間の色反転コマ＋集中線＋「光と影が反転した世界」（金と黒のネガ）
"""
import os, sys, json
import numpy as np
from PIL import Image
import post_block5 as P5
import post_toki2 as P2
HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SRC = os.path.join(HERE, arg("--src", "frames_BLK6W")); DST = os.path.join(HERE, arg("--dst", "frames_BLK6W_post"))
ONLY = [x for x in arg("--only", "").split(",") if x]
W_, H_ = P5.W_, P5.H_
os.makedirs(DST, exist_ok=True)

def process(name):
    m = json.load(open(os.path.join(SRC, name[:-4] + ".json")))
    im = Image.open(os.path.join(SRC, name)).convert("RGB")
    if im.size != (W_, H_): im = im.resize((W_, H_), Image.LANCZOS)
    a = np.asarray(im, np.float32) / 255
    out = a + P5.bloom(a) * 0.4
    sx, sy, sz = m["sun"]; lt = m.get("light", 0.0)
    if sz > 0 and lt > 0.05 and -0.3 < sx < 1.3 and -0.3 < sy < 1.5: out = out + P5.beams(a, sx, sy, 0.95 * lt)
    out = out * (1 + lt * 0.8 * (np.array([1.07, 1.0, 0.88]) - 1.0))
    fr = int(name[:4]); iv = m.get("impact", 0.0); dm = m.get("domain", 0.0); dash = m.get("dash", 0.0)
    lum = np.clip(out @ np.array([0.2126, 0.7152, 0.0722]), 0, 1)[..., None]
    if dm > 0.01:                                                        # 光と影が反転した世界：金と黒のネガ
        neg = 1.0 - lum
        duo = np.clip(neg ** 1.6, 0, 1) * np.array([1.0, 0.78, 0.36]) + np.clip(neg - 0.85, 0, 1) * 2.0
        out = out * (1 - dm) + duo * dm
    cx, cy = W_ / 2, H_ * 0.45
    if "imp" in m and m["imp"][2] > 0: cx, cy = m["imp"][0] * W_, (1 - m["imp"][1]) * H_
    if iv > 0.7:                                                         # 衝撃コマ：色反転＋集中線（2〜3コマ）
        k = min(1.0, (iv - 0.7) / 0.3)
        inv = 1.0 - np.clip(out, 0, 1)
        inv = inv * np.array([1.0, 0.35, 0.3]) if m.get("kind") in ("smash", "fhit") else inv * np.array([0.4, 0.75, 1.0]) + 0.05
        L = P2.speed_lines(cx, cy, fr, 110, 0.22)
        out = out * (1 - k) + (inv * (1 - L * 0.9) + L * 0.0) * k
    elif iv > 0.05:
        L = P2.speed_lines(cx, cy, fr, 80, 0.3); out = out + L * 0.6 * min(1.0, iv * 1.6)
    if dash > 0.05: out = out + P2.speed_lines(W_ / 2, H_ * 0.45, fr + 3, 90, 0.34) * 0.45 * dash
    out = out / (1 + 0.12 * np.maximum(out - 0.9, 0))
    rng = np.random.default_rng(fr)
    out += rng.standard_normal(out.shape[:2])[..., None] * 0.009
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(DST, name))

if __name__ == "__main__":
    names = sorted(f for f in os.listdir(SRC) if f.endswith(".png") and "_tmp" not in f)
    if ONLY: names = [n for n in names if n[:4] in ONLY]
    todo = [n for n in names if ONLY or not os.path.exists(os.path.join(DST, n))]
    for i, n in enumerate(todo):
        process(n)
        if i % 50 == 0: print("post", n, "%d/%d" % (i + 1, len(todo)), flush=True)
    print("done", len(todo))
