"""
make_reel_block1.py ― 『POV：全部がブロックの世界で目覚めたら、夜まで残り3分だった』パート1
  1) --voice で声だけ先に作る（blk1_voice.npy / blk1_lines.json）
  2) create_block1.py で絵（12fps）
  3) 引数なしで 絵＋声＋効果音＋字幕＋HUD（残り時間）＋絵文字2択 → block_part1.mp4
"""
import os, sys, json, math, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R
import s_sfx as X
import s_bgm as B
MEID = int(os.environ.get("MEID", "1368642336"))
from block_lines import PART1 as LINES0

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
FR = os.path.join(HERE, "frames_BLK1")
END = 28.0                       # 絵の長さ（このあと絵文字2択カードが1.5秒つく）
DUR = END
TAIL = 2.8                       # 絵文字2択カード（END-0.5 から 2.8 秒）のぶん、BGMをのばす
R.DUR = DUR
R.MIX = np.zeros((R.n_(DUR) + SR, 2))
add = R.add
R.VV_CAST.update({
    "ruka": (1325133120, 1325133120, 0.0, 1.05, 1.15),     # 花音（ルカ）
    "me":   (MEID, MEID, 0.0, 0.98, 1.0),                    # 自分（男）
})
R.VOICE.update({"ruka": (0, 0, 1.1, 0.04), "me": (0, 0, 1.1, 0.04)})
R.SPK_REF_TEXT[:] = ["今日の放課後、少しだけ話せる", "写真、見せてくれる", "ううん、なんでもない", "また明日ね", "窓の外、きれいだね"]
R.LINES = list(LINES0)
VOICE_NPY = os.path.join(HERE, "blk1_voice.npy"); LINES_JSON = os.path.join(HERE, "blk1_lines.json")

def rr(x0, y0, x1, y1, r):
    k = 0.45 * r
    return ("m %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d"
            % (x0 + r, y0, x1 - r, y0, x1 - r + k, y0, x1, y0 + r - k, x1, y0 + r, x1, y1 - r, x1, y1 - r + k, x1 - r + k, y1, x1 - r, y1,
               x0 + r, y1, x0 + r - k, y1, x0, y1 - r + k, x0, y1 - r, x0, y0 + r, x0, y0 + r - k, x0 + r - k, y0, x0 + r, y0))

STY = (
    "Style: shape,{f},20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n"
    "Style: ruka,{f},44,&H00FFFFFF,&H00FFFFFF,&H008A3CE8,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: me,{f},44,&H00FFFFFF,&H00FFFFFF,&H00306A9A,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: hook,{f},58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,7,0,5,20,20,0,1\n"
    "Style: card,{f},44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,0,0,5,20,20,0,1\n"
    "Style: count,{f},84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,8,0,5,0,0,0,1\n")

NIGHT_AT = 26.6                  # 「夜まで」タイマーが 00:00 になる瞬間

