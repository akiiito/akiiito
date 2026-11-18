"""
make_reel_s3e1.py ― 『恋は心理学で落とせる？』第1話「単純接触効果」のリール書き出し
  表情ちがいの静止画（frames_S3E1/<shot>_<expr>.png）を口パク・まばたきで切り替えてアニメにする
  ＋雑学カード＋回数カウンター＋明るいBGM＋声＋最後に絵文字2択カード
  python make_reel_s3e1.py → koi_shinri_ep1.mp4
"""
import os, random, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
FR = os.path.join(HERE, "frames_S3E1")
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
    (T(0.2), T(4.0), "データによると…人は、会う回数が多いほど\\N相手を好きになるの！", "データによると、ひとは、あうかいすうがおおいほど、あいてをすきになるの！", "normal", "mei"),
    (T(4.6), T(8.2), "つまり…陽太くんの前を\\N1日20回通れば！", "つまり、ようたくんのまえを、いちにち、にじゅっかいとおれば！", "normal", "mei"),
    (T(15.8), T(19.4), "…小鳥遊さん。\\N今日、20回目だよね", "たかなしさん。きょう、にじゅっかいめだよね", "soft", "yota"),
    (T(19.8), T(22.2), "か、数えてたの！？", "か、かぞえてたの！？", "normal", "mei"),
    (T(22.6), T(25.8), "…でも、いないと\\Nなんか気になる", "でも、いないと、なんか、きになる", "soft", "yota"),
    (T(26.2), T(29.4), "り、理論上…\\N完璧…！", "り、りろんじょう、かんぺき！", "normal", "mei"),
    (T(29.8), T(33.4), "※ただし、第一印象が悪いと\\N逆効果だから注意ね！", "ただし、だいいちいんしょうがわるいと、ぎゃっこうかだから、ちゅういね！", "normal", "mei"),
]
# 映像の段取り：(開始, 終了, ショット, 話す人, ふだんの表情, 口あき表情, ズーム0, ズーム1, cx, cy, ゆれ)
SEGS = [
    (0, PRE, "WD4", None, "blush", None, 1.25, 1.4, 0.3, 0.45, 2),               # 冒頭：20回目
    (T(0), T(4.4), "MC", "mei", "base", "talk", 1.0, 1.08, 0.5, 0.4, 2),
    (T(4.4), T(8.4), "MC", "mei", "smile", "smiletalk", 1.1, 1.18, 0.5, 0.4, 2),
    (T(8.4), T(10.2), "WD1", None, "smile", None, 1.0, 1.06, 0.4, 0.5, 3),
    (T(10.2), T(12.0), "WD2", None, "smile", None, 1.06, 1.12, 0.35, 0.5, 3),
    (T(12.0), T(13.8), "WD3", None, "smile", None, 1.1, 1.16, 0.45, 0.5, 3),
    (T(13.8), T(15.6), "WD4", None, "blush", None, 1.12, 1.3, 0.3, 0.45, 3),
    (T(15.6), T(19.6), "YC", "yota", "base", "talk", 1.0, 1.12, 0.5, 0.35, 2),
    (T(19.6), T(22.4), "MC", "mei", "shockc", "shock", 1.25, 1.3, 0.5, 0.35, 8),
    (T(22.4), T(26.0), "YC", "yota", "base", "talk", 1.12, 1.22, 0.5, 0.35, 2),
    (T(26.0), T(29.6), "MC", "mei", "blush", "blushtalk", 1.15, 1.25, 0.5, 0.38, 3),
    (T(29.6), T(END), "MC", "mei", "blushsmile", "smiletalk", 1.0, 1.04, 0.5, 0.4, 1),
]
COUNTS = [(T(8.4), "1回目"), (T(10.2), "7回目"), (T(12.0), "13回目"), (T(13.8), "20回目！")]

