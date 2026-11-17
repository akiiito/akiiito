"""
make_reel_s2e4.py ― 『君は写真に写らない』第4話「未読」のリール書き出し
  3Dカット（frames_S2E4/N,P ＋ 第2話の B）＋スマホ画面UI＋床に落ちた凛のスマホへ貼るUI（s2_phoneui.py）＋声＋環境音
  python make_reel_s2e4.py → kimi_utsuranai_ep4.mp4
"""
import os, re, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
FR = os.environ.get("S2E4_FR", os.path.join(HERE, "frames_S2E4"))
FR2 = os.environ.get("S2E2_FR", os.path.join(HERE, "frames_S2E2"))
PRE = 2.2                                      # 冒頭フック（写真の静止画＋問い）
# 本編の区切り（秒、本編の頭=0）
CHAT1, SEAT, LOCK, BLACK2, NPLAY, NSTILL, PHONE, END = 0.0, 7.6, 11.6, 16.8, 18.6, 20.6, 24.4, 33.2
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
    (T(5.0), T(7.0), "既読…つかない", "きどく、つかない", "soft", "hiyori"),
    (T(8.4), T(10.6), "凛…どこにいるの？", "りん、どこにいるの？", "soft", "hiyori"),
    (T(13.6), T(16.6), "凛ちゃんを探すなら…\\N僕とはもう、会えないよ", "りんちゃんをさがすなら、ぼくとはもう、あえないよ", "soft", "minato"),
    (T(17.0), T(18.5), "…それでも、行く", "それでも、いく", "soft", "hiyori"),
    (T(19.6), T(21.6), "凛…？ そこに、いるの…？", "りん、そこに、いるの？", "soft", "hiyori"),
    (T(24.8), T(26.8), "これ…凛のスマホ…", "これ、りんのすまほ", "soft", "hiyori"),
    (T(27.8), T(29.8), "…来ちゃったんだね", "きちゃったんだね", "soft", "minato"),
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

def phone_ui(tmp, name, notes):
    """凛のスマホのロック画面（0:00と通知）を描いて、床のスマホの画面に貼った静止画を返す"""
    ass = os.path.join(tmp, name + ".ass"); png = os.path.join(tmp, name + "_ui.png")
    ev = ["Dialogue: 0,0:00:00.00,0:00:05.00,ui,,0,0,0,,{\\an5\\pos(180,60)\\fs22\\c&HDDDDDD&}11月21日 金曜日",
          "Dialogue: 0,0:00:00.00,0:00:05.00,ui,,0,0,0,,{\\an5\\pos(180,130)\\fs96}0:00"]
    y = 230
    for who, txt in notes:
        ev.append("Dialogue: 0,0:00:00.00,0:00:05.00,shape,,0,0,0,,{\\an7\\pos(0,0)\\p1\\1c&H3A3A3A&\\1a&H20&}%s{\\p0}" % rr(14, y, 346, y + 84, 18))
        ev.append("Dialogue: 1,0:00:00.00,0:00:05.00,ui,,0,0,0,,{\\an7\\pos(30,%d)\\fs17\\c&HCCCCCC&}トーク · 今" % (y + 10))
        ev.append("Dialogue: 1,0:00:00.00,0:00:05.00,ui,,0,0,0,,{\\an7\\pos(30,%d)\\fs22}{\\b1}%s{\\b0}  %s" % (y + 40, who, txt))
        y += 96
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("PlayResX: 720", "PlayResX: 360").replace("PlayResY: 1280", "PlayResY: 740")
    head = head.replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(ass, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=0x1a2238:s=360x740", "-vf",
                    "ass=%s" % ass, "-frames:v", "1", png], check=True)
    out = os.path.join(tmp, name + ".png")
    subprocess.run(["python3", os.path.join(HERE, "s2_phoneui.py"), os.path.join(FR, "P", "0001.png"),
                    os.path.join(FR, "P", "screen_quad.json"), png, out, "0.9"], check=True)
    return out