def mmss(sec):
    sec = max(0, int(math.ceil(sec))); return "%02d:%02d" % (sec // 60, sec % 60)

def build_ui(path):
    ev = []
    def E(t0, t1, style, text, layer=5):
        ev.append("Dialogue: %d,%s,%s,%s,,0,0,0,,%s" % (layer, R.ts(t0), R.ts(t1), style, text))
    def S(t0, t1, draw, col, alpha="&H00&", layer=4, extra=""):
        E(t0, t1, "shape", r"{\an7\pos(0,0)\p1\1c%s\1a%s\bord0\shad0%s}%s{\p0}" % (col, alpha, extra, draw), layer)
    pop = r"\fscx40\fscy40\t(0,120,\fscx112\fscy112)\t(120,220,\fscx100\fscy100)"
    S(0, END, rr(290, 40, 430, 84, 12), "&H101010&", "&H50&", 6)
    E(0, END, "card", r"{\an5\pos(360,62)\fs28\c&H4090FF&}パート1", 7)
    E(0, 3.2, "hook", r"{\an5\pos(360,235)\fs46\fad(0,150)}{\c&H40D0FF&}POV：{\c&HFFFFFF&}全部がブロックの\N世界で目覚めたら、{\c&H4040FF&}夜まで3分", 8)
    S(0.15, 3.4, rr(70, 352, 650, 420, 20), "&H1A1A1A&", "&H30&", 6, r"\fad(120,200)\fscx80\t(0,150,\fscx100)")
    S(0.15, 3.4, rr(70, 352, 86, 420, 6), "&H30C0FF&", "&H00&", 7, r"\fad(120,200)")
    E(0.15, 3.4, "card", r"{\an5\pos(368,386)\fs32\fad(120,200)}この物語は、{\c&H30C0FF&}あなたのコメント{\c&HFFFFFF&}で進む", 8)
    # 右上：夜まで（3分を 26.6 秒で一気に減らす）
    S(0, END, rr(500, 104, 700, 196, 14), "&H101010&", "&H60&", 6)
    E(0, NIGHT_AT, "card", r"{\an5\pos(600,124)\fs22\c&HD0D0FF&}夜まで", 7)
    t = 0.0
    while t < NIGHT_AT:
        n = min(NIGHT_AT, t + 0.1); sec = 180 * (1 - (t + 0.05) / NIGHT_AT)
        col = "&HFFFFFF&" if sec > 60 else ("&H40C0FF&" if sec > 20 else "&H4040FF&")
        E(t, n, "card", r"{\an5\pos(600,166)\fs48\c%s}%s" % (col, mmss(sec)), 7); t = n
    E(NIGHT_AT, END, "card", r"{\an5\pos(600,150)\fs56\c&H4040FF&%s}夜" % pop, 7)
    # 木ブロック ＋1
    E(9.7, 11.0, "count", r"{\an5\pos(540,820)\fs44\c&HFFFFFF&\3c&H306030&\bord5%s}＋1 白樺ブロック" % pop, 8)
    c0, c1 = 10.6, 13.8                                              # チート能力カード
    S(c0, c1, rr(50, 230, 670, 540, 30), "&H3A2A10&", "&H20&", 6, r"\fad(150,100)\fscx90\fscy90\t(0,150,\fscx100\fscy100)")
    S(c0, c1, rr(50, 230, 670, 310, 30), "&H60C0FF&", "&H00&", 7, r"\fad(150,100)")
    E(c0, c1, "card", r"{\an5\pos(360,270)\fs34\c&H102030&\fad(150,100)}チート能力 獲得！", 8)
    E(c0, c1, "card", r"{\an5\pos(360,385)\fs66\c&HFFF0C0&\3c&HFF9020&\bord3\fad(150,100)}ブロック変形", 8)
    E(c0, c1, "card", r"{\an5\pos(360,470)\fs30\c&HFFFFFF&\fad(150,100)}触れたブロックを一瞬で\N好きな形に組み替えられる", 8)
    E(15.6, 16.6, "count", r"{\an5\pos(360,330)\fs84\c&HFFFFFF&\3c&HE0A040&\bord6%s\frz-5}建築完了！" % pop, 8)
    E(T(6), T(6) + 2.2, "count", r"{\an5\pos(360,330)\fs60\c&HFFFFFF&\3c&H101060&\bord5%s}影ブロック ×48" % pop, 8)
    E(NIGHT_AT, END, "count", r"{\an5\pos(360,470)\fs96\c&H4040FF&\3c&HFFFFFF&\bord7%s}夜が来た" % pop, 8)
    E(NIGHT_AT + 0.3, END, "count", r"{\an5\pos(360,590)\fs40\c&HFFFFFF&\fad(200,0)}― パート2へつづく ―", 8)
    for st, en, text, _, _, who in R.LINES:
        E(st, en, who, r"{\an5\pos(360,1000)\fad(60,100)}%s" % text, 9)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

def T(i): return R.LINES[i][0]

def pop_snd(sec=0.25):
    tt = R.tt(sec); return np.sin(2 * np.pi * np.cumsum(500 + 1600 * tt / sec) / SR) * np.exp(-tt / 0.06)

def build_sfx():
    B.block_part1(add, DUR, tail=TAIL)                                                # BGM（最初から最後まで）
    X.hit(add, 0.05, 0.55, 0); add(X.stinger(), 0.1, 0.18)                           # 0秒
    add(X.whip(), T(1) + 0.1, 0.4); add(X.whip(), 6.3, 0.5)                            # 見回す／木の方へ
    for p in (7.4, 8.15, 8.9, 9.6):                                                    # 木を叩く
        add(R.thud(0.4), p + 0.08, 0.7); add(R.lp(R.noise(0.12), 1800) * R.dec(0.12, 0.03), p + 0.08, 0.5)
    add(pop_snd(), 9.65, 0.6); add(R.chime([1318.5, 1568.0, 2093.0], 0.05, 0.6), 9.8, 0.3)   # ポコン！＋1
    add(X.swell(1.0), 9.6, 0.4); X.hit(add, 10.6, 0.9, 0)                              # チート能力
    add(R.charge(1.6), 12.4, 0.25)
    for i in range(50):                                                                # 家が組み上がる（カカカカッ）
        add(R.lp(R.noise(0.05), 3000) * R.dec(0.05, 0.012), 13.9 + 1.25 * i / 50, 0.35, 0.3 * ((i % 3) - 1))
    X.hit(add, 15.6, 0.9, 0); add(R.chime([1046.5, 1318.5, 1568.0, 2093.0], 0.06, 0.9), 15.65, 0.25)   # 建築完了！
    add(X.swell(1.2), T(5) - 1.0, 0.5); X.hit(add, T(5) + 0.2, 0.75, 0); add(X.braam(2.8), T(5) + 0.2, 0.4)   # 影ブロックが湧く
    rng = np.random.default_rng(3)
    for k in range(40):                                                                # ぴょんぴょん近づく足音
        tm = T(5) + 0.6 + rng.uniform(0, DUR - T(5) - 0.8)
        add(R.lp(R.kick(90, 40, 0.25, 0.06), 400), tm, rng.uniform(0.15, 0.35), rng.uniform(-0.7, 0.7))
    X.hit(add, NIGHT_AT, 1.3, 1.0); add(X.braam(3.0, 46.0), NIGHT_AT, 0.6)            # 夜が来た
    hb = R.heartbeat(); t0 = T(7)
    while t0 < DUR + TAIL - 0.8: add(hb, t0, 0.55 if t0 < DUR else 0.35); t0 += 0.5

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
    tmp = tempfile.mkdtemp(prefix="blk1_")
    out = R.MIX[: R.n_(DUR + TAIL)].copy()
    out[-R.n_(0.8):] *= np.linspace(1, 0, R.n_(0.8))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "blk1_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "blk1_ui.ass"); build_ui(ass)
    mp4 = os.path.join(HERE, "block_part1.mp4"); raw = os.path.join(tmp, "raw.mp4")
    # 12fps の絵を24fpsに（2コマ打ち）＋少し魚眼っぽく＋周辺減光
    grade = "fps=24,lenscorrection=k1=0.12:k2=0.03,crop=700:1244,scale=720:1280,vignette=PI/5,eq=contrast=1.04:saturation=1.08,ass=blk1_ui.ass"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", os.path.join(FR, "%04d.png"), "-i", wav, "-vf", grade,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-maxrate", "6M", "-bufsize", "12M",
                    "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-t", "%.3f" % DUR, raw], check=True, cwd=HERE)
    subprocess.run(["python3", os.path.join(HERE, "s2_endcard.py"), raw, mp4, "%.2f" % (END - 0.5),
                    "次の行動は、あなたが決めて", "🏠", "穴に隠れる", "🔥", "迎え撃つ", "▶ 多かった方が パート2になる", "2.8"],
                   check=True, env=dict(os.environ, ENDCARD_HINT="コメントの多い方で 物語が分かれる"))
    # 選択画面のあいだもBGMが鳴るように、音を全長版に差しかえる
    fin = os.path.join(tmp, "fin.mp4"); shutil.move(mp4, fin)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", fin, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-shortest", "-movflags", "+faststart", mp4], check=True)
    shutil.rmtree(tmp)
    print("wrote", mp4)

if __name__ == "__main__":
    main()
