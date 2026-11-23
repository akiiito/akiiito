"""
make_reel_toki1.py ― 「その罪、時効にさせない」第1話『光る絵の具』（35秒・1080x1920・24fps）
  1) --voice で声（fps1_voice.npy / fps1_lines.json）
  2) create_toki1.py → post_toki1.py で絵
  3) 引数なしで 絵＋声＋効果音＋BGM＋字幕 → fps_ep1.mp4
"""
import os, sys, json, subprocess, wave
import numpy as np
import make_reel as R
import s_sfx as X
import s_bgm as B
import s_hit as K
from fps_lines import EP1 as LINES0
from fps1_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
DUR = END; TAIL = 0.6
R.DUR = DUR; R.MIX = np.zeros((R.n_(DUR) + SR, 2)); add = R.add
R.VV_CAST.update({
    "ren": (1368642336, 1368642336, 0.0, 1.0, 1.0),       # レン（M2）
    "ann": (345585728, 345585728, 0.0, 0.95, 0.9),        # アナウンス（るな）
})
R.VOICE.update({"ren": (0, 0, 1.1, 0.04), "ann": (0, 0, 1.0, 0.18)})
R.SPK_REF_TEXT[:] = ["今日の放課後、少しだけ話せる", "写真、見せてくれる", "ううん、なんでもない", "また明日ね", "窓の外、きれいだね"]
R.LINES = list(LINES0)
R.RETAKE_MIN, R.RETAKES = 0.66, 24
R.VV_READ += [("1発", "いっぱつ"), ("3人", "さんにん"), ("規約違反", "きやくいはん"), ("検知", "けんち"), ("管理者", "かんりしゃ")]
VOICE_NPY = os.path.join(HERE, "fps1_voice.npy"); LINES_JSON = os.path.join(HERE, "fps1_lines.json")


STY = (
    "Style: shape,{f},20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n"
    "Style: ren,{f},68,&H00FFFFFF,&H00FFFFFF,&H00202020,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: ann,{f},60,&H00FFE8A0,&H00FFE8A0,&H00402000,&H00000000,-1,0,0,0,100,100,1,0,1,7,0,5,16,16,0,1\n"
    "Style: hook,{f},58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,7,0,5,20,20,0,1\n"
    "Style: hud,{f},26,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,2,0,5,0,0,0,1\n"
    "Style: card,{f},44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,0,0,5,20,20,0,1\n"
    "Style: count,{f},84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,8,0,5,0,0,0,1\n")

def det_at(t):
    if t < EDIT: return 12
    if t < LOOP: return 12 + int(22 * min(1, (t - EDIT) / 0.8)) + (int(30 * min(1, (t - FIRE) / 6)) if t > FIRE else 0)
    return min(99, 64 + int(35 * min(1, (t - LOOP) / 1.6)))

