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
              q="一人しか選べない", badge="第4話", tag="既読\\Nつかない"),
      5: dict(src="frames_S2E5/U2/0001.png", ring=(470, 790, 200), tagpos=(690, 960), l1="好きな人に", l2="こっち側に来て",
              q="あなたなら、行く？", badge="第5話", tag="君にしか\\N頼めない"),
      6: dict(src="frames_S2E1/A/0072.png", ring=(555, 900, 190), tagpos=(760, 1110), l1="最後の写真に", l2="初めて写った",
              q="「ありがとう」言える？", badge="最終話", tag="やっと…"),
      31: dict(src="frames_S3E1/MC_blushsmile.png", ring=(-500, -500, 1), tagpos=(640, 1180), l1="好きな人と1日", l2="20回会ったら",
              q="恋の心理学 No.1", badge="第1話", tag="バレてた…", out="thumb_koi_ep1.png"),
      32: dict(src="frames_S3E2/HC_blush_smile.png", ring=(-500, -500, 1), tagpos=(700, 1150), l1="好きな人と", l2="お化け屋敷",
              q="恋の心理学 No.2", badge="第2話", tag="俺もかも", out="thumb_koi_ep2.png"),
      33: dict(src="frames_S3E3/TW_blushsmile_smile.png", ring=(-500, -500, 1), tagpos=(330, 1150), l1="好きな人を下の", l2="名前で呼んだら",
              q="恋の心理学 No.3", badge="第3話", tag="…めい", out="thumb_koi_ep3.png"),
      34: dict(src="frames_S3E4/MR_banzai_banzai_blush_smile.png", ring=(-500, -500, 1), tagpos=(330, 1250), l1="好きな人の", l2="しぐさを全部",
              q="恋の心理学 No.4", badge="第4話", tag="つい…", out="thumb_koi_ep4.png"),
      35: dict(src="frames_S3E5/TW_cold_sad.png", ring=(-500, -500, 1), tagpos=(330, 1250), l1="好きな人に", l2="わざと冷たく",
              q="恋の心理学 No.5", badge="第5話", tag="俺、何か\\Nした？", out="thumb_koi_ep5.png"),
      36: dict(src="frames_S3E6/GV2_shockc_base.png", ring=(-500, -500, 1), tagpos=(780, 1250), l1="クッキーの", l2="お返しが…",
              q="恋の心理学 No.6", badge="第6話", tag="でかっ！？", out="thumb_koi_ep6.png"),
      37: dict(src="thumb_src_pov1.png", ring=(-500, -500, 1), tagpos=(720, 1180), l1="POV：好きな人が", l2="7日後に転校",
              q="あと7日で、どうする？", badge="パート1", tag="明日まで\\N待つ", out="thumb_pov_part1.png")}
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
    out = os.path.join(HERE, e.get("out", "thumb_s2e%d.png" % n))
    fc = ("[0]scale=1080:1920:flags=lanczos,eq=contrast=1.08:saturation=1.1:brightness=-0.03,"
          "vignette=PI/4,noise=alls=6,ass=%s" % ass)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(HERE, e["src"]),
                    "-filter_complex", fc, "-frames:v", "1", out], check=True)
    print(out)
if __name__ == "__main__":
    for a in sys.argv[1:] or ["1"]: make(int(a))