def build_picture(tmp):
    N = os.path.join(FR, "N", "%04d.png"); Nlast = os.path.join(FR, "N", "0048.png")
    B = os.path.join(FR2, "B", "0001.png")
    base = [("春野 ひより", "おねがい"), ("春野 ひより", "返事して"), ("春野 ひより", "大丈夫？"), ("春野 ひより", "凛、今日休み？")]
    Pa = phone_ui(tmp, "pa", base)
    Pb = phone_ui(tmp, "pb", [("朝倉 湊", "来ちゃったんだね")] + base[:3])
    segs = [
        seg_cmd(Pa, PRE, "", still=True, zoom0=1.15, zoom1=1.3, cx=0.5, cy=0.5, shake=2),          # cold open: 落ちたスマホ
        black(SEAT - CHAT1, ""),                                                                  # トーク画面（UIが全面）
        seg_cmd(B, LOCK - SEAT, "", still=True, zoom0=1.0, zoom1=1.12, cx=0.4, cy=0.45, shake=3),  # 凛のいない教室
        black(NPLAY - LOCK, ""),                                                                  # 0:00 の通知 → 暗転
        seg_cmd(N, NSTILL - NPLAY, "", zoom0=1.0, zoom1=1.02, shake=6),                            # 懐中電灯で階段を上る
        seg_cmd(Nlast, PHONE - NSTILL, "", still=True, zoom0=1.02, zoom1=1.25, cx=0.5, cy=0.4, shake=6),
        seg_cmd(Pa, 27.2 - PHONE, "", still=True, zoom0=1.0, zoom1=1.1, cx=0.5, cy=0.5, shake=3),    # 凛のスマホ
        seg_cmd(Pb, END - 27.2, "", still=True, zoom0=1.1, zoom1=1.22, cx=0.5, cy=0.5, shake=2),     # 湊からの通知が増える
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
    E(0, PRE, "hook", r"{\an5\pos(360,330)\fs46\fscx70\fscy70\t(0,120,\fscx104\fscy104)\t(120,200,\fscx100\fscy100)}"
                      r"もしも\N「親友を探すなら、\N彼とはもう会えない」\Nと言われたら？", 8)
    # --- 昼：凛とのトーク。ひよりの送ったメッセージに既読がつかない
    h0, h1 = T(CHAT1), T(SEAT)
    S(h0, h1, rr(-10, -10, 730, 1300, 0), "&H14100E&", "&H00&", 3)
    S(h0, h1, rr(-10, -10, 730, 150, 0), "&H261F1C&")
    E(h0, h1, "ui", r"{\an4\pos(26,98)\fs40}‹")
    S(h0, h1, circ(100, 98, 28), "&H4A6A9A&")
    E(h0, h1, "ui", r"{\an4\pos(142,98)\fs32}{\b1}白石 凛{\b0}")
    E(h0, h1, "ui", r"{\an5\pos(360,40)\fs24\c&HCCCCCC&}16:03")
    E(h0, h1, "ui", r"{\an5\pos(360,196)\fs22\c&H999999&}11月20日(木)")
    for k, (txt, tm) in enumerate((("旧校舎、行ってくる", "0:12"), ("確かめてくる", "0:12"))):
        y = 236 + k * 104; w = 44 + int(len(txt) * 39)
        S(h0, h1, rr(84, y, 84 + w, y + 84, 34), "&H3A332E&"); S(h0, h1, circ(46, y + 30, 22), "&H4A6A9A&")
        E(h0, h1, "ui", r"{\an4\pos(106,%d)\fs38}%s" % (y + 42, txt), 6)
        E(h0, h1, "ui", r"{\an1\pos(%d,%d)\fs22\c&H999999&}%s" % (94 + w, y + 84, tm), 6)
    sent = [(0.4, "凛、今日休み？", "8:02"), (1.6, "大丈夫？", "10:15"), (2.8, "返事して", "12:40"), (4.0, "おねがい", "15:58")]
    for k, (t0, txt, tm) in enumerate(sent):
        y = 470 + k * 104; w = 44 + int(len(txt) * 39)
        S(T(t0), h1, rr(636 - w, y, 636, y + 84, 34), "&H5BB06A&", "&H00&", 5, r"\fad(80,0)")    # 送信済み（緑）
        E(T(t0), h1, "ui", r"{\an4\pos(%d,%d)\fs38\c&H101010&\fad(80,0)}%s" % (658 - w, y + 42, txt), 6)
        E(T(t0), h1, "ui", r"{\an3\pos(%d,%d)\fs22\c&H999999&\fad(80,0)}%s" % (626 - w, y + 84, tm), 6)   # 既読なし
    S(h0, h1, rr(-10, 1170, 730, 1300, 0), "&H1C1A18&"); S(h0, h1, rr(80, 1192, 600, 1252, 30), "&H33302C&")
    E(h0, h1, "ui", r"{\an4\pos(104,1222)\fs26\c&H888888&}メッセージを入力")
    # --- 0:00：湊からの通知
    l0, l1 = T(LOCK), T(BLACK2)
    S(l0, l1, rr(-10, -10, 730, 1300, 0), "&H140D0B&", "&H00&", 3)
    E(l0, T(12.6), "big", r"{\an5\pos(360,330)}23:59")
    E(T(12.6), l1, "big", r"{\an5\pos(360,330)}0:00")
    E(l0, l1, "ui", r"{\an5\pos(360,200)\fs30\c&HCCCCCC&}11月21日 金曜日")
    S(T(13.0), l1, rr(28, 470, 692, 650, 30), "&H3A3A3A&", "&H30&", 6, r"\fad(120,0)")
    S(T(13.0), l1, rr(52, 498, 108, 554, 14), "&HD08A3C&", "&H00&", 7, r"\fad(120,0)")
    E(T(13.0), l1, "ui", r"{\an7\pos(126,494)\fs26\c&HDDDDDD&\fad(120,0)}トーク  ·  今", 7)
    E(T(13.0), l1, "ui", r"{\an7\pos(126,530)\fs30\fad(120,0)}{\b1}朝倉 湊{\b0}\N凛ちゃんを探すなら、\N僕とはもう会えない", 7)
    # 時刻と場所
    E(T(NPLAY), T(NPLAY + 2.4), "ui", r"{\an7\pos(30,60)\fs30\bord2\3c&H000000&\fad(200,300)}0:41  旧校舎", 8)
    # 終わり
    E(T(30.6), T(END), "hook", r"{\an5\pos(360,1010)\fs46\fad(200,0)}あなたなら、探しに行く？\Nコメントで教えて！", 8)
    E(T(31.6), T(END), "ui", r"{\an5\pos(360,1120)\fs34\fad(200,0)\c&HDDDDDD&\bord2\3c&H000000&}▶ 第5話「一緒に来て」", 8)
    for st, en, text, _, _, who in R.LINES:
        E(st, en, {"minato": "subm", "rin": "subr"}.get(who, "sub"), r"{\an5\pos(360,%d)\fad(60,120)}%s" % (880 if T(LOCK) < st < T(BLACK2) else 1000, text), 7)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

# ---------------------------------------------------------------- sound
def tick():
    return 0.6 * R.hp(R.noise(0.02), 3000) * R.dec(0.02, 0.003)
def buzz(sec=0.5):
    """マナーモードの振動音"""
    t = R.tt(sec); return np.sin(2 * np.pi * 180 * t) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 31 * t))) * R.dec(sec, 0.35)

