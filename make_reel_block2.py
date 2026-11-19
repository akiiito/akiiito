"""
make_reel_block1.py ― 『POV：全部がブロックの世界で目覚めたら、夜まで残り3分だった』パート1
  1) --voice で声だけ先に作る（blk2_voice.npy / blk2_lines.json）
  2) create_block1.py で絵（12fps）
  3) 引数なしで 絵＋声＋効果音＋字幕＋HUD（残り時間）＋絵文字2択 → block_part2.mp4
"""
import os, sys, json, math, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R
import s_sfx as X
import s_bgm as B
MEID = int(os.environ.get("MEID", "1368642336"))
from block_lines import PART2 as LINES0

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
FR = os.path.join(HERE, "frames_BLK2")
END = 66.0
DUR = END
TAIL = 2.8                       # 絵文字2択カード（END-0.5 から 2.8 秒）のぶん、BGMをのばす
R.DUR = DUR
R.MIX = np.zeros((R.n_(DUR) + SR, 2))
add = R.add
R.VV_CAST.update({
    "ruka": (1325133120, 1325133120, 0.0, 1.05, 1.15),     # 花音（ルカ）
    "me":   (MEID, MEID, 0.0, 0.98, 1.0),                    # 自分（男）
})
R.VOICE.update({"ruka": (0, 0, 1.1, 0.04), "me": (0, 0, 1.1, 0.04)})
R.SPK_REF_TEXT[:] = ["今日の放課後、少しだけ話せる", "写真、見せてくれる", "ううん、なんでもない", "また明日ね", "窓の外、きれいだね"]
R.LINES = list(LINES0)
VOICE_NPY = os.path.join(HERE, "blk2_voice.npy"); LINES_JSON = os.path.join(HERE, "blk2_lines.json")

def rr(x0, y0, x1, y1, r):
    k = 0.45 * r
    return ("m %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d"
            % (x0 + r, y0, x1 - r, y0, x1 - r + k, y0, x1, y0 + r - k, x1, y0 + r, x1, y1 - r, x1, y1 - r + k, x1 - r + k, y1, x1 - r, y1,
               x0 + r, y1, x0 + r - k, y1, x0, y1 - r + k, x0, y1 - r, x0, y0 + r, x0, y0 + r - k, x0 + r - k, y0, x0 + r, y0))

STY = (
    "Style: shape,{f},20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n"
    "Style: ruka,{f},44,&H00FFFFFF,&H00FFFFFF,&H008A3CE8,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: me,{f},44,&H00FFFFFF,&H00FFFFFF,&H00306A9A,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: hook,{f},58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,7,0,5,20,20,0,1\n"
    "Style: card,{f},44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,0,0,5,20,20,0,1\n"
    "Style: count,{f},84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,8,0,5,0,0,0,1\n")

from blk2_timing import *

