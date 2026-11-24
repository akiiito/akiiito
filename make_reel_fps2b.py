"""
make_reel_toki1.py ― 「その罪、時効にさせない」第1話『光る絵の具』（35秒・1080x1920・24fps）
  1) --voice で声（fps2b_voice.npy / fps2b_lines.json）
  2) create_toki1.py → post_toki1.py で絵
  3) 引数なしで 絵＋声＋効果音＋BGM＋字幕 → fps_ep2b.mp4
"""
import os, sys, json, subprocess, wave
import numpy as np
import make_reel as R
import s_sfx as X
import s_bgm as B
import s_hit as K
from fps_lines import EP2B as LINES0
from fps2b_timing import *

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
R.VV_READ += [("異世界", "いせかい"), ("消失", "しょうしつ"), ("登録", "とうろく"), ("1発", "いっぱつ"), ("3人", "さんにん"), ("規約違反", "きやくいはん"), ("検知", "けんち"), ("管理者", "かんりしゃ")]
VOICE_NPY = os.path.join(HERE, "fps2b_voice.npy"); LINES_JSON = os.path.join(HERE, "fps2b_lines.json")


STY = (
    "Style: shape,{f},20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n"
    "Style: ren,{f},68,&H00FFFFFF,&H00FFFFFF,&H00202020,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: mina,{f},68,&H00E0C8FF,&H00E0C8FF,&H00402040,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: ann,{f},60,&H00FFE8A0,&H00FFE8A0,&H00402000,&H00000000,-1,0,0,0,100,100,1,0,1,7,0,5,16,16,0,1\n"
    "Style: hook,{f},58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,7,0,5,20,20,0,1\n"
    "Style: hud,{f},26,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,2,0,5,0,0,0,1\n"
    "Style: card,{f},44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,0,0,5,20,20,0,1\n"
    "Style: count,{f},84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,8,0,5,0,0,0,1\n")

# 編集表：(出力の開始, 終わり, 元の開始, 元の終わり, 種類)  種類 n=そのまま g=選ばなかった方（白黒の幻） k=黒
EDL = [(0.0, 5.4, 0.0, 5.4, "n"), (5.4, 5.9, 16.6, 17.1, "g"), (5.9, 8.6, 8.0, 10.5, "n"), (8.6, 11.4, 5.5, 8.3, "n"), (11.4, 11.9, 8.6, 9.1, "g"),
       (11.9, 14.4, 10.5, 13.0, "n"), (14.4, 16.4, 13.0, 15.0, "n"), (16.4, 22.0, 16.6, 22.2, "n"), (22.0, 23.0, 23.0, 24.0, "n"),
       (23.0, 25.0, 25.0, 27.0, "n"), (25.0, 28.0, 27.4, 30.0, "n"), (28.0, 30.0, 0, 0, "k")]
K1O, K2O, K3O = 18.4, 20.8, 22.0
def det_at(t):
    if t < 11.9: return 12
    if t < 23.0: return 34 + (int(30 * min(1, (t - 16.4) / 5.5)) if t > 16.4 else 0)
    return min(99, 64 + int(35 * min(1, (t - 23.0) / 1.5)))

