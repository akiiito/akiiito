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
})
R.VOICE.update({"ren": (0, 0, 1.1, 0.04), "ann": (0, 0, 1.0, 0.2), "yui": (0, 0, 1.1, 0.05), "kaito": (0, 0, 1.1, 0.05), "sae": (0, 0, 1.0, 0.06)})
R.SPK_REF_TEXT[:] = ["今日の放課後、少しだけ話せる", "写真、見せてくれる", "ううん、なんでもない", "また明日ね", "窓の外、きれいだね"]
R.LINES = list(LINES0)
R.RETAKE_MIN, R.RETAKES = 0.66, 24
R.VV_READ += [("2年B組", "にねんびーぐみ"), ("準備室", "じゅんびしつ"), ("火事", "かじ"), ("味方", "みかた"), ("13番", "じゅうさんばん"), ("11番", "じゅういちばん"), ("12番", "じゅうにばん"), ("14番", "じゅうよんばん"), ("10秒", "じゅうびょう"), ("透けてる", "すけてる"), ("一緒", "いっしょ"), ("機能", "きのう"), ("削除", "さくじょ"), ("権限", "けんげん"), ("移行", "いこう"), ("異世界", "いせかい"), ("消失", "しょうしつ"), ("登録", "とうろく"), ("1発", "いっぱつ"), ("3人", "さんにん"), ("規約違反", "きやくいはん"), ("検知", "けんち"), ("管理者", "かんりしゃ")]
VOICE_NPY = os.path.join(HERE, "gk1_voice.npy"); LINES_JSON = os.path.join(HERE, "gk1_lines.json")


STY = (
    "Style: shape,{f},20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n"
    "Style: ren,{f},68,&H00FFFFFF,&H00FFFFFF,&H00202020,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: yui,{f},68,&H00E8D0FF,&H00E8D0FF,&H00502040,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: kaito,{f},68,&H00FFE0B0,&H00FFE0B0,&H00402010,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
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
    # タイトル
    E(0.6, 3.0, "card", r"{\an8\pos(360,70)\fs30\c&HDDDDDD&\3c&H000000&\bord3\fad(300,300)}学園デスゲーム", 10)
    E(0.6, 3.0, "count", r"{\an8\pos(360,112)\fs56\c&HFFFFFF&\3c&H000000&\bord5\fad(300,300)}出席番号13番　{\fs34}第1話", 10)
    # 放送中の表示
    for a, b in ((2.8, 11.0), (28.2, 29.6)):
        E(a, b, "hud", r"{\an7\pos(28,24)\fs26\c&H3030FF&\fad(100,100)}● {\c&HFFFFFF&}校内放送", 7)
    E(7.4, 11.0, "count", r"{\an5\pos(360,250)\fs40\c&HFFFFFF&\3c&H000000&\bord4\fad(150,150)}ルール：間違えたら、{\c&H3030FF&}消える", 11)
    # LINE風の通知（16:44 で止まったスマホ）
    def line(t0, t1, who, msg):
        S(t0, t1, rect(24, 60, 696, 230), "&HF4F4F4&", "&H08&", 12, r"\fad(120,200)\move(0,-120,0,0,0,150)")
        S(t0, t1, rect(44, 80, 84, 120), "&H55C806&", "&H00&", 13, r"\fad(120,200)\move(0,-120,0,0,0,150)")
        E(t0, t1, "card", r"{\an7\pos(96,80)\fs28\c&H303030&\fad(120,200)\move(96,-40,96,80,0,150)}%s" % who, 14)
        E(t0, t1, "card", r"{\an9\pos(676,80)\fs26\c&H808080&\fad(120,200)\move(676,-40,676,80,0,150)}16:44　100%%", 14)
        E(t0, t1, "card", r"{\an7\pos(44,132)\fs30\c&H202020&\fad(120,200)\move(44,12,44,132,0,150)}%s" % msg, 14)
    line(LINE1, 20.2, "母", r"今日はお花、\N何色がいい？")
    # 投票まで10秒
    E(COUNT, CARD, "count", r"{\an5\pos(360,300)\fs44\c&HFFFFFF&\3c&H000000&\bord5%s}投票まで　{\c&H3030FF&\fs80}10" % pop, 11)
    # 2択カード
    S(CARD, END, rect(0, 0, 720, 1280), "&H000000&", "&H50&", 15, r"\fad(250,0)")
    E(CARD, END, "count", r"{\an5\pos(360,330)\fs64\c&HFFFFFF&\3c&H000000&\bord6\fad(200,0)}あなたなら\Nどうする？", 16)
    S(CARD + 0.15, END, rect(30, 430, 690, 600), "&H2E9AC8&", "&H00&", 16, r"\fad(150,0)\t(0,120,\fscx102\fscy102)")
    E(CARD + 0.15, END, "count", r"{\an4\pos(140,515)\fs50\c&HFFFFFF&\3c&H303030&\bord4\fad(150,0)}ユイを信じる", 17)
    E(CARD + 0.35, END, "count", r"{\an5\pos(360,650)\fs44\c&H40E0FF&\3c&H000000&\bord4\fad(150,0)}それとも", 17)
    S(CARD + 0.5, END, rect(30, 700, 690, 870), "&HC07030&", "&H00&", 16, r"\fad(150,0)\t(0,120,\fscx102\fscy102)")
    E(CARD + 0.5, END, "count", r"{\an4\pos(140,785)\fs50\c&HFFFFFF&\3c&H303030&\bord4\fad(150,0)}カイトを信じる", 17)
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
def build_sfx():
    chime(0.15)
    add(R.lp(R.noise(1.2), 300) * 0.5, 0.0, 0.2)
    add(mix(R.bp(R.noise(0.5), 300, 3000) * R.dec(0.5, 0.2)), 2.65, 0.25)                 # 放送のスイッチ
    B.deathgame_bgm(lambda x, at, g=1.0, pan=0.0: add(x, at + 3.0, g, pan), END - 3.0, ghosts=(), climax=20.6 - 3.0, win_=99.0,
                    alarm=COUNT - 3.0, final=(CARD - 3.0, END - 3.0), tail=0.0)
    add(X.braam(2.4, 33.0), 9.6, 0.35)                                                    # 消えます
    add(K.hit(0.8), 14.1, 0.3)                                                            # 13番は？（だれも振り向かない）
    add(notif(), LINE1, 0.35)
    add(X.stinger(1.2), 18.25, 0.35); add(X.tinnitus(2.0, 5200), 18.3, 0.08)              # 白い菊
    add(K.hit(1.2), 20.6, 0.6); add(X.braam(2.4, 30.0), 20.62, 0.4)                       # いない生徒は、ユイだ
    add(X.swell(1.4), 24.9, 0.3)
    for k in range(4): add(click(0.04, 5000), COUNT + 0.1 + k * 0.4, 0.5)
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
