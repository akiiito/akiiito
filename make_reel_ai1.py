"""
make_reel_ai1.py ― 『POV：AIを使う人と使わない人、5年後の末路』（1話完結・上下2画面）
  1) --voice で声だけ先に作る（ai1_voice.npy / ai1_lines.json）
  2) create_ai1.py で絵（12fps）
  3) 引数なしで 絵＋声＋効果音＋字幕＋HUD（残り時間）＋絵文字2択 → ai_matsuro.mp4
"""
import os, sys, json, math, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R
import s_sfx as X
import s_bgm as B
MEID = int(os.environ.get("MEID", "1368642336"))
from ai_lines import LINES as LINES0

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
FR = os.path.join(HERE, "frames_AI1")
END = 64.0                       # 絵の長さ（このあと絵文字2択カードが1.5秒つく）
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
VOICE_NPY = os.path.join(HERE, "ai1_voice.npy"); LINES_JSON = os.path.join(HERE, "ai1_lines.json")

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
    # 上下のラベル
    S(0, END, rr(16, 16, 196, 66, 14), "&HD08030&", "&H10&", 6); E(0, END, "card", r"{\an5\pos(106,41)\fs30}AIを使う", 7)
    S(0, END, rr(16, 696, 196, 746, 14), "&H3080E0&", "&H10&", 6); E(0, END, "card", r"{\an5\pos(106,721)\fs30}使わない", 7)
    # 真ん中の帯（ナレーション）
    S(0, END, "m 0 596 l 720 596 l 720 684 l 0 684", "&H101010&", "&H18&", 6)
    E(0, T1(0), "hook", r"{\an5\pos(360,640)\fs40}{\c&HFFD080&}AIを使う人{\c&HFFFFFF&}と{\c&H60B0FF&}使わない人{\c&HFFFFFF&}\N5年後の{\c&H4040FF&}末路", 8)
    for i, (st, en, text, _, _, who) in enumerate(R.LINES):
        if who == "nar" and i > 0: E(st, en, "nar", r"{\an5\pos(360,640)\fs34\fad(80,100)}%s" % text, 8)
        elif who == "yotaA": E(st, en, "yotaA", r"{\an5\pos(360,520)\fad(60,100)}%s" % text, 9)
        elif who == "yotaB": E(st, en, "yotaB", r"{\an5\pos(360,1160)\fad(60,100)}%s" % text, 9)
    # 年（右上）
    yrs = [(0, T(1), "2026"), (T(1), T(4), "1年目"), (T(4), T(6), "2年目"), (T(6), T(10), "3年目"), (T(10), END, "5年目")]
    for a, b, y in yrs:
        S(a, b, rr(540, 16, 704, 66, 14), "&H202020&", "&H30&", 6); E(a, b, "card", r"{\an5\pos(622,41)\fs30\c&H40D0FF&%s}%s" % (pop, y), 7)
    def tagA(a, b, text, col): E(a, b, "count", r"{\an5\pos(360,470)\fs56\c%s\3c&H000000&\bord5%s}%s" % (col, pop, text), 8)
    def tagB(a, b, text, col): E(a, b, "count", r"{\an5\pos(360,1110)\fs56\c%s\3c&H000000&\bord5%s}%s" % (col, pop, text), 8)
    tagA(T(2), T1(2), "5分で完了", "&H60FF80&"); tagB(T(2) + 1.6, T1(2), "1時間…", "&H5050FF&")
    tagA(T(3), T1(3), "18:00 定時退社", "&H60D0FF&"); tagB(T(3), T1(3), "22:30 まだ残業", "&H5050FF&")
    tagA(T(4) + 1.5, T1(5), "スキル ＋1", "&H60FF80&"); tagB(T(5), T1(5), "同じ作業 ×365日", "&HC0C0C0&")
    tagA(T(6) + 0.4, T(9), "！ミス発覚", "&H3030FF&"); tagB(T(8), T(9), "信頼 ↑", "&H60FF80&")
    tagA(T(11) + 0.5, T1(11), "AIの下書き＋自分で確認", "&H60FF80&"); tagB(T(12) + 0.5, T1(12), "確かめる力 × AI", "&H60FF80&")
    c0, c1 = T(9), T1(9) + 0.2                                       # 豆知識カード（上の画面）
    S(c0, c1, rr(40, 150, 680, 440, 28), "&HF4F0FF&", "&H10&", 7, r"\fad(150,100)\fscx90\fscy90\t(0,150,\fscx100\fscy100)")
    S(c0, c1, rr(40, 150, 680, 222, 28), "&H9B5CF0&", "&H00&", 8, r"\fad(150,100)")
    E(c0, c1, "card", r"{\an5\pos(360,186)\fs32\fad(150,100)}豆知識", 9)
    E(c0, c1, "card", r"{\an5\pos(360,290)\fs30\c&H303030&\fad(150,100)}AIの“もっともらしい間違い”は", 9)
    E(c0, c1, "card", r"{\an5\pos(360,360)\fs44\c&H6A2BD0&\fad(150,100)}ハルシネーション（幻覚）", 9)
    E(c0, c1, "card", r"{\an5\pos(360,412)\fs26\c&H303030&\fad(150,100)}と呼ばれる", 9)
    # 最後：結論を大きく
    E(T(13) + 3.4, END, "count", r"{\an5\pos(360,300)\fs50\c&HFFFFFF&\3c&H000000&\bord5\fad(300,0)}末路を分けたのは", 9)
    E(T(13) + 3.8, END, "count", r"{\an5\pos(360,960)\fs52\c&H40D0FF&\3c&H000000&\bord6%s}何を頼み、どう確かめるか" % pop, 9)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

