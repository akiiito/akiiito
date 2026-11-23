"""post_fps1.py ― FPS第1話の仕上げ（frames_FPS1 → frames_FPS1_post）：ブルーム／衝撃コマ（色反転＋集中線）／弾道編集中の青白い世界／スロー中の集中線"""
import os, sys, json
import numpy as np
from PIL import Image
import post_block5 as P5
import post_toki2 as P2
HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SRC = os.path.join(HERE, arg("--src", "frames_FPS1v2")); DST = os.path.join(HERE, arg("--dst", "frames_FPS1v2_post"))
ONLY = [x for x in arg("--only", "").split(",") if x]
W_, H_ = P5.W_, P5.H_
os.makedirs(DST, exist_ok=True)
def process(name):
    m = json.load(open(os.path.join(SRC, name[:-4] + ".json")))
    im = Image.open(os.path.join(SRC, name)).convert("RGB")
    if im.size != (W_, H_): im = im.resize((W_, H_), Image.LANCZOS)
    a = np.asarray(im, np.float32) / 255
    out = a + P5.bloom(a) * 0.38
    out = out * np.array([1.03, 0.99, 0.95])                               # 夕方の暖色
    fr = int(name[:4]); iv = m.get("impact", 0.0); ed = m.get("edit", 0.0); dash = m.get("dash", 0.0)
    if ed > 0.01:                                                        # 弾道編集：青白く、光る線だけ色が残る
        lum = np.clip(out @ np.array([0.2126, 0.7152, 0.0722]), 0, 1)[..., None]
        cool = lum * np.array([0.75, 0.9, 1.15]) + 0.04
        keep = np.clip((out[..., 2:3] - out[..., 0:1]) * 3.0, 0, 1) * np.clip(lum * 2, 0, 1)
        out = out * (1 - ed) + (cool * (1 - keep) + out * keep) * ed
        yy = np.linspace(-1, 1, H_)[:, None]; xx = np.linspace(-1, 1, W_)[None, :]
        out *= (1 - 0.35 * ed * np.clip(xx ** 2 + yy ** 2 - 0.3, 0, 1))[..., None]
    cx, cy = W_ / 2, H_ * 0.45
    if "imp" in m and m["imp"][2] > 0: cx, cy = m["imp"][0] * W_, (1 - m["imp"][1]) * H_
    if iv > 0.7 and m.get("kind") != "fire":
        k = min(1.0, (iv - 0.7) / 0.3); inv = (1.0 - np.clip(out, 0, 1)) * np.array([0.45, 0.8, 1.0]) + 0.04
        L = P2.speed_lines(cx, cy, fr, 110, 0.22); out = out * (1 - k) + inv * (1 - L * 0.9) * k
    elif iv > 0.05 and m.get("kind") != "fire":
        out = out + P2.speed_lines(cx, cy, fr, 80, 0.3) * 0.55 * min(1.0, iv * 1.6)
    if dash > 0.05: out = out + P2.speed_lines(W_ / 2, H_ * 0.45, fr + 3, 90, 0.36) * 0.3 * dash
    out = out / (1 + 0.12 * np.maximum(out - 0.9, 0))
    rng = np.random.default_rng(fr); out += rng.standard_normal(out.shape[:2])[..., None] * 0.01
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(DST, name))
if __name__ == "__main__":
    names = sorted(f for f in os.listdir(SRC) if f.endswith(".png") and "_tmp" not in f)
    if ONLY: names = [n for n in names if n[:4] in ONLY]
    todo = [n for n in names if ONLY or not os.path.exists(os.path.join(DST, n))]
    for i, n in enumerate(todo):
        process(n)
        if i % 50 == 0: print("post", n, "%d/%d" % (i + 1, len(todo)), flush=True)
    print("done", len(todo))
