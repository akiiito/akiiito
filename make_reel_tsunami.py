"""
make_reel_tsunami.py ― 『POV：津波警報が出た時、すぐ逃げる人と様子を見に行く人』（1話完結・上下2画面）
  1) --voice で声だけ先に作る（tsu1_voice.npy / tsu1_lines.json）
  2) create_tsu1.py で絵（12fps）
  3) 引数なしで 絵＋声＋効果音＋字幕＋HUD（残り時間）＋絵文字2択 → tsunami_sa.mp4
"""
import math, os, sys, json, math, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R
import s_sfx as X
import s_bgm as B
MEID = int(os.environ.get("MEID", "1368642336"))
from tsunami_lines import LINES as LINES0

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
FR = os.path.join(HERE, "frames_TSU2")
END = 63.0                       # 絵の長さ（このあと絵文字2択カードが1.5秒つく）
DUR = END
TAIL = 2.8                       # 絵文字2択カード（END-0.5 から 2.8 秒）のぶん、BGMをのばす
R.DUR = DUR
R.MIX = np.zeros((R.n_(DUR) + SR, 2))
add = R.add
R.VV_CAST.update({
    "nar":   (2051283136, 2051283136, 0.0, 1.15, 1.0),       # ナレーション（M1）
    "yotaA": (593129376, 593129376, 0.0, 0.95, 0.9),        # 同僚（蒼月ハヤテ）
    "yotaB": (593129376, 593129376, 0.0, 0.95, 0.9),
})
R.VOICE.update({k: (0, 0, 1.1, 0.04) for k in ("nar", "yotaA", "yotaB")})
R.SPK_REF_TEXT[:] = ["今日の放課後、少しだけ話せる", "写真、見せてくれる", "ううん、なんでもない", "また明日ね", "窓の外、きれいだね"]
R.LINES = list(LINES0)
VOICE_NPY = os.path.join(HERE, "tsu1_voice.npy"); LINES_JSON = os.path.join(HERE, "tsu1_lines.json")

def rr(x0, y0, x1, y1, r):
    k = 0.45 * r
    return ("m %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d"
            % (x0 + r, y0, x1 - r, y0, x1 - r + k, y0, x1, y0 + r - k, x1, y0 + r, x1, y1 - r, x1, y1 - r + k, x1 - r + k, y1, x1 - r, y1,
               x0 + r, y1, x0 + r - k, y1, x0, y1 - r + k, x0, y1 - r, x0, y0 + r, x0, y0 + r - k, x0 + r - k, y0, x0 + r, y0))

STY = (
    "Style: shape,{f},20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n"
    "Style: nar,{f},40,&H00FFFFFF,&H00FFFFFF,&H008A3CE8,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: yotaA,{f},40,&H00FFFFFF,&H00FFFFFF,&H00306A9A,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: yotaB,{f},40,&H00FFFFFF,&H00FFFFFF,&H00306A9A,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: hook,{f},58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,7,0,5,20,20,0,1\n"
    "Style: card,{f},44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,0,0,5,20,20,0,1\n"
    "Style: count,{f},84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,8,0,5,0,0,0,1\n")

def T(i): return R.LINES[i][0]
def T1(i): return R.LINES[i][1]

