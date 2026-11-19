"""
make_teaser_tsu.py ― 津波動画の冒頭に「結末まで あと3秒」の予告（約1.6秒）＋巻き戻し（0.4秒）を足す
  tsunami_sa.mp4（本編）→ 予告を前につけて上書き
"""
import os, subprocess, tempfile, shutil, wave
import numpy as np
import make_reel as R
import s_sfx as X
HERE = os.path.dirname(os.path.abspath(__file__))
import sys
MP4 = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "tsunami_sa.mp4")
GOAL = 59.2                     # 「最初の判断」が出る瞬間
T0 = float(sys.argv[2]) if len(sys.argv) > 2 else 57.0      # 予告に使う本編の区間（残り3→2）
LABEL = sys.argv[3] if len(sys.argv) > 3 else "◀◀ 40分前"
MODE = sys.argv[4] if len(sys.argv) > 4 else "tsu"          # blk: 字幕隠しの帯なし・「夜明けまで」
PREFIX = sys.argv[5] if len(sys.argv) > 5 else ("夜明けまで あと" if MODE == "blk" else "結末まで あと")
TL = 1.6                        # 予告の長さ
RW = 0.45                       # 巻き戻しの長さ
SR = R.SR

def ass(path):
    st = ("Style: big,{f},96,&H00FFFFFF,&H00FFFFFF,&H000000C0,&H00000000,-1,0,0,0,100,100,2,0,1,9,0,5,0,0,0,1\n"
          "Style: sub,{f},40,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,0,0,0,1\n")
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", st.replace("{f}", R.FONT) + "\n[Events]")
    pop = r"\fscx50\fscy50\t(0,120,\fscx115\fscy115)\t(120,220,\fscx100\fscy100)"
    ev = [r"Dialogue: 8,%s,%s,sub,,0,0,0,,{\an7\pos(0,0)\p1\1c&H101010&\1a&H00&\bord0\shad0}m 0 520 l 720 520 l 720 740 l 0 740{\p0}" % (R.ts(0), R.ts(TL + RW)),
          r"Dialogue: 9,%s,%s,sub,,0,0,0,,{\an5\pos(360,560)\bord5\3c&H000000&}%s" % (R.ts(0), R.ts(TL), PREFIX),
          r"Dialogue: 9,%s,%s,big,,0,0,0,,{\an5\pos(360,660)\c&H4040FF&%s}3秒" % (R.ts(0), R.ts(1.0), pop),
          r"Dialogue: 9,%s,%s,big,,0,0,0,,{\an5\pos(360,660)\c&H4040FF&%s}2秒" % (R.ts(1.0), R.ts(TL), pop),
          r"Dialogue: 9,%s,%s,big,,0,0,0,,{\an5\pos(360,640)\fs80\c&HFFFFFF&\3c&H000000&\bord6}%s" % (R.ts(TL), R.ts(TL + RW), LABEL)]
    if MODE == "blk": ev = ev[1:]
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

def audio(path):
    n = int((TL + RW) * SR); m = np.zeros(n)
    def add(x, t, g):
        i = int(t * SR); x = x[: n - i]; m[i:i + len(x)] += g * x
    tick = lambda: np.sin(2 * np.pi * 1500 * R.tt(0.08)) * np.exp(-R.tt(0.08) / 0.02)
    add(X.braam(TL + 0.3, 49.0), 0.0, 0.8)
    for t in (0.0, 1.0): add(tick(), t, 0.9); add(X.impact(0.9), t, 0.5)
    add(X.whip(RW), TL, 1.0); add(X.swell(RW), TL - 0.05, 0.4)
    m = np.tanh(m / max(1e-9, np.abs(m).max()) * 1.4) * 0.8
    st = np.stack([m, m], 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype("<i2").tobytes())

def main():
    tmp = tempfile.mkdtemp(prefix="tsut_")
    a = os.path.join(tmp, "t.ass"); ass(a)
    wav = os.path.join(tmp, "t.wav"); audio(wav)
    tv = os.path.join(tmp, "tv.mp4")
    # 予告：本編の残り3→2秒の場面を少し赤く＋揺れ、続けてその場面を早回しで逆再生（巻き戻し）
    fc = ("[0:v]trim=%.3f:%.3f,setpts=PTS-STARTPTS,split[a][b];"
          "[a]colorbalance=rs=0.15:gs=-0.05:bs=-0.08,crop=iw*0.94:ih*0.94:iw*0.03+sin(n*1.9)*12:ih*0.03+cos(n*2.3)*12,scale=720:1280,setsar=1[a1];"
          "[b]reverse,setpts=PTS*%.4f,hue=s=0.2,scale=720:1280,setsar=1[b1];[a1][b1]concat=n=2:v=1,fps=24,ass=%s[v]"
          % (T0, T0 + TL, RW / TL, a))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", MP4, "-i", wav, "-filter_complex", fc, "-map", "[v]", "-map", "1:a",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-ar", str(SR), "-ac", "2", "-t", "%.3f" % (TL + RW), tv], check=True)
    out = os.path.join(tmp, "o.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tv, "-i", MP4, "-filter_complex",
                    "[0:v]setsar=1[v0];[1:v]setsar=1[v1];[v0][0:a][v1][1:a]concat=n=2:v=1:a=1[v][a0];[a0]loudnorm=I=-14:TP=-1.0:LRA=11[a]", "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
                    "-movflags", "+faststart", out], check=True)
    shutil.move(out, MP4); shutil.rmtree(tmp); print("wrote", MP4)

if __name__ == "__main__":
    main()
