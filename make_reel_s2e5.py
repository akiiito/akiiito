"""
make_reel_s2e5.py ― 『君は写真に写らない』第5話「一緒に来て」のリール書き出し
  3Dカット（frames_S2E5/U1,U2,V）＋カメラアプリUI＋声＋環境音
  python make_reel_s2e5.py → kimi_utsuranai_ep5.mp4
"""
import os, re, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
FR = os.environ.get("S2E5_FR", os.path.join(HERE, "frames_S2E5"))
PRE = 2.2                                      # 冒頭フック（写真の静止画＋問い）
# 本編の区切り（秒、本編の頭=0）
CAMV, TELL, HAND, END = 4.2, 9.2, 17.6, 33.2
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
    (T(0.3), T(2.6), "凛ちゃんは、この上にいるよ", "りんちゃんは、このうえにいるよ", "soft", "minato"),
    (T(2.8), T(4.2), "朝倉くん…どうして", "あさくらくん、どうして", "soft", "hiyori"),
    (T(5.4), T(7.6), "…やっぱり、写らない", "やっぱり、うつらない", "soft", "hiyori"),
    (T(9.2), T(12.6), "一年前の今日…\\N僕は、ここから落ちたんだ", "いちねんまえのきょう、ぼくは、ここからおちたんだ", "soft", "minato"),
    (T(12.8), T(14.5), "…凛を、かばって？", "りんを、かばって？", "soft", "hiyori"),
    (T(14.6), T(17.4), "凛ちゃんは、ずっと\\N自分を責めてる", "りんちゃんは、ずっと、じぶんをせめてる", "soft", "minato"),
    (T(18.0), T(20.2), "だから…一緒に来て", "だから、いっしょにきて", "soft", "minato"),
    (T(21.2), T(23.6), "君にしか、\\N頼めないんだ", "きみにしか、たのめないんだ", "soft", "minato"),
    (T(25.0), T(27.2), "……朝倉くん、私…", "あさくらくん、わたし", "soft", "hiyori"),
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
    U1 = os.path.join(FR, "U1", "0001.png"); U2 = os.path.join(FR, "U2", "0001.png"); V = os.path.join(FR, "V", "0001.png")
    segs = [
        seg_cmd(U2, PRE, "", still=True, zoom0=1.2, zoom1=1.35, cx=0.45, cy=0.35, shake=2),          # cold open: 差し出された手
        seg_cmd(U1, CAMV, "", still=True, zoom0=1.0, zoom1=1.1, cx=0.45, cy=0.35, shake=6),            # 階段の上に湊
        seg_cmd(V, TELL - CAMV, "", still=True, zoom0=1.1, zoom1=1.16, cx=0.45, cy=0.35, shake=4),     # カメラ越し：写らない
        seg_cmd(U1, HAND - TELL, "", still=True, zoom0=1.1, zoom1=1.3, cx=0.45, cy=0.3, shake=3),      # 告白
        seg_cmd(U2, END - HAND, "", still=True, zoom0=1.15, zoom1=1.5, cx=0.45, cy=0.35, shake=3),     # 一緒に来て
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
                      r"もしも好きな人に\N「こっち側に来て」\Nと言われたら？", 8)
    E(T(0), T(2.4), "ui", r"{\an7\pos(30,60)\fs30\bord2\3c&H000000&\fad(200,300)}0:44  旧校舎 踊り場", 8)
    # --- カメラ越し（湊は写らない）
    c0, c1 = T(CAMV), T(TELL)
    S(c0, c1, rr(-10, -10, 730, 96, 0), "&H000000&", "&H50&")
    S(c0, c1, rr(-10, 1050, 730, 1300, 0), "&H000000&", "&H40&")
    E(c0, c1, "ui", r"{\an5\pos(360,48)\fs26}⚡  ◯  1x")
    E(c0, c1, "ui", r"{\an5\pos(360,1086)\fs26\c&HAAAAAA&}ビデオ    {\c&H00D7FF&}写真{\c&HAAAAAA&}    ポートレート")
    S(c0, c1, circ(360, 1182, 52), "&HFFFFFF&"); S(c0, c1, circ(360, 1182, 44), "&H000000&", "&H00&", 5)
    S(c0, c1, circ(360, 1182, 40), "&HFFFFFF&", "&H00&", 6)
    S(c0, c1, rr(588, 1158, 636, 1206, 10), "&H404040&")
    fx, fy, fw = 300, 420, 80                                     # ピント枠は誰もいない段の上で迷う
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        x, y = fx + sx * fw, fy + sy * fw
        S(c0, c1, rr(min(x, x - sx * 26), min(y, y - sy * 4), max(x, x - sx * 26), max(y, y - sy * 4), 1), "&H00D7FF&", layer=6,
          extra=r"\t(0,600,\alpha&H80&)\t(600,1200,\alpha&H00&)\t(1200,1800,\alpha&H80&)\t(1800,2400,\alpha&H00&)")
        S(c0, c1, rr(min(x, x - sx * 4), min(y, y - sy * 26), max(x, x - sx * 4), max(y, y - sy * 26), 1), "&H00D7FF&", layer=6)
    E(T(CAMV + 1.2), c1, "ui", r"{\an5\pos(300,530)\fs26\c&H00D7FF&\fad(150,0)}顔が検出されません", 7)
    # 終わり
    for st, en, text, _, _, who in R.LINES:
        E(st, en, {"minato": "subm", "rin": "subr"}.get(who, "sub"), r"{\an5\pos(360,%d)\fad(60,120)}%s" % (880, text), 7)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

