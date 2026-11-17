"""
make_thumbs_s2.py ― 『君は写真に写らない』のサムネ（1080x1920）
  python make_thumbs_s2.py 1  → thumb_s2e1.png
バズ型: 「撮った写真」そのものを見せ、映り込みに赤丸（＝見つけたくなる違和感）。
文字は短く、白＋赤、問いかけで終える。グリッド表示（中央 3:4 = y 240〜1680）に収める。
"""
import os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "IPAPGothic"
EP = {1: dict(src="frames_S2E1/C/0001.png", ring=(144, 960, 138), l1="好きな人が", l2="写真に写らない",
              q="この写真、消す？", badge="第1話"),
      2: dict(src="frames_S2E2/B/0001.png", ring=(230, 770, 175), tagpos=(420, 760), l1="私にしか", l2="見えない彼",
              q="この席、誰の？", badge="第2話", tag="…ここに\\Nいたのに"),
      3: dict(src="frames_S2E3/S/0048.png", ring=(596, 850, 210), tagpos=(780, 640), l1="親友に話したら", l2="彼が消える",
              q="あなたなら、話す？", badge="第3話", tag="去年\\N死んでる"),
      4: dict(src="frames_S2E4/P/cover.png", ring=(560, 1090, 250), tagpos=(700, 780), l1="親友か", l2="好きな人か",
              q="一人しか選べない", badge="第4話", tag="既読\\Nつかない")}
HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: t,{f},110,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,-1,0,0,0,100,100,2,0,1,10,6,5,0,0,0,1
Style: badge,{f},56,&H00FFFFFF,&H00FFFFFF,&H002020C0,&H00000000,-1,0,0,0,100,100,2,0,3,14,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
def circ(cx, cy, r):
    k = 0.5523 * r
    return ("m %d %d b %d %d %d %d %d %d b %d %d %d %d %d %d b %d %d %d %d %d %d b %d %d %d %d %d %d" %
            (cx, cy - r, cx + k, cy - r, cx + r, cy - k, cx + r, cy, cx + r, cy + k, cx + k, cy + r, cx, cy + r,
             cx - k, cy + r, cx - r, cy + k, cx - r, cy, cx - r, cy - k, cx - k, cy - r, cx, cy - r))
def make(n):
    e = EP[n]; cx, cy, r = e["ring"]
    ev = [(r"{\an7\pos(0,0)\p1\bord9\3c&H3030FF&\1a&HFF&\shad0}" + circ(cx, cy, r) + r"{\p0}"),
          (r"{\an4\pos(%d,%d)\fs70\c&H3030FF&\frz8}%s" % (e.get("tagpos", (cx + r - 20, cy - r - 30)) + (e.get("tag", "…いる？"),))),
          (r"{\an5\pos(540,330)}%s" % e["l1"]),
          (r"{\an5\pos(540,470)\fs140\c&H3030FF&}%s" % e["l2"]),
          (r"{\an5\pos(540,1560)\fs100}%s" % e["q"]),
          (r"{\an7\pos(36,60)\1c&HFFFFFF&\3c&H2020C0&\fs56\bord14\shad0} %s " % e["badge"])]
    tmp = tempfile.mkdtemp(); ass = os.path.join(tmp, "t.ass")
    with open(ass, "w", encoding="utf-8") as fh:
        fh.write(HEAD.replace("{f}", FONT))
        for i, txt in enumerate(ev):
            fh.write("Dialogue: %d,0:00:00.00,0:00:01.00,%s,,0,0,0,,%s\n" % (i, "badge" if i == 5 else "t", txt))
    out = os.path.join(HERE, "thumb_s2e%d.png" % n)
    fc = ("[0]scale=1080:1920:flags=lanczos,eq=contrast=1.08:saturation=1.1:brightness=-0.03,"
          "vignette=PI/4,noise=alls=6,ass=%s" % ass)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(HERE, e["src"]),
                    "-filter_complex", fc, "-frames:v", "1", out], check=True)
    print(out)
if __name__ == "__main__":
    for a in sys.argv[1:] or ["1"]: make(int(a))
