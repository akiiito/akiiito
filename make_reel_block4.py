"""
make_reel_block4.py ― ブロック世界パート4『影になった手』（約64秒＋冒頭予告＋絵文字2択）
  1) --voice で声だけ先に作る（blk4_voice.npy / blk4_lines.json）
  2) create_block4.py で絵（12fps）
  3) 引数なしで 絵＋声＋効果音＋BGM＋字幕＋HUD（体力・影化ゲージ・日食までのカウントダウン）＋絵文字2択 → block_part4.mp4
"""
import os, sys, json, math, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R
import s_sfx as X
import s_bgm as B
MEID = int(os.environ.get("MEID", "1368642336"))
from block_lines import PART4 as LINES0
from blk4_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
FR = os.path.join(HERE, "frames_BLK4")
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
R.VV_READ += [("体が", "からだが"), ("その光は", "そのひかりは")]
VOICE_NPY = os.path.join(HERE, "blk4_voice.npy"); LINES_JSON = os.path.join(HERE, "blk4_lines.json")

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
    """影化（%）：99 → 100（暴走）→ ルカの光で 62"""
    if t < FULL: return 99.0
    if t < GLOW0: return 100.0
    if t < GLOW1: return 100.0 - 38.0 * ((t - GLOW0) / (GLOW1 - GLOW0)) ** 0.8
    return 62.0

