"""
make_reel_toki1.py ― 「その罪、時効にさせない」第1話『光る絵の具』（35秒・1080x1920・24fps）
  1) --voice で声（toki3_voice.npy / toki3_lines.json）
  2) create_toki1.py → post_toki1.py で絵
  3) 引数なしで 絵＋声＋効果音＋BGM＋字幕 → toki_ep3.mp4
"""
import os, sys, json, subprocess, wave
import numpy as np
import make_reel as R
import s_sfx as X
import s_bgm as B
import s_hit as K
from toki_lines import TOKI3 as LINES0
from toki3_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
DUR = END; TAIL = 0.6
R.DUR = DUR; R.MIX = np.zeros((R.n_(DUR) + SR, 2)); add = R.add
R.VV_CAST.update({
    "mio": (1717361472, 1717361472, 0.0, 1.0, 1.1),       # みちのくあいり
    "toki": (888753763, 888753763, 0.0, 0.95, 1.05),      # まお（おちつき）
    "doc": (593129376, 593129376, 0.0, 0.95, 1.0),        # 蒼月ハヤテ
})
R.VOICE.update({k: (0, 0, 1.1, 0.04) for k in ("mio", "toki", "doc")})
R.SPK_REF_TEXT[:] = ["今日の放課後、少しだけ話せる", "写真、見せてくれる", "ううん、なんでもない", "また明日ね", "窓の外、きれいだね"]
R.LINES = list(LINES0)
R.RETAKE_MIN, R.RETAKES = 0.66, 24
R.VV_READ += [("何者", "なにもの"), ("10分", "じゅっぷん"), ("患者", "かんじゃ"), ("手術", "しゅじゅつ"), ("時効", "じこう"), ("医者", "いしゃ")]
VOICE_NPY = os.path.join(HERE, "toki3_voice.npy"); LINES_JSON = os.path.join(HERE, "toki3_lines.json")


STY = (
    "Style: shape,{f},20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n"
    "Style: hana,{f},70,&H00FFFFFF,&H00FFFFFF,&H00306A30,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: boss,{f},70,&H00FFFFFF,&H00FFFFFF,&H00303030,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: toki,{f},70,&H0080E8FF,&H0080E8FF,&H00102040,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: mio,{f},70,&H00FFFFFF,&H00FFFFFF,&H00704030,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: doc,{f},70,&H00FFFFFF,&H00FFFFFF,&H00303030,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: hook,{f},70,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,7,0,5,20,20,0,1\n"
    "Style: card,{f},44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,0,0,5,20,20,0,1\n"
    "Style: count,{f},84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,8,0,5,0,0,0,1\n")

