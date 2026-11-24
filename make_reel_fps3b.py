"""
make_reel_toki1.py ― 「その罪、時効にさせない」第1話『光る絵の具』（35秒・1080x1920・24fps）
  1) --voice で声（fps3b_voice.npy / fps3b_lines.json）
  2) create_toki1.py → post_toki1.py で絵
  3) 引数なしで 絵＋声＋効果音＋BGM＋字幕 → fps_ep3b.mp4
"""
import os, sys, json, subprocess, wave
import numpy as np
import make_reel as R
import s_sfx as X
import s_bgm as B
import s_hit as K
from fps_lines import EP3B as LINES0
from fps3b_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
DUR = END; TAIL = 0.0
R.DUR = DUR; R.MIX = np.zeros((R.n_(DUR) + SR, 2)); add = R.add
R.VV_CAST.update({
    "ren": (1368642336, 1368642336, 0.0, 1.0, 1.0),       # レン（M2）
    "ann": (345585728, 345585728, 0.0, 0.95, 0.9),        # アナウンス（るな）
    "mina": (1878365376, 1878365376, 0.0, 1.0, 1.15),     # ミナ（コハク）
})
R.VOICE.update({"ren": (0, 0, 1.1, 0.04), "ann": (0, 0, 1.0, 0.18), "mina": (0, 0, 1.1, 0.06)})
R.SPK_REF_TEXT[:] = ["今日の放課後、少しだけ話せる", "写真、見せてくれる", "ううん、なんでもない", "また明日ね", "窓の外、きれいだね"]
R.LINES = list(LINES0)
R.RETAKE_MIN, R.RETAKES = 0.66, 24
R.VV_READ += [("透けてる", "すけてる"), ("一緒", "いっしょ"), ("機能", "きのう"), ("削除", "さくじょ"), ("権限", "けんげん"), ("移行", "いこう"), ("異世界", "いせかい"), ("消失", "しょうしつ"), ("登録", "とうろく"), ("1発", "いっぱつ"), ("3人", "さんにん"), ("規約違反", "きやくいはん"), ("検知", "けんち"), ("管理者", "かんりしゃ")]
VOICE_NPY = os.path.join(HERE, "fps3b_voice.npy"); LINES_JSON = os.path.join(HERE, "fps3b_lines.json")


