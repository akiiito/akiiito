"""
make_reel_ep6.py ― 最終話「二人なら」のリール書き出し（frames_E6 + 合成音声/効果音/BGM + 中央寄り字幕 + HUD）
  python make_reel_ep6.py      → isekai_deathgame_ep6.mp4
"""
import os, re, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R
import reel_extras as X

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
NF, HOLD = 696, 24
PRE0, PRE = 348, 48      # cold open: 2 s half-speed look at the final thrust, one hook caption throughout
DUR = (NF + HOLD) / FPS
R.DUR = DUR
R.MIX = np.zeros((R.n_(DUR) + SR, 2))
add = R.add
def t(f): return f / FPS

R.VOICE["girl"] = (5.0, 1.0, 1.2, 0.15)
R.VOICE["champ"] = (-5.0, 0.88, 1.3, 0.3)
R.VOICE["rule"] = (-9.0, 0.82, 1.3, 0.5)
LZ0, STAIR0, RUN0, RUN1 = 8, 28, 44, 200
KILLS = [60, 70, 80, 90, 100, 108]
BOSS_IN, BOSS_X, LID, BOUNCE, WEDGE, MEGA, STAB = 120, 152, 198, 226, 262, 286, 372
VOID, TURN, VDASH, CORE_X, FIELD, SIT0, SIT1, SURV, SKILL, FADE0 = 380, 420, 452, 464, 508, 530, 566, 600, 620, 666
R.LINES = [
    (t(11), t(27), "効くかよ！", "きくかよ！", "shout", "hero"),
    (t(29), t(45), "道、作る！", "みち、つくる！", "other", "girl"),
    (t(47), t(60), "どけぇ！", "どけえ！", "resolve", "hero"),
    (t(130), t(152), "邪魔だッ！", "じゃまだ！", "resolve", "hero"),
    (t(160), t(196), "ゲームは、終わらない", "げーむは、おわらない", "foe", "rule"),
    (t(204), t(223), "閉じた！？", "とじた！？", "shout", "hero"),
    (t(230), t(248), "硬っ！", "かたっ！", "hero", "hero"),
    (t(256), t(282), "こじ開ける！", "こじあける！", "other", "girl"),
    (t(290), t(330), "ぐっ…おおおっ！", "ぐっ、おおおお！", "shout", "hero"),
    (t(336), t(370), "届けぇぇ！！", "とどけえええ！", "resolve", "hero"),
    (t(384), t(420), "壊せば、\\Nお前たちも消えるぞ", "こわせば、おまえたちも、きえるぞ", "foe", "rule"),
    (t(424), t(453), "二人なら、いける", "ふたりなら、いける", "resolve", "hero"),
    (t(455), t(468), "行こう！", "いこう！", "other", "girl"),
    (t(538), t(566), "…生きてる？", "いきてる？", "hero", "hero"),
    (t(570), t(604), "ここが、ゲームの外", "ここが、げーむのそと", "other", "girl"),
    (t(636), t(658), "…マジ？", "まじ？", "shout", "hero"),
]

