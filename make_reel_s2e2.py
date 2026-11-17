"""
make_reel_s2e2.py ― 『君は写真に写らない』第2話「花瓶の席」のリール書き出し
  3Dカット（frames_S2E2/A,B,V）＋スマホ画面UI（ASS描画）＋声＋環境音
  python make_reel_s2e2.py → kimi_utsuranai_ep2.mp4
"""
import os, re, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
FR = os.environ.get("S2E2_FR", os.path.join(HERE, "frames_S2E2"))
PRE = 2.2                                      # 冒頭フック（写真の静止画＋問い）
# 本編の区切り（秒、本編の頭=0）
A_PLAY, VASE, CALL, EMPTY, BLACK, LOCK, CHAT, END = 2.5, 7.4, 10.0, 12.6, 19.6, 20.4, 23.6, 33.2
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
    (T(0.3), T(2.2), "…朝倉くん、早いね", "あさくらくん、はやいね", "soft", "hiyori"),
    (T(2.8), T(4.9), "うん。ここ、僕の席だから", "うん。ここ、ぼくのせきだから", "soft", "minato"),
    (T(5.3), T(7.2), "その花…誰が置いたの？", "そのはな、だれがおいたの？", "soft", "hiyori"),
    (T(7.8), T(9.6), "…きれいでしょ、白い花", "きれいでしょ、しろいはな", "soft", "minato"),
    (T(10.0), T(12.4), "ひより！\\Nさっきから誰と話してんの？", "ひより！さっきから、だれとはなしてんの？", "normal", "rin"),
    (T(12.9), T(15.0), "え…朝倉くんが、そこに…", "え、あさくらくんが、そこに", "soft", "hiyori"),
    (T(15.3), T(16.8), "そこ、誰もいないよ", "そこ、だれもいないよ", "normal", "rin"),
    (T(17.0), T(19.6), "その席、去年から\\Nずっと空いてるよ", "そのせき、きょねんからずっと、あいてるよ", "normal", "rin"),
    (T(27.8), T(30.0), "僕のこと…怖くなった？", "ぼくのこと、こわくなった？", "soft", "minato"),
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
    A = os.path.join(FR, "A", "%04d.png"); Alast = os.path.join(FR, "A", "0060.png")
    B = os.path.join(FR, "B", "0001.png"); V = os.path.join(FR, "V", "0001.png")
    segs = [
        seg_cmd(V, PRE, "", still=True, zoom0=1.0, zoom1=1.15, cx=0.5, cy=0.55, shake=2),         # cold open: 白い花瓶
        seg_cmd(A, A_PLAY, "", zoom0=1.0, zoom1=1.02, shake=5),                                    # 教室に入る：窓際に湊
        seg_cmd(Alast, VASE - A_PLAY, "", still=True, zoom0=1.02, zoom1=1.16, cx=0.35, cy=0.45, shake=4),
        seg_cmd(V, CALL - VASE, "", still=True, zoom0=1.0, zoom1=1.08, cx=0.5, cy=0.5, shake=2),    # 花瓶のアップ
        seg_cmd(Alast, EMPTY - CALL, "", still=True, zoom0=1.16, zoom1=1.16, cx=0.35, cy=0.45, shake=9),   # 凛に呼ばれて揺れる
        seg_cmd(B, BLACK - EMPTY, "", still=True, zoom0=1.16, zoom1=1.45, cx=0.35, cy=0.45, shake=3),      # 誰もいない
    ]
    outs = []
    for k, c in enumerate(segs):
        p = os.path.join(tmp, "s%02d.mp4" % k); c[-1] = p; subprocess.run(c, check=True); outs.append(p)
    p = os.path.join(tmp, "s%02d.mp4" % len(segs)); subprocess.run(black(END - BLACK, p), check=True); outs.append(p)
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
    # --- cold open: the question
    E(0, PRE, "hook", r"{\an5\pos(360,420)\fscx70\fscy70\t(0,120,\fscx104\fscy104)\t(120,200,\fscx100\fscy100)}"
                      r"もしも\N「あなたにしか見えない彼」\Nがいたら？", 8)
    # 時刻と場所（リアルさ：朝の教室）
    E(T(0), T(2.4), "ui", r"{\an7\pos(30,60)\fs30\bord2\3c&H000000&\fad(200,300)}7:52  2年B組", 8)
    # 誰もいないと分かった後：花瓶に赤丸ではなく、ピントを合わせ直すように黒枠
    # --- lock screen at night
    l0, l1 = T(LOCK), T(CHAT)
    E(l0, T(21.8), "big", r"{\an5\pos(360,330)}23:59")
    E(T(21.8), l1, "big", r"{\an5\pos(360,330)}0:00")
    E(l0, l1, "ui", r"{\an5\pos(360,200)\fs30\c&HCCCCCC&}11月18日 火曜日")
    S(T(22.2), l1, rr(28, 470, 692, 610, 30), "&H3A3A3A&", "&H30&", 6, r"\fad(120,0)")
    S(T(22.2), l1, rr(52, 498, 108, 554, 14), "&HD08A3C&", "&H00&", 7, r"\fad(120,0)")
    E(T(22.2), l1, "ui", r"{\an7\pos(126,494)\fs26\c&HDDDDDD&\fad(120,0)}トーク  ·  今")
    E(T(22.2), l1, "ui", r"{\an7\pos(126,530)\fs30\fad(120,0)}{\b1}朝倉 湊{\b0}  今日は、ごめんね")
    # --- chat
    h0, h1 = T(CHAT), T(END)
    S(h0, h1, rr(-10, -10, 730, 150, 0), "&H261F1C&")
    E(h0, h1, "ui", r"{\an4\pos(26,98)\fs40}‹")
    S(h0, h1, circ(100, 98, 28), "&H55504C&")
    E(h0, h1, "ui", r"{\an4\pos(142,98)\fs32}{\b1}朝倉 湊{\b0}")
    E(h0, h1, "ui", r"{\an5\pos(360,40)\fs24\c&HCCCCCC&}0:00")
    msgs = [(24.1, "今日は、ごめんね"), (25.4, "みんなには、僕が見えないんだ"), (28.0, "僕のこと、怖くなった？")]
    y = 230
    for t0, txt in msgs:
        w = 44 + int(len(txt) * 39)
        S(T(t0), h1, rr(84, y, 84 + w, y + 84, 34), "&H3A332E&", "&H00&", 5, r"\fad(80,0)")
        S(T(t0), h1, circ(46, y + 30, 22), "&H55504C&", "&H00&", 5, r"\fad(80,0)")
        E(T(t0), h1, "ui", r"{\an4\pos(106,%d)\fs38\fad(80,0)}%s" % (y + 42, txt), 6)
        tx, an = (94 + w, 1) if 94 + w < 650 else (84 + w, 9)       # はみ出す時は吹き出しの下に
        E(T(t0), h1, "ui", r"{\an%d\pos(%d,%d)\fs22\c&H999999&\fad(80,0)}0:00" % (an, tx, y + 84 + (0 if an == 1 else 6)), 6)
        y += 112
    # typing dots before the last message
    S(T(26.6), T(28.0), rr(84, 454, 194, 538, 34), "&H3A332E&", "&H00&", 5)
    E(T(26.6), T(28.0), "ui", r"{\an5\pos(139,496)\fs40\c&HBBBBBB&}{\t(0,400,\alpha&H80&)\t(400,800,\alpha&H00&)}・・・", 6)
    # input bar
    S(h0, h1, rr(-10, 1170, 730, 1300, 0), "&H1C1A18&")
    S(h0, h1, rr(80, 1192, 600, 1252, 30), "&H33302C&")
    E(h0, T(29.0), "ui", r"{\an4\pos(104,1222)\fs26\c&H888888&}メッセージを入力")
    # ひよりが返事を打ちかけて、消す
    for k, (t0, t1, txt) in enumerate(((29.0, 29.4, "こ"), (29.4, 29.8, "こわ"), (29.8, 30.4, "こわく"), (30.4, 30.9, "こわくな"),
                                        (30.9, 31.4, "こわく"), (31.4, 31.8, "こ"))):
        E(T(t0), T(t1), "ui", r"{\an4\pos(104,1222)\fs30}%s{\c&HD08A3C&}|" % txt)
    E(T(31.8), h1, "ui", r"{\an4\pos(104,1222)\fs26\c&H888888&}メッセージを入力")
    # 終わり：コメント誘導と「つづく」
    E(T(30.6), T(END), "hook", r"{\an5\pos(360,800)\fs46\fad(200,0)}あなたなら、そばにいる？\Nコメントで教えて！", 8)
    E(T(31.6), T(END), "ui", r"{\an5\pos(360,960)\fs34\fad(200,0)\c&HDDDDDD&}▶ 第3話「一年前の今日」", 8)
    # spoken lines
    for st, en, text, _, _, who in R.LINES:
        E(st, en, {"minato": "subm", "rin": "subr"}.get(who, "sub"), r"{\an5\pos(360,%d)\fad(60,120)}%s" % (880 if en > T(CHAT) else 820, text), 7)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

