"""
make_reel_gk4.py ― 学園デスゲーム『出席番号13番』第4話「16時44分」（教室から逃げた）
  1) --voice で声（gk4_voice.npy / gk4_lines.json）
  2) create_toki1.py → post_toki1.py で絵
  3) 引数なしで 絵＋声＋効果音＋BGM＋字幕 → gk_ep4.mp4
"""
import os, sys, json, subprocess, wave, math
import numpy as np
import make_reel as R
import s_sfx as X
import s_bgm as B
import s_hit as K
from gk_lines import GK4 as LINES0
from gk4_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
DUR = END; TAIL = 0.0
R.DUR = DUR; R.MIX = np.zeros((R.n_(DUR) + SR, 2)); add = R.add
R.VV_CAST.update({
    "ren": (1368642336, 1368642336, 0.0, 1.0, 1.0),       # あなた
    "ann": (345585728, 345585728, -0.03, 0.92, 0.85),     # 放送の声
    "yui": (1717361472, 1717361472, 0.0, 1.0, 1.15),      # ユイ
    "kaito": (593129376, 593129376, 0.0, 1.05, 1.25),     # カイト
    "sae": (1325133120, 1325133120, 0.0, 1.0, 0.9),       # 委員長サエ
    "mio": (888753760, 888753760, 0.0, 1.1, 1.3),         # 消えていく女子
    "b2": (604166016, 604166016, 0.0, 1.05, 1.2),         # 消えていく男子
})
R.VOICE.update({"ren": (0, 0, 1.1, 0.04), "ann": (0, 0, 1.0, 0.2), "yui": (0, 0, 1.1, 0.05), "kaito": (0, 0, 1.1, 0.05), "sae": (0, 0, 1.0, 0.06), "mio": (0, 0, 1.1, 0.03), "b2": (0, 0, 1.1, 0.03)})
R.SPK_REF_TEXT[:] = ["今日の放課後、少しだけ話せる", "写真、見せてくれる", "ううん、なんでもない", "また明日ね", "窓の外、きれいだね"]
R.LINES = list(LINES0)
R.RETAKE_MIN, R.RETAKES = 0.66, 24
R.VV_READ += [("2年B組", "にねんびーぐみ"), ("準備室", "じゅんびしつ"), ("火事", "かじ"), ("味方", "みかた"), ("13番", "じゅうさんばん"), ("11番", "じゅういちばん"), ("12番", "じゅうにばん"), ("14番", "じゅうよんばん"), ("10秒", "じゅうびょう"), ("透けてる", "すけてる"), ("一緒", "いっしょ"), ("機能", "きのう"), ("削除", "さくじょ"), ("権限", "けんげん"), ("移行", "いこう"), ("異世界", "いせかい"), ("消失", "しょうしつ"), ("登録", "とうろく"), ("1発", "いっぱつ"), ("1票", "いっぴょう"), ("15人", "じゅうごにん"), ("名札", "なふだ"), ("塗りつぶされてる", "ぬりつぶされてる"), ("正解", "せいかい"), ("違反", "いはん"), ("3人", "さんにん"), ("規約違反", "きやくいはん"), ("検知", "けんち"), ("管理者", "かんりしゃ"), ("白石", "しらいし"), ("蓮", "れん"), ("出席簿", "しゅっせきぼ"), ("日直", "にっちょく"), ("一年", "いちねん"), ("委員長", "いいんちょう"), ("黒い枠", "くろいわく"), ("席", "せき"), ("出ろ", "でろ"), ("出口", "でぐち"), ("出られない", "でられない"), ("戻ってる", "もどってる"), ("戻る", "もどる"), ("死んでた", "しんでた"), ("動かない", "うごかない")]
VOICE_NPY = os.path.join(HERE, "gk4_voice.npy"); LINES_JSON = os.path.join(HERE, "gk4_lines.json")


