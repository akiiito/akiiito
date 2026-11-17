"""
make_thumbs.py ― 各話のサムネ（リールのカバー画像 1080x1920）を書き出す
  python make_thumbs.py 4 5 6   → thumb_ep4.png ...
文字はプロフィールのグリッド表示（中央 3:4 = 1080x1440）に収まる位置に置く。
"""
import os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "IPAPGothic"
EP = {
    4: dict(frame=230, top="観客1万人", big="全員、敵。", sub="10000 対 2", col="&H003C3CFF&"),
    5: dict(frame=590, top="最後の敵は", big="未来の“俺”", sub="勝てるはずがない", col="&H003C3CFF&", dy=420),
    6: dict(frame=360, top="デスゲームを", big="ぶっ壊す。", sub="最終話", col="&H0030E8FF&"),
}
HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: badge,{f},64,&H00FFFFFF,&H00FFFFFF,&H001010C0,&H00000000,-1,0,0,0,100,100,2,0,3,18,0,5,0,0,0,1
Style: top,{f},104,&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,-1,0,0,0,100,100,2,0,1,10,6,5,0,0,0,1
Style: big,{f},150,&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,-1,0,0,0,100,100,2,0,1,14,8,5,0,0,0,1
Style: sub,{f},72,&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,-1,0,0,0,100,100,2,0,1,8,4,5,0,0,0,1
Style: series,{f},52,&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,-1,0,0,0,100,100,2,0,1,6,3,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def make(n):
    e = EP[n]
    src = os.path.join(HERE, "frames_E%d" % n, "%04d.png" % e["frame"])
    assert os.path.exists(src), src
    badge = "最終話" if n == 6 else "第%d話" % n
    dy = e.get("dy", 0)                      # 顔に文字を乗せない話は下へずらす
    ev = [("badge", 300, " %s " % badge),
          ("top", 760 + dy, e["top"]),
          ("big", 930 + dy, r"{\c%s\3c&H00000000&\frz-4}%s" % (e["col"], e["big"])),
          ("sub", 1110 + dy, e["sub"]),
          ("series", 1640, "異世界デスゲーム")]
    tmp = tempfile.mkdtemp()
    ass = os.path.join(tmp, "t.ass")
    with open(ass, "w", encoding="utf-8") as fh:
        fh.write(HEAD.replace("{f}", FONT))
        for st, y, txt in ev:
            fh.write("Dialogue: 0,0:00:00.00,0:00:01.00,%s,,0,0,0,,{\\an5\\pos(540,%d)}%s\n" % (st, y, txt))
    out = os.path.join(HERE, "thumb_ep%d.png" % n)
    vf = ("scale=1080:1920:flags=lanczos,eq=brightness=-0.06:saturation=1.25,"
          "vignette=PI/4,ass=%s" % ass)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vf", vf, "-frames:v", "1", out], check=True)
    print("wrote", out)

if __name__ == "__main__":
    for a in sys.argv[1:] or ["4", "5"]:
        make(int(a))
