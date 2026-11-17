"""
make_reel_s2e1.py ― 『君は写真に写らない』第1話「写らない」のリール書き出し
  3Dカット（frames_S2E1/A,C,D）＋スマホ画面UI（ASS描画）＋声＋環境音 → isekai は使わない新シリーズ
  python make_reel_s2e1.py → kimi_utsuranai_ep1.mp4
"""
import os, re, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
FR = os.environ.get("S2E1_FR", os.path.join(HERE, "frames_S2E1"))
PRE = 2.2                                      # 冒頭フック（写真の静止画＋問い）
# 本編の区切り（秒、本編の頭=0）
A_PLAY, SHUT, GAL, EMPTY, BLACK, LOCK, CHAT, END = 3.0, 11.5, 12.0, 16.2, 19.4, 20.2, 23.4, 33.0
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
    (T(0.25), T(1.6), "…きれいだな", "きれいだな", "soft", "hiyori"),
    (T(2.75), T(4.2), "…その写真、撮るんだ", "そのしゃしん、とるんだ", "soft", "minato"),
    (T(4.4), T(5.9), "あっ、ごめん…！", "あっ、ごめん！", "soft", "hiyori"),
    (T(6.2), T(7.4), "いいよ、撮っても", "いいよ、とっても", "soft", "minato"),
    (T(7.3), T(9.2), "君の写真、好きだから", "きみのしゃしん、すきだから", "soft", "minato"),
    (T(9.5), T(11.2), "じゃあ…撮るね", "じゃあ、とるね", "soft", "hiyori"),
    (T(12.6), T(13.9), "…うそでしょ、なんで", "うそでしょ、なんで", "soft", "hiyori"),
    (T(14.0), T(15.8), "写って…ない…？", "うつって、ない？", "soft", "hiyori"),
    (T(16.7), T(18.6), "朝倉くん…どこ？", "あさくらくん、どこ？", "soft", "hiyori"),
    (T(27.5), T(30.2), "僕が写ってないの、\\N見たでしょ", "ぼくがうつってないの、みたでしょ", "soft", "minato"),
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
    A = os.path.join(FR, "A", "%04d.png"); Alast = os.path.join(FR, "A", "0072.png")
    C = os.path.join(FR, "C", "0001.png"); D = os.path.join(FR, "D", "0001.png")
    segs = [
        seg_cmd(C, PRE, "", still=True, zoom0=1.0, zoom1=1.18, cx=0.15, cy=0.48, shake=2),        # cold open: 窓の映り込みへ寄る
        seg_cmd(A, A_PLAY, "", zoom0=1.0, zoom1=1.03, shake=4),                                    # 湊が振り向く
        seg_cmd(Alast, SHUT - A_PLAY, "", still=True, zoom0=1.03, zoom1=1.22, cx=0.5, cy=0.42, shake=4),
        seg_cmd(Alast, GAL - SHUT, "", still=True, zoom0=1.22, zoom1=1.22, cx=0.5, cy=0.42, shake=1),
        seg_cmd(C, EMPTY - GAL, "", still=True, zoom0=1.0, zoom1=1.25, cx=0.12, cy=0.5, shake=1.5),  # 撮った写真：映り込みへ
        seg_cmd(D, BLACK - EMPTY, "", still=True, zoom0=1.02, zoom1=1.1, shake=6),                 # 顔を上げる：誰もいない
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
                      r"もしも好きな人に\N「その写真、消さないで」\Nと言われたら？", 8)
    # --- camera app (本編 0 → SHUT)
    c0, c1 = T(0), T(GAL)
    S(c0, c1, rr(-10, -10, 730, 96, 0), "&H000000&", "&H50&")
    S(c0, c1, rr(-10, 1050, 730, 1300, 0), "&H000000&", "&H40&")
    E(c0, c1, "ui", r"{\an5\pos(360,48)\fs26\c&HFFFFFF&}⚡  ◯  1x")
    E(c0, c1, "ui", r"{\an5\pos(360,1086)\fs26\c&HAAAAAA&}ビデオ    {\c&H00D7FF&}写真{\c&HAAAAAA&}    ポートレート")
    S(c0, c1, circ(360, 1182, 52), "&HFFFFFF&")
    S(c0, c1, circ(360, 1182, 44), "&H000000&", "&H00&", 5)
    S(c0, T(SHUT), circ(360, 1182, 40), "&HFFFFFF&", "&H00&", 6)
    S(T(SHUT), T(SHUT + 0.25), circ(360, 1182, 40), "&HFFFFFF&", "&H00&", 6, r"\t(0,120,\fscx80\fscy80)\t(120,250,\fscx100\fscy100)")
    S(c0, c1, rr(588, 1158, 636, 1206, 10), "&H404040&")                     # last-photo thumbnail
    # focus square (yellow corners) on Minato
    fx, fy, fw = 365, 520, 70
    for t0, t1 in ((T(0.6), T(1.6)), (T(2.6), T(3.4)), (T(8.8), T(SHUT))):
        for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            x, y = fx + sx * fw, fy + sy * fw
            S(t0, t1, "m %d %d l %d %d l %d %d l %d %d l %d %d l %d %d" % (x, y, x - sx * 24, y, x - sx * 24, y - sy * 4 + sy * 0,
                                                                        x - sx * 24, y + sy * 4 * 0 - sy * 4, x, y - sy * 4, x, y)
              if False else rr(min(x, x - sx * 26), min(y, y - sy * 4), max(x, x - sx * 26), max(y, y - sy * 4), 1), "&H00D7FF&", layer=6)
            S(t0, t1, rr(min(x, x - sx * 4), min(y, y - sy * 26), max(x, x - sx * 4), max(y, y - sy * 26), 1), "&H00D7FF&", layer=6)
    # shutter flash
    S(T(SHUT), T(SHUT + 0.45), rr(-10, -10, 730, 1290, 0), "&HFFFFFF&", "&H00&", 9, r"\fad(0,380)")
    # --- gallery (撮った写真)
    g0, g1 = T(GAL), T(EMPTY)
    S(g0, g1, rr(-10, -10, 730, 110, 0), "&H000000&", "&H30&")
    S(g0, g1, rr(-10, 1110, 730, 1300, 0), "&H000000&", "&H30&")
    E(g0, g1, "ui", r"{\an4\pos(28,62)\fs34}‹")
    E(g0, g1, "ui", r"{\an5\pos(360,48)\fs26}今日{\N}{\fs22\c&HBBBBBB&}16:42")
    E(g0, g1, "ui", r"{\an5\pos(360,1190)\fs34\c&HDDDDDD&}⇪      ♡      ⓘ      🗑")
    # 「気づいた？」― 窓への映り込みに赤丸
    S(T(14.6), g1, circ(96, 640, 92), "&H3030FF&", "&HFF&", 7, r"\bord6\3c&H3030FF&\3a&H00&\t(0,200,\fscx100\fscy100)")
    E(T(14.6), g1, "ui", r"{\an7\pos(14,500)\fs40\c&H3030FF&\bord3\3c&H000000&\fad(150,0)}…窓に？", 8)
    # --- lock screen at night
    l0, l1 = T(LOCK), T(CHAT)
    E(l0, T(21.6), "big", r"{\an5\pos(360,330)}23:59")
    E(T(21.6), l1, "big", r"{\an5\pos(360,330)}0:00")
    E(l0, l1, "ui", r"{\an5\pos(360,200)\fs30\c&HCCCCCC&}11月17日 月曜日")
    S(T(22.0), l1, rr(28, 470, 692, 610, 30), "&H3A3A3A&", "&H30&", 6, r"\fad(120,0)")
    S(T(22.0), l1, rr(52, 498, 108, 554, 14), "&HD08A3C&", "&H00&", 7, r"\fad(120,0)")
    E(T(22.0), l1, "ui", r"{\an7\pos(126,494)\fs26\c&HDDDDDD&\fad(120,0)}トーク  ·  今")
    E(T(22.0), l1, "ui", r"{\an7\pos(126,530)\fs30\fad(120,0)}{\b1}朝倉 湊{\b0}  さっきの写真")
    # --- chat
    h0, h1 = T(CHAT), T(END)
    S(h0, h1, rr(-10, -10, 730, 150, 0), "&H261F1C&")
    E(h0, h1, "ui", r"{\an4\pos(26,98)\fs40}‹")
    S(h0, h1, circ(100, 98, 28), "&H55504C&")
    E(h0, h1, "ui", r"{\an4\pos(142,98)\fs32}{\b1}朝倉 湊{\b0}")
    E(h0, h1, "ui", r"{\an5\pos(360,40)\fs24\c&HCCCCCC&}0:00")
    msgs = [(23.9, "さっきの写真"), (25.4, "消さないでね"), (28.0, "僕が写ってないの、見たでしょ")]
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
    E(h0, h1, "ui", r"{\an4\pos(104,1222)\fs26\c&H888888&}メッセージを入力")
    # 終わり：コメント誘導と「つづく」
    E(T(30.6), T(END), "hook", r"{\an5\pos(360,860)\fs46\fad(200,0)}あなたなら、写真を消す？\Nコメントで教えて！", 8)
    E(T(31.6), T(END), "ui", r"{\an5\pos(360,1020)\fs34\fad(200,0)\c&HDDDDDD&}▶ 第2話「花瓶の席」", 8)
    # spoken lines
    for st, en, text, _, _, who in R.LINES:
        E(st, en, "subm" if who == "minato" else "sub", r"{\an5\pos(360,%d)\fad(60,120)}%s" % (880 if en > T(CHAT) else 820, text), 7)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