def build_sfx():
    # 昼：静かな部屋、時計
    add(R.fade(R.lp(R.noise(T(LOCK)), 300) * 0.2, 0.2, 0.4), 0, 0.4)
    add(R.fade(R.pad([55, 82.4, 110], PRE, 400, 0.2, 0.2), 0.2, 0.15), 0, 0.35)
    for t0 in (0.4, 1.6, 2.8, 4.0):                              # 送信音
        add(R.chime([987.8], 0.05, 0.25), T(t0), 0.18, 0.2)
    add(R.fade(R.crowd(LOCK - SEAT, 300, 1500, 1.4), 0.4, 0.4), T(SEAT), 0.06, 0.3)
    add(R.fade(R.pad([46.2, 69.3, 92.5], T(LOCK) - T(5.0), 300, 1.5, 0.3), 0.5, 0.3), T(5.0), 0.35)
    t0 = T(LOCK) + 0.2
    while t0 < T(13.0):
        add(tick(), t0, 0.5, 0.2); t0 += 1.0
    add(R.chime([1318.5, 1760.0], 0.09, 0.6), T(13.0), 0.35); add(R.boom(1.6), T(13.0), 0.45)
    add(R.fade(R.pad([41.2, 61.7, 82.4], T(BLACK2) - T(13.0), 260, 0.8, 0.4), 0.6, 0.4), T(13.0), 0.5)
    # 懐中電灯のスイッチ → 夜の旧校舎：風、きしみ、足音、前の方で振動音
    click = 0.8 * R.hp(R.noise(0.01), 2500) * R.dec(0.01, 0.003)
    add(click, T(18.2), 0.8)
    add(R.fade(R.bp(R.noise(T(END) - T(NPLAY)), 200, 900) * 0.5, 0.6, 0.6), T(NPLAY), 0.3, -0.3)
    for k in range(5):
        add(R.lp(R.noise(0.06), 900) * R.dec(0.06, 0.02), T(NPLAY + 0.1 + k * 0.45), 0.4, 0.1 * (-1) ** k)
    for t0 in (21.6, 22.6, 23.6, 27.2):
        add(buzz(0.5), T(t0), 0.25 if t0 < 24 else 0.35, 0.15)
    hb = R.heartbeat(); t0 = T(22.0)
    while t0 < T(END):
        add(hb, t0, 0.5); t0 += 0.8
    add(R.fade(R.pad([36.7, 55.0, 73.4], T(END) - T(NSTILL), 240, 2.0, 0.5), 0.8, 0.5), T(NSTILL), 0.5)
    add(R.boom(1.8), T(27.2), 0.6)

def main():
    tmp = tempfile.mkdtemp(prefix="s2e4_")
    base = build_picture(tmp)
    build_sfx(); R.build_voice()
    out = R.MIX[: R.n_(DUR)].copy()
    out[-R.n_(0.5):] *= np.linspace(1, 0, R.n_(0.5))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "s2e4_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "s2e4_ui.ass"); build_ui(ass)
    mp4 = os.path.join(HERE, "kimi_utsuranai_ep4.mp4")
    grade = "eq=contrast=1.05:saturation=0.9,vignette=PI/5,noise=alls=8:allf=t,ass=s2e4_ui.ass"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", base, "-i", wav, "-vf", grade, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "20", "-maxrate", "6M", "-bufsize", "12M", "-preset", "slow", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
                    "-movflags", "+faststart", "-t", "%.3f" % DUR, mp4], check=True, cwd=HERE)
    shutil.rmtree(tmp)
    print("wrote", mp4, DUR)

if __name__ == "__main__":
    main()
