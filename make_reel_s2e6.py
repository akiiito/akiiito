"""
make_reel_s2e6.py ― 『君は写真に写らない』最終話「ありがとう」のリール書き出し
  3Dカット（frames_S2E6/R1,R2 ＋ 第1話の A 最終コマ＝湊が写った写真）＋スマホ画面UI＋声＋環境音
  python make_reel_s2e6.py → kimi_utsuranai_ep6.mp4
"""
import os, re, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
FR = os.environ.get("S2E6_FR", os.path.join(HERE, "frames_S2E6"))
FR1 = os.path.join(HERE, "frames_S2E1")
PRE = 2.2                                      # 冒頭フック（写真の静止画＋問い）
# 本編の区切り（秒、本編の頭=0）
DAWN, CLOSE, GONE, GAL, LOCK, END = 2.2, 12.0, 20.4, 24.0, 28.6, 34.0
DUR = PRE + END
R.DUR = DUR
R.MIX = np.zeros((R.n_(DUR) + SR, 2))
add = R.add
def T(s): return PRE + s                       # 本編の秒 → 動画全体の秒

# ---------------------------------------------------------------- cast（声のブレ禁止：1役1スタイル）
R.VV_CAST.update({
    "hiyori": (1717361472, 1717361472, 0.0, 1.0, 1.0),     # みちのくあいり
    "minato": (1937616896, 1937616896, -0.02, 0.92, 0.9),  # にせ
    "rin":    (888753760, 888753760, 0.0, 1.05, 1.1),      # まお
})
R.VOICE.update({"hiyori": (0, 0, 1.15, 0.05), "minato": (0, 0, 1.05, 0.25), "rin": (0, 0, 1.15, 0.05)})
R.SPK_REF_TEXT[:] = ["今日の放課後、少しだけ話せる", "写真、見せてくれる", "ううん、なんでもない", "また明日ね", "窓の外、きれいだね"]
R.LINES = [
    (T(0.4), T(2.0), "ひより…？", "ひより？", "normal", "rin"),
    (T(2.4), T(4.8), "朝倉くん…？\\Nほんとに、いたんだ", "あさくらくん？ほんとに、いたんだ", "normal", "rin"),
    (T(5.0), T(7.2), "久しぶり、凛ちゃん", "ひさしぶり、りんちゃん", "soft", "minato"),
    (T(7.4), T(9.4), "あの日…私のせいで", "あのひ、わたしのせいで", "normal", "rin"),
    (T(9.6), T(11.8), "ちがうよ。\\N僕が、そうしたかったんだ", "ちがうよ。ぼくが、そうしたかったんだ", "soft", "minato"),
    (T(12.4), T(15.0), "…助けてくれて、\\Nありがとう", "たすけてくれて、ありがとう", "normal", "rin"),
    (T(15.4), T(17.4), "…やっと、言ってもらえた", "やっと、いってもらえた", "soft", "minato"),
    (T(17.6), T(20.2), "ひより。写真、\\N消さないでくれて、ありがとう", "ひより。しゃしん、けさないでくれて、ありがとう", "soft", "minato"),
    (T(21.4), T(23.4), "…行っちゃった", "いっちゃった", "soft", "hiyori"),
    (T(25.0), T(27.4), "…写ってる", "うつってる", "soft", "hiyori"),
]

# ---------------------------------------------------------------- picture: segments → base video
def seg_cmd(src, dur, out, still=False, zoom0=1.0, zoom1=1.0, cx=0.5, cy=0.5, shake=5.0, rate=1.0):
    """静止画/連番に手持ちの揺れとゆっくりした寄りを足して dur 秒の映像にする"""
    n = int(round(dur * FPS))
    z = "(%f+(%f-%f)*on/%d)" % (zoom0, zoom1, zoom0, max(n - 1, 1))
    xs = "(sin(on*0.11)*%f+sin(on*0.047+1.3)*%f)" % (shake, shake * 0.7)
    ys = "(sin(on*0.083+0.7)*%f+sin(on*0.031+2.1)*%f)" % (shake * 0.8, shake * 0.6)
    vf = ("scale=1440:2560,zoompan=z='%s*1.06':x='(iw-iw/zoom)*%f+%s':y='(ih-ih/zoom)*%f+%s':d=1:s=720x1280:fps=%d"
          % (z, cx, xs, cy, ys, FPS))
    inp = (["-loop", "1", "-framerate", str(FPS), "-t", "%.3f" % dur, "-i", src] if still
           else ["-framerate", str(FPS * rate), "-i", src])
    return ["ffmpeg", "-y", "-loglevel", "error"] + inp + ["-vf", vf, "-frames:v", str(n), "-pix_fmt", "yuv420p",
                                                         "-c:v", "libx264", "-crf", "14", "-preset", "fast", out]

def black(dur, out):
    return ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=0x0b0d14:s=720x1280:r=%d" % FPS,
            "-t", "%.3f" % dur, "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "14", out]