def build_ui(path):
    ev = []
    def E(t0, t1, style, text, layer=5):
        if t1 > t0: ev.append("Dialogue: %d,%s,%s,%s,,0,0,0,,%s" % (layer, R.ts(t0), R.ts(t1), style, text))
    def S(t0, t1, draw, col, alpha="&H00&", layer=4, extra=""):
        E(t0, t1, "shape", r"{\an7\pos(0,0)\p1\1c%s\1a%s\bord0\shad0%s}%s{\p0}" % (col, alpha, extra, draw), layer)
    def rect(x0, y0, x1, y1): return "m %d %d l %d %d l %d %d l %d %d" % (x0, y0, x1, y0, x1, y1, x0, y1)
    pop = r"\fscx135\fscy135\t(0,140,\fscx100\fscy100)"
    def choice(t0, t1, q, A, B, pick=None):
        """2択：問い＋A/Bのボタン＋減っていく時間のバー。pick='A'/'B' で選んだ方が金色に光る"""
        tp = pick[1] if pick else t1; who = pick[0] if pick else None
        S(t0, t1, rect(0, 700, 720, 960), "&H000000&", "&H60&", 10, r"\fad(120,150)")
        E(t0, t1, "count", r"{\an5\pos(360,745)\fs40\c&HFFFFFF&\3c&H000000&\bord4\fad(120,150)%s}%s" % (pop, q), 12)
        for k, (lab, txt, x0) in enumerate((("A", A, 40), ("B", B, 370))):
            chosen = who == lab
            S(t0, tp, rect(x0, 790, x0 + 310, 890), "&H404040&", "&H30&", 11, r"\fad(120,0)")
            if who:
                col = "&H30C8FF&" if chosen else "&H202020&"
                S(tp, t1, rect(x0, 790, x0 + 310, 890), col, "&H10&" if chosen else "&HA0&", 11, (r"\t(0,120,\fscx104\fscy104)" if chosen else "") + r"\fad(0,150)")
            E(t0, t1, "count", r"{\an5\pos(%d,840)\fs40\c%s\3c&H000000&\bord3\fad(120,150)}%s：%s" % (x0 + 155, "&H000000&" if False else "&HFFFFFF&", lab, txt), 13)
        dur = int((tp - t0) * 1000)
        S(t0, tp, rect(40, 905, 680, 918), "&H3030FF&", "&H00&", 12, r"\clip(40,905,680,918)\t(0,%d,\clip(40,905,40,918))" % dur)
    def ghost(t0, t1, what, res):
        E(t0, t1, "count", r"{\an5\pos(360,240)\fs34\c&HDDDDDD&\bord3\3c&H000000&}もし「%s」を選んでいたら…" % what, 14)
        E(t0, t1, "count", r"{\an5\pos(360,330)\fs86\c&H2020FF&\3c&H000000&\bord8%s}%s" % (pop, res), 14)
    # 冒頭
    E(0, 2.2, "count", r"{\an5\pos(360,300)\fs124\c&H3030FF&\3c&H000000&\bord10%s\fad(0,250)}残弾 1" % pop, 12)
    S(0, 2.2, rect(0, 410, 720, 540), "&H000000&", "&H70&", 8, r"\fad(0,250)")
    E(0, 2.2, "hook", r"{\an5\pos(360,475)\fs44\bord6%s\fad(0,250)}この世界の銃、弾は1発だけ。" % pop, 10)
    # HUD（主観のとき）
    pov = lambda t: not (14.4 <= t < 16.4 or 16.8 <= t < 22.0 or t >= 28.0)
    t = 0.0; step = 1 / 8
    while t < 28.0:
        if pov(t):
            E(t, t + step, "hud", r"{\an1\pos(28,1250)\fs30\c&HFFFFFF&}HP {\c&H60FF60&}100", 7)
            E(t, t + step, "hud", r"{\an3\pos(692,1250)\fs34\c&HFFFFFF&}残弾 {\c&H3030FF&\fs52}%d{\c&HFFFFFF&\fs30}/1" % (0 if t >= 16.4 else 1), 7)
            en = 3 - (t >= K1O) - (t >= K2O) - (t >= K3O)
            E(t, t + step, "hud", r"{\an7\pos(28,24)\fs28\c&HFFFFFF&}敵 {\c&H3030FF&}%d" % en, 7)
            d = det_at(t); dc = "&H40D0FF&" if d < 90 else ("&H3030FF&" if int(t * 6) % 2 else "&HFFFFFF&")
            E(t, t + step, "hud", r"{\an9\pos(692,24)\fs24\c&HFFFFFF&}異常検知 {\c%s\fs30}%d%%" % (dc, d), 7)
        t += step
    # 2択の連続
    choice(2.4, 5.4, "敵が3人、近づいてくる！", "今すぐ撃つ", "隠れる", ("B", 4.6))
    ghost(5.4, 5.9, "今すぐ撃つ", "外れ → 消滅")
    choice(8.6, 11.4, "撃たれて身動きできない！", "一か八か撃つ", "ルールを読む", ("B", 10.2))
    S(10.25, 11.4, rect(60, 560, 660, 690), "&H000000&", "&H40&", 9, r"\fad(100,0)")
    E(10.25, 11.4, "card", r"{\an7\pos(84,575)\fs30\fad(100,0)}・外したら、撃った人は消える", 9)
    E(10.25, 11.4, "card", r"{\an7\pos(84,625)\fs36\c&H40F0FF&\fad(100,0)\t(200,500,\fscx110\fscy110)}・外れ＝弾が止まったとき", 9)
    ghost(11.4, 11.9, "一か八か撃つ", "壁で止まる → 消滅")
    E(11.9, 14.4, "card", r"{\an5\pos(360,120)\fs30\c&H40F0FF&\bord3\3c&H000000&}外れ＝弾が止まったとき", 9)
    E(11.9, 13.0, "count", r"{\an5\pos(360,330)\fs90\c&HFFE0A0&\3c&H402000&\bord9%s}弾道編集" % pop, 12)
    choice(12.0, 14.4, "3人を、1発で。", "一直線に貫く", "止まらない輪", ("B", 13.6))
    def boom(t0, text, x, y, fs, rot, col="&HFFF0A0&", d=0.7):
        st = r"\frz%d\fscx240\fscy240\t(0,90,\fscx100\fscy100)\t(%d,%d,\alpha&HFF&)" % (rot, int(d * 1000) - 200, int(d * 1000))
        E(t0, t0 + d, "count", r"{\an5\pos(%d,%d)\fs%d\c%s\3c&H101010&\bord9\shad0%s}%s" % (x, y, fs, col, st, text), 14)
    boom(K1O, "パキィン！", 380, 330, 110, -8, d=0.9); boom(K2O, "パキン！", 300, 300, 100, 8); boom(K3O, "パキン！", 420, 360, 100, -6)
    E(K3O, 23.0, "count", r"{\an5\pos(360,520)\fs76\c&H40C8FF&\3c&H000000&\bord8%s}トリプルキル" % pop, 12)
    S(23.0, 28.0, rect(0, 0, 720, 1280), "&H0000C0&", "&HD8&", 3, r"\t(0,300,\1a&HC0&)\t(300,600,\1a&HE8&)\t(600,900,\1a&HC0&)\t(900,1200,\1a&HE8&)")
    E(23.0, 28.0, "count", r"{\an5\pos(360,250)\fs44\c&H3030FF&\3c&H000000&\bord5\fad(150,0)}⚠ 規約違反を検知", 12)
    choice(25.9, 28.0, "白い管理者が狙っている！", "声の方へ逃げる", "撃ち返す")
    S(28.0, 30.0, rect(0, 0, 720, 1280), "&H000000&", "&H00&", 15)
    E(28.0, 30.0, "count", r"{\an5\pos(360,520)\fs76\c&HFFFFFF&\3c&H000000&\bord6%s}あなたならどっち？" % pop, 16)
    E(28.2, 30.0, "count", r"{\an5\pos(360,630)\fs40\c&H30C8FF&\bord4\3c&H000000&\fad(150,0)}A か B でコメントしてね", 16)
    E(28.5, 30.0, "card", r"{\an5\pos(360,720)\fs30\c&HDDDDDD&\fad(150,0)}多かった方が、第2話の展開になる", 16)
    E(28.8, 30.0, "card", r"{\an5\pos(360,1180)\fs28\c&HAAAAAA&\fad(150,0)}フォローして続きを待っててね", 16)
    for st_, en, text, _, _, who in R.LINES:
        E(st_, en, who, r"{\an5\pos(360,1060)\fad(60,100)}%s" % text, 9)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

