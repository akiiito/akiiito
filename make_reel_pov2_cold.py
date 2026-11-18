"""
make_reel_pov2_cold.py ― パート2の冒頭を「毎日、ここで会お？」→「…え、毎日って毎日？」にする再編集版（答えは最後まで見せない）
  → 「― 10分前 ―」で屋上の扉を開ける本編へ → 「だめ、かな？」以降はそのまま
入力: pov_tenkou_part2.mp4 出力: pov_tenkou_part2_v2.mp4
"""
import os, subprocess
import make_reel_pov2 as P
R = P.R
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "pov_tenkou_part2.mp4"); OUT = os.path.join(HERE, "pov_tenkou_part2_v2.mp4")
SEGS = [(18.05, 23.3), (0.0, 18.05), (23.3, 32.5)]          # (元の開始, 元の終了)
COLD = SEGS[0][1] - SEGS[0][0]
ev = []
def E(t0, t1, style, text, layer=5):
    ev.append("Dialogue: %d,%s,%s,%s,,0,0,0,,%s" % (layer, R.ts(t0), R.ts(t1), style, text))
# 冒頭0秒から：大きな見出し（顔の上、残り7日と重ならない位置）
E(0, COLD, "hook", r"{\an5\pos(360,215)\fs50}{\c&H40D0FF&}POV：{\c&HFFFFFF&}好きな人が\N{\c&H4040FF&}7日後に転校{\c&HFFFFFF&}する", 8)
# つなぎ目の白フラッシュ（時間が戻った感じ）
E(COLD - 0.1, COLD + 0.3, "shape", r"{\an7\pos(0,0)\p1\1c&HFFFFFF&\bord0\shad0\fad(100,250)}m 0 0 l 720 0 l 720 1280 l 0 1280{\p0}", 7)
# 本編の頭：「5分前」
E(COLD, COLD + 1.2, "count", r"{\an5\pos(360,640)\fs52\c&HFFFFFF&\3c&H000000&\bord5\fad(80,200)}― 10分前 ―", 9)
ass = os.path.join(HERE, "pov2_cold_ui.ass")
head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", P.STY.replace("{f}", R.FONT) + "\n[Events]")
open(ass, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")
fc = []
for i, (a, b) in enumerate(SEGS):
    fc.append("[0:v]trim=%.3f:%.3f,setpts=PTS-STARTPTS[v%d]" % (a, b, i))
    fc.append("[0:a]atrim=%.3f:%.3f,asetpts=PTS-STARTPTS,afade=t=in:d=0.04,afade=t=out:st=%.3f:d=0.06[a%d]" % (a, b, b - a - 0.06, i))
fc.append("".join("[v%d][a%d]" % (i, i) for i in range(len(SEGS))) + "concat=n=%d:v=1:a=1[cv][ca]" % len(SEGS))
# 2つ目のつなぎ目（本編の頭）は白フラッシュで「時間が戻った」感じに
fc.append("[cv]ass=pov2_cold_ui.ass[ov]")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", SRC, "-filter_complex", ";".join(fc), "-map", "[ov]", "-map", "[ca]",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-maxrate", "6M", "-bufsize", "12M",
                "-c:a", "aac", "-b:a", "192k", OUT], check=True, cwd=HERE)
print("wrote", OUT)