def mmss(sec):
    sec = max(0, int(math.ceil(sec))); return "%02d:%02d" % (sec // 60, sec % 60)

def hp_at(t):
    if t < HIT1: return 100.0
    if t < HIT1 + 0.35: return 100 - 65 * (t - HIT1) / 0.35
    if t < HIT2: return 35.0
    if t < HIT2 + 0.35: return 35 - 34 * (t - HIT2) / 0.35
    return 1.0

def build_ui(path):
    ev = []
    def E(t0, t1, style, text, layer=5):
        if t1 > t0: ev.append("Dialogue: %d,%s,%s,%s,,0,0,0,,%s" % (layer, R.ts(t0), R.ts(t1), style, text))
    def S(t0, t1, draw, col, alpha="&H00&", layer=4, extra=""):
        E(t0, t1, "shape", r"{\an7\pos(0,0)\p1\1c%s\1a%s\bord0\shad0%s}%s{\p0}" % (col, alpha, extra, draw), layer)
    pop = r"\fscx40\fscy40\t(0,120,\fscx112\fscy112)\t(120,220,\fscx100\fscy100)"
    # パート2 バッジ・最初の3秒（前回のあらすじ＋コメントで進む）
    S(0, END, rr(290, 112, 430, 152, 12), "&H101010&", "&H50&", 6)
    E(0, END, "card", r"{\an5\pos(360,132)\fs26\c&H4090FF&}パート2", 7)
    E(0, 3.2, "hook", r"{\an5\pos(360,250)\fs40\fad(0,150)}{\c&HD0D0D0&}前回：ブロックの世界で\N{\c&H4040FF&}影ブロックの群れ{\c&HFFFFFF&}に囲まれた", 8)
    S(0.15, 3.2, rr(70, 352, 650, 420, 20), "&H1A1A1A&", "&H30&", 6, r"\fad(120,200)")
    S(0.15, 3.2, rr(70, 352, 86, 420, 6), "&H30C0FF&", "&H00&", 7, r"\fad(120,200)")
    E(0.15, 3.2, "card", r"{\an5\pos(368,386)\fs32\fad(120,200)}この物語は、{\c&H30C0FF&}あなたのコメント{\c&HFFFFFF&}で進む", 8)
    # 左上：体力ゲージ（ヒット時は白い「削れた分」が遅れて縮む）
    X0, X1, Y0, Y1 = 92, 340, 30, 62
    S(0, END, rr(16, 18, 352, 74, 14), "&H101010&", "&H40&", 6)
    E(0, END, "card", r"{\an4\pos(30,46)\fs28\c&H80FFFF&}HP", 8)
    t = 0.0; step = 1 / 12
    while t < END:
        hp = hp_at(t); ghost = max(hp, hp_at(max(0, t - 0.6)))
        col = "&H50E050&" if hp > 50 else ("&H30C0FF&" if hp > 20 else "&H3030FF&")
        w = int((X1 - X0) * hp / 100); gw = int((X1 - X0) * ghost / 100)
        S(t, t + step, "m %d %d l %d %d l %d %d l %d %d" % (X0, Y0, X1, Y0, X1, Y1, X0, Y1), "&H303030&", "&H00&", 6)
        if gw > w: S(t, t + step, "m %d %d l %d %d l %d %d l %d %d" % (X0, Y0, X0 + gw, Y0, X0 + gw, Y1, X0, Y1), "&HFFFFFF&", "&H00&", 7)
        flash = "&H60&" if (hp <= 1 and int(t * 4) % 2) else "&H00&"
        S(t, t + step, "m %d %d l %d %d l %d %d l %d %d" % (X0, Y0, X0 + max(w, 3), Y0, X0 + max(w, 3), Y1, X0, Y1), col, flash, 8)
        t += step
    for a, b, n in ((0, HIT1, "100"), (HIT1, HIT2, "35"), (HIT2, END, "1")):
        E(a, b, "card", r"{\an6\pos(338,47)\fs24\c&HFFFFFF&\bord2\3c&H000000&}%s" % n, 9)
    # 被弾：赤いフラッシュ＋ダメージ数字
    for h, dmg in ((HIT1, "-65"), (HIT2, "-34")):
        S(h, h + 0.7, "m 0 0 l 720 0 l 720 1280 l 0 1280", "&H0000E0&", "&H40&", 10, r"\fad(0,600)")
        E(h, h + 1.2, "count", r"{\an5\pos(360,520)\fs110\c&H3030FF&\3c&HFFFFFF&\bord6%s}%s" % (pop, dmg), 11)
    # 体力1：画面のふちが赤く脈打つ
    t = HIT2 + 0.8
    while t < DAWN:
        S(t, t + 0.5, "m 0 0 l 720 0 l 720 1280 l 0 1280 l 0 0 m 60 60 l 60 1220 l 660 1220 l 660 60 l 60 60", "&H0000C0&", "&H60&", 9, r"\fad(80,380)")
        t += 0.5
    # 2択があたふた揺れる → 時間切れ（前回コメントが来なかった＝どちらも選べなかった）
    cards = [("穴に隠れる", 190, "&HE09040&"), ("迎え撃つ", 530, "&H3060E0&")]
    t = CHOICE0; k = 0
    while t < TIMEUP:
        d = max(0.16, 0.42 - 0.04 * k); t1 = min(TIMEUP, t + d)
        for i, (lab, x, col) in enumerate(cards):
            on = (k % 2 == i)
            S(t, t1, rr(x - 160, 690, x + 160, 800, 22), col if on else "&H303030&", "&H10&" if on else "&H50&", 6)
            E(t, t1, "card", r"{\an5\pos(%d,745)\fs%d}%s" % (x, 40 if on else 34, lab), 7)
        t = t1; k += 1
    E(CHOICE0, TIMEUP, "count", r"{\an5\pos(360,630)\fs40\c&HFFFFFF&\3c&H000000&\bord4}どっちにする…！？", 8)
    for i, (lab, x, col) in enumerate(cards):
        S(TIMEUP, TIMEUP + 1.4, rr(x - 160, 690, x + 160, 800, 22), "&H303030&", "&H50&", 6, r"\fad(0,300)")
        E(TIMEUP, TIMEUP + 1.4, "card", r"{\an5\pos(%d,745)\fs34\c&H909090&\fad(0,300)}%s" % (x, lab), 7)
    E(TIMEUP, TIMEUP + 1.4, "count", r"{\an5\pos(360,740)\fs96\c&H3030FF&\3c&HFFFFFF&\bord6\frz8%s\fad(0,300)}時間切れ" % pop, 9)
    E(TIMEUP + 0.15, TIMEUP + 1.4, "card", r"{\an5\pos(360,860)\fs30\c&HFFFFFF&\bord3\3c&H000000&\fad(150,300)}どちらも、選ばれなかった", 9)
    # 戦うしかない・能力
    E(19.75, 21.6, "count", r"{\an5\pos(360,420)\fs92\c&HFFFFFF&\3c&H2020C0&\bord7%s\frz-4}戦うしかない" % pop, 9)
    c0, c1 = 21.0, WALL0 - 0.1
    S(c0, c1, rr(110, 560, 610, 700, 24), "&H3A2A10&", "&H20&", 6, r"\fad(150,100)")
    E(c0, c1, "card", r"{\an5\pos(360,600)\fs28\c&HFFFFFF&\fad(150,100)}チート能力", 7)
    E(c0, c1, "card", r"{\an5\pos(360,655)\fs50\c&HFFF0C0&\3c&HFF9020&\bord3\fad(150,100)}ブロック変形", 7)
    E(WALL1, WALL1 + 1.0, "count", r"{\an5\pos(360,380)\fs84\c&HFFFFFF&\3c&HE0A040&\bord6%s\frz-5}壁、完成！" % pop, 9)
    # 撃破カウンター
    for i, tk in enumerate(KILLS):
        nx = KILLS[i + 1] if i + 1 < len(KILLS) else RUMBLE
        E(tk, tk + 0.45, "count", r"{\an5\pos(%d,%d)\fs60\c&H40D0FF&\3c&H000000&\bord5%s}撃破！" % (300 + (i % 3) * 60, 430 + (i % 2) * 70, pop), 9)
        S(tk, nx, rr(510, 18, 704, 74, 14), "&H101010&", "&H40&", 6)
        E(tk, nx, "card", r"{\an5\pos(607,46)\fs30\c&H40D0FF&%s}撃破 %d" % (pop if True else "", i + 1), 8)
    # ボス出現・ボスの体力
    E(BOSS1 - 0.6, BOSS1 + 1.6, "count", r"{\an5\pos(360,330)\fs70\c&HFFFFFF&\3c&H1010A0&\bord6%s}影の巨人" % pop, 9)
    t = BOSS1; step = 1 / 12
    while t < DAWN + 0.8:
        bh = 1.0 if t < FINAL else max(0.0, 1 - (t - FINAL) / (DAWN - FINAL))
        S(t, t + step, "m 120 92 l 600 92 l 600 108 l 120 108", "&H202020&", "&H20&", 6)
        S(t, t + step, "m 120 92 l %d 92 l %d 108 l 120 108" % (120 + int(480 * bh), 120 + int(480 * bh)), "&H2020D0&", "&H00&", 7)
        t += step
    E(BOSS1, DAWN + 0.8, "card", r"{\an5\pos(360,82)\fs20\c&HC0C0FF&}影の巨人", 8)
    # 最後の10秒：夜明けまでのカウントダウン＋上端の進行バー
    S(0, DAWN, "m 0 0 l 720 0 l 720 7 l 0 7", "&H40D0FF&", "&H00&", 12, r"\clip(0,0,0,7)\t(0,%d,\clip(0,0,720,7))" % int(DAWN * 1000))
    for k in range(10):
        a = COUNT0 + k; left = 10 - k
        col = "&H40D0FF&" if left > 3 else "&H4040FF&"
        S(a, a + 1, rr(200, 170, 520, 236, 18), "&H101010&", "&H30&", 6)
        E(a, a + 1, "card", r"{\an5\pos(360,203)\fs32}夜明けまで {\c%s\fs44%s}%d秒" % (col, pop, left), 7)
    E(FINAL, FINAL + 1.3, "count", r"{\an5\pos(360,420)\fs80\c&HFFFFFF&\3c&HFF9020&\bord7%s\frz4}最後の一手！" % pop, 9)
    E(DAWN, DAWN + 2.6, "count", r"{\an5\pos(360,330)\fs110\c&H60E0FF&\3c&H2050A0&\bord7%s}夜明け" % pop, 9)
    E(DAWN + 0.4, DAWN + 2.6, "card", r"{\an5\pos(360,440)\fs40\c&HFFFFFF&\3c&H000000&\bord4\fad(200,0)}生き残った", 9)
    E(SHADOW + 1.6, END, "count", r"{\an5\pos(360,420)\fs40\c&HFFFFFF&\3c&H000000&\bord4\fad(300,0)}― パート3へつづく ―", 9)
    for st, en, text, _, _, who in R.LINES:
        E(st, en, who, r"{\an5\pos(360,1010)\fad(60,100)}%s" % text, 9)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

def T(i): return R.LINES[i][0]

def tick(sec=0.07, f=2200):
    tt = R.tt(sec); return np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.015)