def mix(*xs):
    n = max(len(x) for x in xs); out = np.zeros(n)
    for x in xs: out[:len(x)] += x
    return out
def click(sec=0.06, f=3200): return R.lp(R.noise(sec), f) * R.dec(sec, 0.008)
def gunshot():
    return mix(R.hp(R.noise(0.02), 2000) * R.dec(0.02, 0.004) * 1.2, R.lp(R.kick(160, 50, 0.25, 0.05), 1500) * 1.3, R.lp(R.noise(0.6), 2500) * R.dec(0.6, 0.12) * 0.6)
def tick(): return mix(np.sin(2 * np.pi * 1800 * R.tt(0.03)) * R.dec(0.03, 0.006))
def choose(): return mix(click(0.04, 7000) * 1.2, np.sin(2 * np.pi * 1320 * R.tt(0.18)) * R.dec(0.18, 0.05) * 0.6, np.sin(2 * np.pi * 1760 * R.tt(0.18)) * R.dec(0.18, 0.05) * 0.4)
def glitch(sec=0.5): return R.bp(R.noise(sec), 300, 5000) * (np.sin(2 * np.pi * 23 * R.tt(sec)) > 0) * 0.8
def build_sfx():
    B.deathgame_bgm(add, DUR, ghosts=(5.4, 11.4), climax=16.4, win_=22.0, alarm=23.0, final=(25.9, 28.0), tail=TAIL)
    add(K.hit(1.3), 0.0, 0.6); add(X.braam(2.2, 40.0), 0.05, 0.3)
    hb = R.heartbeat(); t = 0.2
    while t < 2.4: add(hb, t, 0.35); t += 0.7
    for k in range(6): add(gunshot() * 0.25, 2.5 + k * 0.45, 0.25, 0.7 * (-1) ** k)
    for (a, b, p) in ((2.4, 5.4, 4.6), (8.6, 11.4, 10.2), (12.0, 14.4, 13.6), (25.9, 28.0, None)):
        t = a
        while t < (p or b): add(tick(), t, 0.18); t += 0.25
        if p: add(choose(), p, 0.5)
    for g in (5.4, 11.4): add(glitch(0.5), g, 0.5); add(K.hit(1.0) * 0.8, g + 0.05, 0.5); add(X.stinger(1.0), g, 0.25)
    for k in range(10): add(mix(gunshot() * 0.5, K.crumble(0.4, 6) * 0.6), 5.95 + k * 0.25, 0.45, 0.5 * (-1) ** k)
    add(K.suck(1.0), 11.5, 0.4); add(X.swell(2.0), 11.9, 0.4); add(X.tinnitus(2.4, 4200), 12.0, 0.1)
    add(K.slash() * 0.4, 14.4, 0.3); add(K.whoosh(1.9, 300, 6000) * 0.6, 14.5, 0.35)
    add(K.suck(0.4), 16.0, 0.5); add(gunshot(), 16.4, 1.0); add(K.whoosh(1.8, 800, 9000), 16.45, 0.4)
    for kt in (K1O, K2O, K3O): K.strike(add, kt, 1.2, 0.0, kt == K1O); add(mix(np.sin(2 * np.pi * 3800 * R.tt(0.3)) * R.dec(0.3, 0.08)), kt, 0.15)
    add(X.impact(1.6, 46.0), K3O + 0.05, 0.4)
    for k in range(6): add(K.whoosh(0.25, 2000, 9000) * 0.5, 23.0 + k * 0.3, 0.3, 0.6 * (-1) ** k)
    for k in range(8): add(mix(np.sin(2 * np.pi * 880 * R.tt(0.15)) * R.dec(0.15, 0.1)), 23.4 + k * 0.32, 0.12)
    add(X.braam(2.6, 33.0), 25.0, 0.5)
    add(K.hit(1.2), 28.0, 0.5); add(X.braam(2.4, 30.0), 28.05, 0.35)

def render_mp4():
    R.LINES = [tuple(l) for l in json.load(open(LINES_JSON, encoding="utf-8"))]
    voice = np.load(VOICE_NPY)
    voice = np.concatenate([voice, np.zeros((max(0, R.n_(DUR + TAIL + 1) - len(voice)), 2))])
    R.MIX = np.zeros_like(voice); build_sfx()
    R.MIX = voice + X.duck(R.MIX, voice)
    out = R.MIX[: R.n_(DUR + TAIL)].copy()
    out[-R.n_(1.2):] *= np.linspace(1, 0, R.n_(1.2))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "fps2b_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "fps2b_ui.ass"); build_ui(ass)
    if "--ui" in sys.argv: print("wrote", wav, ass); return
    SEQ = os.path.join(HERE, "frames_FPS1c_seq")
    subprocess.run(["python3", os.path.join(HERE, "assemble_fps1c.py"), json.dumps(EDL), str(DUR + TAIL)], check=True, cwd=HERE)
    mp4 = os.path.join(HERE, "fps_ep2b.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(SEQ, "%04d.png"), "-i", wav,
                    "-filter_complex", "[0:v]vignette=PI/5.5,ass=fps2b_ui.ass[v]", "-map", "[v]", "-map", "1:a",
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