def build_ui(path):
    ev = []
    def E(t0, t1, style, text, layer=5):
        if t1 > t0: ev.append("Dialogue: %d,%s,%s,%s,,0,0,0,,%s" % (layer, R.ts(t0), R.ts(t1), style, text))
    def S(t0, t1, draw, col, alpha="&H00&", layer=4, extra=""):
        E(t0, t1, "shape", r"{\an7\pos(0,0)\p1\1c%s\1a%s\bord0\shad0%s}%s{\p0}" % (col, alpha, extra, draw), layer)
    pop = r"\fscx135\fscy135\t(0,140,\fscx100\fscy100)"
    pov = lambda t: not (DRAW <= t < FIRE - 0.15 or FIRE + 0.4 <= t < K3 + 0.4)
    # 冒頭
    E(0, 3.0, "count", r"{\an5\pos(360,300)\fs150\c&H3030FF&\3c&H000000&\bord10%s\fad(0,250)}残弾 1" % pop, 12)
    S(0, 3.0, "m 0 410 l 720 410 l 720 540 l 0 540", "&H000000&", "&H70&", 8, r"\fad(0,250)")
    E(0, 3.0, "hook", r"{\an5\pos(360,475)\fs58\bord6%s\fad(0,250)}この世界の銃、弾は1発だけ。" % pop, 10)
    # HUD（主観のときだけ）
    t = 0.0; step = 1 / 8
    while t < END - 2.5:
        if pov(t):
            col = "&H3030FF&" if t < WIN else "&H60FF60&"
            E(t, t + step, "hud", r"{\an1\pos(28,1250)\fs30\c&HFFFFFF&}HP {\c&H60FF60&}100", 7)
            E(t, t + step, "hud", r"{\an3\pos(692,1250)\fs34\c&HFFFFFF&}残弾 {\c%s\fs52}%d{\c&HFFFFFF&\fs30}/1" % (col, 0 if t >= FIRE else 1), 7)
            en = 3 - (t >= K1) - (t >= K2) - (t >= K3)
            E(t, t + step, "hud", r"{\an7\pos(28,24)\fs28\c&HFFFFFF&}敵 {\c&H3030FF&}%d" % en, 7)
            d = det_at(t); dc = "&H40D0FF&" if d < 90 else ("&H3030FF&" if int(t * 6) % 2 else "&HFFFFFF&")
            E(t, t + step, "hud", r"{\an9\pos(692,24)\fs24\c&HFFFFFF&}異常検知 {\c%s\fs30}%d%%" % (dc, d), 7)
            S(t, t + step, "m 352 640 l 368 640 l 368 642 l 352 642 m 359 633 l 361 633 l 361 649 l 359 649", "&HFFFFFF&", "&H20&", 7)
        t += step
    # ルール（伏線の一文が光る）
    S(RULE, DUCK + 0.3, "m 60 560 l 660 560 l 660 780 l 60 780", "&H000000&", "&H50&", 8, r"\fad(150,200)")
    E(RULE, DUCK + 0.3, "card", r"{\an7\pos(84,580)\fs30\c&HDDDDDD&\fad(150,200)}― 今日のルール ―", 9)
    E(RULE + 0.1, DUCK + 0.3, "card", r"{\an7\pos(84,630)\fs34\fad(150,200)}・弾は1人1発", 9)
    E(RULE + 0.3, DUCK + 0.3, "card", r"{\an7\pos(84,675)\fs34\fad(150,200)}・外したら、撃った人は消える", 9)
    E(RULE + 0.6, DUCK + 0.3, "card", r"{\an7\pos(84,720)\fs34\c&H40F0FF&\fad(150,200)\t(300,600,\fscx108\fscy108)}・外れ＝弾が止まったとき", 9)
    # スキル
    E(EDIT, EDIT + 2.2, "count", r"{\an5\pos(360,330)\fs38\c&HFFE0A0&\bord4\3c&H000000&%s}スキル" % pop, 12)
    E(EDIT, EDIT + 2.2, "count", r"{\an5\pos(360,410)\fs96\c&HFFE0A0&\3c&H402000&\bord9%s}弾道編集" % pop, 12)
    E(DRAW, FIRE - 0.15, "card", r"{\an5\pos(360,120)\fs30\c&HFFE0A0&\bord3\3c&H000000&\fad(200,0)}編集できるのは、撃つ前の3秒だけ", 9)
    # 擬音・キル
    def boom(t0, text, x, y, fs, rot, col="&HFFFFFF&", d=0.7):
        st = r"\frz%d\fscx240\fscy240\t(0,90,\fscx100\fscy100)\t(%d,%d,\alpha&HFF&)" % (rot, int(d * 1000) - 200, int(d * 1000))
        E(t0, t0 + d, "count", r"{\an5\pos(%d,%d)\fs%d\c%s\3c&H101010&\bord9\shad0%s}%s" % (x, y, fs, col, st, text), 14)
    boom(K1, "パキィン！", 380, 330, 110, -8, "&HFFF0A0&", 0.9); boom(K2, "パキン！", 300, 300, 100, 8, "&HFFF0A0&"); boom(K3, "パキン！", 420, 360, 100, -6, "&HFFF0A0&")
    for i, kt in enumerate((K1, K2, K3)):
        E(kt, WIN + 1.5, "hud", r"{\an9\pos(692,%d)\fs24\c&HFFFFFF&\fad(100,200)}レン  ⌖  兵士%d" % (70 + 30 * i, i + 1), 9)
    E(K3 + 0.1, K3 + 1.6, "count", r"{\an5\pos(360,520)\fs76\c&H40C8FF&\3c&H000000&\bord8%s}トリプルキル" % pop, 12)
    E(WIN, LOOP, "count", r"{\an5\pos(360,300)\fs90\c&H60FF60&\3c&H003000&\bord8%s\fad(0,200)}勝利" % pop, 12)
    # 警告
    S(LOOP + 0.8, END, "m 0 0 l 720 0 l 720 1280 l 0 1280", "&H0000C0&", "&HD8&", 3, r"\t(0,300,\1a&HC0&)\t(300,600,\1a&HE8&)\t(600,900,\1a&HC0&)\t(900,1200,\1a&HE8&)")
    E(ADMIN, END, "count", r"{\an5\pos(360,250)\fs44\c&H3030FF&\3c&H000000&\bord5\fad(150,0)}⚠ 規約違反を検知", 12)
    E(END - 2.0, END, "card", r"{\an5\pos(360,1180)\fs30\c&HDDDDDD&\bord3\3c&H000000&\fad(200,0)}コメント・フォローで応援してね", 12)
    for st_, en, text, _, _, who in R.LINES:
        E(st_, en, who, r"{\an5\pos(360,1000)\fad(60,100)}%s" % text, 9)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