def build_sfx():
    B.block_part2(add, DUR, HIT1, CAST0, RUMBLE, HIT2, COUNT0, DAWN, SHADOW, tail=TAIL)
    add(X.braam(2.6, 49.0), 0.05, 0.4); add(X.stinger(), 0.1, 0.12)
    rng = np.random.default_rng(3)
    for k in range(70):                                                                # 影ブロックがぴょんぴょん（夜のあいだずっと）
        tm = rng.uniform(0, DAWN)
        add(R.lp(R.kick(90, 40, 0.25, 0.06), 400), tm, rng.uniform(0.12, 0.28), rng.uniform(-0.8, 0.8))
    t = CHOICE0; k = 0                                                                 # 2択の切り替わり（だんだん速く）
    while t < TIMEUP:
        add(tick(), t, 0.45, 0.4 * (-1) ** k); t += max(0.16, 0.42 - 0.04 * k); k += 1
    add(R.horn(0.7), TIMEUP, 0.5); X.hit(add, TIMEUP, 0.7, 0)                           # 時間切れ
    add(X.whip(), TURN, 0.6); add(X.swell(0.9), HIT1 - 0.9, 0.6)
    X.hit(add, HIT1, 1.4, 0); add(R.shatter(0.8), HIT1, 0.3); add(X.tinnitus(2.6), HIT1 + 0.1, 0.5)   # 背後から攻撃
    hb = R.heartbeat()
    for k in range(6): add(hb, HIT1 + 0.6 + k * 0.62, 0.5)
    add(R.whoosh(0.5), DOWN1[1], 0.4)
    add(R.charge(3.0), CAST0, 0.3); add(X.swell(1.0), WALL0 - 1.0, 0.4)
    for i in range(18):                                                                # 壁が組み上がる（カカカッ）
        tw = WALL0 + (WALL1 - WALL0 - 0.35) * i / 18 + 0.33
        add(R.thud(0.3), tw, 0.2, 0.5 * ((i % 3) - 1)); add(R.lp(R.noise(0.06), 3000) * R.dec(0.06, 0.015), WALL0 + (WALL1 - WALL0 - 0.35) * i / 18 + 0.33, 0.35, 0.5 * ((i % 3) - 1))
    X.hit(add, WALL1, 0.9, 0); add(R.chime([1046.5, 1318.5, 1568.0, 2093.0], 0.06, 0.9), WALL1 + 0.05, 0.2)
    for k in range(6): add(R.thud(0.5), CRASH + k * 0.09, 0.45, 0.6 * ((k % 3) - 1))       # 壁にぶつかる
    for k in range(2): add(R.thud(0.4), PILLAR0 + 0.2 + k * 0.3, 0.5); add(X.whip(), PILLAR0, 0.4)
    for i, tk in enumerate(KILLS):                                                      # 撃つ → 砕ける
        add(X.whip(0.3), tk - 0.38, 0.45, 0.3 * (-1) ** i)
        add(R.shatter(0.7), tk, 0.45, 0.3 * (-1) ** i); add(R.kick(120, 50, 0.25, 0.06), tk, 0.5)
        add(R.chime([1568.0 * 2 ** (i / 12)], 0.0, 0.3), tk + 0.03, 0.12)
    add(R.boom(2.5), RUMBLE, 0.7); add(R.lp(R.noise(BOSS1 - RUMBLE), 120) * 0.8, RUMBLE, 0.5)   # 地鳴り
    add(X.braam(3.0, 41.0), BOSS0 + 0.4, 0.6); X.hit(add, BOSS1, 1.1, 0)
    add(R.whoosh(0.5), JUMP, 0.5); add(X.swell(0.8), HIT2 - 0.8, 0.6); add(R.whoosh(0.6, 200, 2000), HIT2 - 0.5, 0.6)
    X.hit(add, HIT2, 1.5, 0); add(R.shatter(1.0), HIT2 - 0.35, 0.4); add(X.tinnitus(3.2, 3800), HIT2 + 0.1, 0.55)
    t = HIT2 + 0.8                                                                      # 体力1：心臓の音（だんだん速く）
    while t < DAWN - 0.2:
        add(hb, t, 0.45); t += 0.62 if t < COUNT0 else 0.5
    for k in range(10): add(tick(0.09, 1800), COUNT0 + k, 0.55)                          # カウントダウンの秒針
    add(R.charge(FINAL - 50.0), 50.0, 0.25)
    X.hit(add, FINAL, 1.6, 0.6); add(X.braam(2.6, 55.0), FINAL, 0.6); add(R.shatter(1.0), FINAL + 0.2, 0.4)   # 最後の一手
    add(X.swell(1.4), DAWN - 1.4, 0.5); add(X.stinger(), DAWN, 0.35)                     # 夜明け
    add(R.chime([880.0, 1108.7, 1318.5, 1760.0], 0.09, 1.4), DAWN + 0.1, 0.3)
    add(X.braam(2.8, 46.0), SHADOW + 0.3, 0.5); add(X.stinger(1.2), SHADOW + 0.9, 0.15)    # 消えない影

