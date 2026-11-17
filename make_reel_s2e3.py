"""
make_reel_s2e3.py ― 『君は写真に写らない』第3話「一年前の今日」のリール書き出し
  3Dカット（frames_S2E3/S,E）＋スマホ画面UI（ASS描画、ニュース記事カードに写真を重ねる）＋声＋環境音
  python make_reel_s2e3.py → kimi_utsuranai_ep3.mp4
"""
import os, re, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
FR = os.environ.get("S2E3_FR", os.path.join(HERE, "frames_S2E3"))
PRE = 2.2                                      # 冒頭フック（写真の静止画＋問い）
# 本編の区切り（秒、本編の頭=0）
S_PLAY, EMPTY, BLACK, LOCK, CHAT, CARD, END = 2.0, 12.4, 15.0, 15.6, 18.4, 21.4, 33.2
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
    (T(0.2), T(2.6), "朝倉くん…やっぱりここにいた", "あさくらくん、やっぱりここにいた", "soft", "hiyori"),
    (T(2.7), T(5.1), "ここ、夕日がきれいに見えるんだ", "ここ、ゆうひがきれいにみえるんだ", "soft", "minato"),
    (T(5.2), T(7.5), "凛がね、朝倉くんのこと…", "りんがね、あさくらくんのこと", "soft", "hiyori"),
    (T(7.6), T(10.2), "凛ちゃんに話したら…\\N僕は、消える", "りんちゃんにはなしたら、ぼくは、きえる", "soft", "minato"),
    (T(10.3), T(12.0), "どうして、言っちゃだめなの？", "どうして、いっちゃだめなの？", "soft", "hiyori"),
    (T(12.1), T(13.6), "…お願いだから", "おねがいだから", "soft", "minato"),
    (T(24.6), T(26.6), "この人…去年、死んでる", "このひと、きょねん、しんでる", "normal", "rin"),
    (T(27.4), T(29.8), "言わないでって…\\N言ったのに", "いわないでって、いったのに", "soft", "minato"),
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
    S = os.path.join(FR, "S", "%04d.png"); Slast = os.path.join(FR, "S", "0048.png")
    E_ = os.path.join(FR, "E", "0001.png")
    segs = [
        seg_cmd(Slast, PRE, "", still=True, zoom0=1.1, zoom1=1.3, cx=0.55, cy=0.45, shake=2),       # cold open: 踊り場の湊
        seg_cmd(S, S_PLAY, "", zoom0=1.0, zoom1=1.02, shake=4),                                    # 階段を上る
        seg_cmd(Slast, EMPTY - S_PLAY, "", still=True, zoom0=1.02, zoom1=1.2, cx=0.55, cy=0.45, shake=3),
        seg_cmd(E_, BLACK - EMPTY, "", still=True, zoom0=1.2, zoom1=1.28, cx=0.55, cy=0.45, shake=7),   # 瞬きすると、いない
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
                      r"もしも好きな人に\N「親友に話したら、\N僕は消える」\Nと言われたら？", 8)
    # 冒頭0.6秒後：結末の通知をチラ見せ（常識外れ＝相手がこちらの画面を読んでいる）
    S(0.6, PRE, rr(20, 900, 700, 1026, 28), "&H2A2A2A&", "&H10&", 9, r"\fad(120,0)")
    S(0.6, PRE, rr(42, 924, 98, 980, 14), "&HD08A3C&", "&H00&", 9, r"\fad(120,0)")
    E(0.6, PRE, "ui", r"{\an7\pos(114,920)\fs24\c&HCCCCCC&\fad(120,0)}トーク  ·  0:00", 9)
    E(0.6, PRE, "ui", r"{\an7\pos(114,952)\fs30\fad(120,0)}{\b1}朝倉 湊{\b0}  言わないでって、言ったのに", 9)
    E(T(0), T(2.4), "ui", r"{\an7\pos(30,60)\fs30\bord2\3c&H000000&\fad(200,300)}16:51  旧校舎 3階", 8)
    # --- lock screen at night
    l0, l1 = T(LOCK), T(CHAT)
    E(l0, T(16.6), "big", r"{\an5\pos(360,330)}23:59")
    E(T(16.6), l1, "big", r"{\an5\pos(360,330)}0:00")
    E(l0, l1, "ui", r"{\an5\pos(360,200)\fs30\c&HCCCCCC&}11月19日 水曜日")
    S(T(17.0), l1, rr(28, 470, 692, 610, 30), "&H3A3A3A&", "&H30&", 6, r"\fad(120,0)")
    S(T(17.0), l1, rr(52, 498, 108, 554, 14), "&HD08A3C&", "&H00&", 7, r"\fad(120,0)")
    E(T(17.0), l1, "ui", r"{\an7\pos(126,494)\fs26\c&HDDDDDD&\fad(120,0)}トーク  ·  今")
    E(T(17.0), l1, "ui", r"{\an7\pos(126,530)\fs30\fad(120,0)}{\b1}白石 凛{\b0}  ひより、起きてる？")
    # --- chat
    h0, h1 = T(CHAT), T(END)
    S(h0, h1, rr(-10, -10, 730, 150, 0), "&H261F1C&")
    E(h0, h1, "ui", r"{\an4\pos(26,98)\fs40}‹")
    S(h0, h1, circ(100, 98, 28), "&H4A6A9A&")
    E(h0, h1, "ui", r"{\an4\pos(142,98)\fs32}{\b1}白石 凛{\b0}")
    E(h0, h1, "ui", r"{\an5\pos(360,40)\fs24\c&HCCCCCC&}0:00")
    msgs = [(18.8, "ひより、起きてる？", 230), (20.0, "朝倉 湊って名前、調べてみた", 342), (24.6, "この人、去年死んでる", 824)]
    for t0, txt, y in msgs:
        w = 44 + int(len(txt) * 39)
        S(T(t0), h1, rr(84, y, 84 + w, y + 84, 34), "&H3A332E&", "&H00&", 5, r"\fad(80,0)")
        S(T(t0), h1, circ(46, y + 30, 22), "&H4A6A9A&", "&H00&", 5, r"\fad(80,0)")
        E(T(t0), h1, "ui", r"{\an4\pos(106,%d)\fs38\fad(80,0)}%s" % (y + 42, txt), 6)
        tx, an = (94 + w, 1) if 94 + w < 650 else (84 + w, 9)
        E(T(t0), h1, "ui", r"{\an%d\pos(%d,%d)\fs22\c&H999999&\fad(80,0)}0:00" % (an, tx, y + 84 + (0 if an == 1 else 6)), 6)
    # ニュース記事のカード（写真は ffmpeg で重ねる: x=96..652, y=466..686）
    c0 = T(CARD)
    S(c0, h1, rr(84, 454, 664, 796, 26), "&H3A332E&", "&H00&", 5, r"\fad(80,0)")
    S(c0, h1, circ(46, 484, 22), "&H4A6A9A&", "&H00&", 5, r"\fad(80,0)")
    E(c0, h1, "ui", r"{\an7\pos(104,700)\fs27\fad(80,0)}{\b1}旧校舎の階段で転落\N高校2年の男子生徒が死亡{\b0}", 6)
    E(c0, h1, "ui", r"{\an7\pos(104,766)\fs20\c&HAAAAAA&\fad(80,0)}2025年11月19日 ・ 地域ニュース", 6)
    # typing dots before the last message
    S(T(23.4), T(24.6), rr(84, 824, 194, 908, 34), "&H3A332E&", "&H00&", 5)
    E(T(23.4), T(24.6), "ui", r"{\an5\pos(139,866)\fs40\c&HBBBBBB&}{\t(0,400,\alpha&H80&)\t(400,800,\alpha&H00&)}・・・", 6)
    # 0:00 ― 上から湊の通知（読まれている）
    S(T(27.0), h1, rr(20, 24, 700, 150, 28), "&H2A2A2A&", "&H10&", 9, r"\move(0,-160,0,0,0,180)")
    S(T(27.0), h1, rr(42, 48, 98, 104, 14), "&HD08A3C&", "&H00&", 9, r"\move(0,-160,0,0,0,180)")
    E(T(27.0), h1, "ui", r"{\an7\move(114,-114,114,44,0,180)\fs24\c&HCCCCCC&}トーク  ·  今", 9)
    E(T(27.0), h1, "ui", r"{\an7\move(114,-84,114,76,0,180)\fs30}{\b1}朝倉 湊{\b0}  言わないでって、言ったのに", 9)
    # input bar
    S(h0, h1, rr(-10, 1170, 730, 1300, 0), "&H1C1A18&")
    S(h0, h1, rr(80, 1192, 600, 1252, 30), "&H33302C&")
    E(h0, h1, "ui", r"{\an4\pos(104,1222)\fs26\c&H888888&}メッセージを入力")
    # 終わり：コメント誘導と「つづく」
    E(T(30.6), T(END), "hook", r"{\an5\pos(360,1010)\fs46\fad(200,0)}あなたなら、親友に話す？\N（話せば、彼は消える）\Nコメントで教えて！", 8)
    E(T(31.6), T(END), "ui", r"{\an5\pos(360,1170)\fs34\fad(200,0)\c&HDDDDDD&}▶ 第4話「未読」", 8)
    # spoken lines
    for st, en, text, _, _, who in R.LINES:
        E(st, en, {"minato": "subm", "rin": "subr"}.get(who, "sub"), r"{\an5\pos(360,%d)\fad(60,120)}%s" % (1020 if en > T(CHAT) else 820, text), 7)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

