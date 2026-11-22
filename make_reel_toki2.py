"""
make_reel_toki1.py ― 「その罪、時効にさせない」第1話『光る絵の具』（35秒・1080x1920・24fps）
  1) --voice で声（toki2_voice.npy / toki2_lines.json）
  2) create_toki1.py → post_toki1.py で絵
  3) 引数なしで 絵＋声＋効果音＋BGM＋字幕 → toki_ep2.mp4
"""
import os, sys, json, subprocess, wave
import numpy as np
import make_reel as R
import s_sfx as X
import s_bgm as B
import s_hit as K
from toki_lines import TOKI2 as LINES0
from toki2_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
DUR = END; TAIL = 0.6
R.DUR = DUR; R.MIX = np.zeros((R.n_(DUR) + SR, 2)); add = R.add
R.VV_CAST.update({
    "sae": (345585728, 345585728, 0.0, 1.0, 1.1),         # るな
    "toki": (888753763, 888753763, 0.0, 0.95, 1.05),      # まお（おちつき）
    "owner": (1310138976, 1310138976, 0.0, 1.0, 1.1),    # 阿井田 茂
})
R.VOICE.update({k: (0, 0, 1.1, 0.04) for k in ("sae", "toki", "owner")})
R.SPK_REF_TEXT[:] = ["今日の放課後、少しだけ話せる", "写真、見せてくれる", "ううん、なんでもない", "また明日ね", "窓の外、きれいだね"]
R.LINES = list(LINES0)
R.RETAKE_MIN, R.RETAKES = 0.63, 10
R.VV_READ += [("罰金", "ばっきん"), ("利子", "りし"), ("時効", "じこう"), ("給料", "きゅうりょう")]
VOICE_NPY = os.path.join(HERE, "toki2_voice.npy"); LINES_JSON = os.path.join(HERE, "toki2_lines.json")


