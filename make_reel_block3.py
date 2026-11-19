"""
make_reel_block3.py ― ブロック世界パート3『消えない影の正体』（約64秒＋冒頭予告＋絵文字2択）
  1) --voice で声だけ先に作る（blk3_voice.npy / blk3_lines.json）
  2) create_block3.py で絵（12fps）
  3) 引数なしで 絵＋声＋効果音＋BGM＋字幕＋HUD（体力・影化ゲージ・日食までのカウントダウン）＋絵文字2択 → block_part3.mp4
"""
import os, sys, json, math, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R
import s_sfx as X
import s_bgm as B
MEID = int(os.environ.get("MEID", "1368642336"))
from block_lines import PART3 as LINES0
from blk3_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
FR = os.path.join(HERE, "frames_BLK3")
DUR = END
TAIL = 2.8
R.DUR = DUR
R.MIX = np.zeros((R.n_(DUR) + SR, 2))
add = R.add
R.VV_CAST.update({
    "ruka": (1325133120, 1325133120, 0.0, 1.05, 1.15),     # 花音（ルカ）
    "me":   (MEID, MEID, 0.0, 0.98, 1.0),                    # 自分（男）
    "kage": (1310138979, 1310138979, -0.08, 0.86, 0.85),     # 阿井田 茂 Heavy を低く遅く＝影（前の召喚者）
})
R.VOICE.update({"ruka": (0, 0, 1.1, 0.04), "me": (0, 0, 1.1, 0.04), "kage": (0, 0, 1.15, 0.6)})
R.SPK_REF_TEXT[:] = ["今日の放課後、少しだけ話せる", "写真、見せてくれる", "ううん、なんでもない", "また明日ね", "窓の外、きれいだね"]
R.LINES = list(LINES0)
VOICE_NPY = os.path.join(HERE, "blk3_voice.npy"); LINES_JSON = os.path.join(HERE, "blk3_lines.json")

def rr(x0, y0, x1, y1, r):
    k = 0.45 * r
    return ("m %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d"
            % (x0 + r, y0, x1 - r, y0, x1 - r + k, y0, x1, y0 + r - k, x1, y0 + r, x1, y1 - r, x1, y1 - r + k, x1 - r + k, y1, x1 - r, y1,
               x0 + r, y1, x0 + r - k, y1, x0, y1 - r + k, x0, y1 - r, x0, y0 + r, x0, y0 + r - k, x0 + r - k, y0, x0 + r, y0))

STY = (
    "Style: shape,{f},20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n"
    "Style: ruka,{f},44,&H00FFFFFF,&H00FFFFFF,&H008A3CE8,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: me,{f},44,&H00FFFFFF,&H00FFFFFF,&H00306A9A,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: kage,{f},46,&H00D8D8FF,&H00FFFFFF,&H00100030,&H00000000,-1,0,0,0,100,100,2,0,1,7,0,5,30,30,0,1\n"
    "Style: hook,{f},58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,7,0,5,20,20,0,1\n"
    "Style: card,{f},44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,0,0,5,20,20,0,1\n"
    "Style: count,{f},84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,8,0,5,0,0,0,1\n")

def shadow_at(t):
    """影化（%）：指先が黒くなった瞬間 23%、迷って 45%、使ってしまって 99%"""
    if t < BLACK1: return 0.0
    if t < BLACK1 + 0.6: return 23.0 * (t - BLACK1) / 0.6
    if t < 50.4: return 23.0
    if t < 52.6: return 23.0 + 22.0 * (t - 50.4) / 2.2
    if t < BLAZE + 0.4: return 45.0
    if t < DARK - 0.2: return 45.0 + 54.0 * ((t - BLAZE - 0.4) / (DARK - 0.2 - BLAZE - 0.4)) ** 1.4
    return 99.0

