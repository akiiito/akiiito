"""
make_reel_block5.py ― ブロック世界・単体回『触れたら影になる』（35秒・前回を知らなくても分かる1本・1080x1920/24fps）
  1) --voice で声だけ先に作る（blk6_voice.npy / blk6_lines.json）
  2) create_block5.py で絵（24fps）→ post_block5.py で光のにじみ・光の筋
  3) 引数なしで 絵＋声＋効果音＋BGM＋字幕＋最小限のUI → block_final.mp4
"""
import os, sys, json, math, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R
import s_sfx as X
import s_bgm as B
import s_hit as K
MEID = int(os.environ.get("MEID", "1368642336"))
from block_lines import FINAL as LINES0
from blk6_timing import *
import blk6_timing as BT
for _k in ("CLENCH", "PILLARS", "PHIT", "SWING", "SMASH", "SWORD", "SLASH", "CATCH", "JOIN", "SWARM", "DOMAIN", "RISE", "FHIT", "SUN", "FADEG", "DAWN", "TITLE", "WAVE"):
    globals()[_k] = BT.out_t(getattr(BT, _k))
END = BT.END_OUT
LINES0 = [(BT.out_t(a), BT.out_t(b)) + tuple(r) for a, b, *r in LINES0]

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
FR = os.path.join(HERE, "frames_BLK6_cut")
DUR = END
TAIL = 0.6
R.DUR = DUR
R.MIX = np.zeros((R.n_(DUR) + SR, 2))
add = R.add
R.VV_CAST.update({
    "ruka": (1325133120, 1325133120, 0.0, 1.05, 1.15),     # 花音（ルカ）
    "me":   (MEID, MEID, 0.0, 0.98, 1.0),                    # 自分（男）
    "giant": (1143949696, 1143949696, -0.03, 0.92, 1.0),     # 影の巨人（前の召喚者）
})
R.VOICE.update({"ruka": (0, 0, 1.1, 0.04), "me": (0, 0, 1.1, 0.04), "giant": (0, 0, 1.2, 0.25)})
R.SPK_REF_TEXT[:] = ["今日の放課後、少しだけ話せる", "写真、見せてくれる", "ううん、なんでもない", "また明日ね", "窓の外、きれいだね"]
R.LINES = list(LINES0)
R.RETAKE_MIN, R.RETAKES = 0.65, 24
R.VV_READ += [("構築", "こうちく"), ("千本柱", "せんぼんばしら"), ("大剣", "たいけん"), ("天穿つ拳", "てんうがつこぶし"), ("上等", "じょうとう")]
VOICE_NPY = os.path.join(HERE, "blk6_voice.npy"); LINES_JSON = os.path.join(HERE, "blk6_lines.json")

def rr(x0, y0, x1, y1, r):
    k = 0.45 * r
    return ("m %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d"
            % (x0 + r, y0, x1 - r, y0, x1 - r + k, y0, x1, y0 + r - k, x1, y0 + r, x1, y1 - r, x1, y1 - r + k, x1 - r + k, y1, x1 - r, y1,
               x0 + r, y1, x0 + r - k, y1, x0, y1 - r + k, x0, y1 - r, x0, y0 + r, x0, y0 + r - k, x0 + r - k, y0, x0 + r, y0))

STY = (
    "Style: shape,{f},20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n"
    "Style: ruka,{f},70,&H00FFFFFF,&H00FFFFFF,&H008A3CE8,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: me,{f},70,&H00FFFFFF,&H00FFFFFF,&H00306A9A,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: giant,{f},70,&H00B0B0FF,&H00B0B0FF,&H00100040,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: hook,{f},58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,7,0,5,20,20,0,1\n"
    "Style: card,{f},44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,0,0,5,20,20,0,1\n"
    "Style: count,{f},84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,8,0,5,0,0,0,1\n")

def blk_at(t):
    if t < CLENCH: return 0.35
    if t < FHIT: return 0.35 + 0.55 * min(1, max(0, (t - CLENCH) / 2.0)) ** 1
    x = min(1, max(0, (t - FHIT - 1.0) / 6.0)); return 0.9 - 0.85 * x * x * (3 - 2 * x)