# ---------------------------------------------------------------- sound
def tick():
    return 0.6 * R.hp(R.noise(0.02), 3000) * R.dec(0.02, 0.003)
def build_sfx():
    n = R.n_(T(BLACK) - 0.0)
    # 放課後の教室：遠くの部活の声、カラス、空調のような低いノイズ
    add(R.fade(R.lp(R.noise(T(BLACK)), 300) * 0.25, 0.3, 0.6), 0, 0.5)
    add(R.fade(R.crowd(T(BLACK) - 0.5, 300, 1400, 1.2), 0.5, 0.8), 0.3, 0.06, -0.4)
    for t0 in (T(1.2), T(8.0)):                                   # 遠くのカラス
        caw = R.bp(R.saw(620, 0.28) * R.dec(0.28, 0.12), 500, 1800)
        add(caw, t0, 0.08, -0.6); add(caw, t0 + 0.42, 0.06, -0.6)
    # 本編へ入る瞬間：冒頭の問いの下の低い持続音を切る
    add(R.fade(R.pad([55, 82.4, 110], PRE, 400, 0.2, 0.2), 0.2, 0.15), 0, 0.35)
    # シャッター
    sh = np.concatenate([0.9 * R.hp(R.noise(0.012), 2000), np.zeros(R.n_(0.05)), 0.7 * R.hp(R.noise(0.03), 1200) * R.dec(0.03, 0.01)])
    add(sh, T(SHUT), 0.7)
    # 写真を見た瞬間から：心臓の音と、耳鳴りのような高音
    hb = R.heartbeat()
    t0 = T(13.0)
    while t0 < T(BLACK):
        add(hb, t0, 0.5); t0 += 0.9
    add(R.fade(np.sin(2 * np.pi * 4200 * R.tt(T(BLACK) - T(13.6))) * 0.02, 1.5, 0.2), T(13.6), 1.0)
    add(R.fade(R.pad([46.2, 69.3, 92.5], T(BLACK) - T(12.6), 300, 1.5, 0.3), 0.5, 0.3), T(12.6), 0.45)
    # 誰もいない窓辺：風の音
    add(R.fade(R.bp(R.noise(T(BLACK) - T(EMPTY)), 300, 1200) * 0.4, 0.4, 0.4), T(EMPTY), 0.3, 0.5)
    # 夜：時計の秒針 → 0:00 の通知音
    t0 = T(BLACK) + 0.2
    while t0 < T(CHAT + 4.3):
        add(tick(), t0, 0.5, 0.2); t0 += 1.0
    for t0, k in ((22.0, 0), (23.9, 1), (25.4, 1), (28.0, 1)):
        add(R.chime([1318.5, 1760.0] if k == 0 else [1568.0], 0.09, 0.6), T(t0), 0.28 if k else 0.35)
    add(R.fade(R.pad([41.2, 61.7, 82.4], T(END) - T(26.6), 260, 1.0, 0.5), 0.8, 0.5), T(26.6), 0.6)
    add(R.boom(1.6), T(28.0), 0.5)

def main():
    tmp = tempfile.mkdtemp(prefix="s2e1_")
    base = build_picture(tmp)
    build_sfx(); R.build_voice()
    out = R.MIX[: R.n_(DUR)].copy()
    out[-R.n_(0.5):] *= np.linspace(1, 0, R.n_(0.5))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "s2e1_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "s2e1_ui.ass"); build_ui(ass)
    mp4 = os.path.join(HERE, "kimi_utsuranai_ep1.mp4")
    grade = "eq=contrast=1.04:saturation=0.92,vignette=PI/5,noise=alls=7:allf=t,ass=s2e1_ui.ass"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", base, "-i", wav, "-vf", grade, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "20", "-maxrate", "6M", "-bufsize", "12M", "-preset", "slow", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
                    "-movflags", "+faststart", "-shortest", mp4], check=True, cwd=HERE)
    shutil.rmtree(tmp)
    print("wrote", mp4, DUR)

if __name__ == "__main__":
    main()