def build_ui(path):
    ev = []
    def E(t0, t1, style, text, layer=5):
        if t1 > t0: ev.append("Dialogue: %d,%s,%s,%s,,0,0,0,,%s" % (layer, R.ts(t0), R.ts(t1), style, text))
    def S(t0, t1, draw, col, alpha="&H00&", layer=4, extra=""):
        E(t0, t1, "shape", r"{\an7\pos(0,0)\p1\1c%s\1a%s\bord0\shad0%s}%s{\p0}" % (col, alpha, extra, draw), layer)
    pop = r"\fscx40\fscy40\t(0,120,\fscx112\fscy112)\t(120,220,\fscx100\fscy100)"
    # パート3 バッジ・最初の3秒（前回のあらすじ＋コメントで進む）
    S(0, END, rr(574, 22, 704, 62, 12), "&H101010&", "&H50&", 6)
    E(0, END, "card", r"{\an5\pos(639,42)\fs26\c&H4090FF&}パート3", 7)
    E(0, 3.2, "hook", r"{\an5\pos(360,250)\fs40\fad(0,150)}{\c&HD0D0D0&}前回：夜明けまで生き残った\N…でも、{\c&H4040FF&}消えない影{\c&HFFFFFF&}が1体", 8)
    S(0.15, 3.2, rr(70, 372, 650, 440, 20), "&H1A1A1A&", "&H30&", 6, r"\fad(120,200)")
    S(0.15, 3.2, rr(70, 372, 86, 440, 6), "&H30C0FF&", "&H00&", 7, r"\fad(120,200)")
    E(0.15, 3.2, "card", r"{\an5\pos(368,406)\fs32\fad(120,200)}この物語は、{\c&H30C0FF&}あなたのコメント{\c&HFFFFFF&}で進む", 8)
    # 左上：体力（前回から1のまま）＋影化ゲージ
    X0, X1 = 92, 340
    S(0, END, rr(16, 18, 352, 74, 14), "&H101010&", "&H40&", 6)
    E(0, END, "card", r"{\an4\pos(30,46)\fs28\c&H80FFFF&}HP", 8)
    S(0, END, "m %d 30 l %d 30 l %d 62 l %d 62" % (X0, X1, X1, X0), "&H303030&", "&H00&", 6)
    t = 0.0
    while t < END:
        S(t, t + 0.25, "m %d 30 l %d 30 l %d 62 l %d 62" % (X0, X0 + 3, X0 + 3, X0), "&H3030FF&", "&H00&" if int(t * 4) % 2 else "&H60&", 8)
        t += 0.25
    E(0, END, "card", r"{\an6\pos(338,47)\fs24\c&HFFFFFF&\bord2\3c&H000000&}1", 9)
    Y0, Y1 = 92, 116
    S(BLACK1, END, rr(16, 80, 352, 128, 12), "&H100810&", "&H30&", 6, r"\fad(100,0)")
    E(BLACK1, END, "card", r"{\an4\pos(26,104)\fs22\c&HFF80D0&\fad(100,0)}影化", 8)
    S(BLACK1, END, "m %d %d l %d %d l %d %d l %d %d" % (X0, Y0, X1, Y0, X1, Y1, X0, Y1), "&H302030&", "&H00&", 6, r"\fad(100,0)")
    t = BLACK1; step = 1 / 12
    while t < END:
        v = shadow_at(t); w = int((X1 - X0) * v / 100)
        if w > 0:
            col = "&HC040A0&" if v < 60 else "&H6020FF&"
            S(t, t + step, "m %d %d l %d %d l %d %d l %d %d" % (X0, Y0, X0 + w, Y0, X0 + w, Y1, X0, Y1), col, "&H00&", 7)
        E(t, t + step, "card", r"{\an6\pos(338,104)\fs22\c&HFFFFFF&\bord2\3c&H000000&}%d%%" % int(round(v)), 9)
        t += step
    # 影化：初めて気づいた瞬間（グリッチ＋大きく）
    for k in range(4):
        a = BLACK1 + 0.07 * k
        S(a, a + 0.05, "m 0 %d l 720 %d l 720 %d l 0 %d" % (300 + 160 * k, 300 + 160 * k, 340 + 160 * k, 340 + 160 * k), "&HFF00C0&", "&H70&", 10)
    E(BLACK1, BLACK1 + 1.6, "count", r"{\an5\pos(360,420)\fs92\c&HFFB0F0&\3c&H400040&\bord7%s\frz-4}影化 23%%" % pop, 11)
    S(BLACK1 + 0.5, BLACK1 + 3.2, rr(130, 520, 590, 620, 22), "&H200020&", "&H20&", 6, r"\fad(150,200)")
    E(BLACK1 + 0.5, BLACK1 + 3.2, "card", r"{\an5\pos(360,570)\fs38\c&HFFFFFF&\fad(150,200)}チート能力の{\c&HFF80D0&}代償{\c&HFFFFFF&}…？", 7)
    # 割れて人の形に
    E(CRACK + 0.1, CRACK + 1.4, "count", r"{\an5\pos(360,380)\fs80\c&HFFFFFF&\3c&H101010&\bord7%s\frz3}割れた…！？" % pop, 9)
    # 正体
    S(REVEAL + 0.3, REVEAL + 3.4, rr(110, 330, 610, 470, 24), "&H101010&", "&H20&", 6, r"\fad(150,250)")
    E(REVEAL + 0.3, REVEAL + 3.4, "card", r"{\an5\pos(360,368)\fs30\c&HC0C0C0&\fad(150,250)}影の正体", 7)
    E(REVEAL + 0.7, REVEAL + 3.4, "count", r"{\an5\pos(360,428)\fs62\c&H40D0FF&\3c&H000000&\bord5%s\fad(0,250)}前の召喚者" % pop, 8)
    # 日食
    E(ECLIPSE0 + 0.2, ECLIPSE0 + 2.2, "count", r"{\an5\pos(360,360)\fs96\c&H2020FF&\3c&HFFFFFF&\bord6%s\frz-3}日食" % pop, 9)
    E(ECLIPSE0 + 0.5, ECLIPSE0 + 2.2, "card", r"{\an5\pos(360,470)\fs34\c&HFFFFFF&\bord3\3c&H000000&\fad(150,200)}昼なのに、夜が来る", 9)
    # 2択（迷い）：使う／使わない が揺れる
    cards = [("使う", 190, "&HC040A0&"), ("使わない", 530, "&HE09040&")]
    t = 50.2; k = 0
    while t < 53.2:
        d = max(0.2, 0.5 - 0.05 * k); t1 = min(53.2, t + d)
        for i, (lab, x, col) in enumerate(cards):
            on = (k % 2 == i)
            S(t, t1, rr(x - 150, 690, x + 150, 790, 22), col if on else "&H303030&", "&H10&" if on else "&H50&", 6)
            E(t, t1, "card", r"{\an5\pos(%d,740)\fs%d}%s" % (x, 40 if on else 34, lab), 7)
        t = t1; k += 1
    # 上端の進行バー＋最後の10秒：完全な闇までのカウントダウン
    S(0, DARK, "m 0 0 l 720 0 l 720 7 l 0 7", "&HC040A0&", "&H00&", 12, r"\clip(0,0,0,7)\t(0,%d,\clip(0,0,720,7))" % int(DARK * 1000))
    for k in range(10):
        a = COUNT0 + k; left = 10 - k
        col = "&HFF80D0&" if left > 3 else "&H4040FF&"
        S(a, a + 1, rr(200, 170, 520, 236, 18), "&H101010&", "&H30&", 6)
        E(a, a + 1, "card", r"{\an5\pos(360,203)\fs32}日食まで {\c%s\fs44%s}%d秒" % (col, pop, left), 7)
    # 使ってしまう → 影化 99%
    E(DARK - 0.2, DARK + 1.8, "count", r"{\an5\pos(360,470)\fs120\c&H6020FF&\3c&HFFFFFF&\bord7%s}影化 99%%" % pop, 11)
    E(DARK + 2.2, END, "count", r"{\an5\pos(360,420)\fs40\c&HFFFFFF&\3c&H000000&\bord4\fad(300,0)}― パート4へつづく ―", 9)
    for st, en, text, _, _, who in R.LINES:
        E(st, en, who, r"{\an5\pos(360,1010)\fad(60,100)}%s" % text, 9)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

