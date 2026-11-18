"""
make_reel_pov1_cold.py ― パート1の「冒頭5秒離脱」対策の再編集版（絵は描き直さない）
  いちばん刺さる場面（「…言ったら、さみしくなるだろ」→「残り7日」）を冒頭に持ってくる（コールドオープン）
  → 「― 5分前 ―」で階段を駆け上がる本編へ → 作戦1 以降はそのまま
入力: pov_tenkou_part1.mp4（通常版） 出力: pov_tenkou_part1_v2.mp4
"""
import os, subprocess
import make_reel_pov1 as P
R = P.R
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "pov_tenkou_part1.mp4"); OUT = os.path.join(HERE, "pov_tenkou_part1_v2.mp4")
SEGS = [(9.75, 13.4), (0.0, 9.75), (13.4, 30.5)]          # (元の開始, 元の終了)
COLD = SEGS[0][1] - SEGS[0][0]
ev = []
def E(t0, t1, style, text, layer=5):
    ev.append("Dialogue: %d,%s,%s,%s,,0,0,0,,%s" % (layer, R.ts(t0), R.ts(t1), style, text))
# 冒頭0秒から：大きな見出し（顔の上、残り7日と重ならない位置）
E(0, COLD, "hook", r"{\an5\pos(360,215)\fs50}{\c&H40D0FF&}POV：{\c&HFFFFFF&}好きな人が\N{\c&H4040FF&}7日後に転校{\c&HFFFFFF&}する", 8)
# つなぎ目の白フラッシュ（時間が戻った感じ）
E(COLD - 0.1, COLD + 0.3, "shape", r"{\an7\pos(0,0)\p1\1c&HFFFFFF&\bord0\shad0\fad(100,250)}m 0 0 l 720 0 l 720 1280 l 0 1280{\p0}", 7)
# 本編の頭：「5分前」
E(COLD, COLD + 1.2, "count", r"{\an5\pos(360,640)\fs52\c&HFFFFFF&\3c&H000000&\bord5\fad(80,200)}― 5分前 ―", 9)
ass = os.path.join(HERE, "pov1_cold_ui.ass")
head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", P.STY.replace("{f}", R.FONT) + "\n[Events]")
open(ass, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")
fc = []
for i, (a, b) in enumerate(SEGS):
    fc.append("[0:v]trim=%.3f:%.3f,setpts=PTS-STARTPTS[v%d]" % (a, b, i))
    fc.append("[0:a]atrim=%.3f:%.3f,asetpts=PTS-STARTPTS,afade=t=in:d=0.04,afade=t=out:st=%.3f:d=0.06[a%d]" % (a, b, b - a - 0.06, i))
fc.append("".join("[v%d][a%d]" % (i, i) for i in range(len(SEGS))) + "concat=n=%d:v=1:a=1[cv][ca]" % len(SEGS))
# 2つ目のつなぎ目（本編の頭）は白フラッシュで「時間が戻った」感じに
fc.append("[cv]ass=pov1_cold_ui.ass[ov]")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", SRC, "-filter_complex", ";".join(fc), "-map", "[ov]", "-map", "[ca]",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-maxrate", "6M", "-bufsize", "12M",
                "-c:a", "aac", "-b:a", "192k", OUT], check=True, cwd=HERE)
print("wrote", OUT)