def build_picture(tmp):
    R1 = os.path.join(FR, "R1", "0001.png"); R2 = os.path.join(FR, "R2", "0001.png"); PH = os.path.join(FR1, "A", "0072.png")
    segs = [
        seg_cmd(R1, PRE, "", still=True, zoom0=1.1, zoom1=1.25, cx=0.55, cy=0.4, shake=2),           # cold open
        black(DAWN, ""),                                                                            # 翌朝
        seg_cmd(R1, CLOSE - DAWN, "", still=True, zoom0=1.0, zoom1=1.12, cx=0.55, cy=0.4, shake=3),
        seg_cmd(R1, GONE - CLOSE, "", still=True, zoom0=1.2, zoom1=1.38, cx=0.65, cy=0.38, shake=2),
        seg_cmd(R2, GAL - GONE, "", still=True, zoom0=1.38, zoom1=1.42, cx=0.65, cy=0.38, shake=2),    # いなくなる
        seg_cmd(PH, LOCK - GAL, "", still=True, zoom0=1.0, zoom1=1.12, cx=0.5, cy=0.42, shake=1),      # 写真に、写っている
        black(END - LOCK, ""),
    ]
    outs = []
    for k, c in enumerate(segs):
        p = os.path.join(tmp, "s%02d.mp4" % k); c[-1] = p; subprocess.run(c, check=True); outs.append(p)
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join("file '%s'\n" % o for o in outs))
    base = os.path.join(tmp, "base.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", base], check=True)
    return base

# ---------------------------------------------------------------- phone UI (ASS drawings)
def rr(x0, y0, x1, y1, r):
    """角丸の四角（ASS ベクター）"""
    k = 0.45 * r
    return ("m %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d"
            % (x0 + r, y0, x1 - r, y0, x1 - r + k, y0, x1, y0 + r - k, x1, y0 + r, x1, y1 - r, x1, y1 - r + k, x1 - r + k, y1, x1 - r, y1,
               x0 + r, y1, x0 + r - k, y1, x0, y1 - r + k, x0, y1 - r, x0, y0 + r, x0, y0 + r - k, x0 + r - k, y0, x0 + r, y0))
def circ(cx, cy, r):
    return rr(cx - r, cy - r, cx + r, cy + r, r)

STY = (
    "Style: ui,{f},30,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n"
    "Style: shape,{f},20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n"
    "Style: sub,{f},54,&H00FFFFFF,&H00FFFFFF,&H00141414,&H96000000,-1,0,0,0,100,100,1,0,1,5,2,5,40,40,0,1\n"
    "Style: subm,{f},54,&H00FFE8D0,&H00FFE8D0,&H00402010,&H96000000,-1,0,0,0,100,100,1,0,1,5,2,5,40,40,0,1\n"
    "Style: subr,{f},54,&H00D0F0FF,&H00D0F0FF,&H00102040,&H96000000,-1,0,0,0,100,100,1,0,1,5,2,5,40,40,0,1\n"
    "Style: hook,{f},52,&H0000E5FF,&H0000E5FF,&H00000000,&HB4000000,-1,0,0,0,100,100,2,0,1,7,3,5,20,20,0,1\n"
    "Style: big,{f},150,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1\n")

