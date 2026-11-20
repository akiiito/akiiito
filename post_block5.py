"""
post_block5.py ― 単体回の仕上げ（frames_BLK5 → frames_BLK5_post）
  1080x1920 へ拡大 ＋ 光のにじみ（ブルーム）＋ 夕日の光の筋（太陽の画面位置から放射状に）＋ ごく弱い粒子ノイズ
  python3 post_block5.py [--src frames_BLK5] [--dst frames_BLK5_post] [--only 0529,0530]
"""
import os, sys, json
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SRC = os.path.join(HERE, arg("--src", "frames_BLK5")); DST = os.path.join(HERE, arg("--dst", "frames_BLK5_post"))
ONLY = [x for x in arg("--only", "").split(",") if x]
W_, H_ = 1080, 1920
os.makedirs(DST, exist_ok=True)

def bloom(a):
    """明るいところだけ取り出して何段かにぼかし、足す（暖色寄り）"""
    lum = a @ np.array([0.2126, 0.7152, 0.0722])
    k = np.clip((lum - 0.72) / 0.28, 0, 1)[..., None]
    br = Image.fromarray((a * k * 255).astype(np.uint8))
    acc = np.zeros_like(a)
    for div, rad, w in ((4, 6, 0.5), (8, 10, 0.35), (16, 14, 0.25)):
        sm = br.resize((W_ // div, H_ // div), Image.BILINEAR).filter(ImageFilter.GaussianBlur(rad))
        acc += np.asarray(sm.resize((W_, H_), Image.BILINEAR), dtype=np.float32) / 255 * w
    return acc * np.array([1.0, 0.9, 0.78])

def beams(a, sx, sy, strength):
    """太陽（画面位置 sx,sy：0..1、上が1）から放射状にのびる光の筋"""
    lum = a @ np.array([0.2126, 0.7152, 0.0722])
    k = np.clip((lum - 0.68) / 0.3, 0, 1)[..., None]
    sw, sh = W_ // 4, H_ // 4
    src = Image.fromarray((a * k * 255).astype(np.uint8)).resize((sw, sh), Image.BILINEAR)
    cx, cy = sx * sw, (1 - sy) * sh
    acc = np.zeros((sh, sw, 3), np.float32); n = 28
    for i in range(n):
        s = 1.0 - 0.55 * i / n                                   # 太陽に向かって縮める＝太陽から外へ伸びる
        img = src.transform((sw, sh), Image.AFFINE, (s, 0, cx * (1 - s), 0, s, cy * (1 - s)), resample=Image.BILINEAR)
        acc += np.asarray(img, dtype=np.float32) / 255 * (1 - i / n)
    acc /= n * 0.5
    acc = np.asarray(Image.fromarray(np.clip(acc * 255, 0, 255).astype(np.uint8)).resize((W_, H_), Image.BILINEAR), np.float32) / 255
    return acc * strength * np.array([1.0, 0.78, 0.5])

def process(name):
    p = os.path.join(SRC, name); meta = os.path.join(SRC, name[:-4] + ".json")
    m = json.load(open(meta)) if os.path.exists(meta) else {"sun": [0.5, 2.0, -1], "light": 0}
    im = Image.open(p).convert("RGB")
    if im.size != (W_, H_): im = im.resize((W_, H_), Image.LANCZOS)
    a = np.asarray(im, dtype=np.float32) / 255
    out = a + bloom(a) * 0.32
    sx, sy, sz = m["sun"]; lt = m.get("light", 0.0)
    if sz > 0 and lt > 0.05 and -0.3 < sx < 1.3 and -0.3 < sy < 1.5:
        out = out + beams(a, sx, sy, 0.95 * lt)
    out = out * (np.array([1.0, 1.0, 1.0]) + lt * 0.8 * (np.array([1.07, 1.0, 0.88]) - 1.0))   # 夕日の暖色
    out = out / (1 + 0.12 * np.maximum(out - 0.9, 0))                    # 白飛びをやわらかく
    rng = np.random.default_rng(int(name[:4]))
    out += (rng.standard_normal(out.shape[:2])[..., None] * 0.008)        # ごく弱い粒子（帯状のムラ防止）
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(DST, name))

if __name__ == "__main__":
    names = sorted(f for f in os.listdir(SRC) if f.endswith(".png") and "_tmp" not in f)
    if ONLY: names = [n for n in names if n[:4] in ONLY]
    todo = [n for n in names if ONLY or not os.path.exists(os.path.join(DST, n))]
    for i, n in enumerate(todo):
        process(n)
        if i % 50 == 0: print("post", n, "%d/%d" % (i + 1, len(todo)), flush=True)
    print("done", len(todo))
