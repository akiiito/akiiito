"""
make_reel_toki1.py ― 「その罪、時効にさせない」第1話『光る絵の具』（35秒・1080x1920・24fps）
  1) --voice で声（gk2_voice.npy / gk2_lines.json）
  2) create_toki1.py → post_toki1.py で絵
  3) 引数なしで 絵＋声＋効果音＋BGM＋字幕 → gk_ep2a.mp4
"""
import os, sys, json, subprocess, wave
import numpy as np
import make_reel as R
import s_sfx as X
import s_bgm as B
import s_hit as K
from gk_lines import GK2A as LINES0
from gk2_timing import *

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
R.VV_READ += [("2年B組", "にねんびーぐみ"), ("準備室", "じゅんびしつ"), ("火事", "かじ"), ("味方", "みかた"), ("13番", "じゅうさんばん"), ("11番", "じゅういちばん"), ("12番", "じゅうにばん"), ("14番", "じゅうよんばん"), ("10秒", "じゅうびょう"), ("透けてる", "すけてる"), ("一緒", "いっしょ"), ("機能", "きのう"), ("削除", "さくじょ"), ("権限", "けんげん"), ("移行", "いこう"), ("異世界", "いせかい"), ("消失", "しょうしつ"), ("登録", "とうろく"), ("1発", "いっぱつ"), ("1票", "いっぴょう"), ("15人", "じゅうごにん"), ("名札", "なふだ"), ("塗りつぶされてる", "ぬりつぶされてる"), ("正解", "せいかい"), ("違反", "いはん"), ("3人", "さんにん"), ("規約違反", "きやくいはん"), ("検知", "けんち"), ("管理者", "かんりしゃ")]
VOICE_NPY = os.path.join(HERE, "gk2_voice.npy"); LINES_JSON = os.path.join(HERE, "gk2_lines.json")


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
    # 前回の選択 → 投票結果（1秒目から結果が出る）
    E(0.0, 1.9, "card", r"{\an8\pos(360,64)\fs26\c&HDDDDDD&\3c&H000000&\bord3\fad(0,300)}前回、あなたは{\c&H40D8FF&}「ユイを信じる」{\c&HDDDDDD&}を選んだ", 10)
    E(0.0, 1.9, "count", r"{\an8\pos(360,104)\fs50\c&HFFFFFF&\3c&H000000&\bord5\fad(0,300)}投票結果：{\c&HFFB050&}カイト", 10)
    E(1.9, 4.0, "card", r"{\an8\pos(360,64)\fs28\c&HDDDDDD&\3c&H000000&\bord3\fad(200,300)}出席番号13番　{\c&HFFFFFF&\fs40}第2話「消えた席」", 10)
    band(KDIS + 0.3, 2.9, 470, 650)
    E(KDIS + 0.3, 2.9, "count", r"{\an5\pos(360,560)\fs110\c&H2020F0&\3c&HFFFFFF&\bord6\frz-8%s\fad(0,250)}脱落" % pop, 12)
    # 生存カウンター
    hud = [(0.0, 30), (KDIS + 0.4, 29), (9.25, 26), (10.35, 22), (10.95, 18), (11.5, 15)]
    for k, (a_, v_) in enumerate(hud):
        b_ = hud[k + 1][0] if k + 1 < len(hud) else CARD
        E(a_, min(b_, a_ + 0.35), "hud", r"{\an9\pos(700,24)\fs30\c&HFFFFFF&}生存　{\c&H3030FF&\fs54%s}%d{\c&HFFFFFF&\fs30}／31" % (pop, v_), 7)
        E(a_ + 0.35, b_, "hud", r"{\an9\pos(700,24)\fs30\c&HFFFFFF&}生存　{\fs40}%d{\fs30}／31" % v_, 7)
    for a, b in ((2.8, 9.0), (25.2, 28.5)):
        E(a, b, "hud", r"{\an7\pos(28,24)\fs26\c&H3030FF&\fad(100,100)}● {\c&HFFFFFF&}校内放送", 7)
    # 不正解
    band(5.64, 6.8, 430, 700)
    E(5.64, 6.8, "count", r"{\an5\pos(360,560)\fs200\c&H2020F0&\3c&HFFFFFF&\bord8%s\fad(0,150)}✕" % pop, 12)
    E(5.7, 6.8, "count", r"{\an5\pos(360,690)\fs64\c&HFFFFFF&\3c&H2020F0&\bord5%s\fad(0,150)}不正解" % pop, 12)
    E(6.85, 9.0, "count", r"{\an5\pos(360,250)\fs42\c&HFFFFFF&\3c&H000000&\bord4\fad(150,150)}カイトに投票した人も、{\c&H3030FF&}消える", 11)
    # 連鎖脱落：コンボのように数が増える
    for k, (a_, n_) in enumerate(((9.25, 3), (10.35, 7), (10.95, 11), (11.5, 14))):
        b_ = (9.25, 10.35, 10.95, 11.5, 12.0)[k + 1]
        E(a_, b_, "count", r"{\an5\pos(360,560)\fs90\c&H2020F0&\3c&HFFFFFF&\bord6\frz%d%s}脱落 {\fs130}×%d" % ((-7, 6, -5, 8)[k], pop, n_), 12)
    # あなたも消えかける → 消去できない
    S(12.0, 13.1, rect(110, 560, 610, 600), "&H000000&", "&H40&", 12)
    for k in range(11):
        a_ = 12.0 + k * 0.09; b_ = a_ + 0.09 if k < 10 else 13.1
        S(a_, b_, rect(114, 564, 114 + int(492 * min(0.73, k * 0.073)), 596), "&HF0F0F0&", "&H00&", 13)
    E(12.0, 13.1, "count", r"{\an5\pos(360,520)\fs40\c&HFFFFFF&\3c&H000000&\bord4}あなた：消去中… {\fs34}%s" % "", 13)
    E(13.1, 14.3, "count", r"{\an5\pos(360,560)\fs64\c&H2020F0&\3c&HFFFFFF&\bord5%s\fad(0,200)}ERROR{\N\fs46\c&HFFFFFF&\3c&H000000&}消去できません" % pop, 13)
    # 数が合わない
    E(18.2, 19.6, "count", r"{\an5\pos(360,250)\fs46\c&HFFFFFF&\3c&H000000&\bord4%s\fad(0,200)}15人　{\c&H40E0FF&}＋　あなた　＝　16人？" % pop, 12)
    # カバンがない（カイトの机）
    ring = r"{\an7\pos(0,0)\p1\1a&HFF&\3c&H2020F0&\bord7\shad0\fad(80,200)\org(%d,%d)\fscx150\fscy150\t(0,160,\fscx100\fscy100)}m %d %d b %d %d %d %d %d %d b %d %d %d %d %d %d b %d %d %d %d %d %d b %d %d %d %d %d %d{\p0}"
    def circle(t0, t1, cx, cy, r):
        k = int(r * 0.552)
        E(t0, t1, "shape", ring % (cx, cy, cx, cy - r, cx + k, cy - r, cx + r, cy - k, cx + r, cy, cx + r, cy + k, cx + k, cy + r, cx, cy + r,
                                   cx - k, cy + r, cx - r, cy + k, cx - r, cy, cx - r, cy - k, cx - k, cy - r, cx, cy - r), 12)
    circle(20.85, 21.6, 150, 660, 85)
    E(20.85, 21.6, "card", r"{\an4\pos(285,380)\fs32\c&H60FF60&\3c&H000000&\bord3\fad(80,200)}← カバンあり", 12)
    E(20.9, 21.6, "count", r"{\an5\pos(230,790)\fs40\c&HFFFFFF&\3c&H2020F0&\bord4%s\fad(0,200)}カバンがない" % pop, 12)
    # 名札の13
    circle(24.4, 25.4, 180, 633, 95)
    E(24.4, 25.4, "count", r"{\an5\pos(360,880)\fs120\c&H2020F0&\3c&HFFFFFF&\bord6%s\fad(0,200)}13" % pop, 12)
    # 投票まで 3・2・1
    for k in range(3):
        a_ = COUNT + k * (CARD - COUNT) / 3; b_ = COUNT + (k + 1) * (CARD - COUNT) / 3
        E(a_, b_, "count", r"{\an5\pos(360,420)\fs56\c&HFFFFFF&\3c&H000000&\bord5}次の投票まで{\N}{\c&H3030FF&\fs160%s}%d" % (pop, 3 - k), 11)
    # 2択カード
    S(CARD, END, rect(0, 0, 720, 1280), "&H000000&", "&H50&", 15, r"\fad(250,0)")
    E(CARD, END, "count", r"{\an5\pos(360,330)\fs64\c&HFFFFFF&\3c&H000000&\bord6\fad(200,0)}あなたなら\Nどうする？", 16)
    S(CARD + 0.15, END, rect(30, 430, 690, 600), "&H2E9AC8&", "&H00&", 16, r"\fad(150,0)\t(0,120,\fscx102\fscy102)")
    E(CARD + 0.15, END, "count", r"{\an4\pos(140,515)\fs50\c&HFFFFFF&\3c&H303030&\bord4\fad(150,0)}名札をはがす", 17)
    E(CARD + 0.35, END, "count", r"{\an5\pos(360,650)\fs44\c&H40E0FF&\3c&H000000&\bord4\fad(150,0)}それとも", 17)
    S(CARD + 0.5, END, rect(30, 700, 690, 870), "&HC07030&", "&H00&", 16, r"\fad(150,0)\t(0,120,\fscx102\fscy102)")
    E(CARD + 0.5, END, "count", r"{\an4\pos(140,785)\fs50\c&HFFFFFF&\3c&H303030&\bord4\fad(150,0)}ユイに聞く", 17)
    E(CARD + 0.8, END, "count", r"{\an5\pos(360,960)\fs50\c&HFFFFFF&\3c&H000000&\bord5\fad(150,0)}コメントで教えて　", 17)
    for st_, en, text, _, _, who in R.LINES:
        if st_ < CARD: E(st_, min(en, CARD), "yui" if text.startswith("…だよね") else who, r"{\an5\pos(360,1040)\fad(60,100)}%s" % text, 9)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

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
def build_sfx():
    add(K.hit(1.0), 0.0, 0.5); add(R.lp(R.noise(1.2), 300) * 0.5, 0.0, 0.2)
    B.deathgame_bgm(add, END, ghosts=(), climax=9.0, win_=99.0, alarm=COUNT, final=(CARD, END), tail=0.0)
    add(sparkle(1.6), KDIS - 0.3, 0.2); add(X.swell(0.6), KDIS - 0.55, 0.3); add(X.braam(2.4, 36.0), KDIS, 0.45)
    add(K.hit(1.2), KDIS + 0.3, 0.6)
    for k in range(3): add(click(0.03, 6000), KDIS + 0.4 + k * 0.06, 0.4)
    add(mix(R.bp(R.noise(0.5), 300, 3000) * R.dec(0.5, 0.2)), 2.75, 0.2)                      # 放送
    add(buzzer(0.7), 5.64, 0.35); add(K.hit(1.2), 5.64, 0.55); add(X.braam(2.4, 30.0), 5.66, 0.4)   # 不正解
    for k, a_ in enumerate((9.25, 10.35, 10.95, 11.5)):                                     # 連鎖脱落
        add(sparkle(1.2), a_ - 0.15, 0.16); add(K.hit(1.0), a_, 0.45 + 0.05 * k)
        for j in range(4): add(click(0.03, 5000 + 400 * j), a_ + 0.05 + j * 0.05, 0.35)
    add(X.swell(1.1), 12.0, 0.35); add(sparkle(1.0), 12.0, 0.12)                            # 自分も光りかける
    add(buzzer(0.45), 13.1, 0.3); add(R.hp(R.noise(0.25), 3000) * R.dec(0.25, 0.08), 13.1, 0.3); add(X.tinnitus(1.4, 5200), 13.15, 0.07)
    add(R.lp(R.kick(70, 35, 0.5, 0.12), 600), 18.2, 0.6)                                    # 16人？
    add(np.sin(2 * np.pi * 1760 * R.tt(0.5)) * R.dec(0.5, 0.15), 20.85, 0.3)                 # カバンがない
    add(X.whip(0.35), 24.2, 0.3); add(K.hit(1.2), 24.4, 0.55); add(X.braam(2.4, 33.0), 24.42, 0.35)   # 13
    add(mix(R.bp(R.noise(0.5), 300, 3000) * R.dec(0.5, 0.2)), 25.15, 0.2)
    add(X.tinnitus(1.6, 4800), 27.5, 0.07)                                                  # …だよね？
    add(X.whip(0.35), 28.4, 0.35); add(X.stinger(1.4), 28.6, 0.4)                           # 真横にユイ
    for k in range(3): add(np.sin(2 * np.pi * 880 * R.tt(0.15)) * R.dec(0.15, 0.06), COUNT + k * (CARD - COUNT) / 3, 0.35)
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
    wav = os.path.join(HERE, "gk2_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "gk2_ui.ass"); build_ui(ass)
    if "--ui" in sys.argv: print("wrote", wav, ass); return
    mp4 = os.path.join(HERE, "gk_ep2a.mp4")
    em = []
    for nm, ch in (("house", "🏷️"), ("globe", "💬"), ("down", "👇")):
        pth = os.path.join(HERE, "gk2_%s.png" % nm); em.append(pth)
        subprocess.run(["python3", "-c", "import s2_endcard as e; e.emoji_png(%r, %r, 160)" % (ch, pth)], check=True, cwd=HERE)
    fc = ("[0:v]vignette=PI/5.5,ass=gk2_ui.ass[v0];"
          "[2:v]scale=110:-1,format=rgba,fade=in:st=%.2f:d=0.15:alpha=1[e1];[3:v]scale=110:-1,format=rgba,fade=in:st=%.2f:d=0.15:alpha=1[e2];[4:v]scale=90:-1,format=rgba,fade=in:st=%.2f:d=0.15:alpha=1[e3];"
          "[v0][e1]overlay=x=60:y=718:enable='gte(t,%.2f)'[v1];[v1][e2]overlay=x=60:y=1123:enable='gte(t,%.2f)'[v2];[v2][e3]overlay=x=860:y=1395:enable='gte(t,%.2f)'[v]"
          % (CARD + 0.15, CARD + 0.5, CARD + 0.8, CARD + 0.15, CARD + 0.5, CARD + 0.8))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(HERE, "frames_GK2_post", "%04d.png"), "-i", wav,
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
