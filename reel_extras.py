"""
reel_extras.py ― 伸びているブロックアニメ系ショートの共通点を字幕レイヤーに取り込む共通部品
  1) 冒頭1.5秒の「もしも〜？」フック（その話だけ見ても分かる一言の企画説明）
  2) 危険度 Lv.1 → Lv.100 の段階表示（Lv1〜Lv100 形式のエスカレーション）
  3) タイトル静止をやめ、引きの瞬間で切って「つづき ▶」を出す（ループ／次の動画へ）
"""
FPS = 24
STYLES = (
    "Style: hook,{f},62,&H0030E8FF,&H0030E8FF,&H00000000,&H96000000,-1,0,0,0,100,100,1,0,1,8,3,5,30,30,0,1\n"
    "Style: lv,{f},40,&H00FFFFFF,&H00FFFFFF,&H002020C0,&H96000000,-1,0,0,0,100,100,1,0,1,5,2,5,30,30,0,1\n"
    "Style: next,{f},50,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,1,0,1,6,2,5,30,30,0,1\n")
EP = {
    3: dict(hook="もしも「仲間を殺せ」と\\N言われたら？", next="▶ つづき：1万人 vs 2人",
            lv=[(1, 1), (112, 10), (160, 30), (240, 50), (310, 70), (403, 85), (476, 99), (520, 100), (612, "???")]),
    4: dict(hook="もしも観客1万人が\\N全員敵になったら？", next="▶ つづき：最後の敵は…俺？",
            lv=[(1, 1), (72, 5), (118, 10), (158, 20), (206, 40), (262, 60), (302, 80), (372, 99), (400, 100), (612, "???")]),
    5: dict(hook="もしもラスボスが\\N“未来の自分”だったら？", next="▶ 次回 最終話",
            lv=[(1, 1), (44, 20), (150, 40), (204, 55), (286, 70), (356, 90), (436, 99), (478, 100), (652, "MAX")]),
    6: dict(hook="もしも「壊せば自分も消える」\\Nと言われたら？", next=None,
            lv=[(1, 50), (60, 60), (120, 70), (198, 80), (286, 90), (372, 99), (380, 100), (464, None)]),
}
def ts(f):
    s = f / FPS
    return "%d:%02d:%05.2f" % (int(s // 3600), int(s % 3600 // 60), s % 60)
def head(ass_head, font):
    return ass_head.replace("\n[Events]", STYLES.replace("{f}", font) + "\n[Events]")
def write(fh, ep, end_f):
    e = EP[ep]
    pop = r"{\an5\pos(360,%d)\fscx60\fscy60\t(0,80,\fscx110\fscy110)\t(80,150,\fscx100\fscy100)\fad(0,120)}"
    fh.write("Dialogue: 3,%s,%s,hook,,0,0,0,,%s%s\n" % (ts(0), ts(40), pop % 370, e["hook"]))
    lv = e["lv"] + [(end_f, None)]
    for (f0, v), (f1, _) in zip(lv, lv[1:]):
        if v is None:
            continue
        col = r"\c&H00FFFFFF&" if not isinstance(v, int) or v < 50 else (r"\c&H0040D0FF&" if v < 90 else r"\c&H003030FF&")
        fh.write("Dialogue: 1,%s,%s,lv,,0,0,0,,%s{%s}危険度 Lv.%s\n" % (ts(max(f0, 41) if f0 == 1 else f0), ts(f1), pop % 176, col, v))
    if e["next"]:
        fh.write("Dialogue: 3,%s,%s,next,,0,0,0,,%s%s\n" % (ts(end_f - 30), ts(end_f), pop % 430, e["next"]))
