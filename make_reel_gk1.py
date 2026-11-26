"""
make_reel_toki1.py ― 「その罪、時効にさせない」第1話『光る絵の具』（35秒・1080x1920・24fps）
  1) --voice で声（gk1_voice.npy / gk1_lines.json）
  2) create_toki1.py → post_toki1.py で絵
  3) 引数なしで 絵＋声＋効果音＋BGM＋字幕 → gk_ep1.mp4
"""
import os, sys, json, subprocess, wave
import numpy as np
import make_reel as R
import s_sfx as X
import s_bgm as B
import s_hit as K
from gk_lines import GK1 as LINES0
from gk1_timing import *

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
    "riku": (2051283137, 2051283137, 0.0, 1.12, 1.3),     # 教室を出ようとする男子
})
R.VOICE.update({"ren": (0, 0, 1.1, 0.04), "ann": (0, 0, 1.0, 0.2), "yui": (0, 0, 1.1, 0.05), "kaito": (0, 0, 1.1, 0.05), "sae": (0, 0, 1.0, 0.06), "riku": (0, 0, 1.15, 0.03)})
R.SPK_REF_TEXT[:] = ["今日の放課後、少しだけ話せる", "写真、見せてくれる", "ううん、なんでもない", "また明日ね", "窓の外、きれいだね"]
R.LINES = list(LINES0)
R.RETAKE_MIN, R.RETAKES = 0.66, 24
R.VV_READ += [("2年B組", "にねんびーぐみ"), ("準備室", "じゅんびしつ"), ("火事", "かじ"), ("味方", "みかた"), ("13番", "じゅうさんばん"), ("11番", "じゅういちばん"), ("12番", "じゅうにばん"), ("14番", "じゅうよんばん"), ("10秒", "じゅうびょう"), ("透けてる", "すけてる"), ("一緒", "いっしょ"), ("機能", "きのう"), ("削除", "さくじょ"), ("権限", "けんげん"), ("移行", "いこう"), ("異世界", "いせかい"), ("消失", "しょうしつ"), ("登録", "とうろく"), ("1発", "いっぱつ"), ("1票", "いっぴょう"), ("違反", "いはん"), ("3人", "さんにん"), ("規約違反", "きやくいはん"), ("検知", "けんち"), ("管理者", "かんりしゃ")]
VOICE_NPY = os.path.join(HERE, "gk1_voice.npy"); LINES_JSON = os.path.join(HERE, "gk1_lines.json")


