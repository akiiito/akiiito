"""
make_reel_block5.py ― ブロック世界・単体回『触れたら影になる』（35秒・前回を知らなくても分かる1本・1080x1920/24fps）
  1) --voice で声だけ先に作る（blk5_voice.npy / blk5_lines.json）
  2) create_block5.py で絵（24fps）→ post_block5.py で光のにじみ・光の筋
  3) 引数なしで 絵＋声＋効果音＋BGM＋字幕＋最小限のUI → block_hikari.mp4
"""
import os, sys, json, math, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R
import s_sfx as X
import s_bgm as B
MEID = int(os.environ.get("MEID", "1368642336"))
from block_lines import SOLO1 as LINES0
from blk5_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
FR = os.path.join(HERE, "frames_BLK5_post")
DUR = END
TAIL = 0.6
R.DUR = DUR
R.MIX = np.zeros((R.n_(DUR) + SR, 2))
add = R.add
R.VV_CAST.update({
    "ruka": (1325133120, 1325133120, 0.0, 1.05, 1.15),     # 花音（ルカ）
    "me":   (MEID, MEID, 0.0, 0.98, 1.0),                    # 自分（男）
})
R.VOICE.update({"ruka": (0, 0, 1.1, 0.04), "me": (0, 0, 1.1, 0.04)})
R.SPK_REF_TEXT[:] = ["今日の放課後、少しだけ話せる", "写真、見せてくれる", "ううん、なんでもない", "また明日ね", "窓の外、きれいだね"]
R.LINES = list(LINES0)
R.RETAKE_MIN, R.RETAKES = 0.63, 10
R.VV_READ += [("指先", "ゆびさき"), ("黒く", "くろく")]
VOICE_NPY = os.path.join(HERE, "blk5_voice.npy"); LINES_JSON = os.path.join(HERE, "blk5_lines.json")

def rr(x0, y0, x1, y1, r):
    k = 0.45 * r
    return ("m %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d"
            % (x0 + r, y0, x1 - r, y0, x1 - r + k, y0, x1, y0 + r - k, x1, y0 + r, x1, y1 - r, x1, y1 - r + k, x1 - r + k, y1, x1 - r, y1,
               x0 + r, y1, x0 + r - k, y1, x0, y1 - r + k, x0, y1 - r, x0, y0 + r, x0, y0 + r - k, x0 + r - k, y0, x0 + r, y0))

STY = (
    "Style: shape,{f},20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n"
    "Style: ruka,{f},44,&H00FFFFFF,&H00FFFFFF,&H008A3CE8,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: me,{f},44,&H00FFFFFF,&H00FFFFFF,&H00306A9A,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: hook,{f},58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,7,0,5,20,20,0,1\n"
    "Style: card,{f},44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,0,0,5,20,20,0,1\n"
    "Style: count,{f},84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,8,0,5,0,0,0,1\n")

def shadow_at(t):
    """自分の影化（%）：97 → ルカの手で 12"""
    if t < GLOW0: return 97.0
    if t < GLOW1: return 97.0 - 85.0 * ((t - GLOW0) / (GLOW1 - GLOW0)) ** 0.8
    return 12.0

def build_ui(path):
    ev = []
    def E(t0, t1, style, text, layer=5):
        if t1 > t0: ev.append("Dialogue: %d,%s,%s,%s,,0,0,0,,%s" % (layer, R.ts(t0), R.ts(t1), style, text))
    def S(t0, t1, draw, col, alpha="&H00&", layer=4, extra=""):
        E(t0, t1, "shape", r"{\an7\pos(0,0)\p1\1c%s\1a%s\bord0\shad0%s}%s{\p0}" % (col, alpha, extra, draw), layer)
    pop = r"\fscx40\fscy40\t(0,120,\fscx112\fscy112)\t(120,220,\fscx100\fscy100)"
    # 冒頭のひとこと（前回を知らなくても分かる）
    E(0.0, 2.9, "hook", r"{\an5\pos(360,250)\fs56\fad(0,200)%s}触れたら、{\c&H4040FF&}影{\c&HFFFFFF&}になる世界。" % pop, 9)
    E(0.9, 2.9, "card", r"{\an5\pos(360,330)\fs36\c&HE0E0E0&\bord3\3c&H000000&\fad(150,200)}それでも彼女は、手を握った", 9)
    # 影化ゲージ（左上・1本だけ）
    X0, X1, Y0, Y1 = 96, 330, 30, 56
    S(0, TIP, rr(16, 18, 352, 68, 14), "&H100810&", "&H40&", 6, r"\fad(0,300)")
    E(0, TIP, "card", r"{\an4\pos(28,43)\fs24\c&HFF80D0&\fad(0,300)}影化", 8)
    S(0, TIP, "m %d %d l %d %d l %d %d l %d %d" % (X0, Y0, X1, Y0, X1, Y1, X0, Y1), "&H302030&", "&H00&", 6, r"\fad(0,300)")
    t = 0.0; step = 1 / 12
    while t < TIP:
        v = shadow_at(t); w = int((X1 - X0) * v / 100)
        col = "&H6020FF&" if v > 90 else ("&H70C0FF&" if t < GLOW1 + 0.4 else "&H60E0FF&")
        if v > 90 and int(t * 4) % 2: col = "&H3010C0&"
        S(t, t + step, "m %d %d l %d %d l %d %d l %d %d" % (X0, Y0, X0 + w, Y0, X0 + w, Y1, X0, Y1), col, "&H00&", 7)
        E(t, t + step, "card", r"{\an6\pos(340,44)\fs22\c&HFFFFFF&\bord2\3c&H000000&}%d%%" % int(round(v)), 9)
        t += step
    E(GLOW1 - 0.4, GLOW1 + 1.6, "count", r"{\an5\pos(360,400)\fs64\c&HFFFFFF&\3c&H303030&\bord6%s}影化 {\c&H6020FF&}97%%{\c&HFFFFFF&} → {\c&H60E0FF&}12%%" % pop, 11)
    # 最後の一文
    S(FIN, END, "m 0 0 l 720 0 l 720 1280 l 0 1280", "&H000000&", "&HA0&", 3, r"\fad(500,0)")
    E(FIN + 0.1, END, "count", r"{\an5\pos(360,520)\fs52\c&HFFFFFF&\3c&H000000&\bord5\fad(400,0)}影は、消えたんじゃない。", 11)
    E(FIN + 1.3, END, "count", r"{\an5\pos(360,610)\fs60\c&HFFB0F0&\3c&H400040&\bord6\fad(300,0)}ルカに、移っただけ。", 11)
    E(END - 1.6, END, "card", r"{\an5\pos(360,740)\fs34\c&HFFFFFF&\bord3\3c&H000000&\fad(200,0)}ルカを助けたい人は", 11)
    E(END - 1.6, END, "card", r"{\an5\pos(360,895)\fs34\c&HFFFFFF&\bord3\3c&H000000&\fad(200,0)}でコメントしてね", 11)
    # 上端の進行バー
    S(0, END, "m 0 0 l 720 0 l 720 6 l 0 6", "&H60D0FF&", "&H00&", 12, r"\clip(0,0,0,6)\t(0,%d,\clip(0,0,720,6))" % int(END * 1000))
    for st, en, text, _, _, who in R.LINES:
        E(st, en, who, r"{\an5\pos(360,1010)\fad(60,100)}%s" % text, 9)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

