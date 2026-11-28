"""post_gk4.py ― 第4話の仕上げ：post_gk1 の処理のあと、世界のバグ（ずれ・色割れ・ブロック崩れ）、1年前の記憶の色、暗転を重ねる
  python3 post_gk4.py --src frames_GK4 --dst frames_GK4_post"""
import os, sys, json
import numpy as np
from PIL import Image
import post_gk1 as P
SRC, DST = P.SRC, P.DST
W_, H_ = P.W_, P.H_
YY = np.linspace(-1, 1, H_)[:, None]; XX = np.linspace(-1, 1, W_)[None, :]
VIG = np.clip(XX ** 2 * 0.7 + YY ** 2 * 0.5 - 0.15, 0, 1)[..., None]
def glitch(a, g, fr):
    rng = np.random.default_rng(fr * 7919 + 11)
    out = a.copy()
    # 横にずれる帯
    y = 0
    while y < H_:
        h = int(rng.integers(6, 90)); 
        if rng.random() < 0.25 + 0.5 * g:
            out[y:y + h] = np.roll(out[y:y + h], int(rng.normal(0, 1) * 140 * g), axis=1)
        y += h
    # 色の割れ（赤と青が左右にずれる）
    d = int(4 + 26 * g)
    out[..., 0] = np.roll(out[..., 0], d, axis=1); out[..., 2] = np.roll(out[..., 2], -d, axis=1)
    # ブロックが崩れる（別の場所の絵が貼りつく／色がつぶれる）
    for _ in range(int(40 * g * g) + (3 if g > 0.3 else 0)):
        bw, bh = int(rng.integers(40, 260)), int(rng.integers(16, 120))
        x0, y0 = int(rng.integers(0, W_ - bw)), int(rng.integers(0, H_ - bh))
        if rng.random() < 0.5:
            sx, sy = int(rng.integers(0, W_ - bw)), int(rng.integers(0, H_ - bh)); out[y0:y0 + bh, x0:x0 + bw] = a[sy:sy + bh, sx:sx + bw]
        else:
            blk = out[y0:y0 + bh, x0:x0 + bw]; out[y0:y0 + bh, x0:x0 + bw] = np.round(blk * 3) / 3 * np.array(rng.choice([[1, 0.3, 1], [0.3, 1, 1], [1, 1, 1], [1, 0.2, 0.2]]))
    # 走査線
    out *= (1 - 0.18 * g * (np.arange(H_) % 4 < 2))[:, None, None]
    if g > 0.85 and rng.random() < 0.5: out = 1 - out                                   # 一瞬の色反転
    return out
def process(name):
    P.process(name)
    m = json.load(open(os.path.join(SRC, name[:-4] + ".json")))
    g, mem, dark = m.get("glitch", 0.0), m.get("mem", 0.0), m.get("dark", 0.0)
    if g < 0.01 and mem < 0.01 and dark < 0.01: return
    a = np.asarray(Image.open(os.path.join(DST, name)).convert("RGB"), np.float32) / 255
    fr = int(name[:4])
    if mem > 0.01:                                                                       # 1年前：赤くくすんだ記憶
        lum = (a @ np.array([0.2126, 0.7152, 0.0722]))[..., None]
        a = a * 0.55 + lum * np.array([1.15, 0.72, 0.5]) * 0.45
        a = a * (1 - 0.55 * VIG) + VIG * 0.55 * a * np.array([0.9, 0.2, 0.1])
        a *= 0.92 + 0.08 * np.random.default_rng(fr).random()
    if g > 0.01: a = glitch(a, g, fr)
    if dark > 0.01: a = a * (1 - dark) * (1 - 0.5 * VIG * dark)
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(DST, name))
if __name__ == "__main__":
    names = sorted(f for f in os.listdir(SRC) if f.endswith(".png") and "_tmp" not in f)
    if P.ONLY: names = [n for n in names if n[:4] in P.ONLY]
    todo = [n for n in names if P.ONLY or not os.path.exists(os.path.join(DST, n))]
    for i, n in enumerate(todo):
        process(n)
        if i % 50 == 0: print("post", n, "%d/%d" % (i + 1, len(todo)), flush=True)
    print("done", len(todo))