STY = (
    "Style: shape,{f},20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n"
    "Style: ren,{f},68,&H00FFFFFF,&H00FFFFFF,&H00202020,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: yui,{f},68,&H00E8D0FF,&H00E8D0FF,&H00502040,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: kaito,{f},68,&H00FFE0B0,&H00FFE0B0,&H00402010,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: riku,{f},70,&H00B0C8FF,&H00B0C8FF,&H00102040,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
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
    # タイトル（小さく、フックの邪魔をしない）
    E(0.3, 2.2, "card", r"{\an8\pos(360,64)\fs28\c&HDDDDDD&\3c&H000000&\bord3\fad(200,300)}学園デスゲーム　{\c&HFFFFFF&\fs40}出席番号13番　{\fs28}第1話", 10)
    # 放送中の表示
    for a, b in ((2.2, 13.0), (32.0, 34.5)):
        E(a, b, "hud", r"{\an7\pos(28,24)\fs26\c&H3030FF&\fad(100,100)}● {\c&HFFFFFF&}校内放送", 7)
    # 脱落の演出（分かりやすい気持ちよさ：赤いスタンプ＋残り人数が減る）
    S(DIS + 0.3, 4.6, rect(0, 470, 720, 730), "&H000000&", "&H60&", 11, r"\fad(80,250)")
    E(DIS + 0.3, 4.6, "count", r"{\an5\pos(360,560)\fs110\c&H2020F0&\3c&HFFFFFF&\bord6\frz-8%s\fad(0,250)}脱落" % pop, 12)
    E(DIS + 0.45, 4.6, "count", r"{\an5\pos(360,690)\fs40\c&HFFFFFF&\3c&H000000&\bord4\fad(120,250)}教室を出た生徒は、{\c&H3030FF&}消える", 12)
    E(1.0, DIS + 0.4, "hud", r"{\an9\pos(700,24)\fs30\c&HFFFFFF&}生存　{\fs40}31{\fs30}／31", 7)
    E(DIS + 0.4, DIS + 0.75, "hud", r"{\an9\pos(700,24)\fs30\c&HFFFFFF&}生存　{\c&H3030FF&\fs52%s}30{\c&HFFFFFF&\fs30}／31" % pop, 7)
    E(DIS + 0.75, CARD, "hud", r"{\an9\pos(700,24)\fs30\c&HFFFFFF&}生存　{\fs40}30{\fs30}／31", 7)
    E(10.55, 13.0, "count", r"{\an5\pos(360,250)\fs40\c&HFFFFFF&\3c&H000000&\bord4\fad(150,150)}ルール：間違えたら、{\c&H3030FF&}消える", 11)
    # 伏線に赤丸（止まった時計 16:44）
    ring = r"{\an7\pos(0,0)\p1\1a&HFF&\3c&H2020F0&\bord7\shad0\fad(80,200)%s}m 360 490 b 443 490 510 557 510 640 b 510 723 443 790 360 790 b 277 790 210 723 210 640 b 210 557 277 490 360 490{\p0}"
    E(13.25, 14.5, "shape", ring % (r"\org(360,640)\fscx150\fscy150\t(0,160,\fscx100\fscy100)"), 12)
    E(13.4, 14.5, "count", r"{\an5\pos(360,850)\fs52\c&HFFFFFF&\3c&H2020F0&\bord5%s\fad(0,200)}16:44" % pop, 12)
    # LINE風の通知（16:44 で止まったスマホ）
    def line(t0, t1, who, msg):
        S(t0, t1, rect(24, 60, 696, 230), "&HF4F4F4&", "&H08&", 12, r"\fad(120,200)\move(0,-120,0,0,0,150)")
        S(t0, t1, rect(44, 80, 84, 120), "&H55C806&", "&H00&", 13, r"\fad(120,200)\move(0,-120,0,0,0,150)")
        E(t0, t1, "card", r"{\an7\pos(96,80)\fs28\c&H303030&\fad(120,200)\move(96,-40,96,80,0,150)}%s" % who, 14)
        E(t0, t1, "card", r"{\an9\pos(676,80)\fs26\c&H808080&\fad(120,200)\move(676,-40,676,80,0,150)}16:44　100%%", 14)
        E(t0, t1, "card", r"{\an7\pos(44,132)\fs30\c&H202020&\fad(120,200)\move(44,12,44,132,0,150)}%s" % msg, 14)
    line(LINE1, 23.2, "母", r"今日はお花、\N何色がいい？")
    # 得票バー：ユイ vs カイト が競り合って同票に
    T0, T1 = TALLY, TALLY + 1.3
    S(T0, CARD, rect(60, 300, 660, 470), "&H000000&", "&H70&", 11, r"\fad(150,150)")
    E(T0, CARD, "card", r"{\an4\pos(80,345)\fs34\c&H40D8FF&\3c&H000000&\bord3\fad(150,150)}ユイに投票", 12)
    E(T0, CARD, "card", r"{\an4\pos(80,425)\fs34\c&HFFB050&\3c&H000000&\bord3\fad(150,150)}カイトに投票", 12)
    seq = [(0, 0), (2, 1), (4, 3), (5, 6), (8, 7), (9, 10), (12, 11), (13, 13), (14, 15), (15, 15)]
    for k, (y_, k_) in enumerate(seq):
        a_ = T0 + 0.15 + k * 0.13; b_ = (T0 + 0.15 + (k + 1) * 0.13) if k + 1 < len(seq) else CARD
        S(a_, b_, rect(290, 330, 290 + y_ * 20, 362), "&H40D8FF&", "&H00&", 12)
        S(a_, b_, rect(290, 410, 290 + k_ * 20, 442), "&HFFB050&", "&H00&", 12)
        E(a_, b_, "card", r"{\an6\pos(645,345)\fs38\c&HFFFFFF&\3c&H000000&\bord3}%d" % y_, 13)
        E(a_, b_, "card", r"{\an6\pos(645,425)\fs38\c&HFFFFFF&\3c&H000000&\bord3}%d" % k_, 13)
    tie = T0 + 0.15 + (len(seq) - 1) * 0.13
    E(tie, 29.6, "count", r"{\an5\pos(360,540)\fs90\c&H20E0FF&\3c&H000000&\bord6\frz6%s\fad(0,200)}同票！" % pop, 13)
    E(32.0, COUNT, "count", r"{\an5\pos(360,540)\fs54\c&HFFFFFF&\3c&H000000&\bord5%s\fad(100,100)}最後の1票は、{\c&H3030FF&}あなた" % pop, 13)
    # 投票まで 3・2・1
    for k in range(3):
        a_ = COUNT + k * (CARD - COUNT) / 3; b_ = COUNT + (k + 1) * (CARD - COUNT) / 3
        E(a_, b_, "count", r"{\an5\pos(360,640)\fs60\c&HFFFFFF&\3c&H000000&\bord5}投票まで{\N}{\c&H3030FF&\fs170%s}%d" % (pop, 3 - k), 11)
    # 2択カード
    S(CARD, END, rect(0, 0, 720, 1280), "&H000000&", "&H50&", 15, r"\fad(250,0)")
    E(CARD, END, "count", r"{\an5\pos(360,330)\fs64\c&HFFFFFF&\3c&H000000&\bord6\fad(200,0)}あなたなら\Nどうする？", 16)
    S(CARD + 0.15, END, rect(30, 430, 690, 600), "&H2E9AC8&", "&H00&", 16, r"\fad(150,0)\t(0,120,\fscx102\fscy102)")
    E(CARD + 0.15, END, "count", r"{\an4\pos(140,500)\fs50\c&HFFFFFF&\3c&H303030&\bord4\fad(150,0)}ユイを信じる", 17)
    E(CARD + 0.15, END, "card", r"{\an4\pos(144,562)\fs28\c&HFFFFFF&\3c&H303030&\bord3\fad(150,0)}（カイトに投票する）", 17)
    E(CARD + 0.35, END, "count", r"{\an5\pos(360,650)\fs44\c&H40E0FF&\3c&H000000&\bord4\fad(150,0)}それとも", 17)
    S(CARD + 0.5, END, rect(30, 700, 690, 870), "&HC07030&", "&H00&", 16, r"\fad(150,0)\t(0,120,\fscx102\fscy102)")
    E(CARD + 0.5, END, "count", r"{\an4\pos(140,770)\fs50\c&HFFFFFF&\3c&H303030&\bord4\fad(150,0)}カイトを信じる", 17)
    E(CARD + 0.5, END, "card", r"{\an4\pos(144,832)\fs28\c&HFFFFFF&\3c&H303030&\bord3\fad(150,0)}（ユイに投票する）", 17)
    E(CARD + 0.8, END, "count", r"{\an5\pos(360,960)\fs50\c&HFFFFFF&\3c&H000000&\bord5\fad(150,0)}コメントで教えて　", 17)
    for st_, en, text, _, _, who in R.LINES:
        if st_ < CARD: E(st_, min(en, CARD), who, r"{\an5\pos(360,1040)\fad(60,100)}%s" % text, 9)
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
def build_sfx():
    add(K.hit(1.0), 0.0, 0.45); add(R.lp(R.noise(1.2), 300) * 0.5, 0.0, 0.2)                # 1コマ目から緊張
    B.deathgame_bgm(add, END, ghosts=(), climax=23.3, win_=99.0, alarm=COUNT, final=(CARD, END), tail=0.0)
    add(R.bp(R.noise(0.45), 200, 1800) * R.dec(0.45, 0.25), DOOR, 0.35, 0.4)                  # 引き戸
    add(mix(R.bp(R.noise(0.5), 300, 3000) * R.dec(0.5, 0.2)), 2.2, 0.2)                      # 放送のスイッチ
    add(X.swell(0.6), DIS - 0.55, 0.3); add(sparkle(1.6), DIS, 0.22); add(X.braam(2.4, 36.0), DIS, 0.45)
    add(K.hit(1.2), DIS + 0.3, 0.6)                                                        # 脱落スタンプ
    for k in range(3): add(click(0.03, 6000), DIS + 0.4 + k * 0.06, 0.4)                    # 残り人数が減る
    add(X.braam(2.4, 33.0), 10.55, 0.35)                                                   # 消えます
    add(X.whip(0.35), 12.75, 0.3); add(np.sin(2 * np.pi * 1760 * R.tt(0.5)) * R.dec(0.5, 0.15), 13.25, 0.3); add(X.tinnitus(1.4, 5200), 13.3, 0.07)
    add(K.hit(0.8), 18.3, 0.3)                                                             # 13番は？（だれも振り向かない）
    add(notif(), LINE1, 0.35)
    add(X.stinger(1.2), 22.0, 0.35); add(X.tinnitus(1.6, 5200), 22.05, 0.08)              # 白い菊
    add(X.whip(0.35), 23.2, 0.35); add(K.hit(1.2), 23.3, 0.6); add(X.braam(2.4, 30.0), 23.32, 0.4)   # いない生徒は、ユイだ
    for k in range(10): add(click(0.03, 4000 + 150 * k), TALLY + 0.15 + k * 0.13, 0.35)    # 得票バー
    add(K.hit(1.0), TALLY + 0.15 + 9 * 0.13, 0.5)                                         # 同票！
    add(X.swell(1.4), 28.9, 0.3)
    add(X.stinger(1.4), 32.0, 0.35)                                                        # 最後の1票は、あなた
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
    wav = os.path.join(HERE, "gk1_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "gk1_ui.ass"); build_ui(ass)
    if "--ui" in sys.argv: print("wrote", wav, ass); return
    mp4 = os.path.join(HERE, "gk_ep1.mp4")
    em = []
    for nm, ch in (("house", "🤝"), ("globe", "👉"), ("down", "👇")):
        pth = os.path.join(HERE, "gk1_%s.png" % nm); em.append(pth)
        subprocess.run(["python3", "-c", "import s2_endcard as e; e.emoji_png(%r, %r, 160)" % (ch, pth)], check=True, cwd=HERE)
    fc = ("[0:v]vignette=PI/5.5,ass=gk1_ui.ass[v0];"
          "[2:v]scale=110:-1,format=rgba,fade=in:st=%.2f:d=0.15:alpha=1[e1];[3:v]scale=110:-1,format=rgba,fade=in:st=%.2f:d=0.15:alpha=1[e2];[4:v]scale=90:-1,format=rgba,fade=in:st=%.2f:d=0.15:alpha=1[e3];"
          "[v0][e1]overlay=x=60:y=718:enable='gte(t,%.2f)'[v1];[v1][e2]overlay=x=60:y=1123:enable='gte(t,%.2f)'[v2];[v2][e3]overlay=x=860:y=1395:enable='gte(t,%.2f)'[v]"
          % (CARD + 0.15, CARD + 0.5, CARD + 0.8, CARD + 0.15, CARD + 0.5, CARD + 0.8))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(HERE, "frames_GK1_post", "%04d.png"), "-i", wav,
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
