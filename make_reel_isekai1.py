"""
make_reel_isekai1.py ― 『POV：異世界に召喚されたら、世界の終わりまで残り3分だった』パート1
  1) --voice で声だけ先に作る（isk1_voice.npy / isk1_lines.json）
  2) create_isekai1.py で絵（12fps）
  3) 引数なしで 絵＋声＋効果音＋字幕＋HUD（残り時間）＋絵文字2択 → isekai_part1.mp4
"""
import os, sys, json, math, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R
from isekai_lines import PART1 as LINES0

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
FR = os.path.join(HERE, "frames_ISK1")
END = 28.0                       # 絵の長さ（このあと絵文字2択カードが1.5秒つく）
DUR = END
R.DUR = DUR
R.MIX = np.zeros((R.n_(DUR) + SR, 2))
add = R.add
R.VV_CAST.update({
    "mei":  (1325133120, 1325133120, 0.0, 1.05, 1.15),     # 花音
    "yota": (593129376, 593129376, 0.0, 0.95, 0.9),        # 蒼月ハヤテ
})
R.VOICE.update({"mei": (0, 0, 1.1, 0.04), "yota": (0, 0, 1.1, 0.04)})
R.SPK_REF_TEXT[:] = ["今日の放課後、少しだけ話せる", "写真、見せてくれる", "ううん、なんでもない", "また明日ね", "窓の外、きれいだね"]
R.LINES = list(LINES0)
VOICE_NPY = os.path.join(HERE, "isk1_voice.npy"); LINES_JSON = os.path.join(HERE, "isk1_lines.json")

def rr(x0, y0, x1, y1, r):
    k = 0.45 * r
    return ("m %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d"
            % (x0 + r, y0, x1 - r, y0, x1 - r + k, y0, x1, y0 + r - k, x1, y0 + r, x1, y1 - r, x1, y1 - r + k, x1 - r + k, y1, x1 - r, y1,
               x0 + r, y1, x0 + r - k, y1, x0, y1 - r + k, x0, y1 - r, x0, y0 + r, x0, y0 + r - k, x0 + r - k, y0, x0 + r, y0))

STY = (
    "Style: shape,{f},20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n"
    "Style: mei,{f},44,&H00FFFFFF,&H00FFFFFF,&H008A3CE8,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: yota,{f},44,&H00FFFFFF,&H00FFFFFF,&H00306A9A,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: hook,{f},58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,7,0,5,20,20,0,1\n"
    "Style: card,{f},44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,0,0,5,20,20,0,1\n"
    "Style: count,{f},84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,8,0,5,0,0,0,1\n")

