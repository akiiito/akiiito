"""make_thumb_ai.py ― 津波動画のサムネイル（上下2画面の顔を隠さず、真ん中の帯に題名を置く）"""
import os, subprocess, tempfile
import make_reel as R
HERE = os.path.dirname(os.path.abspath(__file__))
ass = os.path.join(tempfile.mkdtemp(), "t.ass")
head = R.ASS_HEAD.replace("{f}", R.FONT).replace("PlayResX: 720", "PlayResX: 1080").replace("PlayResY: 1280", "PlayResY: 1920")
ev = [r"{\an7\pos(0,0)\p1\1c&H101010&\1a&H08&\bord0\shad0}m 0 800 l 1080 800 l 1080 1040 l 0 1040{\p0}",
      r"{\an5\pos(540,868)\fs68\bord8\3c&H000000&}{\c&H4040FF&}津波警報{\c&HFFFFFF&}が出た時",
      r"{\an5\pos(540,975)\fs64\bord8\3c&H000000&}{\c&H80FF80&}すぐ逃げる{\c&HFFFFFF&} vs {\c&H60B0FF&}見に行く",
      r"{\an7\pos(24,24)\fs48\bord6\3c&H000000&\c&H80FF80&}すぐ逃げる",
      r"{\an7\pos(24,1064)\fs48\bord6\3c&H000000&\c&H60B0FF&}様子を見に行く",
      r"{\an5\pos(540,1780)\fs60\bord7\3c&H000000&\c&HFFFFFF&}あなたは逃げられる？",
      r"{\an5\pos(540,1260)\fs84\bord8\3c&H000000&\c&H3030FF&}！津波",
      r"{\an9\pos(1060,1064)\fs44\bord6\3c&H000000&\c&H40D0FF&}保存推奨"]
with open(ass, "w", encoding="utf-8") as f:
    f.write(head + "".join("Dialogue: %d,0:00:00.00,0:00:01.00,Default,,0,0,0,,%s\n" % (i, e) for i, e in enumerate(ev)))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(HERE, "thumb_src_tsu1.png"), "-vf",
                "scale=1080:1920:flags=lanczos,eq=contrast=1.06:saturation=1.12,ass=%s" % ass, "-frames:v", "1", os.path.join(HERE, "thumb_tsunami_sa.png")], check=True)
print("wrote thumb_tsunami_sa.png")
