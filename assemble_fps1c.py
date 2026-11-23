"""assemble_fps1c.py ― 編集表どおりにコマを並べる（選ばなかった方の幻は白黒＋赤＋横ずれ）。python3 assemble_fps1c.py '<EDL json>' <秒数>"""
import os, sys, json
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); FPS = 24
EDL = json.loads(sys.argv[1]); DUR = float(sys.argv[2])
SRC = os.path.join(HERE, "frames_FPS1v2_post"); SEQ = os.path.join(HERE, "frames_FPS1c_seq"); os.makedirs(SEQ, exist_ok=True)
black = Image.new("RGB", (1080, 1920), (0, 0, 0))
for f in range(int(round(DUR * FPS))):
    t = f / FPS; seg = next((e for e in EDL if e[0] <= t < e[1]), EDL[-1])
    dst = os.path.join(SEQ, "%04d.png" % (f + 1))
    if os.path.lexists(dst): os.remove(dst)
    if seg[4] == "k": black.save(dst); continue
    st = seg[2] + (t - seg[0]) * (seg[3] - seg[2]) / (seg[1] - seg[0]); src = os.path.join(SRC, "%04d.png" % (min(719, int(round(st * FPS))) + 1))
    if seg[4] == "n": os.symlink(src, dst); continue
    a = np.asarray(Image.open(src).convert("L").convert("RGB"), np.float32) / 255 * np.array([1.0, 0.55, 0.55])
    rng = np.random.default_rng(f)
    for _ in range(8):
        y0 = rng.integers(0, 1900); h = rng.integers(6, 40); a[y0:y0 + h] = np.roll(a[y0:y0 + h], rng.integers(-60, 60), axis=1)
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(dst)
print("assembled", int(round(DUR * FPS)))