# ---------------------------------------------------------------- sound
def tick():
    return 0.6 * R.hp(R.noise(0.02), 3000) * R.dec(0.02, 0.003)
def build_sfx():
    add(R.fade(R.bp(R.noise(T(END)), 200, 900) * 0.5, 0.6, 0.6), 0, 0.28, -0.3)              # 夜の旧校舎の風
    add(R.fade(R.lp(R.noise(T(END)), 220) * 0.25, 0.3, 0.6), 0, 0.45)
    add(R.fade(R.pad([55, 82.4, 110], PRE, 400, 0.2, 0.2), 0.2, 0.15), 0, 0.35)
    add(R.fade(R.pad([36.7, 55.0, 73.4], T(HAND) - T(0), 240, 2.0, 0.6), 0.8, 0.6), T(0), 0.35)
    sh = 0.5 * R.hp(R.noise(0.012), 2000)                           # カメラを向ける小さな操作音
    add(sh, T(CAMV + 0.1), 0.4)
    add(R.boom(1.4), T(TELL), 0.4)
    # 手を差し出す：低い音が上がっていき、心臓
    add(R.fade(R.pad([41.2, 61.7, 82.4, 123.5], T(END) - T(HAND), 300, 4.0, 0.5), 1.0, 0.5), T(HAND), 0.6)
    hb = R.heartbeat(); t0 = T(HAND + 0.4); gap = 0.95
    while t0 < T(END):
        add(hb, t0, 0.55); t0 += gap; gap = max(0.55, gap - 0.03)
    add(R.fade(np.sin(2 * np.pi * 4200 * R.tt(T(END) - T(24.8))) * 0.02, 1.0, 0.3), T(24.8), 1.0)

def main():
    tmp = tempfile.mkdtemp(prefix="s2e5_")
    base = build_picture(tmp)
    build_sfx(); R.build_voice()
    out = R.MIX[: R.n_(DUR)].copy()
    out[-R.n_(0.5):] *= np.linspace(1, 0, R.n_(0.5))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "s2e5_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "s2e5_ui.ass"); build_ui(ass)
    mp4 = os.path.join(HERE, "kimi_utsuranai_ep5.mp4")
    grade = "eq=contrast=1.05:saturation=0.9,vignette=PI/5,noise=alls=8:allf=t,ass=s2e5_ui.ass"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", base, "-i", wav, "-vf", grade, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "20", "-maxrate", "6M", "-bufsize", "12M", "-preset", "slow", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
                    "-movflags", "+faststart", "-t", "%.3f" % DUR, mp4], check=True, cwd=HERE)
    # コメント誘導：絵文字2択のカード（最後のコマを1.5秒のばす）
    tmpmp4 = mp4.replace(".mp4", "_nocard.mp4"); os.replace(mp4, tmpmp4)
    subprocess.run(["python3", os.path.join(HERE, "s2_endcard.py"), tmpmp4, mp4, "%.2f" % (PRE + 31.2 - PRE),
                    "あなたなら、一緒に行く？", "🌙", "行く", "☀️", "行かない", "▶ 最終話「ありがとう」"], check=True)
    os.remove(tmpmp4)
    shutil.rmtree(tmp)
    print("wrote", mp4, DUR)

if __name__ == "__main__":
    main()