STY = (
    "Style: shape,{f},20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n"
    "Style: ren,{f},68,&H00FFFFFF,&H00FFFFFF,&H00202020,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: yui,{f},68,&H00E8D0FF,&H00E8D0FF,&H00502040,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: kaito,{f},68,&H00FFE0B0,&H00FFE0B0,&H00402010,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: mio,{f},64,&H00C0E0FF,&H00C0E0FF,&H00203040,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: b2,{f},70,&H00B0C8FF,&H00B0C8FF,&H00102040,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: sae,{f},66,&H00D0FFD8,&H00D0FFD8,&H00204020,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: ann,{f},60,&H00FFE8A0,&H00FFE8A0,&H00402000,&H00000000,-1,0,0,0,100,100,1,0,1,7,0,5,16,16,0,1\n"
    "Style: hook,{f},58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,7,0,5,20,20,0,1\n"
    "Style: hud,{f},26,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,2,0,5,0,0,0,1\n"
    "Style: card,{f},44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,0,0,5,20,20,0,1\n"
    "Style: count,{f},84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,8,0,5,0,0,0,1\n")

def build_ui(path):
    ev = []
    def E(t0, t1, style, text, layer=5):
        if t1 > t0: ev.append("Dialogue: %d,%s,%s,%s,,0,0,0,,%s" % (layer, R.ts(t0), R.ts(t1), style, text))
    def S(t0, t1, draw, col, alpha="&H00&", layer=4, extra=""):
        E(t0, t1, "shape", r"{\an7\pos(0,0)\p1\1c%s\1a%s\bord0\shad0%s}%s{\p0}" % (col, alpha, extra, draw), layer)
    def rect(x0, y0, x1, y1): return "m %d %d l %d %d l %d %d l %d %d" % (x0, y0, x1, y0, x1, y1, x0, y1)
    pop = r"\fscx135\fscy135\t(0,140,\fscx100\fscy100)"
    band = lambda t0, t1, y0, y1: S(t0, t1, rect(0, y0, 720, y1), "&H000000&", "&H60&", 11, r"\fad(80,250)")
    ring = r"{\an7\pos(0,0)\p1\1a&HFF&\3c&H2020F0&\bord7\shad0\fad(80,200)\org(%d,%d)\fscx150\fscy150\t(0,160,\fscx100\fscy100)}m %d %d b %d %d %d %d %d %d b %d %d %d %d %d %d b %d %d %d %d %d %d b %d %d %d %d %d %d{\p0}"
    def circle(t0, t1, cx, cy, r):
        k = int(r * 0.552)
        E(t0, t1, "shape", ring % (cx, cy, cx, cy - r, cx + k, cy - r, cx + r, cy - k, cx + r, cy, cx + r, cy + k, cx + k, cy + r, cx, cy + r,
                                   cx - k, cy + r, cx - r, cy + k, cx - r, cy, cx - r, cy - k, cx - k, cy - r, cx, cy - r), 12)
    def gl(t0, t1, x, y, fs, text, layer=12, extra=""):
        """バグった文字：赤と青にずれた影＋本体"""
        E(t0, t1, "count", r"{\an5\pos(%d,%d)\fs%d\c&H3030FF&\3c&H3030FF&\bord0\alpha&H60&%s}%s" % (x - 7, y + 2, fs, extra, text), layer)
        E(t0, t1, "count", r"{\an5\pos(%d,%d)\fs%d\c&HFFFF30&\3c&HFFFF30&\bord0\alpha&H60&%s}%s" % (x + 7, y - 2, fs, extra, text), layer)
        E(t0, t1, "count", r"{\an5\pos(%d,%d)\fs%d\c&HFFFFFF&\3c&H000000&\bord5%s}%s" % (x, y, fs, extra, text), layer + 1)
    # 前回の選択 → 扉に飛び込む → 戻っている
    E(0.0, 1.6, "card", r"{\an8\pos(360,64)\fs26\c&HDDDDDD&\3c&H000000&\bord3\fad(0,300)}前回、あなたは{\c&H40C8F0&}「教室から逃げる」{\c&HDDDDDD&}を選んだ", 10)
    band(RESET1 + 0.05, 2.05, 330, 520)
    gl(RESET1 + 0.05, 2.05, 360, 425, 96, "戻ってる！？", 12, pop)
    # 何度逃げても戻る：ループの回数が跳ね上がる
    seq = ["1", "2", "3", "5", "9", "17", "38", "99", "256", "444"]
    for k, n in enumerate(seq):
        a_ = RESET2 + k * (MONT1 - RESET2) / len(seq); b_ = RESET2 + (k + 1) * (MONT1 - RESET2) / len(seq)
        gl(a_, b_ if k + 1 < len(seq) else MONT1 + 0.5, 360, 600, 150 if k < 9 else 180, "LOOP %s" % n, 12, r"\fscx115\fscy115\t(0,60,\fscx100\fscy100)")
    E(RESET2, MONT1 + 0.5, "card", r"{\an5\pos(360,470)\fs40\c&HFFFFFF&\3c&H000000&\bord4}何度逃げても、{\c&H3030FF&}ここに戻る", 11)
    # タイトル
    E(MONT1 + 0.5, 6.4, "card", r"{\an8\pos(360,64)\fs28\c&HDDDDDD&\3c&H000000&\bord3\fad(200,300)}出席番号13番　{\c&HFFFFFF&\fs40}第4話「16時44分」", 10)
    gl(4.3, 4.6, 360, 300, 70, "ERROR", 12)
    # 時計とスマホ：16:44 でそろう
    E(CLK, CLKSTOP, "count", r"{\an5\pos(360,250)\fs44\c&HFFFFFF&\3c&H000000&\bord4\fad(100,0)}時計が、{\c&H3030FF&}狂っていく", 11)
    circle(CLKSTOP, 15.0, CLKXY[0], CLKXY[1], 150)
    gl(CLKSTOP + 0.05, 15.0, 360, CLKXY[1] + 230, 110, "16:44", 12, pop)
    S(13.3, 15.0, rect(24, 60, 696, 200), "&HF4F4F4&", "&H08&", 12, r"\fad(120,200)\move(0,-120,0,0,0,150)")
    E(13.3, 15.0, "card", r"{\an7\pos(44,82)\fs28\c&H303030&\fad(120,200)\move(44,-38,44,82,0,150)}スマホ", 14)
    E(13.3, 15.0, "card", r"{\an9\pos(676,82)\fs30\c&H2020F0&\fad(120,200)\move(676,-38,676,82,0,150)}16:44　100%", 14)
    E(13.3, 15.0, "card", r"{\an7\pos(44,130)\fs30\c&H202020&\fad(120,200)\move(44,10,44,130,0,150)}1年前から、ずっと動いていない", 14)
    # 1年前の記憶
    band(MEM + 0.05, 17.6, 200, 330)
    gl(MEM + 0.05, 17.6, 360, 265, 54, "1年前　11月25日　16:44", 12, r"\fad(0,200)")
    E(MEM, BLACK, "hud", r"{\an7\pos(28,24)\fs26\c&H3030FF&}● {\c&HFFFFFF&}記憶を再生中", 7)
    circle(17.3, 19.4, LIGHTER[0], LIGHTER[1], 80)
    E(17.4, 19.4, "count", r"{\an5\pos(%d,%d)\fs40\c&HFFFFFF&\3c&H2020F0&\bord4%s\fad(0,200)}ライター" % (LIGHTER[0], LIGHTER[1] + 120, pop), 12)
    E(18.4, WIN - 0.3, "count", r"{\an5\pos(360,250)\fs46\c&HFFFFFF&\3c&H000000&\bord5%s\fad(0,150)}火事の原因は――{\c&H40B0FF&}カイト" % pop, 12)
    # ユイを窓から押し出したのは
    band(PUSH + 0.15, FALL + 0.4, 300, 600)
    E(PUSH + 0.15, FALL + 0.4, "count", r"{\an5\pos(360,370)\fs46\c&HFFFFFF&\3c&H000000&\bord5\fad(100,200)}ユイを窓から押し出したのは――", 12)
    E(PUSH + 0.75, FALL + 0.4, "count", r"{\an5\pos(360,500)\fs140\c&H2020F0&\3c&HFFFFFF&\bord7\frz-6%s\fad(0,200)}あなた" % pop, 13)
    # 暗転 → 母からのLINE
    S(BLACK + 0.3, PRES + 2.0, rect(24, 560, 696, 760), "&HF4F4F4&", "&H08&", 12, r"\fad(150,250)")
    S(BLACK + 0.3, PRES + 2.0, rect(44, 582, 84, 622), "&H55C806&", "&H00&", 13, r"\fad(150,250)")
    E(BLACK + 0.3, PRES + 2.0, "card", r"{\an7\pos(96,580)\fs28\c&H303030&\fad(150,250)}母", 14)
    E(BLACK + 0.3, PRES + 2.0, "card", r"{\an9\pos(676,580)\fs26\c&H808080&\fad(150,250)}16:44", 14)
    E(BLACK + 0.3, PRES + 2.0, "card", r"{\an7\pos(44,636)\fs32\c&H202020&\fad(150,250)}白い菊にしたよ。\Nあなた、好きだったでしょ", 14)
    # 気づいてしまった
    band(33.2, CARD, 200, 330)
    gl(33.25, CARD, 360, 265, 60, "あなたは、1年前に――", 12, pop)
    # 2択カード
    S(CARD, END, rect(0, 0, 720, 1280), "&H000000&", "&H50&", 15, r"\fad(250,0)")
    E(CARD, END, "count", r"{\an5\pos(360,330)\fs64\c&HFFFFFF&\3c&H000000&\bord6\fad(200,0)}ユイに、\Nなんて言う？", 16)
    S(CARD + 0.15, END, rect(30, 430, 690, 600), "&H2E9AC8&", "&H00&", 16, r"\fad(150,0)\t(0,120,\fscx102\fscy102)")
    E(CARD + 0.15, END, "count", r"{\an4\pos(140,515)\fs48\c&HFFFFFF&\3c&H303030&\bord4\fad(150,0)}「ありがとう」", 17)
    E(CARD + 0.35, END, "count", r"{\an5\pos(360,650)\fs44\c&H40E0FF&\3c&H000000&\bord4\fad(150,0)}それとも", 17)
    S(CARD + 0.5, END, rect(30, 700, 690, 870), "&HC07030&", "&H00&", 16, r"\fad(150,0)\t(0,120,\fscx102\fscy102)")
    E(CARD + 0.5, END, "count", r"{\an4\pos(140,785)\fs48\c&HFFFFFF&\3c&H303030&\bord4\fad(150,0)}「なんで来た」", 17)
    E(CARD + 0.8, END, "count", r"{\an5\pos(360,960)\fs50\c&HFFFFFF&\3c&H000000&\bord5\fad(150,0)}コメントで教えて　", 17)
    for st_, en, text, _, _, who in R.LINES:
        if st_ < CARD: E(st_, min(en, CARD), who, r"{\an5\pos(360,1040)\fad(60,100)}%s" % text, 9)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