# ---------------------------------------------------------------- sound
def tick():
    return 0.6 * R.hp(R.noise(0.02), 3000) * R.dec(0.02, 0.003)
def build_sfx():
    # 夕方の旧校舎：遠くの吹奏楽部、カラス、古い建物のきしみ
    add(R.fade(R.lp(R.noise(T(BLACK)), 260) * 0.25, 0.3, 0.6), 0, 0.5)
    add(R.fade(R.pad([392.0, 493.9, 587.3], T(EMPTY), 1200, 1.0, 1.0), 0.8, 0.6), 0.3, 0.035, 0.6)   # 遠くの合奏
    for t0 in (T(1.0), T(6.5)):
        caw = R.bp(R.saw(600, 0.3) * R.dec(0.3, 0.12), 500, 1800)
        add(caw, t0, 0.07, -0.6); add(caw, t0 + 0.45, 0.05, -0.6)
    for k in range(4):                                            # 階段を上る足音
        add(R.lp(R.noise(0.06), 900) * R.dec(0.06, 0.02), T(0.1 + k * 0.5), 0.35, 0.1 * (-1) ** k)
    add(R.fade(R.pad([55, 82.4, 110], PRE, 400, 0.2, 0.2), 0.2, 0.15), 0, 0.35)
    add(R.fade(R.pad([46.2, 69.3, 92.5], T(EMPTY) - T(7.0), 300, 2.0, 0.3), 0.5, 0.3), T(7.0), 0.35)
    # 消える：無音→耳鳴り→心臓
    add(R.boom(1.2), T(EMPTY), 0.4)
    hb = R.heartbeat(); t0 = T(EMPTY + 0.3)
    while t0 < T(BLACK):
        add(hb, t0, 0.5); t0 += 0.85
    add(R.fade(np.sin(2 * np.pi * 4200 * R.tt(T(BLACK) - T(EMPTY))) * 0.02, 0.6, 0.2), T(EMPTY), 1.0)
    # 夜
    t0 = T(BLACK) + 0.2
    while t0 < T(CHAT + 3.0):
        add(tick(), t0, 0.5, 0.2); t0 += 1.0
    for t0, k in ((17.0, 0), (18.8, 1), (20.0, 1), (21.4, 1), (24.6, 1)):
        add(R.chime([1318.5, 1760.0] if k == 0 else [1568.0], 0.09, 0.6), T(t0), 0.28 if k else 0.35)
    add(R.fade(R.pad([41.2, 61.7, 82.4], T(END) - T(23.4), 260, 1.0, 0.5), 0.8, 0.5), T(23.4), 0.6)
    add(R.boom(1.6), T(24.6), 0.45)
    add(R.chime([1318.5, 1760.0], 0.09, 0.6), T(27.0), 0.4)        # 湊からの通知
    add(R.boom(1.8), T(27.0), 0.6)