def build_ui(path):
    ev = []
    def E(t0, t1, style, text, layer=5):
        if t1 > t0: ev.append("Dialogue: %d,%s,%s,%s,,0,0,0,,%s" % (layer, R.ts(t0), R.ts(t1), style, text))
    def S(t0, t1, draw, col, alpha="&H00&", layer=4, extra=""):
        E(t0, t1, "shape", r"{\an7\pos(0,0)\p1\1c%s\1a%s\bord0\shad0%s}%s{\p0}" % (col, alpha, extra, draw), layer)
    pop = r"\fscx150\fscy150\t(0,140,\fscx100\fscy100)"
    S(0, 2.9, "m 0 100 l 720 100 l 720 410 l 0 410", "&H000000&", "&H60&", 8, r"\fad(0,200)")
    E(0, 2.9, "hook", r"{\an5\pos(360,195)\fs60\bord7%s\fad(0,200)}目の奥から、{\c&H4040FF&}アイスピック{\c&HFFFFFF&}で" % pop, 10)
    E(0, 2.9, "hook", r"{\an5\pos(360,310)\fs60\bord7%s\fad(0,200)}脳を削られた人たちがいた" % pop, 10)
    E(0.3, 2.9, "card", r"{\an5\pos(360,445)\fs28\c&HDDDDDD&\bord3\3c&H000000&\fad(150,200)}実話をもとにしたフィクション", 10)
    E(STOPT + 0.3, RESUME, "card", r"{\an5\pos(360,120)\fs34\c&H80D8FF&\bord3\3c&H000000&\fad(250,150)}― 裁きの時間 ―", 9)
    E(11.7, 13.9, "card", r"{\an4\pos(46,560)\fs30\c&HDDDDDD&\bord3\3c&H000000&\fad(200,200)}時の裁判官", 10)
    E(11.7, 13.9, "count", r"{\an4\pos(40,620)\fs72\c&H80E0FF&\bord6\3c&H102030&\fad(200,200)%s}トキモリ" % pop, 10)
    # 擬音（マンガの描き文字）
    def boom(t0, text, x, y, fs, rot, col="&H30D0FF&", d=0.75):
        st = r"\frz%d\fscx240\fscy240\t(0,90,\fscx100\fscy100)\t(%d,%d,\fscx110\fscy110\alpha&HFF&)" % (rot, int(d * 1000) - 200, int(d * 1000))
        E(t0, t0 + d, "count", r"{\an5\pos(%d,%d)\fs%d\c%s\3c&H101010&\bord9\shad0%s}%s" % (x, y, fs, col, st, text), 13)
    boom(LUNGE + 0.2, "ヒュッ", 520, 260, 80, 10, "&HFFFFFF&", 0.5)
    boom(COUNTER, "バキィッ！", 250, 360, 110, -10)
    boom(CHAIN, "ジャララッ", 470, 260, 80, 8, "&H40D8FF&", 0.6)
    boom(SLAM, "ガシャァン！！", 360, 380, 110, -6, "&HFFFFFF&", 0.8)
    boom(XSLASH, "ザザンッ！！", 300, 330, 120, 12, "&H30D0FF&", 0.9)
    boom(FINISH, "ドガァァン！！", 360, 360, 120, -8, "&H2040FF&", 1.0)
    tech_t = CLOCK + 0.2
    E(tech_t, tech_t + 1.4, "count", r"{\an5\pos(360,640)\fs40\c&HDDDDDD&\bord4\3c&H000000&\fscx180\fscy180\t(0,120,\fscx100\fscy100)}時の裁き――", 13)
    E(tech_t, tech_t + 1.4, "count", r"{\an5\pos(360,730)\fs104\c&H40C8FF&\3c&H000000&\bord11\fscx180\fscy180\t(0,120,\fscx100\fscy100)}十分間の刑", 13)
    st = r"\frz-12\fscx260\fscy260\t(0,110,\fscx100\fscy100)"
    S(STAMP, DAWN + 0.5, "m 190 462 l 530 462 l 530 648 l 190 648 l 190 462 m 212 484 l 212 626 l 508 626 l 508 484 l 212 484", "&H2020D0&", "&H00&", 11, r"\org(360,555)%s\fad(0,300)" % st)
    E(STAMP, DAWN + 0.5, "count", r"{\an5\pos(360,555)\fs130\b1\c&H2020D0&\3c&HFFFFFF&\bord2\shad0%s\fad(0,300)}有罪" % st, 12)
    S(FACT, END, "m 0 0 l 720 0 l 720 1280 l 0 1280", "&H000000&", "&H70&", 3, r"\fad(500,0)")
    E(FACT + 0.1, END, "card", r"{\an5\pos(360,300)\fs34\c&H80E0FF&\bord3\3c&H000000&\fad(300,0)}実際にあった話", 11)
    E(FACT + 0.2, END, "card", r"{\an5\pos(360,420)\fs33\bord3\3c&H000000&\fad(300,0)}1946年、アメリカで\N目の奥から器具を差しこむ\N「ロボトミー手術」が始まった", 11)
    E(FACT + 0.9, END, "card", r"{\an5\pos(360,590)\fs33\bord3\3c&H000000&\fad(300,0)}1人の医師だけで約2,500人に行われ、\Nのちに危険性から行われなくなった", 11)
    E(END - 2.0, END, "card", r"{\an5\pos(360,790)\fs40\c&H80E0FF&\bord4\3c&H000000&\fad(200,0)}面白かったら\Nコメント・フォローで応援してね！", 12)
    S(0, END, "m 0 0 l 720 0 l 720 6 l 0 6", "&H60D0FF&", "&H00&", 12, r"\clip(0,0,0,6)\t(0,%d,\clip(0,0,720,6))" % int(END * 1000))
    for st_, en, text, _, _, who in R.LINES:
        if st_ >= FACT: continue
        E(st_, min(en, FACT), who, r"{\an5\pos(360,1000)\fad(60,100)}%s" % text, 9)
    head = R.ASS_HEAD.replace("{f}", R.FONT).replace("\n[Events]", STY.replace("{f}", R.FONT) + "\n[Events]")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

def mix(*xs):
    n = max(len(x) for x in xs); out = np.zeros(n)
    for x in xs: out[:len(x)] += x
    return out
def click(sec=0.06, f=3200):
    return R.lp(R.noise(sec), f) * R.dec(sec, 0.008)
def punch(big=1.0):
    return mix(R.lp(R.kick(140, 45, 0.35, 0.07), 900) * 1.2, R.lp(R.noise(0.35), 3500) * R.dec(0.35, 0.03) * 0.8 * big)
