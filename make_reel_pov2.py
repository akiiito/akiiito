"""
make_reel_pov2.py ― 『POV：好きな人が7日後に転校する』パート2「残り6日」の書き出し
  1) python make_reel_pov2.py --voice  → 声だけ先に作る（pov2_voice.npy と口パク用の pov2_lines.json）
  2) create_pov2.py で絵を1コマずつ描く（12fps、口パクは pov2_lines.json に合わせる）
  3) python make_reel_pov2.py          → 絵＋声＋効果音＋字幕＋絵文字2択カード → pov_tenkou_part2.mp4
"""
import os, sys, json, math, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R
from pov_lines import PART2

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
FR = os.path.join(HERE, "frames_POV2")
END = 31.0                       # 絵の長さ（このあと絵文字2択カードが1.5秒つく）
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
R.LINES = list(PART2)
VOICE_NPY = os.path.join(HERE, "pov2_voice.npy"); LINES_JSON = os.path.join(HERE, "pov2_lines.json")

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

def build_ui(path):
    ev = []
    def E(t0, t1, style, text, layer=5):
        ev.append("Dialogue: %d,%s,%s,%s,,0,0,0,,%s" % (layer, R.ts(t0), R.ts(t1), style, text))
    def S(t0, t1, draw, col, alpha="&H00&", layer=4, extra=""):
        E(t0, t1, "shape", r"{\an7\pos(0,0)\p1\1c%s\1a%s\bord0\shad0%s}%s{\p0}" % (col, alpha, extra, draw), layer)
    # 上の「パート2」札（ずっと出す）
    S(0, END, rr(290, 40, 430, 84, 12), "&H101010&", "&H50&", 6)
    E(0, END, "card", r"{\an5\pos(360,62)\fs28\c&H4090FF&}パート2", 7)
    pop = r"\fscx40\fscy40\t(0,120,\fscx112\fscy112)\t(120,220,\fscx100\fscy100)"
    E(0, 3.3, "hook", r"{\an5\pos(360,300)\fs46\fad(0,150)}{\c&H40D0FF&}POV：{\c&HFFFFFF&}好きな人が\N{\c&H4040FF&}7日後に転校{\c&HFFFFFF&}する", 8)
    E(0.1, 3.3, "count", r"{\an5\pos(360,480)\fs120\c&H4040FF&\3c&HFFFFFF&\bord7%s\fad(0,150)}残り6日" % pop, 8)
    c0, c1 = 14.6, 18.0                                               # 雑学カード
    S(c0, c1, rr(50, 150, 670, 470, 30), "&HF4F0FF&", "&H10&", 6, r"\fad(150,100)\fscx90\fscy90\t(0,150,\fscx100\fscy100)")
    S(c0, c1, rr(50, 150, 670, 230, 30), "&H9B5CF0&", "&H00&", 7, r"\fad(150,100)")
    E(c0, c1, "card", r"{\an5\pos(360,190)\fs34\fad(150,100)}作戦2｜恋の心理学", 8)
    E(c0, c1, "card", r"{\an5\pos(360,300)\fs60\c&H6A2BD0&\fad(150,100)}単純接触効果", 8)
    E(c0, c1, "card", r"{\an5\pos(360,385)\fs30\c&H303030&\fad(150,100)}会う回数が多い人ほど\N好きになりやすい", 8)
    E(21.3, 22.3, "count", r"{\an5\pos(360,330)\fs90\c&HFFFFFF&\3c&H8A5CFF&\bord6%s\frz-6}毎日！？" % pop, 8)
    E(30.1, END, "count", r"{\an5\pos(360,470)\fs110\c&H4040FF&\3c&HFFFFFF&\bord7%s}残り5日" % pop, 8)
    E(30.3, END, "count", r"{\an5\pos(360,600)\fs40\c&HFFFFFF&\fad(200,0)}― パート3へつづく ―", 8)
    for st, en, text, _, _, who in R.LINES:
        E(st, en, who, r"{\an5\pos(360,1000)\fad(60,100)}%s" % text, 9)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