def build_sfx():
    hb = R.heartbeat()
    add(R.charge(7 / FPS), 0, 0.5); add(R.zap(0.8), t(LZ0), 1.0); add(R.clang(1.0, 700), t(LZ0), 0.9); add(R.boom(1.4), t(LZ0), 0.9)
    for k in range(14):
        add(R.chime([523 * 2 ** (k / 12.0), 1047 * 2 ** (k / 12.0)], 0.03, 0.4), t(STAIR0 + 2 + k * 2), 0.3)
    f = RUN0
    while f < RUN1:
        add(R.step(), t(f), 0.38, 0.3 if (f // 5) % 2 else -0.3); f += 5
    for i, kf in enumerate(KILLS):
        add(R.thud(0.3), t(kf - 9), 0.5)
        add(R.whoosh(0.2, 800, 6000), t(kf - 4), 0.7, -0.5 if i % 2 else 0.5)
        add(R.clang(0.4, 900 + 70 * i), t(kf), 0.5); add(R.shatter(0.6), t(kf), 0.7)
        add(R.chime([880 * 2 ** (i * 2 / 12.0)], 0.01, 0.3), t(kf + 1), 0.45)
    for k in range(11):
        add(R.zap(0.6), t(56 + 13 * k), 0.4, 0.7 if k % 2 else -0.7)
    add(R.boom(2.0), t(BOSS_IN + 8), 1.1); add(R.thud(0.6), t(BOSS_IN + 8), 0.8)
    add(R.whoosh(0.3, 600, 7000), t(BOSS_X - 5), 1.0)
    add(R.clang(1.2, 500), t(BOSS_X), 1.0, -0.3); add(R.clang(1.2, 650), t(BOSS_X + 1), 1.0, 0.3)
    add(R.shatter(1.6), t(BOSS_X), 1.0); add(R.boom(2.2), t(BOSS_X), 1.1)
    add(R.chime([1568, 2093, 2637], 0.03, 0.6), t(BOSS_X + 2), 0.45)
    add(R.clang(1.4, 180), t(LID + 6), 1.0); add(R.boom(1.6), t(LID + 6), 0.9)
    add(R.whoosh(0.25, 900, 7000), t(BOUNCE - 5), 0.7); add(R.zap(0.5), t(BOUNCE), 0.8); add(R.clang(0.9, 1400), t(BOUNCE + 2), 0.8)
    for k, f in enumerate((232, 250, 268)):                              # countdown
        add(R.chime([784 * 2 ** (k * 2 / 12.0)], 0.01, 0.35), t(f), 0.5); add(hb, t(f), 0.6); add(hb, t(f + 9), 0.6)
    add(R.charge((MEGA - 232) / FPS), t(232), 0.5)
    add(R.clang(0.8, 400), t(WEDGE), 0.7); add(R.riser((MEGA - WEDGE) / FPS), t(WEDGE), 0.6)
    for k in range(4):
        add(R.thud(0.3), t(WEDGE + 4 + 5 * k), 0.5)
    add(R.boom(2.6), t(MEGA), 1.2); add(R.zap(1.4), t(MEGA), 1.0)
    n = R.n_((STAB - MEGA) / FPS)
    tt = np.arange(n) / R.SR
    roar = R.lp(np.random.RandomState(4).randn(n), 900) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * tt)) + 0.4 * np.sin(2 * np.pi * (70 + 30 * tt) * tt)
    add(R.fade(roar / np.abs(roar).max(), 0.05, 0.05), t(MEGA), 0.6)
    f = MEGA + 6
    while f < STAB - 6:
        add(R.zap(0.3), t(f), 0.35, 0.7 * np.sin(f)); f += 7
    add(R.riser((STAB - 330) / FPS), t(330), 0.7)
    add(R.clang(1.4, 800), t(STAB), 1.0); add(R.shatter(1.6), t(STAB), 1.0); add(R.boom(2.6), t(STAB), 1.2)
    f = VOID + 6
    while f < VDASH:
        add(hb, t(f), 0.6); f += 20
    for k in range(4):
        add(R.step(), t(VDASH + 3 * k), 0.5)
    add(R.whoosh(0.3, 600, 7000), t(CORE_X - 5), 1.0)
    add(R.clang(1.6, 500), t(CORE_X), 1.0, -0.3); add(R.clang(1.6, 750), t(CORE_X + 1), 1.0, 0.3)
    add(R.shatter(2.2), t(CORE_X), 1.1); add(R.boom(3.0), t(CORE_X), 1.3)
    add(R.fade(np.sin(2 * np.pi * 2800 * R.tt(1.6)) * R.dec(1.6, 0.6), 0.01, 0.4), t(CORE_X + 6), 0.05)
    add(R.chime([1047, 1319, 1568, 2093, 2637], 0.07, 1.6), t(CORE_X + 12), 0.5)                 # GAME CLEAR
    wind = R.fade(R.lp(R.hp(np.random.RandomState(9).randn(R.n_(t(FADE0 + 20 - FIELD))), 200), 900), 1.5, 1.0)
    add(wind / np.abs(wind).max(), t(FIELD), 0.10)
    for k, f in enumerate((FIELD + 20, FIELD + 44, FIELD + 70, FIELD + 104, FIELD + 130)):          # birds
        add(R.chime([2637 + 200 * (k % 3), 3136 + 150 * (k % 2)], 0.05, 0.25), t(f), 0.12, 0.6 if k % 2 else -0.6)
    add(R.chime([880, 1175, 1480], 0.06, 1.2), t(SURV), 0.35)
    add(R.chime([880, 1175, 1480, 1760, 2349], 0.06), t(SKILL), 0.5); add(R.zap(0.6), t(SKILL + 6), 0.35)
    add(R.chime([587, 880, 1175, 1760], 0.12, 1.8), t(FADE0 + 12), 0.4)