def build_sfx():
    B.toki_ep2(add, DUR, STOPT, LUNGE, RESUME, STAMP, DAWN, tail=TAIL)
    add(X.braam(2.4, 41.0), 0.05, 0.22)
    for k in range(4): add(mix(np.sin(2 * np.pi * 2200 * R.tt(0.08)) * R.dec(0.08, 0.02)), 1.0 + k * 1.3, 0.04)          # 器具の音
    add(X.stinger(1.4), RAISE, 0.3); add(K.suck(1.2), STOPT - 1.2, 0.3)
    add(click(0.08, 6000), STOPT - 0.05, 0.5); add(click(0.05, 4000), STOPT + 0.08, 0.4)
    add(R.whoosh(0.9, 200, 2000), STOPT, 0.4); add(X.tinnitus(1.6, 5200), STOPT + 0.1, 0.12); add(X.swell(1.0), STOPT + 0.2, 0.25)
    add(K.whoosh(0.25, 600, 8000), LUNGE + 0.15, 0.6); add(K.whoosh(0.2, 900, 9000), LUNGE + 0.35, 0.5)
    K.strike(add, COUNTER, 1.2)
    for k in range(10): add(click(0.025, 7000), CHAIN + k * 0.025, 0.2, 0.3)
    add(K.whoosh(0.5, 300, 4000), CHAIN + 0.1, 0.4)
    K.strike(add, SLAM, 1.4, 0.0, False); add(K.crumble(1.2, 30) * 0.8, SLAM + 0.05, 0.6)
    for k in range(18): add(mix(np.sin(2 * np.pi * (3000 + 300 * (k % 7)) * R.tt(0.15)) * R.dec(0.15, 0.04)), SLAM + 0.05 + k * 0.04, 0.05, 0.6 * (-1) ** k)   # ガラス
    add(X.swell(1.2), HANDS, 0.35); add(K.slash() * 0.5, HANDS + 0.3, 0.3)
    add(K.suck(0.3), XSLASH - 0.3, 0.4); add(K.slash(), XSLASH - 0.05, 1.0); add(K.slash(), XSLASH + 0.2, 0.9); K.strike(add, XSLASH, 1.3, 0.0, False); K.strike(add, XSLASH + 0.25, 1.1, 0.0, False)
    add(K.hit(0.8), KNEEL, 0.5)
    for k in range(12): add(click(0.04, 5000), CLOCK + k * 0.15, 0.25)                                     # 時計の秒針（速く）
    add(X.swell(2.0), CLOCK, 0.4); add(R.riser(2.0), CLOCK, 0.2)
    K.strike(add, FINISH, 1.6); add(K.boom_big(3.0), FINISH + 0.02, 0.8)
    for k in range(24): add(mix(np.sin(2 * np.pi * (2800 + 350 * (k % 9)) * R.tt(0.18)) * R.dec(0.18, 0.05)), FINISH + 0.25 + k * 0.03, 0.06, 0.6 * (-1) ** k)
    add(K.crumble(1.0, 16), FINISH + 0.3, 0.5); add(K.hit(0.9), FINISH + 1.0, 0.5)
    for k in range(3): add(click(0.06, 2500), RESUME + 0.1 * k, 0.3)                                          # ベルトがはずれる
    add(X.impact(2.0, 44.0), STAMP, 0.6); add(X.whip(0.35), STAMP - 0.12, 0.35)
    for k in range(6):
        f0 = 3200 + 600 * (k % 3); tt = R.tt(0.12)
        add(np.sin(2 * np.pi * (f0 + 2500 * tt) * tt) * R.dec(0.12, 0.04), DAWN + 0.8 + k * 0.55 + 0.1 * (k % 2), 0.035, 0.5 * (-1) ** k)

def render_mp4():
    R.LINES = [tuple(l) for l in json.load(open(LINES_JSON, encoding="utf-8"))]
    voice = np.load(VOICE_NPY)
    voice = np.concatenate([voice, np.zeros((max(0, R.n_(DUR + TAIL + 1) - len(voice)), 2))])
    R.MIX = np.zeros_like(voice); build_sfx()
    R.MIX = voice + X.duck(R.MIX, voice)
    out = R.MIX[: R.n_(DUR + TAIL)].copy()
    out[-R.n_(0.8):] *= np.linspace(1, 0, R.n_(0.8))[:, None]
    out = np.tanh(out * 1.1 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.8
    wav = os.path.join(HERE, "toki3_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "toki3_ui.ass"); build_ui(ass)
    if "--ui" in sys.argv: print("wrote", wav, ass); return
    mp4 = os.path.join(HERE, "toki_ep3.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(HERE, "frames_TOKI3_post", "%04d.png"), "-i", wav,
                    "-filter_complex", "[0:v]vignette=PI/5.5,ass=toki3_ui.ass[v]", "-map", "[v]", "-map", "1:a",
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
