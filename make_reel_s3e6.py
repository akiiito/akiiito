"""
make_reel_s3e6.py ― 『恋は心理学で落とせる？』第6話「返報性の原理」のリール書き出し
  表情ちがいの静止画（frames_S3E1/<shot>_<expr>.png）を口パク・まばたきで切り替えてアニメにする
  ＋雑学カード＋回数カウンター＋明るいBGM＋声＋最後に絵文字2択カード
  python make_reel_s3e6.py → koi_shinri_ep6.mp4
"""
import os, random, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
FR = os.path.join(HERE, "frames_S3E3")
FR1 = os.path.join(HERE, "frames_S3E1")
PRE = 2.2
END = 37.2
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
    (T(0.1), T(4.2), "データによると、何かもらうと\\Nお返ししたくなるの！", "データによると、なにかもらうと、おかえし、したくなるの！", "normal", "mei"),
    (T(4.5), T(7.9), "クッキーをあげれば、\\N好きが返ってくる…はず！", "クッキーをあげれば、すきが、かえってくる、はず！", "normal", "mei"),
    (T(8.3), T(10.9), "こ、これ！\\N作りすぎただけだから！", "こ、これ！つくりすぎた、だけだから！", "normal", "mei"),
    (T(11.2), T(13.6), "…ありがとう。\\N大事に食べる", "ありがとう。だいじに、たべる", "soft", "yota"),
    (T(15.0), T(16.7), "これ、クッキーのお返し", "これ、クッキーのおかえし", "soft", "yota"),
    (T(17.6), T(20.6), "えっ、こんなに！？\\Nお返し、大きすぎない…？", "えっ、こんなに！？おかえし、おおきすぎない？", "normal", "mei"),
    (T(21.0), T(24.6), "返報性の原理。\\N…俺の気持ちも、入ってるから", "へんぽうせいの、げんり。おれの、きもちも、はいってるから", "soft", "yota"),
    (T(25.6), T(28.4), "じゃ、じゃあ、\\Nお返しのお返し…！", "じゃ、じゃあ、おかえしの、おかえし！", "normal", "mei"),
    (T(31.2), T(35.2), "※お返しは小さめがコツ！\\N大きいと気をつかわせちゃう", "おかえしは、ちいさめがコツ！おおきいと、きを、つかわせちゃう", "normal", "mei"),
]
FR6 = os.path.join(HERE, "frames_S3E6")
# 映像の段取り：(開始, 終了, 絵のフォルダ, 話す人, ふだんの絵, 口あきの絵, まばたきの絵, ズーム0, ズーム1, cx, cy, ゆれ)
SEGS = [
    (0, PRE, FR6, None, "GV2_shockc_base", None, None, 1.05, 1.2, 0.5, 0.3, 3),              # 冒頭：大きすぎるお返し
    (T(0), T(4.2), FR1, "mei", "MC_base", "MC_talk", "MC_blink", 1.0, 1.08, 0.5, 0.25, 2),
    (T(4.2), T(8.0), FR1, "mei", "MC_smile", "MC_smiletalk", None, 1.1, 1.18, 0.5, 0.25, 2),
    (T(8.0), T(11.0), FR6, "mei", "GV1_blush_base", "GV1_blushtalk_base", None, 1.05, 1.12, 0.6, 0.35, 2),
    (T(11.0), T(13.7), FR6, "yota", "GV1_blush_smile", "GV1_blush_talk", "GV1_blush_blink", 1.12, 1.18, 0.4, 0.32, 1),
    (T(13.7), T(14.6), FR6, None, "GV1_blushsmile_smile", None, None, 1.0, 1.04, 0.5, 0.35, 1),
    (T(14.6), T(16.8), FR6, "yota", "GV2_shockc_base", "GV2_shockc_talk", "GV2_shockc_blink", 1.0, 1.05, 0.5, 0.35, 2),
    (T(16.8), T(17.5), FR6, None, "GV2_shock_base", None, None, 1.05, 1.2, 0.55, 0.32, 10),
    (T(17.5), T(20.8), FR1, "mei", "MC_shockc", "MC_shock", None, 1.1, 1.18, 0.5, 0.25, 4),
    (T(20.8), T(24.7), FR6, "yota", "GV2_blush_smile", "GV2_blush_talk", "GV2_blush_blink", 1.1, 1.2, 0.42, 0.3, 1),
    (T(24.7), T(25.5), FR6, None, "GV2_blushsmile_smile", None, None, 1.0, 1.05, 0.5, 0.3, 1),
    (T(25.5), T(28.6), FR1, "mei", "MC_blush", "MC_blushtalk", None, 1.15, 1.25, 0.5, 0.25, 3),
    (T(28.6), T(31.0), FR6, None, "GV2_blushsmile_smile", None, None, 1.05, 1.0, 0.5, 0.3, 1),
    (T(31.0), T(END), FR1, "mei", "MC_blushsmile", "MC_smiletalk", None, 1.0, 1.04, 0.5, 0.4, 1),
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
                      r"もしも好きな人に\N手作りクッキーをあげたら…？", 8)
    c0, c1 = T(4.2), T(8.0)
    S(c0, c1, rr(50, 150, 670, 470, 30), "&HF4F0FF&", "&H10&", 6, r"\fad(150,100)\fscx90\fscy90\t(0,150,\fscx100\fscy100)")
    S(c0, c1, rr(50, 150, 670, 230, 30), "&H9B5CF0&", "&H00&", 7, r"\fad(150,100)")
    E(c0, c1, "card", r"{\an5\pos(360,190)\fs34\fad(150,100)}恋の心理学 No.6", 8)
    E(c0, c1, "card", r"{\an5\pos(360,300)\fs66\c&H6A2BD0&\fad(150,100)}返報性の原理", 8)
    E(c0, c1, "card", r"{\an5\pos(360,385)\fs30\c&H303030&\fad(150,100)}何かしてもらうと\N“お返ししなきゃ”と思う心理", 8)
    E(T(8.0), T(10.4), "card", r"{\an7\pos(30,60)\fs28\bord3\3c&H000000&\fad(150,200)}放課後の教室", 8)
    E(T(14.6), T(16.6), "card", r"{\an7\pos(30,60)\fs28\bord3\3c&H000000&\fad(150,200)}― 次の日 ―", 8)
    pop = r"\fscx40\fscy40\t(0,120,\fscx112\fscy112)\t(120,220,\fscx100\fscy100)"
    E(T(13.7), T(14.6), "count", r"{\an5\pos(360,260)\fs76%s}作戦成功…？" % pop, 8)
    E(T(16.8), T(17.6), "count", r"{\an5\pos(360,250)\fs110\c&HFFFFFF&\3c&H2020E0&\bord7%s\frz-6}でかっ！？" % pop, 8)
    E(T(24.7), T(25.5), "count", r"{\an5\pos(360,250)\fs96\c&H8A5CFF&\3c&HFFFFFF&\bord6%s}キュン" % pop, 8)
    E(T(28.6), T(31.0), "count", r"{\an5\pos(360,260)\fs64%s}お返し無限ループ" % pop, 8)
    E(T(29.1), T(31.0), "count", r"{\an5\pos(360,350)\fs110\c&HFFFFFF&\3c&H8A5CFF&\bord6\frz0\t(0,1900,\frz-720)}∞", 8)
    c0, c1 = T(31.0), T(END)
    S(c0, c1, rr(50, 150, 670, 420, 30), "&HE8FFF6&", "&H10&", 6, r"\fad(150,0)")
    S(c0, c1, rr(50, 150, 670, 220, 30), "&H50B060&", "&H00&", 7, r"\fad(150,0)")
    E(c0, c1, "card", r"{\an5\pos(360,185)\fs32\fad(150,0)}ホントの使い方", 8)
    E(c0, c1, "card", r"{\an5\pos(360,280)\fs34\c&H205020&\fad(150,0)}あげるのは、相手が気をつかわない", 8)
    E(c0, c1, "card", r"{\an5\pos(360,350)\fs34\c&H205020&\fad(150,0)}小さなもの（お菓子1個くらい）", 8)
    for st, en, text, _, _, who in R.LINES:
        E(st, en, who, r"{\an5\pos(360,1010)\fad(60,100)}%s" % text, 9)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

