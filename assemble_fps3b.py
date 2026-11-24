"""assemble_fps3b.py ― 第3話の全コマを frames_FPS3B_final に並べる（python3）
  0〜3.2秒   : 第2話の最後（ミナ）＋「BAD STORY」グリッチ
  3.2〜22.4秒: frames_FPS3B_post（3D）
  22.4〜36秒 : 分岐の全体図（ここで描く）。30秒からは投票カードの下地
"""
import os, sys, math, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from fps3b_timing import *
HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 24; W, H = 1080, 1920
DST = os.path.join(HERE, "frames_FPS3B_final"); os.makedirs(DST, exist_ok=True)
EP2 = os.path.join(HERE, "frames_FPS2B_post"); SRC = os.path.join(HERE, "frames_FPS3B_post")
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"
def fnt(s): return ImageFont.truetype(FONT, s)
def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def back(x):                      # ぽんと出る
    x = min(max(x, 0.0), 1.0); c = 1.70158; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

# ---------------------------------------------------------------- 0〜3.2秒：BAD STORY
def bad_story(i, t):
    src = Image.open(os.path.join(EP2, "%04d.png" % (560 + i))).convert("RGB")
    a = np.asarray(src, np.float32) / 255
    if t >= 1.6:
        k = t - 1.6; rng = np.random.default_rng(i)
        lum = a @ np.array([0.3, 0.59, 0.11])
        a = a * 0.35 + lum[..., None] * np.array([0.9, 0.12, 0.12]) * 0.65          # 赤く染める
        if k < 0.12: a = 1 - a * 0.2                                                  # 最初の一瞬は白飛び
        g = 0.25 + 0.75 * math.exp(-k / 0.35)                                          # グリッチの強さ
        sh = int(26 * g); a = np.stack([np.roll(a[..., 0], sh, 1), a[..., 1], np.roll(a[..., 2], -sh, 1)], -1)
        for _ in range(int(10 * g) + 2):                                              # 横にずれる帯
            y0 = rng.integers(0, H - 80); hh = rng.integers(8, 90); a[y0:y0 + hh] = np.roll(a[y0:y0 + hh], rng.integers(-90, 90), 1)
        im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
        # 文字
        txt = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(txt)
        s = 1.0 + 0.6 * math.exp(-k / 0.08)
        f1 = fnt(int(200 * s)); f2 = fnt(int(58 * s))
        d.text((W / 2, H * 0.45), "BAD", font=f1, fill=(255, 40, 50), anchor="mm", stroke_width=10, stroke_fill=(255, 255, 255))
        d.text((W / 2, H * 0.45 + 190 * s), "STORY", font=fnt(int(150 * s)), fill=(255, 40, 50), anchor="mm", stroke_width=8, stroke_fill=(255, 255, 255))
        d.text((W / 2, H * 0.45 + 330 * s), "あなたが選んだのは BADルート", font=f2, fill=(255, 255, 255), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0))
        ta = np.asarray(txt).copy()
        for _ in range(int(6 * g) + 1):                                               # 文字にもグリッチ
            y0 = rng.integers(int(H * 0.3), int(H * 0.75)); hh = rng.integers(6, 40); ta[y0:y0 + hh] = np.roll(ta[y0:y0 + hh], rng.integers(-40, 40), 1)
        txt = Image.fromarray(ta)
        if k >= 1.35: txt.putalpha(txt.getchannel("A").point(lambda v: int(v * max(0, 1 - (k - 1.35) / 0.25))))
        im.paste(txt, (0, 0), txt)
        return im
    a = a * 0.8
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

# ---------------------------------------------------------------- 22.4秒〜：分岐の全体図
RED = (255, 60, 70); GREY = (120, 124, 135); WHITE = (245, 245, 250)
NODES = {   # 名前: (中心x, 中心y, 幅, 高さ, 小見出し, 本文, 出る時刻, 色が付く時刻)
    "ep1":   (540, 380, 820, 170, "第1話", "白い管理者が狙っている！", 0.4, 0.4),
    "run":   (285, 660, 460, 130, "", "声の方へ逃げる", 1.0, None),
    "shoot": (795, 660, 460, 130, "", "撃ち返す", 1.0, 1.5),
    "ep2":   (540, 960, 820, 170, "第2話", "閉じるか、残すか", 2.4, 2.4),
    "close": (285, 1250, 460, 160, "", "世界を閉じて\n現実に帰る", 3.0, None),
    "stay":  (795, 1250, 460, 160, "", "世界を残して\nここに留まる", 3.0, 3.5),
}
EDGES = [("ep1", "run", 1.0, False), ("ep1", "shoot", 1.0, True), ("shoot", "ep2", 2.0, True),
         ("ep2", "close", 3.0, False), ("ep2", "stay", 3.0, True), ("stay", "end", 4.5, True)]