def mmss(sec):
    sec = max(0, int(math.ceil(sec))); return "%02d:%02d" % (sec // 60, sec % 60)

def world_clock(t):
    """画面右上の「世界の終わりまで」タイマー。月を止めている間は止まり、ひびが入ると一気に減る"""
    if t < 21.0: return 180 - t, "run"
    if t < 23.6: return 180 - 21.0, "stop"
    return 180 - 21.0 - (t - 23.6) * 9.0, "fast"

def build_ui(path):
    ev = []
    def E(t0, t1, style, text, layer=5):
        ev.append("Dialogue: %d,%s,%s,%s,,0,0,0,,%s" % (layer, R.ts(t0), R.ts(t1), style, text))
    def S(t0, t1, draw, col, alpha="&H00&", layer=4, extra=""):
        E(t0, t1, "shape", r"{\an7\pos(0,0)\p1\1c%s\1a%s\bord0\shad0%s}%s{\p0}" % (col, alpha, extra, draw), layer)
    pop = r"\fscx40\fscy40\t(0,120,\fscx112\fscy112)\t(120,220,\fscx100\fscy100)"
    S(0, END, rr(290, 40, 430, 84, 12), "&H101010&", "&H50&", 6)
    E(0, END, "card", r"{\an5\pos(360,62)\fs28\c&H4090FF&}パート1", 7)
    # 見出し（0秒から）
    E(0, 3.2, "hook", r"{\an5\pos(360,250)\fs48\fad(0,150)}{\c&H40D0FF&}POV：{\c&HFFFFFF&}異世界に召喚されたら\N{\c&H4040FF&}世界の終わり{\c&HFFFFFF&}まで残り3分", 8)
    # HUD：世界の終わりまで（右上・ずっと）
    S(0, END, rr(500, 104, 700, 196, 14), "&H101010&", "&H60&", 6)
    E(0, END, "card", r"{\an5\pos(600,124)\fs22\c&HD0D0FF&}世界の終わりまで", 7)
    t = 0.0
    while t < END:
        n = min(END, t + 0.1); sec, mode = world_clock(t + 0.05)
        col = {"run": "&H4040FF&", "stop": "&HFFD070&", "fast": "&H2020FF&"}[mode]
        blink = mode == "fast" and int(t * 6) % 2 == 0
        E(t, n, "card", r"{\an5\pos(600,166)\fs48\c%s%s}%s%s" % (col, r"\alpha&H60&" if blink else "", mmss(sec), "" ), 7)
        t = n
    E(21.0, 23.6, "card", r"{\an5\pos(600,214)\fs24\c&HFFE0A0&\3c&H000000&\bord3}停止中", 7)
    E(7.8, 8.8, "count", r"{\an5\pos(360,360)\fs86\c&HFFFFFF&\3c&H2020D0&\bord6%s\frz6}危ない！" % pop, 8)
    c0, c1 = 10.3, 13.6                                              # チート能力カード
    S(c0, c1, rr(50, 230, 670, 540, 30), "&H2A1A10&", "&H20&", 6, r"\fad(150,100)\fscx90\fscy90\t(0,150,\fscx100\fscy100)")
    S(c0, c1, rr(50, 230, 670, 310, 30), "&HFFC060&", "&H00&", 7, r"\fad(150,100)")
    E(c0, c1, "card", r"{\an5\pos(360,270)\fs34\c&H301000&\fad(150,100)}チート能力 獲得！", 8)
    E(c0, c1, "card", r"{\an5\pos(360,385)\fs66\c&HFFE0A0&\3c&HFF9020&\bord3\fad(150,100)}時間停止", 8)
    E(c0, c1, "card", r"{\an5\pos(360,470)\fs30\c&HFFFFFF&\fad(150,100)}手でふれたものの時間を\N止められる", 8)
    E(20.8, 22.8, "count", r"{\an5\pos(360,360)\fs92\c&HFFF0C0&\3c&HFF9020&\bord7%s}STOP！" % pop, 8)
    E(23.6, 24.6, "count", r"{\an5\pos(360,360)\fs80\c&HFFFFFF&\3c&H2020D0&\bord6%s\frz-5}ピキッ…" % pop, 8)
    E(26.7, END, "count", r"{\an5\pos(360,470)\fs92\c&H4040FF&\3c&HFFFFFF&\bord7%s}止まらない…！" % pop, 8)
    E(27.0, END, "count", r"{\an5\pos(360,590)\fs40\c&HFFFFFF&\fad(200,0)}― パート2へつづく ―", 8)
    for st, en, text, _, _, who in R.LINES:
        E(st, en, who, r"{\an5\pos(360,1000)\fad(60,100)}%s" % text, 9)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

def build_sfx():
    # 重い低音のドローン＋太鼓（90BPM）。時間が止まる瞬間（9.0〜10.3）は無音にして際立たせる
    tt = R.tt(DUR); drone = (np.sin(2 * np.pi * 55 * tt) + 0.5 * np.sin(2 * np.pi * 82.4 * tt) + 0.3 * np.sin(2 * np.pi * 110 * tt * (1 + 0.002 * np.sin(tt))))
    gate = np.ones_like(tt); gate[(tt > 9.0) & (tt < 10.3)] = 0.0; gate[(tt > 20.9) & (tt < 23.5)] = 0.25
    add(R.lp(drone * gate * 0.5, 600), 0, 0.12)
    rum = R.lp(R.noise(DUR), 120) * gate; add(rum, 0, 0.5)                              # 地鳴り
    beat = 60 / 90; t = 0.2; k = 0
    while t < DUR - 0.5:
        if not (8.9 < t < 10.4) and not (20.9 < t < 23.5):
            add(R.lp(R.boom(0.5), 180), t, 0.3 if k % 4 == 0 else 0.16)
        t += beat * (1 if t < 16 else 0.5); k += 1
    for tm in (1.2, 4.1, 6.4, 14.5, 17.4, 25.0):                                       # 遠くの流星の着弾
        add(R.boom(1.6), tm, 0.22)
    add(R.whoosh(1.1, 300, 2500), 7.9, 0.5)                                            # 岩が飛んでくる
    add(R.chime([2093.0, 1567.9, 2637.0], 0.03, 1.4), 9.0, 0.35)                       # 時間停止（キン…）
    add(R.chime([1046.5, 1318.5, 1568.0, 2093.0], 0.06, 0.9), 10.3, 0.25)              # チート能力カード
    add(R.whoosh(1.6, 200, 4000), 20.6, 0.4); add(R.chime([523.3, 784.0, 1046.5], 0.08, 2.0), 20.9, 0.3)   # 月を止める
    add(R.boom(2.2), 23.6, 0.8); add(R.lp(R.noise(1.2), 2500) * np.exp(-R.tt(1.2) / 0.3), 23.6, 0.35)  # ひび
    hb = R.heartbeat(); t0 = 24.0
    while t0 < DUR - 0.4:
        add(hb, t0, 0.45); t0 += 0.38

def main():
    if "--voice" in sys.argv:
        R.build_voice()
        np.save(VOICE_NPY, R.MIX)
        json.dump([list(l) for l in R.LINES], open(LINES_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("wrote", VOICE_NPY, LINES_JSON); return
    R.LINES = [tuple(l) for l in json.load(open(LINES_JSON, encoding="utf-8"))]
    R.MIX = np.load(VOICE_NPY)
    build_sfx()
    tmp = tempfile.mkdtemp(prefix="isk1_")
    out = R.MIX[: R.n_(DUR)].copy()
    out[-R.n_(0.3):] *= np.linspace(1, 0, R.n_(0.3))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "isk1_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "isk1_ui.ass"); build_ui(ass)
    mp4 = os.path.join(HERE, "isekai_part1.mp4"); raw = os.path.join(tmp, "raw.mp4")
    # 12fps の絵を24fpsに（2コマ打ち）＋少し魚眼っぽく＋周辺減光
    grade = "fps=24,lenscorrection=k1=0.12:k2=0.03,crop=700:1244,scale=720:1280,vignette=PI/5,eq=contrast=1.04:saturation=1.08,ass=isk1_ui.ass"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", os.path.join(FR, "%04d.png"), "-i", wav, "-vf", grade,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-maxrate", "6M", "-bufsize", "12M",
                    "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-t", "%.3f" % DUR, raw], check=True, cwd=HERE)
    subprocess.run(["python3", os.path.join(HERE, "s2_endcard.py"), raw, mp4, "%.2f" % (END - 0.5),
                    "次の行動は、あなたが決めて", "🌕", "もう一度止める", "🏃", "逃げる", "▶ 多かった方が パート2になる", "2.8"],
                   check=True, env=dict(os.environ, ENDCARD_HINT="コメントの多い方で 物語が分かれる"))
    shutil.rmtree(tmp)
    print("wrote", mp4)

if __name__ == "__main__":
    main()