def pluck(f, sec=0.35):
    t = R.tt(sec); return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * np.exp(-t / 0.12)

def build_sfx():
    # 明るいBGM（C-G-Am-F、120BPM）。陽太の告白っぽい一言の間だけ止める
    beat = 0.5; chords = [(261.6, 329.6, 392.0), (196.0, 246.9, 293.7), (220.0, 261.6, 329.6), (174.6, 220.0, 261.6)]
    t = 0.0; bar = 0
    quiet = lambda x: T(20.8) <= x < T(24.7)
    while t < DUR - 0.5:
        ch = chords[bar % 4]
        for i in range(8):
            tt_ = t + i * beat / 2
            if tt_ >= DUR - 0.5: break
            gain = 0.0 if quiet(tt_) else (0.05 if T(8.0) <= tt_ < T(31.0) else 0.08)
            add(pluck(ch[i % 3] * (2 if i % 4 == 3 else 1)), tt_, gain, 0.3 * ((-1) ** i))
        if not quiet(t):
            add(R.lp(pluck(ch[0] / 2, 0.9), 600), t, 0.18); add(R.lp(pluck(ch[0] / 2, 0.9), 600), t + 2 * beat, 0.14)
        t += 4 * beat; bar += 1
    add(R.fade(R.crowd(DUR, 300, 1500, 1.4), 0.4, 0.4), 0, 0.02, 0.3)                # 放課後のざわめき
    add(R.chime([1046.5, 1318.5, 1568.0], 0.06, 0.8), T(4.2), 0.3)
    add(R.chime([784.0, 1046.5], 0.05, 0.5), T(13.7), 0.18)
    add(R.chime([523.3, 659.3, 784.0, 1046.5], 0.04, 0.6), T(14.6), 0.18)              # 次の日
    add(R.boom(1.0), T(16.8), 0.4)                                                  # でかっ
    hb = R.heartbeat(); t0 = T(21.0)
    while t0 < T(24.7):
        add(hb, t0, 0.4); t0 += 0.42
    add(R.chime([1568.0, 2093.0, 2637.0, 3136.0], 0.05, 1.0), T(24.7), 0.3)
    for k in range(6):
        add(R.chime([880.0 * (1.06 ** k)], 0.02, 0.25), T(28.7) + k * 0.36, 0.1)      # 無限ループ
    add(R.chime([1046.5, 1568.0], 0.06, 0.8), T(31.0), 0.25)

def main():
    tmp = tempfile.mkdtemp(prefix="s3e6_")
    build_sfx(); R.build_voice()                                                   # 先に声 → 口パクのタイミングに使う
    base = build_picture(tmp)
    out = R.MIX[: R.n_(DUR)].copy()
    out[-R.n_(0.3):] *= np.linspace(1, 0, R.n_(0.3))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "s3e6_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "s3e6_ui.ass"); build_ui(ass)
    mp4 = os.path.join(HERE, "koi_shinri_ep6.mp4"); raw = os.path.join(tmp, "raw.mp4")
    grade = "eq=contrast=1.03:saturation=1.08,ass=s3e6_ui.ass"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", base, "-i", wav, "-vf", grade, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "18", "-preset", "slow", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
                    "-t", "%.3f" % DUR, raw], check=True, cwd=HERE)
    subprocess.run(["python3", os.path.join(HERE, "s2_endcard.py"), raw, mp4, "%.2f" % T(35.5),
                    "あなたは、どっち派？", "🍪", "あげる派", "🎁", "もらう派", "次はどの心理学がいい？コメントで教えて"], check=True)
    shutil.rmtree(tmp)
    print("wrote", mp4)

if __name__ == "__main__":
    main()