LOCKS = [(285, 795, 2.0), (285, 1400, 4.0)]
END_ = (540, 1590, 860, 210, 5.0)
def bottom(n): x, y, w, h = NODES[n][:4]; return (x, y + h / 2)
def top(n):
    if n == "end": return (END_[0], END_[1] - END_[3] / 2)
    x, y, w, h = NODES[n][:4]; return (x, y - h / 2)
def map_bg():
    last = Image.open(os.path.join(SRC, sorted(os.listdir(SRC))[-1])).convert("RGB")
    bg = last.filter(ImageFilter.GaussianBlur(30))
    a = np.asarray(bg, np.float32) / 255 * 0.18 + np.array([0.02, 0.03, 0.07])
    yy, xx = np.mgrid[0:H, 0:W]
    grid = ((xx % 60 < 2) | (yy % 60 < 2)) * 0.035
    a = a + grid[..., None] * np.array([0.6, 0.8, 1.0])
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
BG = None
GLOW = []; GLOWL = []
def draw_map(t):
    tm = t - MAP; im = BG.copy()
    im = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, ease(tm / 0.4))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov); GLOW.clear(); GLOWL.clear()
    al = int(255 * ease(tm / 0.4))
    d.text((W / 2, 170), "あなたが選んだルート", font=fnt(66), fill=(*WHITE, al), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0, al))
    # 線
    for a_, b_, t0, hot in EDGES:
        k = ease((tm - t0) / 0.5)
        if k <= 0: continue
        p0 = bottom(a_); p1 = top(b_); my = (p0[1] + p1[1]) / 2
        pts = [p0, (p0[0], my), (p1[0], my), p1]
        segs = [(pts[j], pts[j + 1]) for j in range(3)]; L = sum(math.dist(*s) for s in segs); rem = L * k
        lit = hot and tm >= t0
        col = RED if lit else GREY
        for s0, s1 in segs:
            ln = math.dist(s0, s1)
            if rem <= 0: break
            u = min(1, rem / max(ln, 1e-6)); e = (s0[0] + (s1[0] - s0[0]) * u, s0[1] + (s1[1] - s0[1]) * u)
            if lit: GLOWL.append((s0, e))
            d.line([s0, e], fill=(*col, 255), width=10 if lit else 6); rem -= ln
    # 箱
    for n, (x, y, w, h, sub, body, t0, tl) in NODES.items():
        k = back((tm - t0) / 0.35)
        if tm < t0: continue
        w_, h_ = w * k, h * k; lit = tl is not None and tm >= tl
        fill = (120, 20, 30, 235) if lit else (30, 32, 40, 235); edge = RED if lit else GREY
        if lit: GLOW.append([x - w_ / 2, y - h_ / 2, x + w_ / 2, y + h_ / 2])
        d.rounded_rectangle([x - w_ / 2, y - h_ / 2, x + w_ / 2, y + h_ / 2], 24, fill=fill, outline=(*edge, 255), width=6)
        if k > 0.6:
            if sub:
                d.text((x, y - 36), sub, font=fnt(40), fill=(255, 220, 120, 255), anchor="mm")
                d.text((x, y + 26), body, font=fnt(54), fill=(*WHITE, 255), anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0, 255))
            else:
                d.multiline_text((x, y), body, font=fnt(48), fill=(*WHITE, 255) if lit or tl is None else (*WHITE, 255), anchor="mm", align="center", spacing=10, stroke_width=2, stroke_fill=(0, 0, 0, 255))
        if lit and n in ("shoot", "stay") and tm >= tl:
            kk = back((tm - tl) / 0.3)
            d.rounded_rectangle([x + w / 2 - 210 * kk, y - h / 2 - 40, x + w / 2 + 10, y - h / 2 + 12], 14, fill=(255, 220, 60, 255))
            if kk > 0.7: d.text((x + w / 2 - 100, y - h / 2 - 14), "あなたの選択", font=fnt(32), fill=(40, 20, 0, 255), anchor="mm")
    for x, y, t0 in LOCKS:
        if tm >= t0:
            a2 = int(255 * ease((tm - t0) / 0.3))
            d.text((x, y), "？？？", font=fnt(64), fill=(170, 175, 190, a2), anchor="mm")
    # BAD END
    x, y, w, h, t0 = END_
    if tm >= t0:
        k = tm - t0; s = 1 + 0.8 * math.exp(-k / 0.08)
        w_, h_ = w * s, h * s
        GLOW.append([x - w_ / 2, y - h_ / 2, x + w_ / 2, y + h_ / 2])
        d.rounded_rectangle([x - w_ / 2, y - h_ / 2, x + w_ / 2, y + h_ / 2], 30, fill=(150, 10, 20, 245), outline=(255, 255, 255, 255), width=6)
        d.text((x, y - 42 * s), "第3話　BAD END", font=fnt(int(70 * s)), fill=(255, 255, 255, 255), anchor="mm", stroke_width=4, stroke_fill=(60, 0, 0, 255))
        d.text((x, y + 50 * s), "「永遠の管理者」", font=fnt(int(52 * s)), fill=(255, 220, 120, 255), anchor="mm")
    if tm >= 5.8:
        a3 = int(255 * ease((tm - 5.8) / 0.4))
        d.text((W / 2, 1800), "ほかの結末は、まだ誰も知らない", font=fnt(46), fill=(*WHITE, a3), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0, a3))
    gl = Image.new("RGB", (W // 4, H // 4), (0, 0, 0)); gd = ImageDraw.Draw(gl)
    for r in GLOW: gd.rounded_rectangle([v / 4 for v in r], 6, fill=(255, 40, 50))
    for a_, b_ in GLOWL: gd.line([(a_[0] / 4, a_[1] / 4), (b_[0] / 4, b_[1] / 4)], fill=(255, 40, 50), width=4)
    gl = gl.filter(ImageFilter.GaussianBlur(7)).resize((W, H), Image.BILINEAR)
    im = Image.fromarray(np.clip(np.asarray(im, np.int16) + (np.asarray(gl, np.int16) * 0.7).astype(np.int16), 0, 255).astype(np.uint8))
    im = im.convert("RGBA"); im.alpha_composite(ov); im = im.convert("RGB")
    if tm >= END_[4]:                                     # BAD END の衝撃：白い閃光と揺れ
        k = tm - END_[4]
        if k < 0.25:
            sh = int(24 * math.exp(-k / 0.08)) * (1 if int(k * 48) % 2 else -1)
            im = Image.fromarray(np.roll(np.asarray(im), sh, 1))
            im = Image.blend(im, Image.new("RGB", (W, H), (255, 255, 255)), 0.6 * math.exp(-k / 0.05))
    return im

def main():
    global BG
    N = int(END * FPS); i0 = int(R0 * FPS); i1 = int(MAP * FPS)
    for f in range(N):
        t = f / FPS; p = os.path.join(DST, "%04d.png" % (f + 1))
        if f < i0: bad_story(f, t).save(p)
        elif f < i1: shutil.copyfile(os.path.join(SRC, "%04d.png" % (f + 1)), p)
        else:
            if BG is None: BG = map_bg()
            draw_map(t).save(p)
        if f % 100 == 0: print("assemble", f, flush=True)
    print("done", N)

if __name__ == "__main__":
    if "--preview" in sys.argv:          # 確認用：数枚だけ
        BG = map_bg() if os.path.isdir(SRC) and os.listdir(SRC) else Image.new("RGB", (W, H), (10, 12, 20))
        for t in [float(x) for x in sys.argv[sys.argv.index("--preview") + 1].split(",")]:
            (bad_story(int(t * FPS), t) if t < R0 else draw_map(t)).save("/tmp/claude-0/-home-user-akiiito/d0fa9e40-b6b7-5dbc-898d-de3863fd2cf2/scratchpad/a3_%.1f.png" % t)
    else: main()