def build_ui(path):
    ev = []
    def E(t0, t1, style, text, layer=5):
        if t1 > t0: ev.append("Dialogue: %d,%s,%s,%s,,0,0,0,,%s" % (layer, R.ts(t0), R.ts(t1), style, text))
    def S(t0, t1, draw, col, alpha="&H00&", layer=4, extra=""):
        E(t0, t1, "shape", r"{\an7\pos(0,0)\p1\1c%s\1a%s\bord0\shad0%s}%s{\p0}" % (col, alpha, extra, draw), layer)
    pop = r"\fscx40\fscy40\t(0,120,\fscx112\fscy112)\t(120,220,\fscx100\fscy100)"
    S(0, END, rr(574, 22, 704, 62, 12), "&H101010&", "&H50&", 6)
    E(0, END, "card", r"{\an5\pos(639,42)\fs26\c&H4090FF&}パート4", 7)
    E(0, 3.2, "hook", r"{\an5\pos(360,250)\fs40\fad(0,150)}{\c&HD0D0D0&}前回：力を、使ってしまった\N影化 {\c&H4040FF&}99%{\c&HFFFFFF&}", 8)
    S(0.15, 3.2, rr(70, 372, 650, 440, 20), "&H1A1A1A&", "&H30&", 6, r"\fad(120,200)")
    S(0.15, 3.2, rr(70, 372, 86, 440, 6), "&H30C0FF&", "&H00&", 7, r"\fad(120,200)")
    E(0.15, 3.2, "card", r"{\an5\pos(368,406)\fs32\fad(120,200)}この物語は、{\c&H30C0FF&}あなたのコメント{\c&HFFFFFF&}で進む", 8)
    # 左上：体力＋影化ゲージ
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
    S(0, END, rr(16, 80, 352, 128, 12), "&H100810&", "&H30&", 6)
    E(0, END, "card", r"{\an4\pos(26,104)\fs22\c&HFF80D0&}影化", 8)
    S(0, END, "m %d %d l %d %d l %d %d l %d %d" % (X0, Y0, X1, Y0, X1, Y1, X0, Y1), "&H302030&", "&H00&", 6)
    t = 0.0; step = 1 / 12
    while t < END:
        v = shadow_at(t); w = int((X1 - X0) * v / 100)
        col = "&H6020FF&" if v >= 99.5 and int(t * 6) % 2 else ("&HC040A0&" if v < 80 else "&H6020FF&")
        if v < 99.5 and t > GLOW0: col = "&H70C0FF&" if t < GLOW1 + 0.4 else "&HC040A0&"
        S(t, t + step, "m %d %d l %d %d l %d %d l %d %d" % (X0, Y0, X0 + w, Y0, X0 + w, Y1, X0, Y1), col, "&H00&", 7)
        E(t, t + step, "card", r"{\an6\pos(338,104)\fs22\c&HFFFFFF&\bord2\3c&H000000&}%d%%" % int(round(v)), 9)
        t += step
    # 暴走
    E(BURST + 0.1, BURST + 1.7, "count", r"{\an5\pos(360,380)\fs78\c&HFFFFFF&\3c&H2000A0&\bord7%s\frz-3}ブロック変形\N{\fs96\c&H4040FF&}全開" % pop, 11)
    # 影化100%まで（最後の5秒）
    for k in range(5):
        a = FULL - 5 + k; left = 5 - k
        S(a, a + 1, rr(170, 170, 550, 236, 18), "&H101010&", "&H30&", 6)
        E(a, a + 1, "card", r"{\an5\pos(360,203)\fs30}影化100%%まで {\c&H4040FF&\fs44%s}%d秒" % (pop, left), 7)
    for k in range(6):
        a = FULL + 0.06 * k
        S(a, a + 0.05, "m 0 %d l 720 %d l 720 %d l 0 %d" % (260 + 150 * k, 260 + 150 * k, 300 + 150 * k, 300 + 150 * k), "&H2000FF&", "&H60&", 10)
    E(FULL, FULL + 1.8, "count", r"{\an5\pos(360,420)\fs110\c&H3030FF&\3c&HFFFFFF&\bord7%s\frz4}影化 100%%" % pop, 11)
    S(FULL + 0.6, FULL + 3.4, rr(170, 530, 550, 620, 22), "&H200020&", "&H20&", 6, r"\fad(150,200)")
    E(FULL + 0.6, FULL + 3.4, "card", r"{\an5\pos(360,575)\fs40\c&H4040FF&\fad(150,200)}制御不能", 7)
    # ルカの光
    E(GLOW1 - 0.2, GLOW1 + 2.2, "count", r"{\an5\pos(360,400)\fs66\c&HFFFFFF&\3c&H303030&\bord6%s}影化 {\c&H6020FF&}100%%{\c&HFFFFFF&} → {\c&H60E0FF&}62%%" % pop, 11)
    S(GLOW1 + 0.4, GLOW1 + 2.2, rr(150, 480, 570, 560, 20), "&H102030&", "&H20&", 6, r"\fad(150,200)")
    E(GLOW1 + 0.4, GLOW1 + 2.2, "card", r"{\an5\pos(360,520)\fs34\c&H90E8FF&\fad(150,200)}ルカの手が、光ってる…？", 7)
    # 日食が明ける
    E(SUN0 + 0.3, SUN0 + 2.6, "card", r"{\an5\pos(360,330)\fs46\c&HFFFFFF&\bord4\3c&H000000&\fad(200,300)}日食が、明ける", 9)
    # 光の器
    S(VESSEL + 0.3, VESSEL + 3.6, rr(110, 330, 610, 470, 24), "&H101010&", "&H20&", 6, r"\fad(150,250)")
    E(VESSEL + 0.3, VESSEL + 3.6, "card", r"{\an5\pos(360,368)\fs30\c&HC0C0C0&\fad(150,250)}ルカの正体", 7)
    E(VESSEL + 0.7, VESSEL + 3.6, "count", r"{\an5\pos(360,428)\fs62\c&H60E0FF&\3c&H000000&\bord5%s\fad(0,250)}光の器" % pop, 8)
    # 言いかけて消える
    E(DIS1 - 1.4, DIS1 + 0.4, "card", r"{\an5\pos(360,420)\fs44\c&HFFFFFF&\bord4\3c&H000000&\fad(200,300)}言いかけたまま、消えた", 9)
    # 塔
    E(TOWER0 + 1.0, TOWER0 + 3.0, "count", r"{\an5\pos(360,330)\fs88\c&HFFFFFF&\3c&H101010&\bord7%s\frz-3}謎の塔" % pop, 9)
    # ルカの指先（最後）
    for k in range(3):
        a = TIP + 1.4 + 0.07 * k
        S(a, a + 0.05, "m 0 %d l 720 %d l 720 %d l 0 %d" % (380 + 170 * k, 380 + 170 * k, 420 + 170 * k, 420 + 170 * k), "&HFF00C0&", "&H70&", 10)
    S(TIP + 1.4, END, rr(150, 380, 570, 470, 20), "&H200020&", "&H20&", 6)
    E(TIP + 1.4, END, "count", r"{\an5\pos(360,425)\fs54\c&HFFB0F0&\3c&H400040&\bord5%s}ルカ 影化 3%%" % pop, 11)
    E(END - 2.0, END, "count", r"{\an5\pos(360,540)\fs38\c&HFFFFFF&\3c&H000000&\bord4\fad(300,0)}― パート5へつづく ―", 9)
    # 上端の進行バー
    S(0, END, "m 0 0 l 720 0 l 720 7 l 0 7", "&HC040A0&", "&H00&", 12, r"\clip(0,0,0,7)\t(0,%d,\clip(0,0,720,7))" % int(END * 1000))
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
    B.block_part4(add, DUR, BURST, FULL, GRAB, GLOW0, SUN0, VESSEL, DIS0, TOWER0, TIP, tail=TAIL)
    add(X.braam(2.6, 41.0), 0.05, 0.4); add(R.charge(BURST - 0.2), 0.1, 0.3)
    for k in range(6): add(glitch(0.2, 20 + k), 0.3 + k * 0.55, 0.12 + 0.02 * k)
    X.hit(add, BURST, 1.6, 0); add(R.boom(3.0), BURST, 0.8); add(R.shatter(1.4), BURST + 0.3, 0.6)
    rng = np.random.default_rng(7)
    for k in range(12):                                                                     # 柱が突き出す
        tm = BURST + 0.03 * k + rng.uniform(0, 0.05)
        add(R.thud(0.5), tm, 0.35, rng.uniform(-0.9, 0.9))
    for k in range(8): add(R.shatter(0.8), BURST + 0.5 + k * 0.12 + rng.uniform(0, 0.05), 0.3, rng.uniform(-0.8, 0.8))
    add(X.braam(3.0, 36.0), BURST + 0.1, 0.6); add(X.tinnitus(2.0, 4800), BURST + 0.4, 0.25)
    hb = R.heartbeat()
    t = 7.0
    while t < FULL: add(hb, t, 0.4); t += 0.7 - 0.05 * (t - 7.0)
    for k in range(5): add(tick(0.09, 1800), FULL - 5 + k, 0.5)
    add(glitch(0.8, 3), FULL, 0.45); X.hit(add, FULL, 1.3, 0); add(X.stinger(1.4), FULL, 0.35); add(X.tinnitus(3.0, 5600), FULL + 0.1, 0.3)
    for k in range(8): add(glitch(0.2, 30 + k), FULL + 0.6 + k * 0.55, 0.15)
    t = FULL + 0.5
    while t < GRAB: add(hb, t, 0.45); t += 0.45
    add(R.whoosh(0.5, 300, 1500), GRAB - 0.2, 0.3); add(R.lp(R.kick(80, 40, 0.2, 0.05), 600), GRAB, 0.3)
    add(X.swell(2.0), GLOW0 - 1.6, 0.4); add(R.sparkle(1.5) if hasattr(R, "sparkle") else X.swell(1.2), GLOW0, 0.3)
    add(R.whoosh(1.2, 600, 3000), SUN0, 0.25); add(X.swell(3.0), SUN0, 0.45)
    X.hit(add, VESSEL, 0.8, 0.3)
    add(R.lp(R.noise(DIS1 - DIS0), 2000) * 0.3, DIS0, 0.35)
    for k in range(10): add(R.lp(R.noise(0.15), 3000) * R.dec(0.15, 0.05), DIS0 + 0.4 + k * 0.45, 0.25, 0.4 * (-1) ** k)
    add(R.boom(3.0), TOWER0, 0.6); add(R.lp(R.noise(3.6), 120) * 0.8, TOWER0, 0.45); add(X.braam(3.0, 38.0), TOWER0 + 0.3, 0.5)
    add(glitch(0.5, 9), TIP + 1.4, 0.35); add(X.stinger(1.4), TIP + 1.4, 0.35); add(X.tinnitus(3.0, 3600), TIP + 1.5, 0.3)
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
    tmp = tempfile.mkdtemp(prefix="blk4_")
    out = R.MIX[: R.n_(DUR + TAIL)].copy()
    out[-R.n_(0.8):] *= np.linspace(1, 0, R.n_(0.8))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "blk4_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "blk4_ui.ass"); build_ui(ass)
    if "--ui" in sys.argv: print("wrote", wav, ass); return
    mp4 = os.path.join(HERE, "block_part4.mp4"); raw = os.path.join(tmp, "raw.mp4")
    grade = "fps=24,lenscorrection=k1=0.07:k2=0.0,crop=680:1208,scale=720:1280,vignette=PI/5,eq=contrast=1.04:saturation=1.08,ass=blk4_ui.ass"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", os.path.join(FR, "%04d.png"), "-i", wav, "-vf", grade,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-maxrate", "6M", "-bufsize", "12M",
                    "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-t", "%.3f" % DUR, raw], check=True, cwd=HERE)
    subprocess.run(["python3", os.path.join(HERE, "s2_endcard.py"), raw, mp4, "%.2f" % (END - 0.5),
                    "次は、どうする？", "🗼", "塔へ行く", "🏠", "ここに残る", "▶ 次回：光の器", "2.8"],
                   check=True, env=dict(os.environ, ENDCARD_HINT="絵文字ひとつでOK！"))
    fin = os.path.join(tmp, "fin.mp4"); shutil.move(mp4, fin)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", fin, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-shortest", "-movflags", "+faststart", mp4], check=True)
    shutil.rmtree(tmp)
    # 冒頭に「影化100%まで あと3秒」の予告＋巻き戻し
    subprocess.run([sys.executable, os.path.join(HERE, "make_teaser_tsu.py"), mp4, "%.1f" % (FULL - 3.0), "◀◀ %d秒前" % int(FULL - 3.0), "blk", "影化100%まで あと"], check=True, cwd=HERE)
    print("wrote", mp4)

if __name__ == "__main__":
    main()