def frames_for(seg, rnd):
    """1コマずつ使う静止画を決める（話している間は口パク、ときどきまばたき）"""
    t0, t1, shot, who, rest, talk = seg[:6]
    n = int(round((t1 - t0) * FPS)); out = []
    spans = [(st, en) for st, en, *_x, w in R.LINES if w == who] if who else []
    next_blink = t0 + rnd.uniform(0.8, 2.0); blink_left = 0; flap = 0
    for k in range(n):
        t = t0 + k / FPS
        speaking = any(st <= t <= en - 0.05 for st, en in spans)
        e = rest
        if speaking:
            flap = (flap + 1) % 6; e = talk if flap < 3 else rest
        if who and rest in ("base", "blush") and not speaking:
            if t >= next_blink and blink_left == 0: blink_left = 3; next_blink = t + rnd.uniform(2.2, 3.8)
            if blink_left: e = "blink"; blink_left -= 1
        p = os.path.join(FR, "%s_%s.png" % (shot, e))
        if not os.path.exists(p): p = os.path.join(FR, "%s_%s.png" % (shot, rest))
        out.append(p)
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
        seg_video(frames_for(seg, rnd), seg[1] - seg[0], p, *seg[6:], tmp, k); outs.append(p)
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
    "Style: mei,{f},50,&H00FFFFFF,&H00FFFFFF,&H008A3CE8,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: yota,{f},50,&H00FFFFFF,&H00FFFFFF,&H00306A9A,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
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
                      r"もしも好きな人と\N1日20回会ったら…？", 8)
    # 雑学カード（ノート風）
    c0, c1 = T(4.4), T(8.4)
    S(c0, c1, rr(50, 150, 670, 470, 30), "&HF4F0FF&", "&H10&", 6, r"\fad(150,100)\fscx90\fscy90\t(0,150,\fscx100\fscy100)")
    S(c0, c1, rr(50, 150, 670, 230, 30), "&H9B5CF0&", "&H00&", 7, r"\fad(150,100)")
    E(c0, c1, "card", r"{\an5\pos(360,190)\fs34\fad(150,100)}恋の心理学 No.1", 8)
    E(c0, c1, "card", r"{\an5\pos(360,300)\fs62\c&H6A2BD0&\fad(150,100)}単純接触効果", 8)
    E(c0, c1, "card", r"{\an5\pos(360,350)\fs28\c&H6A2BD0&\fad(150,100)}（ザイオンス効果）", 8)
    E(c0, c1, "card", r"{\an5\pos(360,415)\fs32\c&H303030&\fad(150,100)}会う回数が増えるほど、好感度が上がる", 8)
    # 回数カウンター
    for k, (t0, txt) in enumerate(COUNTS):
        t1 = COUNTS[k + 1][0] if k + 1 < len(COUNTS) else T(15.6)
        E(t0, t1, "count", r"{\an5\pos(360,250)\fscx40\fscy40\t(0,140,\fscx115\fscy115)\t(140,240,\fscx100\fscy100)\frz-6}%s" % txt, 8)
    # 驚き（集中線のかわりに放射する線）
    for k in range(18):
        a = k / 18 * 6.283
        import math
        x0, y0 = 360 + math.cos(a) * 420, 640 + math.sin(a) * 760; x1, y1 = 360 + math.cos(a) * 900, 640 + math.sin(a) * 1500
        S(T(19.6), T(20.6), "m %d %d l %d %d l %d %d" % (x0, y0, x1 + math.sin(a) * 40, y1 - math.cos(a) * 40, x1 - math.sin(a) * 40, y1 + math.cos(a) * 40),
          "&HFFFFFF&", "&H40&", 6, r"\fad(0,300)")
    # 補足カード
    c0, c1 = T(29.6), T(END)
    S(c0, c1, rr(50, 150, 670, 420, 30), "&HE8FFF6&", "&H10&", 6, r"\fad(150,0)")
    S(c0, c1, rr(50, 150, 670, 220, 30), "&H50B060&", "&H00&", 7, r"\fad(150,0)")
    E(c0, c1, "card", r"{\an5\pos(360,185)\fs32\fad(150,0)}ホントの使い方", 8)
    E(c0, c1, "card", r"{\an5\pos(360,280)\fs36\c&H205020&\fad(150,0)}第一印象が悪いと、逆効果", 8)
    E(c0, c1, "card", r"{\an5\pos(360,350)\fs36\c&H205020&\fad(150,0)}“自然な回数”がいちばん効く", 8)
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
            gain = 0.05 if T(15.6) <= tt_ < T(26.0) else 0.09               # 陽太が話す所は控えめに
            add(pluck(ch[i % 3] * (2 if i % 4 == 3 else 1)), tt_, gain, 0.3 * ((-1) ** i))
        add(R.lp(pluck(ch[0] / 2, 0.9), 600), t, 0.18); add(R.lp(pluck(ch[0] / 2, 0.9), 600), t + 2 * beat, 0.14)
        t += 4 * beat; bar += 1
    add(R.fade(R.crowd(DUR, 300, 1500, 1.4), 0.4, 0.4), 0, 0.03, 0.3)                # 朝の教室のざわめき
    # 効果音
    for t0, _ in COUNTS:                                                            # シュッ＋ポン
        add(R.fade(R.bp(R.noise(0.25), 800, 5000) * np.linspace(0.2, 1, R.n_(0.25)) ** 2, 0.01, 0.05), t0 - 0.12, 0.25)
        add(pluck(880, 0.25) + pluck(1320, 0.25), t0 + 0.05, 0.25)
    add(R.chime([1046.5, 1318.5, 1568.0], 0.06, 0.8), T(4.4), 0.3)                   # 雑学カード
    add(R.boom(1.0), T(19.6), 0.45)                                                 # ガーン
    add(R.fade(np.sin(2 * np.pi * np.cumsum(np.linspace(900, 300, R.n_(0.6))) / SR), 0.01, 0.1), T(19.65), 0.12)
    add(R.chime([1568.0, 2093.0, 2637.0, 3136.0], 0.05, 1.0), T(26.0), 0.25)          # 照れ（キラキラ）
    add(R.chime([1046.5, 1568.0], 0.06, 0.8), T(29.6), 0.25)

def main():
    tmp = tempfile.mkdtemp(prefix="s3e1_")
    build_sfx(); R.build_voice()                                                   # 先に声 → 口パクのタイミングに使う
    base = build_picture(tmp)
    out = R.MIX[: R.n_(DUR)].copy()
    out[-R.n_(0.3):] *= np.linspace(1, 0, R.n_(0.3))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "s3e1_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "s3e1_ui.ass"); build_ui(ass)
    mp4 = os.path.join(HERE, "koi_shinri_ep1.mp4"); raw = os.path.join(tmp, "raw.mp4")
    grade = "eq=contrast=1.03:saturation=1.08,ass=s3e1_ui.ass"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", base, "-i", wav, "-vf", grade, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "18", "-preset", "slow", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
                    "-t", "%.3f" % DUR, raw], check=True, cwd=HERE)
    subprocess.run(["python3", os.path.join(HERE, "s2_endcard.py"), raw, mp4, "%.2f" % T(33.7),
                    "あなたなら、どっち？", "💌", "毎日会いに行く", "🙈", "あえて会わない", "▶ 次回「吊り橋効果」"], check=True)
    shutil.rmtree(tmp)
    print("wrote", mp4)

if __name__ == "__main__":
    main()
