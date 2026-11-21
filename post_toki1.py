"""
post_toki1.py ― 第1話の仕上げ（frames_TOKI1 → frames_TOKI1_post）
  拡大＋ブルーム＋窓からの光の筋＋「時が止まった」間は色を抜いて金と緑だけ残す＋フラッシュ＋夜明けの暖色＋粒子
"""
import os, sys, json
import numpy as np
from PIL import Image
import post_block5 as P5
HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SRC = os.path.join(HERE, arg("--src", "frames_TOKI1")); DST = os.path.join(HERE, arg("--dst", "frames_TOKI1_post"))
ONLY = [x for x in arg("--only", "").split(",") if x]
W_, H_ = P5.W_, P5.H_
os.makedirs(DST, exist_ok=True)

def keep_mask(a):
    """金（黄〜橙）と夜光の緑だけ色を残す"""
    mx = a.max(-1); mn = a.min(-1); sat = (mx - mn) / (mx + 1e-4)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    gold = np.clip((r - b) * 3.0, 0, 1) * np.clip((g - b) * 3.0, 0, 1) * (r >= g * 0.85)
    green = np.clip((g - r) * 4.0, 0, 1) * np.clip((g - b) * 4.0, 0, 1)
    return np.clip(np.maximum(gold, green) * np.clip(sat * 2.5, 0, 1) * np.clip(mx * 2.0, 0, 1), 0, 1)[..., None]

def process(name):
    p = os.path.join(SRC, name); m = json.load(open(os.path.join(SRC, name[:-4] + ".json")))
    im = Image.open(p).convert("RGB")
    if im.size != (W_, H_): im = im.resize((W_, H_), Image.LANCZOS)
    a = np.asarray(im, dtype=np.float32) / 255
    out = a + P5.bloom(a) * 0.36
    sx, sy, sz = m["sun"]; lt = m["light"]
    if sz > 0 and -0.3 < sx < 1.3 and -0.3 < sy < 1.5:
        out = out + P5.beams(a, sx, sy, 0.5 * lt) * (np.array([0.6, 0.8, 1.2]) * (1 - m["dawn"]) + np.array([1.0, 1.0, 1.0]) * m["dawn"])
    if m["stop"]:                                                        # 時が止まった世界：青みの白黒、金と緑だけ色が残る
        lum = (out @ np.array([0.2126, 0.7152, 0.0722]))[..., None]
        mono = lum * np.array([0.82, 0.9, 1.08])
        k = keep_mask(np.clip(a, 0, 1))
        out = mono * (1 - k) + out * k * 1.15
        yy = np.linspace(-1, 1, H_)[:, None]; xx = np.linspace(-1, 1, W_)[None, :]
        out *= (1 - 0.35 * np.clip(xx ** 2 + yy ** 2 - 0.3, 0, 1))[..., None]          # 周辺を暗く
    fl = min(1.0, m.get("flash", 0.0))
    if fl > 0.02: out = out + fl * 0.55 * np.array([0.95, 0.97, 1.0])
    dn = m["dawn"]
    out = out * (1 + dn * 0.8 * (np.array([1.07, 1.0, 0.88]) - 1.0))
    out = out / (1 + 0.12 * np.maximum(out - 0.9, 0))
    rng = np.random.default_rng(int(name[:4]))
    out += rng.standard_normal(out.shape[:2])[..., None] * (0.012 if m["stop"] else 0.008)
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(DST, name))

if __name__ == "__main__":
    names = sorted(f for f in os.listdir(SRC) if f.endswith(".png") and "_tmp" not in f)
    if ONLY: names = [n for n in names if n[:4] in ONLY]
    todo = [n for n in names if ONLY or not os.path.exists(os.path.join(DST, n))]
    for i, n in enumerate(todo):
        process(n)
        if i % 50 == 0: print("post", n, "%d/%d" % (i + 1, len(todo)), flush=True)
    print("done", len(todo))