def tick(sec=0.07, f=2200):
    tt = R.tt(sec); return np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.015)

def glitch(sec=0.5, seed=0):
    r = np.random.default_rng(seed); x = np.zeros(R.n_(sec)); i = 0
    while i < len(x):
        n = int(r.uniform(0.01, 0.05) * SR); f = r.uniform(200, 3000)
        seg = np.sign(np.sin(2 * np.pi * f * np.arange(n) / SR)) * r.uniform(0.3, 1.0) if r.random() < 0.6 else np.zeros(n)
        x[i:i + n] = seg[: len(x) - i]; i += n
    return x * 0.5

def build_sfx():
    B.block_part3(add, DUR, CRACK, BLACK1, REVEAL, ECLIPSE0, COUNT0, BLAZE, DARK, tail=TAIL)
    add(X.braam(2.6, 46.0), 0.05, 0.35); add(X.stinger(), 0.1, 0.12)
    hops = [APPROACH0 + (APPROACH1 - APPROACH0) * k / 6 for k in range(7)]                  # 跳ねて近づく
    for k, h in enumerate(hops[1:]): add(R.lp(R.kick(90, 40, 0.3, 0.07), 500), h, 0.25 + 0.06 * k)
    add(X.swell(1.0), CRACK - 1.0, 0.45); X.hit(add, CRACK, 1.1, 0); add(R.shatter(1.2), CRACK, 0.5)
    add(X.braam(2.4, 41.0), CRACK + 0.1, 0.45)
    add(R.whoosh(0.6, 150, 1200), POINT0, 0.35)
    add(glitch(0.6, 1), BLACK1, 0.35); add(X.stinger(1.4), BLACK1, 0.3); add(X.tinnitus(2.0, 5200), BLACK1 + 0.1, 0.35)
    hb = R.heartbeat()
    for k in range(5): add(hb, BLACK1 + 0.8 + k * 0.7, 0.4)
    for k in range(5): add(R.lp(R.noise(0.08), 2500) * R.dec(0.08, 0.02), CRACKS0 + 0.16 * k, 0.4, 0.3 * (-1) ** k)   # ひび
    X.hit(add, REVEAL, 1.0, 0.4); add(R.shatter(1.0), REVEAL, 0.45)
    add(R.boom(3.0), ECLIPSE0, 0.6); add(R.lp(R.noise(4.0), 120) * 0.8, ECLIPSE0, 0.45); add(X.braam(3.0, 38.0), ECLIPSE0 + 0.2, 0.55)
    rng = np.random.default_rng(5)
    for k in range(9):                                                                       # 地面から湧く
        tm = RISE0 + k * 0.32 + rng.uniform(0, 0.1)
        add(R.thud(0.5), tm, 0.35, rng.uniform(-0.8, 0.8)); add(R.lp(R.noise(0.4), 300) * R.dec(0.4, 0.15), tm, 0.3, rng.uniform(-0.8, 0.8))
    for k in range(30):
        add(R.lp(R.kick(90, 40, 0.25, 0.06), 400), rng.uniform(RISE0 + 2, DARK), rng.uniform(0.12, 0.25), rng.uniform(-0.8, 0.8))
    t = 50.2; k = 0
    while t < 53.2: add(tick(), t, 0.4, 0.4 * (-1) ** k); t += max(0.2, 0.5 - 0.05 * k); k += 1
    add(glitch(0.4, 2), 50.4, 0.25)
    t = COUNT0
    while t < DARK - 0.2: add(hb, t, 0.4); t += 0.6 if t < BLAZE else 0.42
    for k in range(10): add(tick(0.09, 1800), COUNT0 + k, 0.55)
    add(R.charge(DARK - BLAZE), BLAZE, 0.35); add(X.swell(2.0), DARK - 2.0, 0.6)
    for k in range(6): add(glitch(0.25, 10 + k), BLAZE + 0.5 + k * 0.5, 0.2 + 0.03 * k)
    X.hit(add, DARK, 1.6, 0.6); add(X.braam(3.2, 36.0), DARK, 0.7); add(X.tinnitus(3.0, 3600), DARK + 0.2, 0.45)
    add(X.stinger(1.4), END - 1.2, 0.2)

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
    tmp = tempfile.mkdtemp(prefix="blk3_")
    out = R.MIX[: R.n_(DUR + TAIL)].copy()
    out[-R.n_(0.8):] *= np.linspace(1, 0, R.n_(0.8))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "blk3_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "blk3_ui.ass"); build_ui(ass)
    if "--ui" in sys.argv: print("wrote", wav, ass); return
    mp4 = os.path.join(HERE, "block_part3.mp4"); raw = os.path.join(tmp, "raw.mp4")
    grade = "fps=24,lenscorrection=k1=0.07:k2=0.0,crop=680:1208,scale=720:1280,vignette=PI/5,eq=contrast=1.04:saturation=1.08,ass=blk3_ui.ass"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", os.path.join(FR, "%04d.png"), "-i", wav, "-vf", grade,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-maxrate", "6M", "-bufsize", "12M",
                    "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-t", "%.3f" % DUR, raw], check=True, cwd=HERE)
    subprocess.run(["python3", os.path.join(HERE, "s2_endcard.py"), raw, mp4, "%.2f" % (END - 0.5),
                    "あなたなら、使う？", "🔥", "使う", "🤝", "使わない", "▶ 次回：影になった手", "2.8"],
                   check=True, env=dict(os.environ, ENDCARD_HINT="絵文字ひとつでOK！"))
    fin = os.path.join(tmp, "fin.mp4"); shutil.move(mp4, fin)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", fin, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-shortest", "-movflags", "+faststart", mp4], check=True)
    shutil.rmtree(tmp)
    # 冒頭に「日食まで あと3秒」の予告＋巻き戻し
    subprocess.run([sys.executable, os.path.join(HERE, "make_teaser_tsu.py"), mp4, "%.1f" % (DARK - 3.0), "◀◀ %d秒前" % int(DARK - 3.0), "blk", "日食まで あと"], check=True, cwd=HERE)
    print("wrote", mp4)

if __name__ == "__main__":
    main()