CLKXY = (360, 640)      # 止まった時計（画面上の位置）
LIGHTER = (520, 600)    # カイトのライター

def mix(*xs):
    n = max(len(x) for x in xs); out = np.zeros(n)
    for x in xs: out[:len(x)] += x
    return out
def click(sec=0.06, f=3200): return R.lp(R.noise(sec), f) * R.dec(sec, 0.008)
def gunshot():
    return mix(R.hp(R.noise(0.02), 2000) * R.dec(0.02, 0.004) * 1.2, R.lp(R.kick(160, 50, 0.25, 0.05), 1500) * 1.3, R.lp(R.noise(0.6), 2500) * R.dec(0.6, 0.12) * 0.6)
def notif(): return mix(np.sin(2 * np.pi * 1568 * R.tt(0.12)) * R.dec(0.12, 0.05), np.concatenate([np.zeros(R.n_(0.1)), np.sin(2 * np.pi * 2093 * R.tt(0.2)) * R.dec(0.2, 0.07)]))
def chime(t0):
    """ゆがんだ学校のチャイム"""
    for k, f in enumerate((659.3, 523.3, 587.3, 392.0, 392.0, 587.3, 659.3, 523.3)):
        n = R.tt(1.6); w = 1 + 0.004 * np.sin(2 * np.pi * 3 * n) - 0.02 * k / 8
        sig = (np.sin(2 * np.pi * f * w * n) + 0.3 * np.sin(2 * np.pi * f * 2.01 * w * n)) * R.dec(1.6, 0.6)
        add(sig, t0 + k * 0.42, 0.22, 0.3 * (-1) ** k)
