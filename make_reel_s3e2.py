"""
make_reel_s3e2.py ― 『恋は心理学で落とせる？』第2話「吊り橋効果」のリール書き出し
  表情ちがいの静止画（frames_S3E1/<shot>_<expr>.png）を口パク・まばたきで切り替えてアニメにする
  ＋雑学カード＋回数カウンター＋明るいBGM＋声＋最後に絵文字2択カード
  python make_reel_s3e2.py → koi_shinri_ep2.mp4
"""
import os, random, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
FR = os.path.join(HERE, "frames_S3E2")
FR1 = os.path.join(HERE, "frames_S3E1")
PRE = 2.2
END = 35.2
DUR = PRE + END
R.DUR = DUR
R.MIX = np.zeros((R.n_(DUR) + SR, 2))
add = R.add
def T(s): return PRE + s

R.VV_CAST.update({
    "mei":  (1325133120, 1325133120, 0.0, 1.05, 1.15),     # 花音
    "yota": (593129376, 593129376, 0.0, 0.95, 0.9),        # 蒼月ハヤテ
})
R.VOICE.update({"mei": (0, 0, 1.1, 0.04), "yota": (0, 0, 1.1, 0.04)})
R.SPK_REF_TEXT[:] = ["今日の放課後、少しだけ話せる", "写真、見せてくれる", "ううん、なんでもない", "また明日ね", "窓の外、きれいだね"]
R.LINES = [
    (T(0.2), T(3.8), "データによると、ドキドキを\\N恋と勘違いするの！", "データによると、ドキドキを、こいと、かんちがいするの！", "normal", "mei"),
    (T(4.4), T(7.8), "だから、お化け屋敷に\\Nさそえば…完璧！", "だから、おばけやしきに、さそえば、かんぺき！", "normal", "mei"),
    (T(8.2), T(10.8), "ふふん、私は\\N怖くないし！", "ふふん、わたしは、こわくないし！", "normal", "mei"),
    (T(12.0), T(14.0), "で、出たああっ！", "で、でたああっ！", "normal", "mei"),
    (T(17.2), T(20.4), "…小鳥遊さん。\\Nドキドキしてる？", "たかなしさん。ドキドキしてる？", "soft", "yota"),
    (T(20.6), T(23.8), "し、してない！\\Nこれは吊り橋効果で…！", "し、してない！これは、つりばしこうかで！", "normal", "mei"),
    (T(24.2), T(27.0), "…じゃあ、\\N俺もかも", "じゃあ、おれもかも", "soft", "yota"),
    (T(29.2), T(33.2), "※ただし、もともと好かれてないと\\N逆効果だから注意！", "ただし、もともと、すかれてないと、ぎゃっこうかだから、ちゅうい！", "normal", "mei"),
]
# 映像の段取り：(開始, 終了, 絵のフォルダ, 話す人, ふだんの絵, 口あきの絵, まばたきの絵, ズーム0, ズーム1, cx, cy, ゆれ)
SEGS = [
    (0, PRE, FR, None, "HC_blush_smile", None, None, 1.1, 1.25, 0.62, 0.3, 2),               # 冒頭：しがみつく
    (T(0), T(4.2), FR1, "mei", "MC_base", "MC_talk", "MC_blink", 1.0, 1.08, 0.5, 0.25, 2),
    (T(4.2), T(8.0), FR1, "mei", "MC_smile", "MC_smiletalk", None, 1.1, 1.18, 0.5, 0.25, 2),
    (T(8.0), T(11.0), FR, "mei", "HW_smile_base", "HW_smile_base", None, 1.0, 1.12, 0.5, 0.4, 3),
    (T(11.0), T(12.0), FR, None, "HG", None, None, 1.0, 1.35, 0.5, 0.35, 16),               # おばけ！
    (T(12.0), T(14.0), FR, "mei", "HM_shockc", "HM_shock", None, 1.1, 1.2, 0.5, 0.25, 10),
    (T(14.0), T(17.0), FR, None, "HC_shockc_base", None, None, 1.0, 1.08, 0.62, 0.3, 4),
    (T(17.0), T(20.5), FR, "yota", "HC_blush_base", "HC_blush_talk", "HC_blush_blink", 1.08, 1.16, 0.62, 0.3, 2),
    (T(20.5), T(24.0), FR, "mei", "HC_blush_base", "HC_blushtalk_base", None, 1.16, 1.24, 0.62, 0.3, 3),
    (T(24.0), T(27.2), FR, "yota", "HC_shockc_base", "HC_shockc_talk", None, 1.24, 1.3, 0.62, 0.3, 2),
    (T(27.2), T(29.0), FR, None, "HC_blush_smile", None, None, 1.3, 1.36, 0.62, 0.3, 1),
    (T(29.0), T(END), FR1, "mei", "MC_blushsmile", "MC_smiletalk", None, 1.0, 1.04, 0.5, 0.4, 1),
]
def frames_for(seg, rnd):
    """1コマずつ使う静止画を決める（話している間は口パク、ときどきまばたき）"""
    t0, t1, d, who, rest, talk, blink = seg[:7]
    n = int(round((t1 - t0) * FPS)); out = []
    spans = [(st, en) for st, en, *_x, w in R.LINES if w == who] if who else []
    next_blink = t0 + rnd.uniform(0.8, 2.0); blink_left = 0; flap = 0
    for k in range(n):
        t = t0 + k / FPS
        speaking = any(st <= t <= en - 0.05 for st, en in spans)
        e = rest
        if speaking and talk:
            flap = (flap + 1) % 6; e = talk if flap < 3 else rest
        elif blink:
            if t >= next_blink and blink_left == 0: blink_left = 3; next_blink = t + rnd.uniform(2.2, 3.8)
            if blink_left: e = blink; blink_left -= 1
        out.append(os.path.join(d, e + ".png"))
    return out