def build_ui(path):
    ev = []
    def E(t0, t1, style, text, layer=5):
        if t1 > t0: ev.append("Dialogue: %d,%s,%s,%s,,0,0,0,,%s" % (layer, R.ts(t0), R.ts(t1), style, text))
    def S(t0, t1, draw, col, alpha="&H00&", layer=4, extra=""):
        E(t0, t1, "shape", r"{\an7\pos(0,0)\p1\1c%s\1a%s\bord0\shad0%s}%s{\p0}" % (col, alpha, extra, draw), layer)
    pop = r"\fscx125\fscy125\t(0,140,\fscx100\fscy100)"
    S(0, 2.9, "m 0 90 l 720 90 l 720 320 l 0 320", "&H000000&", "&H60&", 8, r"\fad(0,200)")
    E(0, 2.9, "hook", r"{\an5\pos(360,165)\fs54\bord7%s\fad(0,200)}触れたら、{\c&H4040FF&}影{\c&HFFFFFF&}になる世界。" % pop, 10)
    E(0.2, 2.9, "hook", r"{\an5\pos(360,262)\fs76\c&H3030FF&\3c&H000000&\bord8%s\fad(0,200)}最終話" % pop, 10)
    # 影化ゲージ
    X0, X1, Y0, Y1 = 96, 330, 30, 56
    S(0, DAWN + 2.5, rr(16, 18, 352, 68, 14), "&H100810&", "&H40&", 6, r"\fad(0,300)")
    E(0, DAWN + 2.5, "card", r"{\an4\pos(28,43)\fs24\c&HFF80D0&\fad(0,300)}影化", 8)
    S(0, DAWN + 2.5, "m %d %d l %d %d l %d %d l %d %d" % (X0, Y0, X1, Y0, X1, Y1, X0, Y1), "&H302030&", "&H00&", 6, r"\fad(0,300)")
    t = 0.0; step = 1 / 12
    while t < DAWN + 2.5:
        v = 100 * blk_at(t) + (9 if DOMAIN <= t < FHIT else 0); w = int((X1 - X0) * min(v, 100) / 100)
        col = "&H6020FF&" if v > 80 else ("&H70C0FF&" if v > 40 else "&H60E0FF&")
        if v > 95 and int(t * 6) % 2: col = "&HFFFFFF&"
        S(t, t + step, "m %d %d l %d %d l %d %d l %d %d" % (X0, Y0, X0 + w, Y0, X0 + w, Y1, X0, Y1), col, "&H00&", 7)
        E(t, t + step, "card", r"{\an6\pos(340,44)\fs22\c&HFFFFFF&\bord2\3c&H000000&}%d%%" % int(round(min(v, 99))), 9)
        t += step
    # 技名（大きく・墨のふち）
    def tech(t0, text, sub, col="&HFFFFFF&", y=520, d=1.3):
        st = r"\fscx180\fscy180\t(0,120,\fscx100\fscy100)\t(%d,%d,\alpha&HFF&)" % (int(d * 1000) - 250, int(d * 1000))
        E(t0, t0 + d, "count", r"{\an5\pos(360,%d)\fs40\c&HDDDDDD&\bord4\3c&H000000&%s}%s" % (y - 85, st, sub), 13)
        E(t0, t0 + d, "count", r"{\an5\pos(360,%d)\fs110\c%s\3c&H000000&\bord11\shad0%s}%s" % (y, col, st, text), 13)
    tech(PILLARS - 0.05, "千本柱", "構築――", "&HFFE0A0&")
    tech(SWORD + 0.05, "大剣", "構築――", "&HFFE0A0&")
    tech(RISE - 0.05, "天穿つ拳", "光影合一――", "&H40C8FF&", 470, 1.5)
    def boom(t0, text, x, y, fs, rot, col="&H30D0FF&", d=0.75):
        st = r"\frz%d\fscx240\fscy240\t(0,90,\fscx100\fscy100)\t(%d,%d,\fscx110\fscy110\alpha&HFF&)" % (rot, int(d * 1000) - 200, int(d * 1000))
        E(t0, t0 + d, "count", r"{\an5\pos(%d,%d)\fs%d\c%s\3c&H101010&\bord9\shad0%s}%s" % (x, y, fs, col, st, text), 14)
    boom(PHIT, "ズドドドッ！", 380, 300, 100, -8)
    boom(SMASH, "ドゴォン！！", 360, 760, 120, 6, "&H2040FF&", 0.9)
    boom(SLASH, "ザンッ！", 470, 330, 130, -14, "&HFFFFFF&", 0.8)
    boom(WAVE, "パァンッ！", 250, 260, 90, 8, "&H40E0FF&", 0.6)
    boom(FHIT, "ドォォォン！！！", 360, 330, 120, -6, "&H2040FF&", 1.2)
    E(DOMAIN, FHIT, "card", r"{\an5\pos(360,140)\fs36\c&H40C8FF&\bord3\3c&H000000&\fad(300,200)}― 光と影が、反転する ―", 9)
    # 完
    S(TITLE, END, "m 0 0 l 720 0 l 720 1280 l 0 1280", "&H000000&", "&HA0&", 3, r"\fad(600,0)")
    E(TITLE + 0.2, END, "count", r"{\an5\pos(360,480)\fs52\c&HFFFFFF&\3c&H000000&\bord5\fad(500,0)}触れたら、影になる世界", 11)
    E(TITLE + 0.9, END, "count", r"{\an5\pos(360,590)\fs76\c&HB0E8FF&\3c&H203040&\bord6\fad(500,0)}― 完 ―", 11)
    E(END - 2.2, END, "card", r"{\an5\pos(360,760)\fs40\c&H80E0FF&\bord4\3c&H000000&\fad(200,0)}面白かったら\Nコメント・フォローで応援してね！", 12)
    S(0, END, "m 0 0 l 720 0 l 720 6 l 0 6", "&H60D0FF&", "&H00&", 12, r"\clip(0,0,0,6)\t(0,%d,\clip(0,0,720,6))" % int(END * 1000))
    for st_, en, text, _, _, who in R.LINES:
        E(st_, en, who, r"{\an5\pos(360,1000)\fad(60,100)}%s" % text, 9)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

