"""
make_reel_hana1.py ― 『POV：異世界で目を覚ましたら、昔飼っていた犬が女の子になって待っていた』パート1
  1) --voice で声だけ先に作る（hana1_voice.npy / hana1_lines.json）
  2) create_hana1.py で絵（12fps）
  3) 引数なしで 絵＋声＋効果音＋字幕＋HUD（残り時間）＋絵文字2択 → hana_part1.mp4
"""
import os, sys, json, math, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R
MEID = int(os.environ.get("MEID", "1368642336"))
from hana_lines import PART1 as LINES0

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
FR = os.path.join(HERE, "frames_HANA1")
END = 28.0                       # 絵の長さ（このあと絵文字2択カードが1.5秒つく）
DUR = END
R.DUR = DUR
R.MIX = np.zeros((R.n_(DUR) + SR, 2))
add = R.add
R.VV_CAST.update({
    "hana": (1878365376, 1878365376, 0.0, 1.0, 1.15),     # コハク（ハナ）
    "me":   (MEID, MEID, 0.0, 0.98, 1.0),                    # 自分（男）
})
R.VOICE.update({"hana": (0, 0, 1.1, 0.04), "me": (0, 0, 1.1, 0.04)})
R.SPK_REF_TEXT[:] = ["今日の放課後、少しだけ話せる", "写真、見せてくれる", "ううん、なんでもない", "また明日ね", "窓の外、きれいだね"]
R.LINES = list(LINES0)
VOICE_NPY = os.path.join(HERE, "hana1_voice.npy"); LINES_JSON = os.path.join(HERE, "hana1_lines.json")

def rr(x0, y0, x1, y1, r):
    k = 0.45 * r
    return ("m %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d"
            % (x0 + r, y0, x1 - r, y0, x1 - r + k, y0, x1, y0 + r - k, x1, y0 + r, x1, y1 - r, x1, y1 - r + k, x1 - r + k, y1, x1 - r, y1,
               x0 + r, y1, x0 + r - k, y1, x0, y1 - r + k, x0, y1 - r, x0, y0 + r, x0, y0 + r - k, x0 + r - k, y0, x0 + r, y0))

STY = (
    "Style: shape,{f},20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n"
    "Style: hana,{f},44,&H00FFFFFF,&H00FFFFFF,&H008A3CE8,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: me,{f},44,&H00FFFFFF,&H00FFFFFF,&H00306A9A,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: hook,{f},58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,7,0,5,20,20,0,1\n"
    "Style: card,{f},44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,0,0,5,20,20,0,1\n"
    "Style: count,{f},84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,8,0,5,0,0,0,1\n")

def build_ui(path):
    ev = []
    def E(t0, t1, style, text, layer=5):
        ev.append("Dialogue: %d,%s,%s,%s,,0,0,0,,%s" % (layer, R.ts(t0), R.ts(t1), style, text))
    def S(t0, t1, draw, col, alpha="&H00&", layer=4, extra=""):
        E(t0, t1, "shape", r"{\an7\pos(0,0)\p1\1c%s\1a%s\bord0\shad0%s}%s{\p0}" % (col, alpha, extra, draw), layer)
    pop = r"\fscx40\fscy40\t(0,120,\fscx112\fscy112)\t(120,220,\fscx100\fscy100)"
    S(0, END, rr(290, 40, 430, 84, 12), "&H101010&", "&H50&", 6)
    E(0, END, "card", r"{\an5\pos(360,62)\fs28\c&H4090FF&}パート1", 7)
    E(0, 3.2, "hook", r"{\an5\pos(360,250)\fs46\fad(0,150)}{\c&H40D0FF&}POV：{\c&HFFFFFF&}異世界で目を覚ましたら\N昔飼っていた{\c&H5080FF&}犬{\c&HFFFFFF&}が待っていた", 8)
    S(0.15, 3.4, rr(70, 352, 650, 420, 20), "&H1A1A1A&", "&H30&", 6, r"\fad(120,200)\fscx80\t(0,150,\fscx100)")
    S(0.15, 3.4, rr(70, 352, 86, 420, 6), "&H30C0FF&", "&H00&", 7, r"\fad(120,200)")
    E(0.15, 3.4, "card", r"{\an5\pos(368,386)\fs32\fad(120,200)}この物語は、{\c&H30C0FF&}あなたのコメント{\c&HFFFFFF&}で進む", 8)
    E(5.9, 6.9, "count", r"{\an5\pos(360,330)\fs84\c&H2020C0&\3c&H000000&\bord6%s\frz-4}グルルル…" % pop, 8)
    # 消えるまでの残り（右上・ここから先ずっと出す）
    S(25.0, END, rr(480, 104, 700, 196, 14), "&H101010&", "&H60&", 6, r"\fad(200,0)")
    E(25.0, END, "card", r"{\an5\pos(590,124)\fs22\c&HD0D0FF&\fad(200,0)}ハナが消えるまで", 7)
    E(25.0, END, "card", r"{\an5\pos(590,166)\fs46\c&H4040FF&%s}残り 7日" % pop, 7)
    c0, c1 = 25.3, 27.8                                              # 異世界のルール
    S(c0, c1, rr(50, 240, 670, 520, 30), "&HF4F0FF&", "&H10&", 6, r"\fad(150,100)\fscx90\fscy90\t(0,150,\fscx100\fscy100)")
    S(c0, c1, rr(50, 240, 670, 320, 30), "&H9B5CF0&", "&H00&", 7, r"\fad(150,100)")
    E(c0, c1, "card", r"{\an5\pos(360,280)\fs34\fad(150,100)}この世界のルール", 8)
    E(c0, c1, "card", r"{\an5\pos(360,385)\fs40\c&H6A2BD0&\fad(150,100)}強く想われた魂だけが", 8)
    E(c0, c1, "card", r"{\an5\pos(360,460)\fs40\c&H303030&\fad(150,100)}7日間だけ、人の姿になれる", 8)
    E(27.0, END, "count", r"{\an5\pos(360,600)\fs40\c&HFFFFFF&\fad(200,0)}― パート2へつづく ―", 8)
    for st, en, text, _, _, who in R.LINES:
        E(st, en, who, r"{\an5\pos(360,1000)\fad(60,100)}%s" % text, 9)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