def mix(*xs):
    n = max(len(x) for x in xs); out = np.zeros(n)
    for x in xs: out[:len(x)] += x
    return out
def click(sec=0.06, f=3200): return R.lp(R.noise(sec), f) * R.dec(sec, 0.008)
def gunshot():
    return mix(R.hp(R.noise(0.02), 2000) * R.dec(0.02, 0.004) * 1.2, R.lp(R.kick(160, 50, 0.25, 0.05), 1500) * 1.3, R.lp(R.noise(0.6), 2500) * R.dec(0.6, 0.12) * 0.6)
def build_sfx():
    B.fps_ep1(add, DUR, DUCK, EDIT, FIRE, K3, WIN, LOOP, ADMIN, tail=TAIL)
    add(K.hit(1.3), 0.0, 0.6); add(X.braam(2.2, 40.0), 0.05, 0.3)
    hb = R.heartbeat(); t = 0.2
    while t < 3.0: add(hb, t, 0.35); t += 0.7
    for k in range(5): add(mix(np.sin(2 * np.pi * 1200 * R.tt(0.05)) * R.dec(0.05, 0.01)), 1.2 + k * 0.08, 0.06)    # 電子ノイズ
    for k in range(10): add(gunshot() * 0.25, 3.5 + k * 0.42, 0.25, 0.7 * (-1) ** k)                                  # 遠くの銃声
    add(click(0.05, 6000), RULE + 0.6, 0.4)
    for k in range(12): add(mix(gunshot() * 0.5, K.crumble(0.4, 6) * 0.6), DUCK + 0.15 + k * 0.2, 0.45, 0.5 * (-1) ** k)    # バリケードに着弾
    add(K.suck(1.0), EDIT - 0.4, 0.4); add(X.swell(2.0), EDIT, 0.4); add(X.tinnitus(2.4, 4200), EDIT + 0.2, 0.1)
    add(K.slash() * 0.4, DRAW, 0.3); add(K.whoosh(2.4, 300, 6000) * 0.6, DRAW + 0.2, 0.35)
    add(K.suck(0.4), FIRE - 0.4, 0.5); add(gunshot(), FIRE, 1.0)
    add(K.whoosh(1.8, 800, 9000), FIRE + 0.05, 0.4)
    for kt in (K1, K2, K3): K.strike(add, kt, 1.2, 0.0, kt == K1); add(mix(np.sin(2 * np.pi * 3800 * R.tt(0.3)) * R.dec(0.3, 0.08)), kt, 0.15)
    add(X.impact(1.6, 46.0), K3 + 0.05, 0.4)
    for k in range(8): add(K.whoosh(0.25, 2000, 9000) * 0.5, LOOP + k * 0.3, 0.3, 0.6 * (-1) ** k)                      # 回り続ける弾
    for k in range(6): add(mix(np.sin(2 * np.pi * 880 * R.tt(0.15)) * R.dec(0.15, 0.1)), LOOP + 0.8 + k * 0.3, 0.12)   # 警告音
    add(X.braam(2.6, 33.0), ADMIN, 0.5)

def render_mp4():
    R.LINES = [tuple(l) for l in json.load(open(LINES_JSON, encoding="utf-8"))]
    voice = np.load(VOICE_NPY)
    voice = np.concatenate([voice, np.zeros((max(0, R.n_(DUR + TAIL + 1) - len(voice)), 2))])
    R.MIX = np.zeros_like(voice); build_sfx()
    R.MIX = voice + X.duck(R.MIX, voice)
    out = R.MIX[: R.n_(DUR + TAIL)].copy()
    out[-R.n_(0.8):] *= np.linspace(1, 0, R.n_(0.8))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "fps1_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "fps1_ui.ass"); build_ui(ass)
    if "--ui" in sys.argv: print("wrote", wav, ass); return
    mp4 = os.path.join(HERE, "fps_ep1.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(HERE, "frames_FPS1_post", "%04d.png"), "-i", wav,
                    "-filter_complex", "[0:v]vignette=PI/5.5,ass=fps1_ui.ass[v]", "-map", "[v]", "-map", "1:a",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-maxrate", "12M", "-bufsize", "24M",
                    "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-t", "%.3f" % DUR,
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