def build_ui(path):
    ev = []
    def E(t0, t1, style, text, layer=5):
        ev.append("Dialogue: %d,%s,%s,%s,,0,0,0,,%s" % (layer, R.ts(t0), R.ts(t1), style, text))
    def S(t0, t1, draw, col, alpha="&H00&", layer=4, extra=""):
        E(t0, t1, "shape", r"{\an7\pos(0,0)\p1\1c%s\1a%s\bord0\shad0%s}%s{\p0}" % (col, alpha, extra, draw), layer)
    pop = r"\fscx40\fscy40\t(0,120,\fscx112\fscy112)\t(120,220,\fscx100\fscy100)"
    S(0, END, rr(16, 16, 216, 66, 14), "&H40A040&", "&H10&", 6); E(0, END, "card", r"{\an5\pos(116,41)\fs30}すぐ逃げる", 7)
    S(0, END, rr(16, 696, 256, 746, 14), "&H3060E0&", "&H10&", 6); E(0, END, "card", r"{\an5\pos(136,721)\fs30}様子を見に行く", 7)
    S(0, END, "m 0 596 l 720 596 l 720 684 l 0 684", "&H101010&", "&H18&", 6)
    E(0, T1(0), "hook", r"{\an5\pos(360,640)\fs38}{\c&H4040FF&}津波警報{\c&HFFFFFF&}が出た時\N{\c&H80FF80&}すぐ逃げる人{\c&HFFFFFF&}と{\c&H60B0FF&}様子を見に行く人", 8)
    for i, (st, en, text, _, _, who) in enumerate(R.LINES):
        if who == "nar" and i > 0: E(st, en, "nar", r"{\an5\pos(360,640)\fs32\fad(80,100)}%s" % text, 8)
        elif who == "yotaB": E(st, en, "yotaB", r"{\an5\pos(360,1160)\fad(60,100)}%s" % text, 9)
    # 上中央：結末までのカウントダウン＋上端の進行バー（「短いし最後まで見よう」と思わせる）
    goal = T(12) + 4.0
    n = int(math.ceil(goal))
    for k in range(n):
        a = k; b = min(k + 1, goal); left = int(math.ceil(goal - k))
        col = "&H40D0FF&" if left > 10 else "&H4040FF&"
        S(a, b, rr(236, 16, 500, 66, 14), "&H101010&", "&H30&", 6)
        E(a, b, "card", r"{\an5\pos(368,41)\fs28}結末まで {\c%s}%d秒" % (col, left), 7)
    S(0, goal, "m 0 0 l 720 0 l 720 7 l 0 7", "&H40D0FF&", "&H00&", 8, r"\clip(0,0,0,7)\t(0,%d,\clip(0,0,720,7))" % int(goal * 1000))
    # 右上：地震からの時間
    clock = [(0, T(1), "14:00"), (T(1), T(2), "地震発生"), (T(2), T(6), "3分後"), (T(6), T(9), "15分後"), (T(9), T(11), "20分後"), (T(11), END, "40分後")]
    for a, b, c in clock:
        S(a, b, rr(520, 16, 704, 66, 14), "&H202020&", "&H30&", 6); E(a, b, "card", r"{\an5\pos(612,41)\fs30\c&H40D0FF&%s}%s" % (pop, c), 7)
    E(T(1), T(1) + 2.0, "count", r"{\an5\pos(360,400)\fs70\c&HFFFFFF&\3c&H2020C0&\bord6%s\frz-4}グラグラッ" % pop, 9)
    E(T(1), T(1) + 2.0, "count", r"{\an5\pos(360,1040)\fs70\c&HFFFFFF&\3c&H2020C0&\bord6%s\frz4}グラグラッ" % pop, 9)
    def tagA(a, b, text, col, y=470): E(a, b, "count", r"{\an5\pos(360,%d)\fs50\c%s\3c&H000000&\bord5%s}%s" % (y, col, pop, text), 8)
    def tagB(a, b, text, col, y=1110): E(a, b, "count", r"{\an5\pos(360,%d)\fs50\c%s\3c&H000000&\bord5%s}%s" % (y, col, pop, text), 8)
    tagA(T(2) + 0.4, T1(2), "警報を待たずに 高台へ", "&H80FF80&"); tagB(T(3) + 0.4, T1(3), "● 撮影中…", "&H5050FF&")
    tagA(T(6), T(8), "高台に到着", "&H80FF80&"); tagB(T(8), T(9), "！津波", "&H3030FF&", 840)
    tagB(T(9) + 0.3, T1(9), "避難ビルへ", "&H80FF80&", 840)
    # 豆知識カード（公的な防災資料で確認した内容）
    cards = [(T(4), T1(4), "豆知識①", "強い揺れ・弱くても長い揺れ", "→ 警報を待たずに避難"),
             (T(5), T1(5), "豆知識②", "避難は原則「徒歩」", "車は渋滞で動けなくなるおそれ"),
             (T(8), T1(8), "豆知識③", "津波は見てからでは間に合わない", "陸でも人が全力で走るほど速い"),
             (T(11), T1(11), "豆知識④", "第1波が最大とは限らない", "警報が解除されるまで戻らない")]
    for c0, c1, hd, l1, l2 in cards:
        S(c0, c1, rr(40, 150, 680, 430, 28), "&HF4F0FF&", "&H10&", 7, r"\fad(150,100)\fscx90\fscy90\t(0,150,\fscx100\fscy100)")
        S(c0, c1, rr(40, 150, 680, 222, 28), "&H3070E0&", "&H00&", 8, r"\fad(150,100)")
        E(c0, c1, "card", r"{\an5\pos(360,186)\fs32\fad(150,100)}%s" % hd, 9)
        E(c0, c1, "card", r"{\an5\pos(360,290)\fs38\c&H2030B0&\fad(150,100)}%s" % l1, 9)
        E(c0, c1, "card", r"{\an5\pos(360,365)\fs30\c&H303030&\fad(150,100)}%s" % l2, 9)
        E(c0, c1, "card", r"{\an5\pos(360,410)\fs18\c&H707070&\fad(150,100)}出典：内閣府・気象庁・消防庁などの防災資料", 9)
    E(T(12) + 3.6, END, "count", r"{\an5\pos(360,300)\fs46\c&HFFFFFF&\3c&H000000&\bord5\fad(300,0)}運命を分けたのは", 9)
    E(T(12) + 4.0, END, "count", r"{\an5\pos(360,960)\fs56\c&H40D0FF&\3c&H000000&\bord6%s}最初の判断" % pop, 9)
    E(T(12) + 4.4, END, "count", r"{\an5\pos(360,1220)\fs24\c&HFFFFFF&\3c&H000000&\bord3\fad(300,0)}自分の地域のハザードマップと避難場所を確認しよう", 9)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

