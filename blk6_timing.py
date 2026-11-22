END = 38.0
CLENCH = 6.0       # 拳をにぎる（影化ゲージ上昇）
PILLARS = 8.3      # 千本柱：地面から柱が巨人へ
PHIT = 8.9
SWING = 9.6        # 巨人の拳が振りおろされる
SMASH = 10.5       # 地面をたたき割る（よける）
SWORD = 11.5       # 大剣を組み上げる
SLASH = 12.8       # 巨人の腕を斬り落とす
CATCH = 13.9       # 落ちてくるルカを受けとめる
JOIN = 14.8        # 手をつなぐ
SWARM = 17.0       # 影の群れがおしよせる
DOMAIN = 19.1      # 光と影が反転した世界
RISE = 21.5        # 天穿つ拳が地面からせり上がる
FHIT = 22.3        # 巨人を貫く
SUN = 23.2         # 日食が割れて太陽
FADEG = 24.0       # 巨人が金の粒になって消えていく
DAWN = 27.6        # 夜明け
TITLE = 34.4       # 完
WAVE = 17.4       # 金の波（影の群れを消す）

# ---- スロー演出（出力の時間 ↔ 物語の時間）。千本柱・大剣・斬撃をゆっくり見せる
WARP = [(8.3, 9.6, 2.9), (11.5, 12.8, 2.15), (12.8, 13.9, 1.1 + 1.1 + 34 / 24 - 1.1 - 1.1 + 1.1 - 0.2 + 0.2 + 0.0)]
WARP[2] = (12.8, 13.9, 86 / 24 - (2.9 - 1.3) - (2.15 - 1.3) + 1.1)   # 全体で 86 コマ延びるように
def out_t(s):
    """物語の時間 s → 出力（動画）の時間"""
    add = 0.0
    for a, b, d in WARP:
        if s <= a: break
        if s < b: return s + add + (s - a) * (d / (b - a) - 1.0)
        add += d - (b - a)
    return s + add
def story_t(o):
    """出力の時間 o → 物語の時間"""
    add = 0.0
    for a, b, d in WARP:
        oa = a + add
        if o <= oa: return o - add
        if o < oa + d: return a + (o - oa) * (b - a) / d
        add += d - (b - a)
    return o - add
EXTRA = 86 / 24
END_OUT = END + EXTRA