# ---------------------------------------------------------------- sound
def tick():
    return 0.6 * R.hp(R.noise(0.02), 3000) * R.dec(0.02, 0.003)
def build_sfx():
    # 朝の教室：ざわめき、遠くのチャイム、窓の外のスズメ
    add(R.fade(R.lp(R.noise(T(BLACK)), 300) * 0.25, 0.3, 0.6), 0, 0.45)
    add(R.fade(R.crowd(T(EMPTY) - 0.2, 300, 1600, 1.4), 0.4, 0.3), 0.2, 0.09, 0.3)
    for k in range(6):                                            # スズメ
        t0 = T(0.6 + k * 1.3)
        add(R.bp(R.saw(3800 + 300 * (k % 3), 0.05) * R.dec(0.05, 0.02), 2500, 6000), t0, 0.05, -0.7)
        add(R.bp(R.saw(4100, 0.04) * R.dec(0.04, 0.015), 2500, 6000), t0 + 0.09, 0.04, -0.7)
    add(R.fade(R.pad([55, 82.4, 110], PRE, 400, 0.2, 0.2), 0.2, 0.15), 0, 0.35)
    # 凛に呼ばれた瞬間：ざわめきが止まる → 低い持続音と心臓
    add(R.boom(1.0), T(CALL), 0.35)
    add(R.fade(R.pad([46.2, 69.3, 92.5], T(BLACK) - T(EMPTY), 300, 1.0, 0.3), 0.5, 0.3), T(EMPTY), 0.45)
    hb = R.heartbeat(); t0 = T(EMPTY + 0.3)
    while t0 < T(BLACK):
        add(hb, t0, 0.5); t0 += 0.85
    add(R.fade(np.sin(2 * np.pi * 4200 * R.tt(T(BLACK) - T(EMPTY))) * 0.02, 1.5, 0.2), T(EMPTY), 1.0)
    # 夜：時計の秒針 → 0:00 の通知音
    t0 = T(BLACK) + 0.2
    while t0 < T(CHAT + 4.3):
        add(tick(), t0, 0.5, 0.2); t0 += 1.0
    for t0, k in ((22.2, 0), (24.1, 1), (25.4, 1), (28.0, 1)):
        add(R.chime([1318.5, 1760.0] if k == 0 else [1568.0], 0.09, 0.6), T(t0), 0.28 if k else 0.35)
    for t0 in (29.0, 29.4, 29.8, 30.4, 30.9, 31.4):              # 打っては消すキー音
        add(tick() * 0.6, T(t0), 0.35, -0.1)
    add(R.fade(R.pad([41.2, 61.7, 82.4], T(END) - T(26.6), 260, 1.0, 0.5), 0.8, 0.5), T(26.6), 0.6)
    add(R.boom(1.6), T(28.0), 0.5)

def main():
    tmp = tempfile.mkdtemp(prefix="s2e2_")
    base = build_picture(tmp)
    build_sfx(); R.build_voice()
    out = R.MIX[: R.n_(DUR)].copy()
    out[-R.n_(0.5):] *= np.linspace(1, 0, R.n_(0.5))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "s2e2_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "s2e2_ui.ass"); build_ui(ass)
    mp4 = os.path.join(HERE, "kimi_utsuranai_ep2.mp4")
    grade = "eq=contrast=1.04:saturation=0.92,vignette=PI/5,noise=alls=7:allf=t,ass=s2e2_ui.ass"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", base, "-i", wav, "-vf", grade, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "20", "-maxrate", "6M", "-bufsize", "12M", "-preset", "slow", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
                    "-movflags", "+faststart", "-shortest", mp4], check=True, cwd=HERE)
    shutil.rmtree(tmp)
    print("wrote", mp4, DUR)

if __name__ == "__main__":
    main()