STY = (
    "Style: shape,{f},20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n"
    "Style: ren,{f},68,&H00FFFFFF,&H00FFFFFF,&H00202020,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: mina,{f},68,&H00E0C8FF,&H00E0C8FF,&H00402040,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
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
    # 前回の選択
    S(0, 1.7, rect(0, 130, 720, 250), "&H000000&", "&H50&", 9, r"\fad(0,200)")
    E(0, 1.7, "card", r"{\an5\pos(360,165)\fs28\c&HDDDDDD&\fad(0,200)}前回、あなたは――", 10)
    E(0, 1.7, "count", r"{\an5\pos(360,215)\fs48\c&H3070FF&\3c&H000000&\bord5%s\fad(0,200)}「撃ち返す」を選んだ" % pop, 10)
    # HUD
    t = 0.0; step = 1 / 8
    while t < CARD:
        if not (HIT <= t < 3.1):
            d = 99 if t < WHITE else 100
            E(t, t + step, "hud", r"{\an9\pos(692,24)\fs24\c&HFFFFFF&}異常検知 {\c&H3030FF&\fs30}%d%%" % d, 7)
            E(t, t + step, "hud", r"{\an3\pos(692,1250)\fs34\c&HFFFFFF&}残弾 {\c&H3030FF&\fs52}0{\c&HFFFFFF&\fs30}/1", 7)
            if t >= 14.7: E(t, t + step, "hud", r"{\an7\pos(28,24)\fs26\c&HFFFFFF&}権限：{\c&H40F0FF&}管理者", 7)
        t += step
    E(3.2, 6.6, "count", r"{\an5\pos(360,300)\fs40\c&HFFFFFF&\3c&H000000&\bord4\fad(150,150)}⚠ 世界の終了まで 残り 60秒", 11)
    # LINE風の通知（現実からのメッセージ）
    def line(t0, t1, who, msg):
        S(t0, t1, rect(24, 60, 696, 230), "&HF4F4F4&", "&H08&", 12, r"\fad(120,200)\move(0,-120,0,0,0,150)")
        S(t0, t1, rect(44, 80, 84, 120), "&H55C806&", "&H00&", 13, r"\fad(120,200)\move(0,-120,0,0,0,150)")
        E(t0, t1, "card", r"{\an7\pos(96,80)\fs28\c&H303030&\fad(120,200)\move(96,-40,96,80,0,150)}%s" % who, 14)
        E(t0, t1, "card", r"{\an7\pos(44,132)\fs30\c&H202020&\fad(120,200)\move(44,12,44,132,0,150)}%s" % msg, 14)
    line(LINE1, 10.6, "母", r"さっきから、あなたの部屋で\N銃声がするんだけど")
    line(LINE2, 21.6, "妹", r"お兄ちゃん、パソコンの画面の中に\Nいるの、お兄ちゃんだよね？")
    line(LINE3, CARD, "妹", "帰ってきて")
    E(14.7, 17.0, "count", r"{\an5\pos(360,320)\fs46\c&H40F0FF&\3c&H000000&\bord5%s}新しい管理者：あなた" % pop, 11)
    # 2択カード（参考の形：黄と青、それとも、コメントで教えて）
    S(CARD, END, rect(0, 0, 720, 1280), "&H000000&", "&H70&", 15, r"\fad(250,0)")
    E(CARD, END, "count", r"{\an5\pos(360,330)\fs64\c&HFFFFFF&\3c&H000000&\bord6\fad(200,0)}あなたなら\Nどうする？", 16)
    S(CARD + 0.15, END, rect(30, 430, 690, 600), "&H2E9AC8&", "&H00&", 16, r"\fad(150,0)\t(0,120,\fscx102\fscy102)")
    E(CARD + 0.15, END, "count", r"{\an4\pos(140,515)\fs46\c&HFFFFFF&\3c&H303030&\bord4\fad(150,0)}世界を閉じて\N現実に帰る", 17)
    E(CARD + 0.35, END, "count", r"{\an5\pos(360,650)\fs44\c&H40E0FF&\3c&H000000&\bord4\fad(150,0)}それとも", 17)
    S(CARD + 0.5, END, rect(30, 700, 690, 870), "&HC07030&", "&H00&", 16, r"\fad(150,0)\t(0,120,\fscx102\fscy102)")
    E(CARD + 0.5, END, "count", r"{\an4\pos(140,785)\fs46\c&HFFFFFF&\3c&H303030&\bord4\fad(150,0)}世界を残して\Nここに留まる", 17)
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
def build_sfx():
    B.deathgame_bgm(add, DUR, ghosts=(), climax=14.7, win_=99.0, alarm=CHOICE, final=(CHOICE + 0.5, CARD), tail=TAIL)
    add(K.suck(0.6), FIRE - 0.6, 0.4); add(gunshot(), FIRE, 1.0); add(K.whoosh(0.8, 800, 9000), FIRE + 0.05, 0.4)
    K.strike(add, HIT, 1.4, 0.0, False); add(K.crumble(1.4, 30), HIT + 0.05, 0.5); add(mix(np.sin(2 * np.pi * 3800 * R.tt(0.4)) * R.dec(0.4, 0.1)), HIT, 0.15)
    add(X.braam(2.6, 33.0), DELETE, 0.45)
    for k in range(16): add(mix(R.bp(R.noise(0.25), 1500, 7000) * R.dec(0.25, 0.08)), DELETE + 0.6 + k * 1.2, 0.12, 0.6 * (-1) ** k)   # 消えていく音
    add(K.whoosh(0.5, 400, 4000), MINA, 0.3)
    for t_ in (LINE1, LINE2, LINE3): add(notif(), t_, 0.35)
    add(X.swell(2.0), 14.7, 0.35); add(X.tinnitus(2.6, 5000), 15.6, 0.1)
    add(click(0.08, 3000), AIM + 0.2, 0.5); add(X.stinger(1.2), AIM + 0.2, 0.3)
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
    wav = os.path.join(HERE, "fps3b_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "fps3b_ui.ass"); build_ui(ass)
    if "--ui" in sys.argv: print("wrote", wav, ass); return
    mp4 = os.path.join(HERE, "fps_ep3b.mp4")
    em = []
    for nm, ch in (("house", "🏠"), ("globe", "🌍"), ("down", "👇")):
        pth = os.path.join(HERE, "fps3b_%s.png" % nm); em.append(pth)
        subprocess.run(["python3", "-c", "import s2_endcard as e; e.emoji_png(%r, %r, 160)" % (ch, pth)], check=True, cwd=HERE)
    fc = ("[0:v]vignette=PI/5.5,ass=fps3b_ui.ass[v0];"
          "[2:v]scale=110:-1,format=rgba,fade=in:st=%.2f:d=0.15:alpha=1[e1];[3:v]scale=110:-1,format=rgba,fade=in:st=%.2f:d=0.15:alpha=1[e2];[4:v]scale=90:-1,format=rgba,fade=in:st=%.2f:d=0.15:alpha=1[e3];"
          "[v0][e1]overlay=x=60:y=718:enable='gte(t,%.2f)'[v1];[v1][e2]overlay=x=60:y=1123:enable='gte(t,%.2f)'[v2];[v2][e3]overlay=x=860:y=1395:enable='gte(t,%.2f)'[v]"
          % (CARD + 0.15, CARD + 0.5, CARD + 0.8, CARD + 0.15, CARD + 0.5, CARD + 0.8))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(HERE, "frames_FPS3B_final", "%04d.png"), "-i", wav,
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
