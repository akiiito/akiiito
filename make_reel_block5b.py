"""
make_reel_block5b.py ― 『触れたら影になる』冒頭強化版 → block_hikari_v2.mp4
  ・最初の0.83秒に「黒くなる指先」→「夕日」をチラ見せ（ラストの“ルカに移った”から自然に頭へループ）
  ・冒頭のひとことを画面中央に大きく
  先に make_reel_block5.py --ui で blk5_audio.wav / blk5_ui.ass を作っておくこと
"""
import os, re, subprocess, tempfile, wave
import numpy as np
import make_reel_block5 as M
import make_reel as R
import s_sfx as X
from blk5_timing import END

HERE = M.HERE; FPS, SR = 24, R.SR
TEASER = list(range(680, 690)) + list(range(430, 440))   # 指先 → 夕日
T0 = len(TEASER) / FPS
TOTAL = END + T0

def tsec(s):
    h, m, x = s.split(":"); return int(h) * 3600 + int(m) * 60 + float(x)

def build_ass(path):
    src = os.path.join(HERE, "blk5_ui.ass"); M.build_ui(src)
    out = []
    for ln in open(src, encoding="utf-8").read().split("\n"):
        if ln.startswith("Dialogue:"):
            if "触れたら" in ln or "それでも彼女は" in ln or r"\clip(0,0,0,6)" in ln: continue
            p = ln.split(",", 3)
            p[1] = R.ts(tsec(p[1]) + T0); p[2] = R.ts(tsec(p[2]) + T0)
            ln = ",".join(p)
        out.append(ln)
    txt = "\n".join(out).rstrip("\n")
    def E(t0, t1, style, text, layer):
        return "Dialogue: %d,%s,%s,%s,,0,0,0,,%s" % (layer, R.ts(t0), R.ts(t1), style, text)
    pop = r"\fscx150\fscy150\t(0,140,\fscx100\fscy100)"
    H1 = T0 + 2.6
    add = [
        # 文字の裏に帯（流し見でも読める）
        E(0, H1, "shape", r"{\an7\pos(0,0)\p1\1c&H000000&\1a&H60&\bord0\shad0\fad(0,200)}m 0 100 l 720 100 l 720 410 l 0 410{\p0}", 8),
        E(0, H1, "hook", r"{\an5\pos(360,195)\fs88\bord8%s\fad(0,200)}触れたら、" % pop, 10),
        E(0, H1, "hook", r"{\an5\pos(360,315)\fs88\bord8%s\fad(0,200)}{\c&H4040FF&}影{\c&HFFFFFF&}になる世界。" % pop, 10),
        E(T0 + 0.5, H1, "card", r"{\an5\pos(360,460)\fs44\c&HFFFFFF&\bord4\3c&H000000&\fad(150,200)}それでも彼女は、手を握った", 10),
        E(0, TOTAL, "shape", r"{\an7\pos(0,0)\p1\1c&H60D0FF&\1a&H00&\bord0\shad0\clip(0,0,0,6)\t(0,%d,\clip(0,0,720,6))}m 0 0 l 720 0 l 720 6 l 0 6{\p0}" % int(TOTAL * 1000), 12),
    ]
    open(path, "w", encoding="utf-8").write(txt + "\n" + "\n".join(add) + "\n")

def build_audio(path):
    with wave.open(os.path.join(HERE, "blk5_audio.wav")) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), "<i2").reshape(-1, 2).astype(np.float64) / 32767
    n0 = int(round(T0 * SR))
    R.DUR = TOTAL; R.MIX = np.zeros((n0 + SR, 2))
    R.add(X.stinger(1.4), 0.0, 0.5)                          # チラ見せの一撃
    R.add(R.whoosh(0.5, 400, 3000), T0 - 0.45, 0.35)
    head = R.MIX[:n0]; tail = R.MIX[n0:n0 + SR]
    out = np.concatenate([head, a])
    out[n0:n0 + len(tail)] += tail[: max(0, min(len(tail), len(out) - n0))]
    out = np.clip(out, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())

def main():
    ass = os.path.join(HERE, "blk5b_ui.ass"); build_ass(ass)
    wav = os.path.join(HERE, "blk5b_audio.wav"); build_audio(wav)
    seq = tempfile.mkdtemp(prefix="blk5b_")
    names = ["%04d.png" % f for f in TEASER] + ["%04d.png" % f for f in range(1, 841)]
    for i, n in enumerate(names):
        os.symlink(os.path.join(M.FR, n), os.path.join(seq, "%04d.png" % (i + 1)))
    fire = os.path.join(HERE, "blk5_fire.png")
    if not os.path.exists(fire):
        subprocess.run(["python3", "-c", "import s2_endcard as e; e.emoji_png('🔥', %r, 150)" % fire], check=True, cwd=HERE)
    t1 = TOTAL - 1.6
    grade = ("[0:v]vignette=PI/5.5,eq=contrast=1.03:saturation=1.06,ass=blk5b_ui.ass[v];[2:v]scale=120:-1,format=rgba,fade=in:st=%.2f:d=0.2:alpha=1[f];"
             "[v][f]overlay=x=(W-w)/2:y=1215-h/2:enable='gte(t,%.2f)'" % (t1, t1))
    mp4 = os.path.join(HERE, "block_hikari_v2.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(seq, "%04d.png"), "-i", wav,
                    "-loop", "1", "-framerate", str(FPS), "-i", fire, "-filter_complex", grade,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-maxrate", "12M", "-bufsize", "24M",
                    "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-t", "%.3f" % TOTAL,
                    "-shortest", "-movflags", "+faststart", mp4], check=True, cwd=HERE)
    print("wrote", mp4, "%.2fs" % TOTAL)

if __name__ == "__main__":
    main()