def siren(sec):
    tt = R.tt(sec); f = 600 + 250 * np.sin(2 * np.pi * tt / 3.0)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, tt / 1.0) * np.minimum(1, (sec - tt) / 1.0)

def build_sfx():
    B.disaster(add, DUR, s_quake=T(1), s_wave=T(6), s_end=T(12), tail=TAIL)            # BGM
    X.hit(add, 0.05, 0.5, 0)
    q = R.lp(R.noise(3.2), 90) * np.sin(np.pi * R.tt(3.2) / 3.2); add(q, T(1), 1.3)       # 地鳴り・揺れ
    add(X.impact(2.0), T(1) + 0.1, 0.8)
    for k in range(18): add(R.lp(R.noise(0.08), 3000) * R.dec(0.08, 0.02), T(1) + 0.2 + k * 0.15, 0.12, (k % 3 - 1) * 0.5)   # 物がカタカタ
    add(R.lp(siren(T(6) - T(2)), 1800), T(2), 0.06, -0.4)                                  # 町のサイレン（遠く）
    for k in range(int((T(6) - T(2) - 0.6) / 0.33)): add(R.step(), T(2) + 0.4 + k * 0.33, 0.22, 0.2)   # 走る足音
    roar = R.lp(R.noise(16.0), 350) * np.minimum(1, R.tt(16.0) / 6.0) ** 2; add(roar, T(6), 1.0)        # 波の音
    add(X.swell(1.0), T(8) - 1.0, 0.4); X.hit(add, T(8), 1.0, 0); add(X.braam(3.0, 44.0), T(8), 0.5)
    roar2 = R.lp(R.noise(8.0), 300) * np.minimum(1, R.tt(8.0) / 3.0) ** 2; add(roar2, T(11), 1.1)
    X.hit(add, T(11) + 0.4, 0.9, 0)
    hb = R.heartbeat(); t0 = T(7)
    while t0 < T(10): add(hb, t0, 0.4, -0.2); t0 += 0.45
    add(R.riser(3.0), T(12), 0.2); X.hit(add, T(12) + 3.8, 0.7, 0)

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
    tmp = tempfile.mkdtemp(prefix="tsu1_")
    out = R.MIX[: R.n_(DUR + TAIL)].copy()
    out[-R.n_(0.8):] *= np.linspace(1, 0, R.n_(0.8))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "tsu1_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "tsu1_ui.ass"); build_ui(ass)
    mp4 = os.path.join(HERE, "tsunami_sa.mp4"); raw = os.path.join(tmp, "raw.mp4")
    # 12fps の絵を24fpsに（2コマ打ち）＋少し魚眼っぽく＋周辺減光
    grade = "[0][1]vstack,fps=24,eq=contrast=1.12:saturation=1.12:gamma=0.95,unsharp=5:5:0.4,vignette=PI/6,noise=alls=3:allf=t,ass=tsu1_ui.ass[v]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "8", "-i", os.path.join(FR, "A_%04d.png"), "-framerate", "8", "-i", os.path.join(FR, "B_%04d.png"),
                    "-i", wav, "-filter_complex", grade, "-map", "[v]", "-map", "2:a",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-maxrate", "6M", "-bufsize", "12M",
                    "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-t", "%.3f" % DUR, raw], check=True, cwd=HERE)
    subprocess.run(["python3", os.path.join(HERE, "s2_endcard.py"), raw, mp4, "%.2f" % (END - 0.5),
                    "あなたは逃げられる？", "🏃", "すぐ逃げる", "📱", "見に行くかも", "▶ 家族に送って、避難場所を確かめよう", "2.8"], check=True)
    # 選択画面のあいだもBGMが鳴るように、音を全長版に差しかえる
    fin = os.path.join(tmp, "fin.mp4"); shutil.move(mp4, fin)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", fin, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-shortest", "-movflags", "+faststart", mp4], check=True)
    shutil.rmtree(tmp)
    print("wrote", mp4)

if __name__ == "__main__":
    main()