def keys(sec, rate):
    out = np.zeros(R.n_(sec)); rng = np.random.default_rng(int(rate * 10))
    t = 0.0
    while t < sec - 0.05:
        c = R.hp(R.noise(0.03), 2500) * R.dec(0.03, 0.006); i = R.n_(t); out[i:i + len(c)] += c[: len(out) - i] * rng.uniform(0.5, 1)
        t += rng.uniform(0.6, 1.4) / rate
    return out

def build_sfx():
    B.ai_matsuro(add, DUR, s_tense=T(6), s_calm=T(9), s_hope=T(10), tail=TAIL)        # BGM
    X.hit(add, 0.05, 0.6, 0); add(X.stinger(), 0.1, 0.18)
    for i in (1, 4, 6, 10):                                                              # 年が変わる
        add(X.whip(0.4), T(i) - 0.2, 0.5); add(R.chime([1046.5, 1568.0], 0.05, 0.6), T(i), 0.18)
    add(keys(1.5, 9), T(1), 0.25, 0.3)                                                   # 上：少しだけ打つ
    add(keys(T(4) - T(1) - 0.2, 7), T(1), 0.22, -0.3)                                    # 下：ずっと打っている
    add(R.chime([1318.5, 1760.0, 2093.0], 0.05, 0.8), T(2) + 0.1, 0.3)                   # 5分で完了
    add(R.lp(R.noise(0.6), 400) * R.dec(0.6, 0.2), T(2) + 1.6, 0.2)                      # 1時間…
    add(X.whip(0.5), T(3) - 0.1, 0.4)
    add(R.chime([1568.0, 2093.0, 2637.0], 0.05, 0.8), T(4) + 1.5, 0.25)                  # スキル＋1
    X.hit(add, T(6) + 0.4, 1.1, 0.9)                                                     # ミス発覚
    tt = R.tt(1.2); buzz = np.sign(np.sin(2 * np.pi * 220 * tt)) * (np.sin(2 * np.pi * 4 * tt) > 0) * R.dec(1.2, 0.8)
    add(R.lp(buzz, 2500), T(6) + 0.45, 0.18)
    add(X.stinger(), T(8) + 0.2, 0.3)                                                     # 信頼↑
    add(X.swell(1.0), T(10) - 1.0, 0.4); X.hit(add, T(10), 0.8, 0)                       # 5年目
    add(X.riser(3.0) if hasattr(X, "riser") else R.riser(3.0), T(13), 0.25)              # 俯瞰へ
    X.hit(add, T(13) + 3.6, 0.9, 0)

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
    tmp = tempfile.mkdtemp(prefix="ai1_")
    out = R.MIX[: R.n_(DUR + TAIL)].copy()
    out[-R.n_(0.8):] *= np.linspace(1, 0, R.n_(0.8))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "ai1_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "ai1_ui.ass"); build_ui(ass)
    mp4 = os.path.join(HERE, "ai_matsuro.mp4"); raw = os.path.join(tmp, "raw.mp4")
    # 12fps の絵を24fpsに（2コマ打ち）＋少し魚眼っぽく＋周辺減光
    grade = "[0][1]vstack,fps=24,eq=contrast=1.06:saturation=1.15,vignette=PI/6,ass=ai1_ui.ass[v]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "8", "-i", os.path.join(FR, "A_%04d.png"), "-framerate", "8", "-i", os.path.join(FR, "B_%04d.png"),
                    "-i", wav, "-filter_complex", grade, "-map", "[v]", "-map", "2:a",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-maxrate", "6M", "-bufsize", "12M",
                    "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-t", "%.3f" % DUR, raw], check=True, cwd=HERE)
    subprocess.run(["python3", os.path.join(HERE, "s2_endcard.py"), raw, mp4, "%.2f" % (END - 0.5),
                    "あなたはどっち？", "🤖", "もう使ってる", "✋", "まだ使ってない", "▶ 保存して、5年後に見返してね", "2.8"], check=True)
    # 選択画面のあいだもBGMが鳴るように、音を全長版に差しかえる
    fin = os.path.join(tmp, "fin.mp4"); shutil.move(mp4, fin)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", fin, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-shortest", "-movflags", "+faststart", mp4], check=True)
    shutil.rmtree(tmp)
    print("wrote", mp4)

if __name__ == "__main__":
    main()