def pluck(f, sec=1.4, decay=0.5):
    tt = R.tt(sec); return (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt / decay)

def build_sfx():
    # 0〜5.8秒：オルゴール（やさしい再会）
    mel = [784.0, 659.3, 523.3, 659.3, 784.0, 1046.5, 987.8, 784.0, 880.0, 784.0, 659.3, 587.3]
    for i, f in enumerate(mel):
        if 0.3 + i * 0.45 < 5.7: add(pluck(f, 1.2, 0.35), 0.3 + i * 0.45, 0.07, 0.3 * (-1) ** i)
    # 魔物のうなり声
    tt = R.tt(1.6); growl = R.lp(R.noise(1.6), 160) * (0.6 + 0.4 * np.sin(2 * np.pi * 22 * tt)) * np.minimum(1, tt * 4) * np.exp(-tt / 1.0)
    add(growl, 5.85, 1.0); add(R.boom(1.6), 5.9, 0.6)
    # 走る：太鼓＋足音＋風
    t = 6.9
    while t < 13.0:
        add(R.lp(R.boom(0.4), 200), t, 0.28); t += 0.33
    for k in range(17): add(R.lp(R.boom(0.12), 600), 7.4 + k * 0.33, 0.12)
    wind = R.lp(R.noise(6.0), 900) * np.sin(np.pi * R.tt(6.0) / 6.0); add(wind, 7.0, 0.12)
    # 15.9〜：思い出のピアノ（Am-F-C-G、ゆっくり）
    chords = [(220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (261.6, 329.6, 392.0), (196.0, 246.9, 293.7)]
    t = 15.9; bar = 0; beat = 60 / 66
    while t < DUR - 0.6:
        ch = chords[bar % 4]; add(R.lp(pluck(ch[0] / 2, 3.0, 1.0), 900), t, 0.14)
        for i, f in enumerate((ch[0], ch[1], ch[2], ch[1])):
            if t + i * beat < DUR - 0.6: add(pluck(f, 1.8, 0.8), t + i * beat, 0.08, 0.25 * (-1) ** i)
        t += 4 * beat; bar += 1
    add(R.chime([1046.5, 1318.5, 1568.0], 0.06, 1.0), 21.0, 0.22)                     # 「ハナ…？」
    add(R.chime([1568.0, 1760.0, 2093.0, 2349.3, 2637.0], 0.08, 1.4), 24.6, 0.22)      # 光の粒
    add(R.boom(1.4), 25.0, 0.35)
    hb = R.heartbeat(); t0 = 25.2
    while t0 < DUR - 0.4: add(hb, t0, 0.4); t0 += 0.55

def main():
    if "--voice" in sys.argv:
        R.build_voice()
        np.save(VOICE_NPY, R.MIX)
        json.dump([list(l) for l in R.LINES], open(LINES_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("wrote", VOICE_NPY, LINES_JSON); return
    R.LINES = [tuple(l) for l in json.load(open(LINES_JSON, encoding="utf-8"))]
    R.MIX = np.load(VOICE_NPY)
    build_sfx()
    tmp = tempfile.mkdtemp(prefix="hana1_")
    out = R.MIX[: R.n_(DUR)].copy()
    out[-R.n_(0.3):] *= np.linspace(1, 0, R.n_(0.3))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "hana1_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "hana1_ui.ass"); build_ui(ass)
    mp4 = os.path.join(HERE, "hana_part1.mp4"); raw = os.path.join(tmp, "raw.mp4")
    # 12fps の絵を24fpsに（2コマ打ち）＋少し魚眼っぽく＋周辺減光
    grade = "fps=24,lenscorrection=k1=0.12:k2=0.03,crop=700:1244,scale=720:1280,vignette=PI/5,eq=contrast=1.04:saturation=1.08,ass=hana1_ui.ass"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", os.path.join(FR, "%04d.png"), "-i", wav, "-vf", grade,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-maxrate", "6M", "-bufsize", "12M",
                    "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-t", "%.3f" % DUR, raw], check=True, cwd=HERE)
    subprocess.run(["python3", os.path.join(HERE, "s2_endcard.py"), raw, mp4, "%.2f" % (END - 0.5),
                    "次の行動は、あなたが決めて", "🐾", "救う方法を探す", "🌸", "7日間そばにいる", "▶ 多かった方が パート2になる", "2.8"],
                   check=True, env=dict(os.environ, ENDCARD_HINT="コメントの多い方で 物語が分かれる"))
    shutil.rmtree(tmp)
    print("wrote", mp4)

if __name__ == "__main__":
    main()