def build_sfx():
    B.block_hikari(add, DUR, GRAB, GLOW0, WAVE, TIP, HIDE, FIN, tail=TAIL)
    add(X.braam(2.4, 41.0), 0.05, 0.3)
    hb = R.heartbeat()
    t = 0.3
    while t < GRAB: add(hb, t, 0.42); t += 0.62 - 0.02 * t
    add(R.whoosh(0.4, 300, 1400), GRAB - 0.25, 0.25); add(R.lp(R.kick(80, 40, 0.2, 0.05), 600), GRAB, 0.3)
    add(X.swell(2.0), GLOW0 - 0.6, 0.35)
    if hasattr(R, "sparkle"): add(R.sparkle(1.5), GLOW0 + 0.4, 0.25)
    add(X.swell(1.6), WAVE - 1.5, 0.4); add(R.boom(3.0), WAVE, 0.55); add(R.whoosh(1.6, 500, 4000), WAVE, 0.35)
    for k in range(10): add(R.lp(R.noise(0.2), 4000) * R.dec(0.2, 0.06), WAVE + 0.5 + k * 0.35, 0.18, 0.5 * (-1) ** k)
    add(X.stinger(1.4), TIP + 1.2, 0.3); add(X.tinnitus(2.6, 3600), TIP + 1.3, 0.22)
    add(X.stinger(1.4), FIN + 1.3, 0.22)

def main():
    if "--voice" in sys.argv:
        R.build_voice()
        np.save(VOICE_NPY, R.MIX)
        json.dump([list(l) for l in R.LINES], open(LINES_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("wrote", VOICE_NPY, LINES_JSON); return
    R.LINES = [tuple(l) for l in json.load(open(LINES_JSON, encoding="utf-8"))]
    voice = np.load(VOICE_NPY)
    voice = np.concatenate([voice, np.zeros((max(0, R.n_(DUR + TAIL + 1) - len(voice)), 2))])
    R.MIX = np.zeros_like(voice); build_sfx()
    R.MIX = voice + X.duck(R.MIX, voice)
    out = R.MIX[: R.n_(DUR + TAIL)].copy()
    out[-R.n_(0.8):] *= np.linspace(1, 0, R.n_(0.8))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "blk5_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "blk5_ui.ass"); build_ui(ass)
    if "--ui" in sys.argv: print("wrote", wav, ass); return
    mp4 = os.path.join(HERE, "block_hikari.mp4")
    fire = os.path.join(HERE, "blk5_fire.png")                                  # 絵文字はカラーで（字幕フォントだと白黒になる）
    subprocess.run(["python3", "-c", "import s2_endcard as e; e.emoji_png('🔥', %r, 150)" % fire], check=True, cwd=HERE)
    grade = ("[0:v]vignette=PI/5.5,eq=contrast=1.03:saturation=1.06,ass=blk5_ui.ass[v];[2:v]scale=120:-1,format=rgba,fade=in:st=%.2f:d=0.2:alpha=1[f];"
             "[v][f]overlay=x=(W-w)/2:y=1215-h/2:enable='gte(t,%.2f)'" % (END - 1.6, END - 1.6))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(FR, "%04d.png"), "-i", wav,
                    "-loop", "1", "-framerate", str(FPS), "-i", fire, "-filter_complex", grade,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "slow", "-maxrate", "14M", "-bufsize", "28M",
                    "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-t", "%.3f" % DUR,
                    "-shortest", "-movflags", "+faststart", mp4], check=True, cwd=HERE)
    print("wrote", mp4)

if __name__ == "__main__":
    main()