STY = (
    "Style: shape,{f},20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n"
    "Style: hana,{f},70,&H00FFFFFF,&H00FFFFFF,&H00306A30,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: boss,{f},70,&H00FFFFFF,&H00FFFFFF,&H00303030,&H00000000,-1,0,0,0,100,100,1,0,1,6,0,5,30,30,0,1\n"
    "Style: toki,{f},70,&H0080E8FF,&H0080E8FF,&H00102040,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: sae,{f},70,&H00FFFFFF,&H00FFFFFF,&H00704030,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
    "Style: owner,{f},70,&H00FFFFFF,&H00FFFFFF,&H00303030,&H00000000,-1,0,0,0,100,100,1,0,1,8,0,5,16,16,0,1\n"
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
    E(0, 2.9, "hook", r"{\an5\pos(360,195)\fs64\bord7%s\fad(0,200)}マッチを作るたび、" % pop, 10)
    E(0, 2.9, "hook", r"{\an5\pos(360,310)\fs64\bord7%s\fad(0,200)}{\c&H40D0FF&}あごの骨{\c&HFFFFFF&}が壊れていった" % pop, 10)
    E(0.3, 2.9, "card", r"{\an5\pos(360,445)\fs28\c&HDDDDDD&\bord3\3c&H000000&\fad(150,200)}実話をもとにしたフィクション", 10)
    E(STOPT + 0.3, RESUME, "card", r"{\an5\pos(360,120)\fs34\c&H80D8FF&\bord3\3c&H000000&\fad(250,150)}― 裁きの時間 ―", 9)
    E(12.5, 14.6, "card", r"{\an4\pos(46,560)\fs30\c&HDDDDDD&\bord3\3c&H000000&\fad(200,200)}時の裁判官", 10)
    E(12.5, 14.6, "count", r"{\an4\pos(40,620)\fs72\c&H80E0FF&\bord6\3c&H102030&\fad(200,200)%s}トキモリ" % pop, 10)
    # 擬音（マンガの描き文字）
    def boom(t0, text, x, y, fs, rot, col="&H30D0FF&", d=0.75):
        st = r"\frz%d\fscx240\fscy240\t(0,90,\fscx100\fscy100)\t(%d,%d,\fscx110\fscy110\alpha&HFF&)" % (rot, int(d * 1000) - 200, int(d * 1000))
        E(t0, t0 + d, "count", r"{\an5\pos(%d,%d)\fs%d\c%s\3c&H101010&\bord9\shad0%s}%s" % (x, y, fs, col, st, text), 13)
    boom(PUNCH1, "ドゴォッ！", 470, 380, 110, 10)
    boom(UPPER, "バキィッ！！", 250, 330, 110, -12)
    boom(UPPER + 0.4, "ゴンッ", 520, 200, 80, 8, "&HFFFFFF&", 0.6)
    boom(FALL + 0.1, "ドサッ", 230, 820, 76, -6, "&HFFFFFF&", 0.6)
    boom(FINISH, "ドガァァン！！", 360, 360, 120, -8, "&H2040FF&", 1.0)
    boom(RESUME + 0.1, "ジャラジャラ…", 360, 300, 70, 0, "&H40D8FF&", 1.6)
    st = r"\frz-12\fscx260\fscy260\t(0,110,\fscx100\fscy100)"
    S(STAMP, DAWN + 0.5, "m 190 462 l 530 462 l 530 648 l 190 648 l 190 462 m 212 484 l 212 626 l 508 626 l 508 484 l 212 484", "&H2020D0&", "&H00&", 11, r"\org(360,555)%s\fad(0,300)" % st)
    E(STAMP, DAWN + 0.5, "count", r"{\an5\pos(360,555)\fs130\b1\c&H2020D0&\3c&HFFFFFF&\bord2\shad0%s\fad(0,300)}有罪" % st, 12)
    S(FACT, END, "m 0 0 l 720 0 l 720 1280 l 0 1280", "&H000000&", "&H70&", 3, r"\fad(500,0)")
    E(FACT + 0.1, END, "card", r"{\an5\pos(360,300)\fs34\c&H80E0FF&\bord3\3c&H000000&\fad(300,0)}実際にあった話", 11)
    E(FACT + 0.2, END, "card", r"{\an5\pos(360,420)\fs33\bord3\3c&H000000&\fad(300,0)}1880年代のロンドンのマッチ工場では、\N有毒な黄リンで\Nあごの骨が壊れる病が出ていた", 11)
    E(FACT + 0.9, END, "card", r"{\an5\pos(360,590)\fs33\bord3\3c&H000000&\fad(300,0)}1888年、少女たちはストライキで\N会社に立ち向かい、要求を勝ちとった", 11)
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
    B.toki_ep2(add, DUR, STOPT, DASH, RESUME, STAMP, DAWN, tail=TAIL)
    add(X.braam(2.4, 41.0), 0.05, 0.22)
    for k in range(6): add(R.lp(R.noise(0.12), 2500) * R.dec(0.12, 0.03), 0.4 + k * 0.42, 0.05)          # マッチ棒の音
    add(R.lp(R.kick(90, 50, 0.3, 0.05), 900), 3.3, 0.35)                                                  # 机をたたく
    add(R.whoosh(0.4, 300, 2500), KICKBOX - 0.1, 0.3); add(punch(0.6), KICKBOX, 0.3)
    for k in range(8): add(click(0.03, 5000), KICKBOX + 0.25 + k * 0.06, 0.12, 0.5 * (-1) ** k)
    add(click(0.08, 6000), STOPT - 0.05, 0.5); add(click(0.05, 4000), STOPT + 0.08, 0.4)
    add(R.whoosh(0.9, 200, 2000), STOPT, 0.4); add(X.tinnitus(1.6, 5200), STOPT + 0.1, 0.12); add(X.swell(1.0), STOPT + 0.2, 0.25)
    add(K.whoosh(0.3, 400, 7000), DASH - 0.05, 0.6)                                                        # 踏みこみ
    K.strike(add, PUNCH1, 1.2); add(X.impact(1.2, 50.0), PUNCH1, 0.3)
    add(K.whoosh(0.18, 800, 8000), UPPER - 0.16, 0.5); K.strike(add, UPPER, 1.3, 0.0, False); add(K.whoosh(0.4, 600, 4000), UPPER + 0.02, 0.35)
    add(mix(R.lp(R.kick(70, 35, 0.5, 0.12), 700), 0.6 * R.lp(R.noise(0.6), 2500) * R.dec(0.6, 0.15)), UPPER + 0.4, 0.6)   # 天井
    add(K.crumble(1.0, 18), UPPER + 0.45, 0.6)
    add(K.hit(0.9), FALL + 0.1, 0.7)
    for k in range(4): add(np.sin(2 * np.pi * (1800 + 400 * k) * R.tt(0.25)) * R.dec(0.25, 0.08), FALL + 0.3 + k * 0.18, 0.04)   # ピヨピヨ
    add(X.swell(0.8), CHARGE, 0.4); add(R.riser(0.7), CHARGE, 0.2)
    K.strike(add, FINISH, 1.6); add(K.boom_big(3.0), FINISH + 0.02, 0.8); add(K.whoosh(1.0, 300, 3000), FINISH + 0.05, 0.4)
    add(K.crumble(1.6, 36), FINISH + 0.25, 0.7)                                                          # 壁が砕ける
    for k in range(14): add(R.lp(R.noise(0.1), 2500) * R.dec(0.1, 0.03), FINISH + 0.4 + k * 0.08, 0.18, 0.6 * (-1) ** k)
    add(R.lp(R.kick(70, 30, 0.5, 0.12), 500), FINISH + 1.4, 0.5)
    rr = np.random.default_rng(3)
    for k in range(40):                                                                                    # 金貨
        f0 = rr.uniform(2600, 5200); add(mix(np.sin(2 * np.pi * f0 * R.tt(0.3)) * R.dec(0.3, 0.06), 0.5 * np.sin(2 * np.pi * f0 * 2.7 * R.tt(0.3)) * R.dec(0.3, 0.03)),
                                         RESUME + 0.3 + rr.uniform(0, 2.4), 0.03, rr.uniform(-0.7, 0.7))
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
    wav = os.path.join(HERE, "toki2_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "toki2_ui.ass"); build_ui(ass)
    if "--ui" in sys.argv: print("wrote", wav, ass); return
    mp4 = os.path.join(HERE, "toki_ep2.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(HERE, "frames_TOKI2_post", "%04d.png"), "-i", wav,
                    "-filter_complex", "[0:v]vignette=PI/5.5,ass=toki2_ui.ass[v]", "-map", "[v]", "-map", "1:a",
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