def sparkle(sec=1.6):
    rng = np.random.default_rng(3); out = np.zeros(R.n_(sec))
    for k in range(70):
        f = rng.uniform(2500, 7000); d = rng.uniform(0.05, 0.25); o = int(rng.uniform(0, sec - d) * SR)
        g = np.sin(2 * np.pi * f * R.tt(d)) * R.dec(d, d * 0.3) * (1 - o / len(out)); out[o:o + len(g)] += g
    return out
def buzzer(sec=0.7):
    n = R.tt(sec); sq = np.sign(np.sin(2 * np.pi * 110 * n)) * 0.5 + np.sign(np.sin(2 * np.pi * 116.5 * n)) * 0.5
    return R.lp(sq, 2500) * np.minimum(1, (sec - n) / 0.08)
def rip(sec=0.45):
    n = R.tt(sec); env = np.minimum(1, n / 0.03) * R.dec(sec, sec * 0.5)
    x = R.noise(sec) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 38 * n * (1 + 2 * n))))
    return R.bp(x, 900, 6000) * env
def step():
    a = R.lp(R.kick(90, 45, 0.18, 0.04), 700) * 0.8
    b = R.lp(R.noise(0.05), 2500) * R.dec(0.05, 0.01) * 0.4
    a[:len(b)] += b[:len(a)]
    return a