def build_ui(path):
    ev = []
    def E(t0, t1, style, text, layer=5):
        ev.append("Dialogue: %d,%s,%s,%s,,0,0,0,,%s" % (layer, R.ts(t0), R.ts(t1), style, text))
    def S(t0, t1, draw, col="&HFFFFFF&", alpha="&H00&", layer=4, extra=""):
        E(t0, t1, "shape", r"{\an7\pos(0,0)\p1\1c%s\1a%s\bord0\shad0%s}%s{\p0}" % (col, alpha, extra, draw), layer)
    E(0, PRE, "hook", r"{\an5\pos(360,420)\fscx70\fscy70\t(0,120,\fscx104\fscy104)\t(120,200,\fscx100\fscy100)}"
                      r"もしも\N「その一言で、彼が消える」\Nと言われたら？", 8)
    E(T(0.2), T(DAWN), "ui", r"{\an5\pos(360,560)\fs40\fad(300,200)}翌朝 5:48", 8)
    # 消える瞬間：白い光
    S(T(GONE - 0.2), T(GONE + 1.2), rr(-10, -10, 730, 1290, 0), "&HE0F0FF&", "&H00&", 9, r"\fad(200,900)")
    # 写真（ギャラリー）
    g0, g1 = T(GAL), T(LOCK)
    S(g0, g1, rr(-10, -10, 730, 110, 0), "&H000000&", "&H30&")
    S(g0, g1, rr(-10, 1110, 730, 1300, 0), "&H000000&", "&H30&")
    E(g0, g1, "ui", r"{\an4\pos(28,62)\fs34}‹")
    E(g0, g1, "ui", r"{\an5\pos(360,48)\fs26}11月17日{\N}{\fs22\c&HBBBBBB&}16:42")
    E(g0, g1, "ui", r"{\an5\pos(360,1190)\fs34\c&HDDDDDD&}⇪      ♡      ⓘ      🗑")
    # 0:00
    l0, l1 = T(LOCK), T(END)
    E(l0, T(29.6), "big", r"{\an5\pos(360,330)}23:59")
    E(T(29.6), l1, "big", r"{\an5\pos(360,330)}0:00")
    E(l0, l1, "ui", r"{\an5\pos(360,200)\fs30\c&HCCCCCC&}11月22日 土曜日")
    S(T(30.0), l1, rr(28, 470, 692, 610, 30), "&H3A3A3A&", "&H30&", 6, r"\fad(120,0)")
    S(T(30.0), l1, rr(52, 498, 108, 554, 14), "&HD08A3C&", "&H00&", 7, r"\fad(120,0)")
    E(T(30.0), l1, "ui", r"{\an7\pos(126,494)\fs26\c&HDDDDDD&\fad(120,0)}トーク  ·  今", 7)
    E(T(30.0), l1, "ui", r"{\an7\pos(126,530)\fs30\fad(120,0)}{\b1}朝倉 湊{\b0}  またね", 7)
    E(T(31.2), T(END), "hook", r"{\an5\pos(360,860)\fs46\fad(200,0)}泣いた？ 怖かった？\Nコメントで教えて！", 8)
    E(T(32.0), T(END), "ui", r"{\an5\pos(360,980)\fs32\fad(200,0)\c&HDDDDDD&}『君は写真に写らない』 完", 8)
    for st, en, text, _, _, who in R.LINES:
        E(st, en, {"minato": "subm", "rin": "subr"}.get(who, "sub"), r"{\an5\pos(360,%d)\fad(60,120)}%s" % (880, text), 7)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

# ---------------------------------------------------------------- sound
def tick():
    return 0.6 * R.hp(R.noise(0.02), 3000) * R.dec(0.02, 0.003)
def build_sfx():
    add(R.fade(R.pad([55, 82.4, 110], PRE, 400, 0.2, 0.2), 0.2, 0.15), 0, 0.35)
    # 夜明け：スズメ、遠くの車
    add(R.fade(R.lp(R.noise(T(GAL)), 300) * 0.22, 0.6, 0.6), T(0), 0.4)
    for k in range(10):
        t0 = T(0.8 + k * 1.9)
        add(R.bp(R.saw(3900 + 250 * (k % 3), 0.05) * R.dec(0.05, 0.02), 2500, 6000), t0, 0.04, 0.6)
    # やさしい和音（最終話だけ少し音楽を足す）
    add(R.fade(R.pad([220.0, 277.2, 329.6, 440.0], T(GONE) - T(DAWN), 1600, 3.0, 2.0), 2.0, 2.0), T(DAWN), 0.12)
    add(R.fade(R.pad([196.0, 246.9, 293.7, 392.0], T(LOCK) - T(12.4), 1600, 2.0, 1.5), 1.5, 1.5), T(12.4), 0.14)
    # 消える：高い鈴のような音
    add(R.chime([1760.0, 2217.5, 2637.0], 0.12, 1.8), T(GONE - 0.2), 0.3)
    # 夜：秒針 → 0:00 の通知 → 低い音で終わる
    t0 = T(LOCK) + 0.2
    while t0 < T(END):
        add(tick(), t0, 0.5, 0.2); t0 += 1.0
    add(R.chime([1318.5, 1760.0], 0.09, 0.6), T(30.0), 0.35)
    add(R.boom(1.8), T(30.0), 0.5)
    add(R.fade(R.pad([41.2, 61.7, 82.4], T(END) - T(30.0), 260, 0.5, 0.4), 0.6, 0.4), T(30.0), 0.5)

def main():
    tmp = tempfile.mkdtemp(prefix="s2e6_")
    base = build_picture(tmp)
    build_sfx(); R.build_voice()
    out = R.MIX[: R.n_(DUR)].copy()
    out[-R.n_(0.5):] *= np.linspace(1, 0, R.n_(0.5))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "s2e6_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "s2e6_ui.ass"); build_ui(ass)
    mp4 = os.path.join(HERE, "kimi_utsuranai_ep6.mp4")
    grade = "eq=contrast=1.05:saturation=0.9,vignette=PI/5,noise=alls=8:allf=t,ass=s2e6_ui.ass"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", base, "-i", wav, "-vf", grade, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "20", "-maxrate", "6M", "-bufsize", "12M", "-preset", "slow", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
                    "-movflags", "+faststart", "-t", "%.3f" % DUR, mp4], check=True, cwd=HERE)
    shutil.rmtree(tmp)
    print("wrote", mp4, DUR)

if __name__ == "__main__":
    main()