def seg_video(paths, dur, out, z0, z1, cx, cy, shake, tmp, k):
    d = os.path.join(tmp, "seg%02d" % k); os.makedirs(d)
    for i, p in enumerate(paths): os.symlink(p, os.path.join(d, "%04d.png" % (i + 1)))
    n = len(paths)
    z = "(%f+(%f-%f)*on/%d)" % (z0, z1, z0, max(n - 1, 1))
    xs = "(sin(on*0.11)*%f+sin(on*0.047+1.3)*%f)" % (shake, shake * 0.7)
    ys = "(sin(on*0.083+0.7)*%f+sin(on*0.031+2.1)*%f)" % (shake * 0.8, shake * 0.6)
    vf = ("scale=1440:2560,zoompan=z='%s*1.04':x='(iw-iw/zoom)*%f+%s':y='(ih-ih/zoom)*%f+%s':d=1:s=720x1280:fps=%d"
          % (z, cx, xs, cy, ys, FPS))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(d, "%04d.png"), "-vf", vf,
                    "-frames:v", str(n), "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "14", "-preset", "fast", out], check=True)

def build_picture(tmp):
    rnd = random.Random(3); outs = []
    for k, seg in enumerate(SEGS):
        p = os.path.join(tmp, "s%02d.mp4" % k)
        seg_video(frames_for(seg, rnd), seg[1] - seg[0], p, *seg[7:], tmp, k); outs.append(p)
    lst = os.path.join(tmp, "list.txt"); open(lst, "w").write("".join("file '%s'\n" % o for o in outs))
    base = os.path.join(tmp, "base.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", base], check=True)
    return base

def rr(x0, y0, x1, y1, r):
    k = 0.45 * r
    return ("m %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d"
            % (x0 + r, y0, x1 - r, y0, x1 - r + k, y0, x1, y0 + r - k, x1, y0 + r, x1, y1 - r, x1, y1 - r + k, x1 - r + k, y1, x1 - r, y1,
               x0 + r, y1, x0 + r - k, y1, x0, y1 - r + k, x0, y1 - r, x0, y0 + r, x0, y0 + r - k, x0 + r - k, y0, x0 + r, y0))

STY = (
    "Style: shape,{f},20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n"
    "Style: mei,{f},46,&H00FFFFFF,&H00FFFFFF,&H008A3CE8,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: yota,{f},46,&H00FFFFFF,&H00FFFFFF,&H00306A9A,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: hook,{f},56,&H0000E5FF,&H0000E5FF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,7,0,5,20,20,0,1\n"
    "Style: card,{f},44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,0,0,5,20,20,0,1\n"
    "Style: count,{f},84,&H0033E0FF,&H0033E0FF,&H00300C88,&H00000000,-1,1,0,0,100,100,2,0,1,8,0,5,0,0,0,1\n")

