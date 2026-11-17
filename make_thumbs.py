"""
make_thumbs.py ― 各話のサムネ（リールのカバー画像 1080x1920）を書き出す
  python make_thumbs.py 5 6   → thumb_ep5.png ...

バズ型の作り：
  ・顔のアップ（伸びた動画のサムネで最も多い要素）
  ・上下分割の「VS」構図で、一目で対立が分かる
  ・短い文字を極太の黄色＋黒フチ（周りの投稿から浮く色）
  ・「どっち？」で答えを考えさせる（キャプションの絵文字2択とつながる）
文字はプロフィールのグリッド表示（中央 3:4 = y 240〜1680）に収める。
"""
import os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "IPAPGothic"
EP = {
    # 未来の俺（赤・そのまま）を上、色を変えて左右反転した「今の俺」を下に置く
    6: dict(frame=380, crop="720:640:0:170", top="生き残る", bot="壊す", hook="あなたならどっち？", badge="最終話"),
    5: dict(frame=590, crop="720:640:0:170", top="未来の俺", bot="今の俺", hook="勝てば次のラスボス", badge="第5話"),
}
HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: badge,{f},60,&H00FFFFFF,&H00FFFFFF,&H00D04000,&H00000000,-1,0,0,0,100,100,2,0,3,16,0,5,0,0,0,1
Style: lab,{f},96,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,-1,0,0,0,100,100,2,0,1,12,6,5,0,0,0,1
Style: vs,{f},250,&H0000E5FF,&H0000E5FF,&H00000000,&HC8000000,-1,1,0,0,100,100,0,0,1,18,10,5,0,0,0,1
Style: hook,{f},150,&H0000E5FF,&H0000E5FF,&H00000000,&HC8000000,-1,0,0,0,100,100,4,0,1,16,8,5,0,0,0,1
Style: bolt,{f},20,&H0000E5FF,&H0000E5FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,6,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
# 上下の境目に走るギザギザの稲妻（ASS ベクター描画）
BOLT = r"{\an7\pos(0,0)\p1}m 0 940 l 180 900 l 300 975 l 470 905 l 600 985 l 760 910 l 900 980 l 1080 925 l 1080 960 l 900 1015 l 760 945 l 600 1020 l 470 940 l 300 1010 l 180 935 l 0 975{\p0}"

def make(n):
    e = EP[n]
    src = os.path.join(HERE, "frames_E%d" % n, "%04d.png" % e["frame"])
    assert os.path.exists(src), src
    ev = [("bolt", BOLT),
          ("lab", r"{\an5\pos(220,850)\c&H004040FF&}%s" % e["top"]),
          ("lab", r"{\an5\pos(880,1080)\c&H00FFC040&}%s" % e["bot"]),
          ("vs", r"{\an5\pos(540,955)\frz8}VS"),
          ("hook", r"{\an5\pos(540,1790)\fs110}%s" % e["hook"]),
          ("badge", r"{\an7\pos(36,60)} %s " % e["badge"])]
    tmp = tempfile.mkdtemp()
    ass = os.path.join(tmp, "t.ass")
    with open(ass, "w", encoding="utf-8") as fh:
        fh.write(HEAD.replace("{f}", FONT))
        for st, txt in ev:
            fh.write("Dialogue: 0,0:00:00.00,0:00:01.00,%s,,0,0,0,,%s\n" % (st, txt))
    out = os.path.join(HERE, "thumb_ep%d.png" % n)
    fc = ("[0]crop=%s,scale=1080:960:flags=lanczos,eq=contrast=1.12:saturation=1.35,split[a][b];"
          "[a]vignette=PI/5[top];"
          "[b]hflip,colorchannelmixer=rr=0:rb=1:br=1:bb=0,eq=brightness=-0.03,vignette=PI/5[bot];"   # 赤⇔青を入れ替え（紫の背景はそのまま）
          "[top][bot]vstack,ass=%s" % (e["crop"], ass))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-filter_complex", fc, "-frames:v", "1", out], check=True)
    print("wrote", out)

if __name__ == "__main__":
    for a in sys.argv[1:] or ["5"]:
        make(int(a))
