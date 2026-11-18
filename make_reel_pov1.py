"""
make_reel_pov1.py ― 『POV：好きな人が7日後に転校する』パート1 の書き出し
  1) python make_reel_pov1.py --voice  → 声だけ先に作る（pov1_voice.npy と口パク用の pov1_lines.json）
  2) create_pov1.py で絵を1コマずつ描く（12fps、口パクは pov1_lines.json に合わせる）
  3) python make_reel_pov1.py          → 絵＋声＋効果音＋字幕＋絵文字2択カード → pov_tenkou_part1.mp4
"""
import os, sys, json, math, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R
from pov_lines import PART1

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
FR = os.path.join(HERE, "frames_POV1R")
END = 29.0                       # 絵の長さ（このあと絵文字2択カードが1.5秒つく）
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
R.LINES = list(PART1)
VOICE_NPY = os.path.join(HERE, "pov1_voice.npy"); LINES_JSON = os.path.join(HERE, "pov1_lines.json")

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
    # 上の「パート1」札（ずっと出す）
    S(0, END, rr(290, 40, 430, 84, 12), "&H101010&", "&H50&", 6)
    E(0, END, "card", r"{\an5\pos(360,62)\fs28\c&H4090FF&}パート1", 7)
    E(0, 3.6, "hook", r"{\an5\pos(360,330)\fscx70\fscy70\t(0,120,\fscx104\fscy104)\t(120,200,\fscx100\fscy100)}"
                      r"{\c&H40D0FF&}POV：{\c&HFFFFFF&}好きな人が\N{\c&H4040FF&}7日後に転校{\c&HFFFFFF&}する", 8)
    pop = r"\fscx40\fscy40\t(0,120,\fscx112\fscy112)\t(120,220,\fscx100\fscy100)"
    E(12.3, 13.4, "count", r"{\an5\pos(360,420)\fs40\c&HFFFFFF&\fad(0,150)}好きな人に会えるのは", 8)
    E(12.4, 13.4, "count", r"{\an5\pos(360,520)\fs120\c&H4040FF&\3c&HFFFFFF&\bord7%s\fad(0,150)}残り7日" % pop, 8)
    c0, c1 = 13.4, 17.0                                              # 雑学カード
    S(c0, c1, rr(50, 150, 670, 470, 30), "&HF4F0FF&", "&H10&", 6, r"\fad(150,100)\fscx90\fscy90\t(0,150,\fscx100\fscy100)")
    S(c0, c1, rr(50, 150, 670, 230, 30), "&H9B5CF0&", "&H00&", 7, r"\fad(150,100)")
    E(c0, c1, "card", r"{\an5\pos(360,190)\fs34\fad(150,100)}作戦1｜恋の心理学", 8)
    E(c0, c1, "card", r"{\an5\pos(360,300)\fs54\c&H6A2BD0&\fad(150,100)}ツァイガルニク効果", 8)
    E(c0, c1, "card", r"{\an5\pos(360,385)\fs30\c&H303030&\fad(150,100)}途中で終わった話ほど\N気になって頭から離れない", 8)
    E(20.4, 21.2, "count", r"{\an5\pos(360,330)\fs90\c&HFFFFFF&\3c&H8A5CFF&\bord6%s\frz-6}ストップ！" % pop, 8)
    E(27.2, END, "count", r"{\an5\pos(360,470)\fs110\c&H4040FF&\3c&HFFFFFF&\bord7%s}残り6日" % pop, 8)
    E(27.5, END, "count", r"{\an5\pos(360,600)\fs40\c&HFFFFFF&\fad(200,0)}― パート2へつづく ―", 8)
    for st, en, text, _, _, who in R.LINES:
        E(st, en, who, r"{\an5\pos(360,1000)\fad(60,100)}%s" % text, 9)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

def build_sfx():
    # しっとりしたピアノ風（Am-F-C-G、70BPM）。転校を聞いた瞬間は無音にする
    beat = 60 / 70; chords = [(220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (261.6, 329.6, 392.0), (196.0, 246.9, 293.7)]
    t = 3.8; bar = 0
    def note(f, sec=1.6):
        tt = R.tt(sec); return (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt) + 0.08 * np.sin(6 * np.pi * f * tt)) * np.exp(-tt / 0.7)
    while t < DUR - 1.0:
        ch = chords[bar % 4]
        add(R.lp(note(ch[0] / 2, 3.0), 900), t, 0.16)
        for i, f in enumerate((ch[0], ch[1], ch[2], ch[1])):
            if t + i * beat < DUR - 0.8:
                add(note(f), t + i * beat, 0.07 if 17.2 <= t < 27.0 else 0.09, 0.25 * (-1) ** i)
        t += 4 * beat; bar += 1
    add(R.fade(R.crowd(DUR, 300, 1500, 1.4), 0.4, 0.4), 0, 0.03, 0.3)              # 教室のざわめき
    for k in range(8):                                                            # 足音（POVで歩く）
        add(R.lp(R.boom(0.15), 400), 0.2 + k * 0.42, 0.14)
    add(R.boom(1.2), 12.4, 0.45)                                                   # 残り7日
    add(R.chime([1046.5, 1318.5, 1568.0], 0.06, 0.8), 13.4, 0.25)
    add(R.chime([1318.5, 987.8], 0.04, 0.4), 20.4, 0.2)                          # ストップ
    hb = R.heartbeat(); t0 = 21.2
    while t0 < 27.0:
        add(hb, t0, 0.4); t0 += 0.45
    add(R.boom(1.4), 27.2, 0.4)                                                   # 残り6日

def main():
    if "--voice" in sys.argv:
        R.build_voice()
        np.save(VOICE_NPY, R.MIX)
        json.dump([list(l) for l in R.LINES], open(LINES_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("wrote", VOICE_NPY, LINES_JSON); return
    R.LINES = [tuple(l) for l in json.load(open(LINES_JSON, encoding="utf-8"))]
    R.MIX = np.load(VOICE_NPY)
    build_sfx()
    tmp = tempfile.mkdtemp(prefix="pov1_")
    out = R.MIX[: R.n_(DUR)].copy()
    out[-R.n_(0.3):] *= np.linspace(1, 0, R.n_(0.3))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "pov1_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "pov1_ui.ass"); build_ui(ass)
    mp4 = os.path.join(HERE, "pov_tenkou_part1.mp4"); raw = os.path.join(tmp, "raw.mp4")
    # 12fps の絵を24fpsに（2コマ打ち）＋少し魚眼っぽく＋周辺減光
    grade = "fps=24,lenscorrection=k1=0.12:k2=0.03,crop=700:1244,scale=720:1280,vignette=PI/5,eq=contrast=1.06:saturation=1.1:brightness=0.03:gamma=1.08,ass=pov1_ui.ass"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", os.path.join(FR, "%04d.png"), "-i", wav, "-vf", grade,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-maxrate", "6M", "-bufsize", "12M",
                    "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-t", "%.3f" % DUR, raw], check=True, cwd=HERE)
    subprocess.run(["python3", os.path.join(HERE, "s2_endcard.py"), raw, mp4, "%.2f" % (END - 0.5),
                    "あなたなら、明日言う？", "🗣️", "言う", "🤐", "まだ言わない", "▶ パート2「残り6日」"], check=True)
    shutil.rmtree(tmp)
    print("wrote", mp4)

if __name__ == "__main__":
    main()