def build_ui(path):
    ev = []
    def E(t0, t1, style, text, layer=5):
        ev.append("Dialogue: %d,%s,%s,%s,,0,0,0,,%s" % (layer, R.ts(t0), R.ts(t1), style, text))
    def S(t0, t1, draw, col, alpha="&H00&", layer=4, extra=""):
        E(t0, t1, "shape", r"{\an7\pos(0,0)\p1\1c%s\1a%s\bord0\shad0%s}%s{\p0}" % (col, alpha, extra, draw), layer)
    E(0, PRE, "hook", r"{\an5\pos(360,300)\fscx70\fscy70\t(0,120,\fscx104\fscy104)\t(120,200,\fscx100\fscy100)}"
                      r"もしも好きな人と\Nお化け屋敷に入ったら…？", 8)
    c0, c1 = T(4.2), T(8.0)
    S(c0, c1, rr(50, 150, 670, 470, 30), "&HF4F0FF&", "&H10&", 6, r"\fad(150,100)\fscx90\fscy90\t(0,150,\fscx100\fscy100)")
    S(c0, c1, rr(50, 150, 670, 230, 30), "&H9B5CF0&", "&H00&", 7, r"\fad(150,100)")
    E(c0, c1, "card", r"{\an5\pos(360,190)\fs34\fad(150,100)}恋の心理学 No.2", 8)
    E(c0, c1, "card", r"{\an5\pos(360,300)\fs66\c&H6A2BD0&\fad(150,100)}吊り橋効果", 8)
    E(c0, c1, "card", r"{\an5\pos(360,385)\fs30\c&H303030&\fad(150,100)}怖さのドキドキを、脳が\N“恋のドキドキ”と勘違いする", 8)
    E(T(8.0), T(10.6), "card", r"{\an7\pos(30,60)\fs28\bord3\3c&H000000&\fad(150,200)}文化祭・1年A組「お化け屋敷」", 8)
    # おばけ：白フラッシュ
    S(T(11.0), T(11.25), rr(-10, -10, 730, 1290, 0), "&HFFFFFF&", "&H00&", 9, r"\fad(0,200)")
    for k in range(18):                                               # 驚きの放射線
        import math
        a_ = k / 18 * 6.283
        x0, y0 = 360 + math.cos(a_) * 380, 640 + math.sin(a_) * 700; x1, y1 = 360 + math.cos(a_) * 900, 640 + math.sin(a_) * 1500
        S(T(12.0), T(13.0), "m %d %d l %d %d l %d %d" % (x0, y0, x1 + math.sin(a_) * 40, y1 - math.cos(a_) * 40, x1 - math.sin(a_) * 40, y1 + math.cos(a_) * 40),
          "&HFFFFFF&", "&H40&", 6, r"\fad(0,300)")
    # ドキドキ（ハートの文字）
    for k, (x, y) in enumerate(((560, 300), (610, 420), (520, 230))):
        E(T(14.3 + k * 0.4), T(17.0), "count", r"{\an5\pos(%d,%d)\fs70\c&H8A5CFF&\3c&HFFFFFF&\bord5\fscx40\fscy40\t(0,150,\fscx110\fscy110)\t(150,300,\fscx100\fscy100)\frz%d}ドキッ" % (x, y, (-1) ** k * 10), 8)
    E(T(27.2), T(29.0), "count", r"{\an5\pos(560,330)\fs90\c&H8A5CFF&\3c&HFFFFFF&\bord6\fscx40\fscy40\t(0,160,\fscx115\fscy115)\t(160,300,\fscx100\fscy100)}キュン", 8)
    c0, c1 = T(29.0), T(END)
    S(c0, c1, rr(50, 150, 670, 420, 30), "&HE8FFF6&", "&H10&", 6, r"\fad(150,0)")
    S(c0, c1, rr(50, 150, 670, 220, 30), "&H50B060&", "&H00&", 7, r"\fad(150,0)")
    E(c0, c1, "card", r"{\an5\pos(360,185)\fs32\fad(150,0)}ホントの使い方", 8)
    E(c0, c1, "card", r"{\an5\pos(360,280)\fs34\c&H205020&\fad(150,0)}もともと“アリ”な相手にだけ効く", 8)
    E(c0, c1, "card", r"{\an5\pos(360,350)\fs34\c&H205020&\fad(150,0)}苦手な相手だと、怖さが嫌な記憶に", 8)
    for st, en, text, _, _, who in R.LINES:
        E(st, en, who, r"{\an5\pos(360,1010)\fad(60,100)}%s" % text, 9)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