def main():
    if "--voice" in sys.argv:
        R.build_voice()
        np.save(VOICE_NPY, R.MIX)
        json.dump([list(l) for l in R.LINES], open(LINES_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("wrote", VOICE_NPY, LINES_JSON); return
    R.LINES = [tuple(l) for l in json.load(open(LINES_JSON, encoding="utf-8"))]
    voice = np.load(VOICE_NPY)
    voice = np.concatenate([voice, np.zeros((max(0, R.n_(DUR + TAIL + 1) - len(voice)), 2))])
    R.MIX = np.zeros_like(voice); build_sfx()
    R.MIX = voice + X.duck(R.MIX, voice)
    tmp = tempfile.mkdtemp(prefix="blk2_")
    out = R.MIX[: R.n_(DUR + TAIL)].copy()
    out[-R.n_(0.8):] *= np.linspace(1, 0, R.n_(0.8))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "blk2_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "blk2_ui.ass"); build_ui(ass)
    mp4 = os.path.join(HERE, "block_part2.mp4"); raw = os.path.join(tmp, "raw.mp4")
    # 12fps の絵を24fpsに（2コマ打ち）＋少し魚眼っぽく＋周辺減光
    grade = "fps=24,lenscorrection=k1=0.07:k2=0.0,crop=680:1208,scale=720:1280,vignette=PI/5,eq=contrast=1.04:saturation=1.08,ass=blk2_ui.ass"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", os.path.join(FR, "%04d.png"), "-i", wav, "-vf", grade,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-maxrate", "6M", "-bufsize", "12M",
                    "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-t", "%.3f" % DUR, raw], check=True, cwd=HERE)
    subprocess.run(["python3", os.path.join(HERE, "s2_endcard.py"), raw, mp4, "%.2f" % (END - 0.5),
                    "続き、見たい？", "🔥", "続きが見たい", "❤️", "ルカ推し", "▶ 次回：消えない影の正体", "2.8"],
                   check=True, env=dict(os.environ, ENDCARD_HINT="絵文字ひとつでOK！"))
    # 選択画面のあいだもBGMが鳴るように、音を全長版に差しかえる
    fin = os.path.join(tmp, "fin.mp4"); shutil.move(mp4, fin)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", fin, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-shortest", "-movflags", "+faststart", mp4], check=True)
    shutil.rmtree(tmp)
    # 冒頭に「夜明けまで あと3秒」の予告＋巻き戻し
    subprocess.run([sys.executable, os.path.join(HERE, "make_teaser_tsu.py"), mp4, "55.0", "◀◀ 55秒前", "blk"], check=True, cwd=HERE)
    print("wrote", mp4)

if __name__ == "__main__":
    main()