def build_sfx():
    # しっとりしたピアノ風（Am-F-C-G、70BPM）。転校を聞いた瞬間は無音にする
    beat = 60 / 70; chords = [(220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (261.6, 329.6, 392.0), (196.0, 246.9, 293.7)]
    t = 0.6; bar = 0
    def note(f, sec=1.6):
        tt = R.tt(sec); return (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt) + 0.08 * np.sin(6 * np.pi * f * tt)) * np.exp(-tt / 0.7)
    while t < DUR - 1.0:
        ch = chords[bar % 4] if t < 24.4 else [c * 2 for c in ((261.6, 329.6, 392.0), (196.0, 246.9, 293.7), (220.0, 261.6, 329.6), (174.6, 220.0, 261.6))[bar % 4]]
        add(R.lp(note(ch[0] / 2, 3.0), 900), t, 0.16)
        for i, f in enumerate((ch[0], ch[1], ch[2], ch[1])):
            if t + i * beat < DUR - 0.8:
                add(note(f), t + i * beat, 0.06 if 14.6 <= t < 24.9 else 0.09, 0.25 * (-1) ** i)
        t += 4 * beat; bar += 1
    add(R.fade(R.crowd(DUR, 300, 1500, 1.4), 0.4, 0.4), 0, 0.03, 0.3)              # 教室のざわめき
    for k in range(6):                                                            # 駆け寄る足音
        add(R.lp(R.boom(0.12), 500), 0.65 + k * 0.42, 0.16)
    add(R.whoosh(0.6), 0.05, 0.25)                                                # 扉が開く
    add(R.chime([880.0, 1174.7], 0.04, 0.5), 7.3, 0.18)                          # 振り向く
    add(R.chime([1046.5, 1318.5, 1568.0], 0.06, 0.8), 14.6, 0.25)                # 作戦2
    add(R.chime([1318.5, 987.8], 0.04, 0.4), 21.3, 0.2)                          # 毎日！？
    hb = R.heartbeat(); t0 = 23.1
    while t0 < 30.0:
        add(hb, t0, 0.4); t0 += 0.45
    add(R.boom(1.4), 30.1, 0.4)                                                   # 残り5日

def main():
    if "--voice" in sys.argv:
        R.build_voice()
        np.save(VOICE_NPY, R.MIX)
        json.dump([list(l) for l in R.LINES], open(LINES_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("wrote", VOICE_NPY, LINES_JSON); return
    R.LINES = [tuple(l) for l in json.load(open(LINES_JSON, encoding="utf-8"))]
    R.MIX = np.load(VOICE_NPY)
    build_sfx()
    tmp = tempfile.mkdtemp(prefix="pov2_")
    out = R.MIX[: R.n_(DUR)].copy()
    out[-R.n_(0.3):] *= np.linspace(1, 0, R.n_(0.3))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "pov2_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "pov2_ui.ass"); build_ui(ass)
    mp4 = os.path.join(HERE, "pov_tenkou_part2.mp4"); raw = os.path.join(tmp, "raw.mp4")
    # 12fps の絵を24fpsに（2コマ打ち）＋少し魚眼っぽく＋周辺減光
    grade = "fps=24,lenscorrection=k1=0.12:k2=0.03,crop=700:1244,scale=720:1280,vignette=PI/5,eq=contrast=1.04:saturation=1.08,ass=pov2_ui.ass"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", os.path.join(FR, "%04d.png"), "-i", wav, "-vf", grade,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-maxrate", "6M", "-bufsize", "12M",
                    "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-t", "%.3f" % DUR, raw], check=True, cwd=HERE)
    subprocess.run(["python3", os.path.join(HERE, "s2_endcard.py"), raw, mp4, "%.2f" % (END - 0.5),
                    "あなたなら、毎日誘える？", "🙋", "誘える", "🙈", "むり…", "▶ パート3「残り5日」"], check=True)
    shutil.rmtree(tmp)
    print("wrote", mp4)

if __name__ == "__main__":
    main()