def slide(sec=0.6):
    n = R.tt(sec); return R.bp(R.noise(sec), 200, 1800) * np.sin(np.pi * n / sec) * (1 + 0.3 * np.sin(2 * np.pi * 23 * n))
def glitch_snd(sec=0.35, seed=0):
    """デジタルのバグ音：ガリガリした粗いノイズ＋途切れる矩形波"""
    rng = np.random.default_rng(seed); n = R.n_(sec)
    hold = int(rng.integers(20, 90)); x = np.repeat(rng.uniform(-1, 1, n // hold + 1), hold)[:n]
    f = rng.uniform(180, 900); sq = np.sign(np.sin(2 * np.pi * f * R.tt(sec) * (1 - 0.5 * R.tt(sec) / sec)))
    gate = np.repeat(rng.random(n // 1200 + 1) < 0.6, 1200)[:n]
    return (x * 0.7 + sq * 0.35) * gate * np.minimum(1, (sec - R.tt(sec)) / 0.03)
def bell(sec):
    """火災報知器のベル"""
    n = R.tt(sec); tone = sum(np.sin(2 * np.pi * f * n) * g for f, g in ((1840, 1.0), (2470, 0.6), (3710, 0.35), (5020, 0.2)))
    return tone * (0.55 + 0.45 * np.sign(np.sin(2 * np.pi * 19 * n))) * np.minimum(1, n / 0.05) * np.minimum(1, (sec - n) / 0.2)
def crackle(sec):
    rng = np.random.default_rng(9); base = R.lp(R.noise(sec), 900) * 0.6
    for _ in range(int(sec * 30)):
        o = int(rng.uniform(0, sec - 0.02) * SR); d = R.hp(R.noise(0.012), 1500) * R.dec(0.012, 0.003) * rng.uniform(0.5, 1.6)
        base[o:o + len(d)] += d
    return base
def heart():
    return mix(R.lp(R.kick(55, 38, 0.22, 0.05), 300), np.concatenate([np.zeros(R.n_(0.16)), R.lp(R.kick(50, 35, 0.2, 0.05), 300) * 0.7]))
def build_sfx():
    B.deathgame_bgm(add, END, ghosts=(), climax=CLK, win_=99.0, alarm=MEM, final=(CARD, END), tail=0.0)
    # 扉に飛び込む → 戻っている
    for t_ in np.arange(0.05, RESET1, 0.19): add(step(), t_, 0.35)
    add(X.swell(0.7), 0.05, 0.3); add(K.hit(1.3), RESET1, 0.7); add(glitch_snd(0.5, 1), RESET1, 0.5); add(X.braam(2.4, 30.0), RESET1 + 0.02, 0.4)
    add(X.tinnitus(1.2, 5200), RESET1 + 0.1, 0.06)
    for t_ in np.arange(DASH2, RESET2, 0.17): add(step(), t_, 0.35)
    add(K.hit(1.2), RESET2, 0.6); add(glitch_snd(0.4, 2), RESET2, 0.5)
    for k in range(1, 7):                                                         # ループの連打
        t_ = MONT0 + 0.25 * k; add(glitch_snd(0.16, 10 + k), t_, 0.4); add(K.hit(0.8), t_, 0.35); add(X.whip(0.2), t_ - 0.18, 0.15)
    add(K.hit(1.3), 4.3, 0.6); add(X.braam(2.4, 28.0), 4.32, 0.5); add(glitch_snd(0.3, 30), 4.3, 0.4)
    for k in range(8):                                                            # ふと世界がちらつく
        add(glitch_snd(0.08, 40 + k), 5.6 + k * 0.7 + (k % 3) * 0.2, 0.15)
    # 時計の針が狂う
    t_, dt = CLK, 0.03
    while t_ < CLKSTOP:
        add(click(0.03, 4000), t_, 0.3); t_ += dt; dt *= 1.08
    add(glitch_snd(0.2, 50), CLK, 0.3)
    add(K.hit(1.3), CLKSTOP, 0.65); add(X.braam(2.4, 30.0), CLKSTOP + 0.02, 0.45); add(X.tinnitus(1.5, 4800), CLKSTOP + 0.1, 0.07)
    add(notif(), 13.3, 0.35)
    # 記憶へ
    add(X.swell(1.1), 14.9, 0.45)
    for k in range(6): add(glitch_snd(0.12, 60 + k), 14.95 + k * 0.17, 0.2 + 0.05 * k)
    add(K.hit(1.4), MEM, 0.75); add(X.braam(2.4, 26.0), MEM + 0.02, 0.55); add(glitch_snd(0.6, 70), MEM, 0.5)
    add(bell(FALL - MEM), MEM + 0.1, 0.08); add(crackle(BLACK - MEM), MEM, 0.3)
    add(K.hit(0.9), 17.0, 0.35); add(click(0.05, 3000), 16.9, 0.4)                # ライター
    add(X.whip(0.35), WIN - 0.3, 0.35)
    for t_ in np.arange(RUN, PUSH, 0.2): add(step(), t_, 0.4)
    add(X.swell(0.7), PUSH - 0.6, 0.35); add(K.hit(1.4), PUSH, 0.75); add(X.whip(0.4), PUSH - 0.05, 0.4)
    add(K.hit(1.3), PUSH + 0.75, 0.6); add(X.braam(2.4, 29.0), PUSH + 0.77, 0.5)  # あなた
    t_, dt = FALL, 0.75                                                           # 心臓の音がゆっくり止まる
    while t_ < BLACK:
        add(heart(), t_, 0.55); t_ += dt; dt *= 1.25
    add(X.tinnitus(2.4, 3800), FALL + 0.5, 0.06)
    add(notif(), BLACK + 0.3, 0.4)
    # 今の教室：静かなピアノ
    for k, ch in enumerate(([220.0, 261.6, 329.6], [174.6, 220.0, 261.6], [196.0, 246.9, 293.7], [164.8, 207.7, 246.9])):
        for j, f in enumerate(ch): add(B.piano(f, 2.4, 0.6), PRES + 0.2 + k * 1.5 + j * 0.06, 0.18)
    add(glitch_snd(0.3, 80), PRES, 0.35); add(K.hit(0.9), PRES, 0.35)
    add(glitch_snd(0.25, 90), 33.2, 0.35); add(X.braam(2.4, 27.0), 33.25, 0.4)
    add(K.hit(1.2), CARD, 0.5); add(X.braam(2.4, 30.0), CARD + 0.05, 0.3)

def render_mp4():
    R.LINES = [tuple(l) for l in json.load(open(LINES_JSON, encoding="utf-8"))]
    voice = np.load(VOICE_NPY)
    voice = np.concatenate([voice, np.zeros((max(0, R.n_(DUR + TAIL + 1) - len(voice)), 2))])
    R.MIX = np.zeros_like(voice); build_sfx()
    R.MIX = voice + X.duck(R.MIX, voice)
    out = R.MIX[: R.n_(DUR + TAIL)].copy()
    out[-R.n_(1.2):] *= np.linspace(1, 0, R.n_(1.2))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "gk4_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "gk4_ui.ass"); build_ui(ass)
    if "--ui" in sys.argv: print("wrote", wav, ass); return
    mp4 = os.path.join(HERE, "gk_ep4.mp4")
    em = []
    for nm, ch in (("thanks", "🙏"), ("angry", "💢"), ("down", "👇")):
        pth = os.path.join(HERE, "gk4_%s.png" % nm); em.append(pth)
        subprocess.run(["python3", "-c", "import s2_endcard as e; e.emoji_png(%r, %r, 160)" % (ch, pth)], check=True, cwd=HERE)
    fc = ("[0:v]vignette=PI/5.5,ass=gk4_ui.ass[v0];"
          "[2:v]scale=110:-1,format=rgba,fade=in:st=%.2f:d=0.15:alpha=1[e1];[3:v]scale=110:-1,format=rgba,fade=in:st=%.2f:d=0.15:alpha=1[e2];[4:v]scale=90:-1,format=rgba,fade=in:st=%.2f:d=0.15:alpha=1[e3];"
          "[v0][e1]overlay=x=60:y=718:enable='gte(t,%.2f)'[v1];[v1][e2]overlay=x=60:y=1123:enable='gte(t,%.2f)'[v2];[v2][e3]overlay=x=860:y=1395:enable='gte(t,%.2f)'[v]"
          % (CARD + 0.15, CARD + 0.5, CARD + 0.8, CARD + 0.15, CARD + 0.5, CARD + 0.8))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(HERE, "frames_GK4_post", "%04d.png"), "-i", wav,
                    "-loop", "1", "-i", em[0], "-loop", "1", "-i", em[1], "-loop", "1", "-i", em[2],
                    "-filter_complex", fc, "-map", "[v]", "-map", "1:a",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-maxrate", "12M", "-bufsize", "24M",
                    "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-t", "%.3f" % (DUR + TAIL),
                    "-movflags", "+faststart", mp4], check=True, cwd=HERE)
    print("wrote", mp4)

def main():
    if "--voice" in sys.argv:
        R.build_voice()
        np.save(VOICE_NPY, R.MIX)
        json.dump([list(l) for l in R.LINES], open(LINES_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("wrote", VOICE_NPY, LINES_JSON); return
    render_mp4()

if __name__ == "__main__":
    main()