def build_music():
    beat = 0.1875
    ost = [82.4, 82.4, 98.0, 82.4, 123.5, 110.0, 98.0, 110.0]
    def drive(f0, f1, tr=1.0, vol=0.3):
        tt_, i = t(f0), 0
        while tt_ < t(f1):
            n = ost[i % 8] * tr
            add(R.fade(R.lp(R.saw(n, beat * 0.9) + R.saw(n * 2, beat * 0.9, 0.006), 750), 0.004, 0.03), tt_, vol)
            if i % 2 == 0: add(R.taiko(), tt_, 0.5)
            if i % 4 == 2: add(R.snare(), tt_, 0.3)
            if i % 8 in (3, 7): add(R.taiko(), tt_ + beat / 2, 0.28)
            tt_ += beat; i += 1
    drive(RUN0, BOSS_IN + 8, 2 ** (2 / 12))
    drive(BOSS_X, LID + 6, 2 ** (4 / 12), 0.34)
    add(R.pad([164.8, 246.9, 329.6, 493.9], t(LID - RUN0), 1600, 0.4, 0.2), t(RUN0), 0.2)
    add(R.pad([55, 82.4, 116.5, 164.8], t(MEGA - LID), 500, 0.3, 0.1), t(LID + 6), 0.45)
    drive(MEGA, STAB, 2 ** (5 / 12), 0.3)
    add(R.pad([174.6, 261.6, 349.2, 523.3, 698.5], t(STAB - MEGA), 2000, 0.6, 0.1), t(MEGA), 0.3)
    add(R.pad([51.9, 73.4, 103.8], t(VDASH - VOID), 400, 0.5, 0.3), t(VOID), 0.5)
    add(R.pad([146.8, 220, 293.7, 440], t(CORE_X - TURN), 1500, 0.8, 0.1), t(TURN), 0.3)
    # ending: warm major chords + a simple melody
    for k, (f0, ch) in enumerate(((FIELD, [130.8, 196.0, 261.6, 329.6, 392.0]), (FIELD + 48, [174.6, 220.0, 261.6, 349.2, 440.0]),
                                  (FIELD + 96, [196.0, 246.9, 293.7, 392.0, 493.9]), (FIELD + 144, [130.8, 196.0, 261.6, 329.6, 523.3]))):
        add(R.pad(ch, 2.6 if k < 3 else 3.6, 1800, 0.5, 1.2), t(f0), 0.36)
    mel = [659.3, 784.0, 1046.5, 987.8, 784.0, 880.0, 1046.5, 1174.7, 1318.5, 1174.7, 1046.5, 1568.0]
    for k, n in enumerate(mel):
        add(R.chime([n, n * 2], 0.01, 0.7), t(FIELD + 24 + k * 12), 0.22, 0.3 * np.sin(k))

EXTRA_STYLES = (
    "Style: other,{f},66,&H00FFF0A0,&H00FFF0A0,&H00401000,&H96000000,-1,0,0,0,100,100,1,0,1,7,3,5,30,30,0,1\n"
    "Style: foe,{f},68,&H00FFFFFF,&H00FFFFFF,&H001010C0,&H96000000,-1,0,0,0,100,100,1,0,1,8,3,5,30,30,0,1\n"
    "Style: hud,{f},54,&H003C3CFF,&H003C3CFF,&H00100818,&H96000000,-1,0,0,0,100,100,1,0,1,6,2,5,30,30,0,1\n"
    "Style: clear,{f},110,&H0050C820,&H0050C820,&H00103008,&H96000000,-1,0,0,0,100,100,2,0,1,8,3,5,30,30,0,1\n"
    "Style: skill,{f},64,&H00FFF060,&H00FFF060,&H00602000,&H96000000,-1,0,0,0,100,100,1,0,1,8,3,5,30,30,0,1\n")
