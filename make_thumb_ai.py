"""make_thumb_ai.py ― AI動画のサムネイル（上下2画面の顔を隠さず、真ん中の帯に題名を置く）"""
import os, subprocess, tempfile
import make_reel as R
HERE = os.path.dirname(os.path.abspath(__file__))
ass = os.path.join(tempfile.mkdtemp(), "t.ass")
head = R.ASS_HEAD.replace("{f}", R.FONT).replace("PlayResX: 720", "PlayResX: 1080").replace("PlayResY: 1280", "PlayResY: 1920")
ev = [r"{\an7\pos(0,0)\p1\1c&H101010&\1a&H08&\bord0\shad0}m 0 800 l 1080 800 l 1080 1040 l 0 1040{\p0}",
      r"{\an5\pos(540,868)\fs72\bord8\3c&H000000&}{\c&HFFD080&}AIを使う人{\c&HFFFFFF&} vs {\c&H60B0FF&}使わない人",
      r"{\an5\pos(540,975)\fs96\bord9\3c&H000000&\c&H3030FF&}5年後の末路",
      r"{\an9\pos(1060,1150)\fs50\bord6\3c&H000000&\c&H40D0FF&}1話完結"]
with open(ass, "w", encoding="utf-8") as f:
    f.write(head + "".join("Dialogue: %d,0:00:00.00,0:00:01.00,Default,,0,0,0,,%s\n" % (i, e) for i, e in enumerate(ev)))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(HERE, "thumb_src_ai1.png"), "-vf",
                "scale=1080:1920:flags=lanczos,eq=contrast=1.06:saturation=1.12,ass=%s" % ass, "-frames:v", "1", os.path.join(HERE, "thumb_ai_matsuro.png")], check=True)
print("wrote thumb_ai_matsuro.png")