def pluck(f, sec=0.35):
    t = R.tt(sec); return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * np.exp(-t / 0.12)

def build_sfx():
    # 明るいBGM（C-G-Am-F、120BPM のはずむアルペジオとベース）
    beat = 0.5; chords = [(261.6, 329.6, 392.0), (196.0, 246.9, 293.7), (220.0, 261.6, 329.6), (174.6, 220.0, 261.6)]
    t = 0.0; bar = 0
    while t < DUR - 0.5:
        ch = chords[bar % 4]
        for i in range(8):
            tt_ = t + i * beat / 2
            if tt_ >= DUR - 0.5: break
            gain = 0.0 if T(8.0) <= tt_ < T(17.0) else (0.05 if T(17.0) <= tt_ < T(29.0) else 0.09)   # お化け屋敷では止める
            add(pluck(ch[i % 3] * (2 if i % 4 == 3 else 1)), tt_, gain, 0.3 * ((-1) ** i))
        if not (T(8.0) <= t < T(17.0)):
            add(R.lp(pluck(ch[0] / 2, 0.9), 600), t, 0.18); add(R.lp(pluck(ch[0] / 2, 0.9), 600), t + 2 * beat, 0.14)
        t += 4 * beat; bar += 1
    add(R.fade(R.crowd(DUR, 300, 1500, 1.4), 0.4, 0.4), 0, 0.03, 0.3)                # 文化祭のざわめき
    add(R.fade(R.pad([55, 58.3, 82.4], T(17.0) - T(8.0), 300, 0.8, 0.8), 0.6, 0.6), T(8.0), 0.35)   # お化け屋敷の不気味な音
    # 効果音
    add(R.chime([1046.5, 1318.5, 1568.0], 0.06, 0.8), T(4.2), 0.3)
    add(R.boom(1.4), T(11.0), 0.7)                                                  # おばけ
    add(R.fade(R.bp(R.saw(700, 0.7) * (1 + 0.5 * np.sin(2 * np.pi * 9 * R.tt(0.7))), 400, 3000), 0.01, 0.2), T(11.05), 0.12)
    hb = R.heartbeat(); t0 = T(14.2)
    while t0 < T(17.0):
        add(hb, t0, 0.55); t0 += 0.42
    add(R.chime([1568.0, 2093.0, 2637.0, 3136.0], 0.05, 1.0), T(27.2), 0.3)
    add(R.chime([1046.5, 1568.0], 0.06, 0.8), T(29.0), 0.25)

def main():
    tmp = tempfile.mkdtemp(prefix="s3e2_")
    build_sfx(); R.build_voice()                                                   # 先に声 → 口パクのタイミングに使う
    base = build_picture(tmp)
    out = R.MIX[: R.n_(DUR)].copy()
    out[-R.n_(0.3):] *= np.linspace(1, 0, R.n_(0.3))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "s3e2_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "s3e2_ui.ass"); build_ui(ass)
    mp4 = os.path.join(HERE, "koi_shinri_ep2.mp4"); raw = os.path.join(tmp, "raw.mp4")
    grade = "eq=contrast=1.03:saturation=1.08,ass=s3e2_ui.ass"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", base, "-i", wav, "-vf", grade, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "18", "-preset", "slow", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
                    "-t", "%.3f" % DUR, raw], check=True, cwd=HERE)
    subprocess.run(["python3", os.path.join(HERE, "s2_endcard.py"), raw, mp4, "%.2f" % T(33.5),
                    "あなたなら、どっちに誘う？", "👻", "お化け屋敷", "🎢", "ジェットコースター", "▶ 次回「ネームコーリング」"], check=True)
    shutil.rmtree(tmp)
    print("wrote", mp4)

if __name__ == "__main__":
    main()