def build_subs(path):
    head = X.head(R.ASS_HEAD.replace("\n[Events]", EXTRA_STYLES + "\n[Events]").replace("{f}", R.FONT), R.FONT)
    pop = r"{\an5\pos(360,%d)\fscx70\fscy70\t(0,90,\fscx112\fscy112)\t(90,170,\fscx100\fscy100)\fad(0,80)}"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(head)
        for st, en, text, _, style, _ in R.LINES:
            if text:
                p = pop % R.SUB_Y
                if style == "shout": p = p[:-1] + r"\frz-3}"
                fh.write("Dialogue: 0,%s,%s,%s,,0,0,0,,%s%s\n" % (R.ts(st), R.ts(en), style, p, text))
        marks = [(kf, "COMBO ×%d" % (i + 1)) for i, kf in enumerate(KILLS)] + [(BOSS_X, "COMBO ×7!!"), (BOSS_X + 36, None)]
        marks2 = [(232, "発射まで 3"), (250, "発射まで 2"), (268, "発射まで 1"), (MEGA, None)]
        for mk in (marks, marks2):
            for (f0, label), (f1, _) in zip(mk, mk[1:]):
                fh.write("Dialogue: 1,%s,%s,hud,,0,0,0,,%s%s\n" % (R.ts(t(f0)), R.ts(t(f1)), pop % 250, label))
        fh.write("Dialogue: 2,%s,%s,skill,,0,0,0,,%s%s\n" % (R.ts(t(STAIR0 + 4)), R.ts(t(RUN0 + 4)), pop % 540, "スキル発動【足場】"))
        fh.write("Dialogue: 2,%s,%s,clear,,0,0,0,,%s%s\n" % (R.ts(t(CORE_X + 12)), R.ts(t(FIELD + 14)), pop % 600, "GAME CLEAR"))
        fh.write("Dialogue: 2,%s,%s,skill,,0,0,0,,%s%s\n" % (R.ts(t(SKILL + 2)), R.ts(t(FADE0)), pop % 540, "スキル引き継ぎ：全部"))
        X.write(fh, 6, NF)
        cp = r"{\an5\pos(360,%d)\fscx70\fscy70\t(0,90,\fscx112\fscy112)\t(90,170,\fscx100\fscy100)\fad(0,80)}"
        fh.write("Dialogue: 3,%s,%s,next,,0,0,0,,%s%s\n" % (R.ts(t(FADE0)), R.ts(t(NF + HOLD)), cp % 1060,
                                                             "あなたなら、それでも壊す？\\Nコメントで教えて！"))   # comment prompt
    sh = PRE / FPS                                    # shift every cue behind the cold open; a single hook over it
    def sec(x):
        h, m, c = x.split(":"); return int(h) * 3600 + int(m) * 60 + float(c)
    txt = re.sub(r"Dialogue: (\d+),([\d:.]+),([\d:.]+),",
                 lambda m: "Dialogue: %s,%s,%s," % (m.group(1), R.ts(sec(m.group(2)) + sh), R.ts(sec(m.group(3)) + sh)),
                 open(path, encoding="utf-8").read())
    txt = "".join(l for l in txt.splitlines(True) if ",hook," not in l)
    big = r"{\an5\pos(360,%d)\fs56\fscx60\fscy60\t(0,100,\fscx110\fscy110)\t(100,180,\fscx100\fscy100)}"
    txt += "Dialogue: 3,%s,%s,hook,,0,0,0,,%s%s\n" % (R.ts(0), R.ts(sh + 0.25), big % 420, X.EP[6]["hook"])
    open(path, "w", encoding="utf-8").write(txt)

def main():
    src = os.path.join(HERE, "frames_E6")
    tmp = tempfile.mkdtemp(prefix="reel6_")
    order = [PRE0 + k // 2 for k in range(PRE)] + [min(k, NF) for k in range(1, NF + HOLD + 1)]
    for k, f in enumerate(order, 1):
        p = os.path.join(src, "%04d.png" % f)
        assert os.path.exists(p), p
        os.symlink(p, os.path.join(tmp, "%04d.png" % k))
    build_sfx(); build_music(); R.build_voice()
    body = R.MIX[: R.n_(DUR)].copy()
    R.MIX = np.zeros((R.n_(DUR) + SR, 2))             # cold-open sting: rising charge + impact, cut hard into the scene
    add(R.riser(PRE / FPS), 0, 0.5); add(R.zap(1.0), 0, 0.8); add(R.boom(1.6), 0.08, 1.0)
    for k in range(4):
        add(R.shatter(0.9), 0.1 + k * 0.4, 0.6, 0.8 * np.sin(k * 0.9))
    pre = R.MIX[: R.n_(PRE / FPS)].copy()
    pre[-R.n_(0.06):] *= np.linspace(1, 0, R.n_(0.06))[:, None]
    out = np.concatenate([pre, body])
    out[-R.n_(0.6):] *= np.linspace(1, 0, R.n_(0.6))[:, None]
    out = np.tanh(out * 1.25 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.84
    wav = os.path.join(HERE, "ep6_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((out * 32767).astype("<i2").tobytes())
    build_subs(os.path.join(HERE, "ep6_subs.ass"))
    mp4 = os.path.join(HERE, "isekai_deathgame_ep6.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "%04d.png"),
                    "-i", wav, "-vf", "ass=ep6_subs.ass", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                    "-preset", "slow", "-r", str(FPS), "-af", "volume=-3dB", "-c:a", "aac", "-b:a", "192k",
                    "-ar", str(SR), "-movflags", "+faststart", "-shortest", mp4], check=True, cwd=HERE)
    shutil.rmtree(tmp)
    print("wrote", mp4, DUR)

if __name__ == "__main__":
    main()