def main():
    tmp = tempfile.mkdtemp(prefix="s2e3_")
    base = build_picture(tmp)
    build_sfx(); R.build_voice()
    out = R.MIX[: R.n_(DUR)].copy()
    out[-R.n_(0.5):] *= np.linspace(1, 0, R.n_(0.5))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "s2e3_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "s2e3_ui.ass"); build_ui(ass)
    mp4 = os.path.join(HERE, "kimi_utsuranai_ep3.mp4")
    photo = os.path.join(tmp, "photo.png")                       # 記事の写真：誰もいない階段（報道写真らしく少し色を抜く）
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(FR, "E", "0001.png"), "-vf",
                    "crop=720:284:0:420,scale=556:220,eq=saturation=0.55:contrast=1.05,unsharp=5:5:0.4", photo], check=True)
    fc = ("[0]eq=contrast=1.04:saturation=0.92,vignette=PI/5,noise=alls=7:allf=t,ass=s2e3_ui.ass[v];"
          "[2]format=rgba,fade=t=in:st=0:d=0.08:alpha=1[p];"
          "[v][p]overlay=x=96:y=466:enable='between(t,%.2f,%.2f)'[o]" % (T(CARD), T(END) + 1))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", base, "-i", wav, "-loop", "1", "-i", photo, "-filter_complex", fc,
                    "-map", "[o]", "-map", "1:a", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "20", "-maxrate", "6M", "-bufsize", "12M", "-preset", "slow", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
                    "-movflags", "+faststart", "-t", "%.3f" % DUR, mp4], check=True, cwd=HERE)
    shutil.rmtree(tmp)
    print("wrote", mp4, DUR)

if __name__ == "__main__":
    main()