def build_sfx():
    B.block_final(add, DUR, CLENCH, PILLARS, SWING, SLASH, CATCH, SWARM, DOMAIN, RISE, FHIT, SUN, DAWN, TITLE, tail=TAIL)
    add(X.braam(2.4, 38.0), 0.05, 0.3)
    add(X.braam(2.0, 36.0), 3.0, 0.25)                                                       # 巨人の声に低音
    add(K.build(10, 0.05), CLENCH + 0.2, 0.25); add(X.swell(1.6), CLENCH + 0.3, 0.3)
    add(K.build(16, 0.03), PILLARS - 0.1, 0.4); add(K.whoosh(0.5, 300, 5000), PILLARS, 0.5)
    for k in range(6): K.strike(add, PHIT + k * 0.07, 0.8 + 0.1 * k, 0.4 * (-1) ** k, k == 0)
    add(K.crumble(1.2, 24), PHIT + 0.2, 0.5)
    add(K.whoosh(0.9, 150, 1200), SWING - 0.2, 0.5); add(X.swell(0.8), SWING + 0.1, 0.3)
    K.strike(add, SMASH, 1.6); add(K.boom_big(2.4), SMASH, 0.7); add(K.crumble(1.6, 34), SMASH + 0.1, 0.7)
    add(K.whoosh(0.25, 800, 8000), SMASH - 0.15, 0.5)                                      # よける
    add(K.build(24, 0.025), SWORD + 0.05, 0.45); add(K.slash() * 0.6, SWORD + 0.8, 0.4)
    add(K.suck(0.3), SLASH - 0.3, 0.4); add(K.slash(), SLASH - 0.05, 1.0); K.strike(add, SLASH + 0.02, 1.2, 0.0, False)
    add(K.crumble(1.0, 16), SLASH + 0.3, 0.4)
    add(R.whoosh(1.0, 200, 1500), SLASH + 0.3, 0.3); add(K.hit(0.6), CATCH, 0.4)
    add(X.swell(1.6), JOIN - 0.2, 0.35)
    add(K.boom_big(2.0) * 0.6, SWARM - 0.4, 0.5)                                             # 咆哮
    for k in range(3): K.strike(add, WAVE + 0.5 * k, 1.0, 0.3 * (k - 1), True); add(K.whoosh(0.4, 400, 6000), WAVE + 0.5 * k, 0.4)
    add(X.tinnitus(2.0, 4800), DOMAIN, 0.15); add(X.swell(2.0), DOMAIN + 0.2, 0.4)
    add(K.suck(0.8), RISE - 0.8, 0.5); add(K.build(30, 0.02), RISE, 0.4); add(R.riser(0.8), RISE, 0.3)
    K.strike(add, FHIT, 2.0); add(K.boom_big(3.5), FHIT, 1.0); add(K.boom_big(3.0) * 0.7, FHIT + 0.35, 0.8)
    add(X.impact(2.0, 34.0), SUN, 0.5); add(X.swell(2.0), SUN - 0.5, 0.3)
    for k in range(6):
        f0 = 3200 + 600 * (k % 3); tt = R.tt(0.12)
        add(np.sin(2 * np.pi * (f0 + 2500 * tt) * tt) * R.dec(0.12, 0.04), DAWN + 0.8 + k * 0.55, 0.035, 0.5 * (-1) ** k)

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
    wav = os.path.join(HERE, "blk6_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "blk6_ui.ass"); build_ui(ass)
    if "--ui" in sys.argv: print("wrote", wav, ass); return
    os.makedirs(FR, exist_ok=True)
    for f in range(int(round(END * FPS))):
        src = os.path.join(HERE, "frames_BLK6W_post", "%04d.png" % (f + 1)) if 199 <= f < 420 else os.path.join(HERE, "frames_BLK6_post", "%04d.png" % ((f if f < 199 else f - 86) + 1))
        dst = os.path.join(FR, "%04d.png" % (f + 1))
        if os.path.lexists(dst): os.remove(dst)
        os.symlink(src, dst)
    mp4 = os.path.join(HERE, "block_final.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(FR, "%04d.png"), "-i", wav,
                    "-filter_complex", "[0:v]vignette=PI/5.5,eq=contrast=1.03:saturation=1.06,ass=blk6_ui.ass[v]", "-map", "[v]", "-map", "1:a",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-maxrate", "12M", "-bufsize", "24M",
                    "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-t", "%.3f" % DUR,
                    "-movflags", "+faststart", mp4], check=True, cwd=HERE)
    print("wrote", mp4)

if __name__ == "__main__":
    main()
