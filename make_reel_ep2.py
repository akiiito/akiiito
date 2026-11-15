"""
make_reel_ep2.py ― 第二話「十対一」のリール書き出し（frames_E2 + 合成音声/効果音/BGM + 中央寄り字幕 + 撃破カウンター）
  python make_reel_ep2.py      → isekai_deathgame_ep2.mp4
"""
import os, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
NF, HOLD = 696, 24
DUR = (NF + HOLD) / FPS
R.DUR = DUR
R.MIX = np.zeros((R.n_(DUR) + SR, 2))
add = R.add
def t(f): return f / FPS

KILLS = [92, 132, 139, 142, 235, 237, 239, 241, 243, 540]
R.VOICE["girl"] = (5.0, 0.9, 1.2, 0.25)
R.LINES = [
    (t(2), t(40), "10体は聞いてない！", "じゅったいは、きいてない！", "shout", "hero"),
    (t(48), t(72), "待て待て待て！", "まてまてまて！", "shout", "hero"),
    (t(86), t(102), "…いける！", "いける！", "resolve", "hero"),
    (t(106), t(126), "3体同時！？", "さんたいどうじ？", "hero", "hero"),
    (t(130), t(152), "回転斬りッ！", "かいてんぎり！", "resolve", "hero"),
    (t(164), t(188), "雷まで撃つの！？", "かみなりまでうつの？", "shout", "hero"),
    (t(194), t(206), "…吸った！？", "すった？", "hero", "hero"),
    (t(228), t(250), "お返しだッ！", "おかえしだ！", "resolve", "hero"),
    (t(258), t(284), "あと1体", "あといったい", "hero", "hero"),
    (t(288), t(314), "…さっきの俺じゃん", "さっきのおれじゃん", "hero", "hero"),
    (t(322), t(344), "は？", "は？", "hero", "hero"),
    (t(348), t(372), "でっっか！！", "でっか！", "shout", "hero"),
    (t(380), t(402), "危なっ！", "あぶな！", "shout", "hero"),
    (t(422), t(448), "拳を、足場に――", "こぶしを、あしばに", "hero", "hero"),
    (t(458), t(488), "雷刃ッ！！", "らいじん！", "resolve", "hero"),
    (t(506), t(534), "…やったか？", "やったか？", "hero", "hero"),
    (t(566), t(598), "…人？", "ひと？", "hero", "hero"),
    (t(610), t(638), "たすけて…", "たすけて", "other", "girl"),
    (t(646), t(668), "", "なかまを、ころせ", "", "rule"),
    (t(664), t(684), "……は？", "は？", "hero", "hero"),
]

def build_sfx():
    add(R.fade(R.crowd(DUR), 1.0, 1.0), 0, 0.04)
    for k in range(10):                                           # ten landings
        add(R.thud(0.6), t(3 + int(k * 2.8)), 0.55 + 0.04 * k, (k % 5 - 2) * 0.4)
    add(R.gong(2.4, 98), t(1), 0.35)
    f = 46
    while f < 76:                                                 # stampede
        add(R.step(), t(f), 0.3 + (f - 46) * 0.012, ((f // 2) % 3 - 1) * 0.6); f += 2
    add(R.whoosh(0.3), t(80), 0.5)
    add(R.clang(1.2, 700), t(84), 0.95); add(R.thud(0.4), t(84), 0.6)
    add(R.whoosh(0.25, 900, 7000), t(89), 0.7)
    add(R.whoosh(0.75, 500, 6000), t(127), 0.8)
    add(R.whoosh(0.4, 900, 7000), t(136), 0.5)
    for i, kf in enumerate(KILLS[:9]):                            # every kill: shatter + rising ding
        add(R.shatter(0.9), t(kf), 0.6, ((i * 3) % 5 - 2) * 0.3)
        add(R.chime([880 * 2 ** (i / 12.0), 1320 * 2 ** (i / 12.0)], 0.05, 0.5), t(kf + 1), 0.45)
    add(R.charge((190 - 174) / FPS), t(174), 0.5)
    add(R.zap(1.2), t(190), 0.9)
    buzz = R.bp(np.sign(np.sin(2 * np.pi * 55 * R.tt(1.1))) * (0.6 + 0.4 * R.noise(1.1)), 200, 4000)
    add(R.fade(buzz, 0.05, 0.3), t(192), 0.16)                    # blade charged hum
    add(R.chime([659, 988, 1319, 1976], 0.07, 1.0), t(202), 0.5)  # SKILL GET
    add(R.whoosh(0.4, 600, 7000), t(230), 0.9); add(R.zap(1.3), t(234), 1.0)
    add(R.boom(1.2), t(235), 0.7)
    for f in (262, 270, 278, 286):
        add(R.step(), t(f), 0.3)
    for k in range(12):                                           # shards streaming in
        add(R.whoosh(0.35, 500 + k * 120, 3000 + k * 300), t(300 + k * 2.6), 0.25, (k % 3 - 1) * 0.7)
    add(R.riser((340 - 300) / FPS), t(300), 0.55)
    add(R.boom(1.6), t(320), 0.7); add(R.boom(2.0), t(338), 1.0)
    add(R.boom(1.2), t(352), 0.9); add(R.boom(1.2), t(364), 1.0)
    add(R.whoosh(0.45, 150, 1500), t(370), 0.9)
    add(R.boom(2.2), t(378), 1.2); add(R.thud(1.0), t(378), 1.0); add(R.shatter(0.8), t(379), 0.3)
    for f in (422, 427, 432):
        add(R.step(), t(f), 0.6)
    add(R.whoosh(0.9, 300, 4000), t(436), 0.7)
    add(R.riser((478 - 448) / FPS), t(448), 0.6)
    add(R.clang(1.6, 600), t(478), 1.0); add(R.zap(1.5), t(478), 1.0); add(R.boom(2.0), t(478), 1.1)
    add(R.thud(0.7), t(500), 0.8)
    crk = R.hp(R.noise(1.6), 3000) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 27 * R.tt(1.6)))) * np.linspace(0.2, 1, R.n_(1.6))
    add(crk, t(502), 0.14)
    add(R.shatter(1.6), t(540), 1.0); add(R.boom(2.4), t(540), 1.2)
    add(R.chime([1047, 1319, 1568, 2093], 0.06, 0.8), t(542), 0.4)
    hb, f = R.heartbeat(), 560
    while f < 668:
        add(hb, t(f), 0.6); f += 17
    add(R.gong(3.0, 65), t(640), 0.75); add(R.boom(1.8), t(644), 0.7)
    add(R.boom(1.8), t(684), 0.9); add(R.chime([587, 880, 1175], 0.12, 1.4), t(688), 0.3)

def build_music():
    beat = 0.1875                                                 # 160 bpm eighths
    ost = [73.4, 73.4, 87.3, 73.4, 110.0, 98.0, 87.3, 98.0]
    tt_, i = t(44), 0
    while tt_ < t(478):
        fr = tt_ * FPS
        quiet = 250 < fr < 344                                    # comedy beat: drums drop out
        gap = abs(fr - 84) < 2 or 190 <= fr < 196
        if not gap:
            n = ost[i % 8] * (2 ** (3 / 12) if fr > 344 else 1.0)  # key lift for the boss
            add(R.fade(R.lp(R.saw(n, beat * 0.9) + R.saw(n * 2, beat * 0.9, 0.006), 700), 0.004, 0.03), tt_, 0.16 if quiet else 0.3)
            if not quiet:
                if i % 2 == 0: add(R.taiko(), tt_, 0.5)
                if i % 4 == 2: add(R.snare(), tt_, 0.3)
                if i % 8 in (3, 7): add(R.taiko(), tt_ + beat / 2, 0.28)
        tt_ += beat; i += 1
    add(R.pad([73.4, 110, 146.8], t(44), 600, 0.2, 0.3), 0, 0.35)
    add(R.pad([146.8, 220, 293.7], t(250 - 44), 1400, 0.3, 0.5), t(44), 0.16)
    add(R.pad([174.6, 261.6, 349.2], t(478 - 344), 1500, 0.5, 0.2), t(344), 0.2)
    add(R.pad([58.3, 87.3, 116.5], t(540 - 482), 500, 0.3, 0.2), t(482), 0.4)
    add(R.pad([220, 277.2, 329.6, 440], t(640 - 548), 1600, 1.2, 0.6), t(548), 0.22)   # fragile hope
    add(R.pad([58.3, 82.4, 116.5, 164.8], t(690 - 640), 600, 0.2, 1.0), t(640), 0.5)   # ...crushed

EXTRA_STYLES = (
    "Style: other,{f},68,&H00FFF0A0,&H00FFF0A0,&H00401000,&H96000000,-1,0,0,0,100,100,1,0,1,7,3,5,30,30,0,1\n"
    "Style: hud,{f},50,&H0050D8FF,&H0050D8FF,&H00100818,&H96000000,-1,0,0,0,100,100,1,0,1,6,2,5,30,30,0,1\n"
    "Style: skill,{f},64,&H00FFF060,&H00FFF060,&H00602000,&H96000000,-1,0,0,0,100,100,1,0,1,8,3,5,30,30,0,1\n")
def build_subs(path):
    head = R.ASS_HEAD.replace("\n[Events]", EXTRA_STYLES + "\n[Events]").replace("{f}", R.FONT)
    pop = r"{\an5\pos(360,%d)\fscx70\fscy70\t(0,90,\fscx112\fscy112)\t(90,170,\fscx100\fscy100)\fad(0,80)}"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(head)
        for st, en, text, _, style, _ in R.LINES:
            if text:
                p = pop % R.SUB_Y
                if style == "shout": p = p[:-1] + r"\frz-3}"
                fh.write("Dialogue: 0,%s,%s,%s,,0,0,0,,%s%s\n" % (R.ts(st), R.ts(en), style, p, text))
        # kill counter, upper-middle (below the Reels top bar)
        marks = [44] + KILLS
        for n, f0 in enumerate(marks):
            f1 = marks[n + 1] if n + 1 < len(marks) else 600
            label = "撃破 %d / 10" % n if n < 10 else "撃破 10 / 10　全滅！"
            fh.write("Dialogue: 1,%s,%s,hud,,0,0,0,,%s%s\n" % (R.ts(t(f0)), R.ts(t(f1)), pop % 250, label))
        fh.write("Dialogue: 2,%s,%s,skill,,0,0,0,,%s%s\n" % (R.ts(t(202)), R.ts(t(226)), pop % 560, "スキル獲得【雷刃】"))

def main():
    src = os.path.join(HERE, "frames_E2")
    tmp = tempfile.mkdtemp(prefix="reel2_")
    for k in range(1, NF + HOLD + 1):
        p = os.path.join(src, "%04d.png" % min(k, NF))
        assert os.path.exists(p), p
        os.symlink(p, os.path.join(tmp, "%04d.png" % k))
    build_sfx(); build_music(); R.build_voice()
    out = R.MIX[: R.n_(DUR)]
    out[-R.n_(0.6):] *= np.linspace(1, 0, R.n_(0.6))[:, None]
    out = np.tanh(out * 1.25 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.84
    wav = os.path.join(HERE, "ep2_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((out * 32767).astype("<i2").tobytes())
    build_subs(os.path.join(HERE, "ep2_subs.ass"))
    mp4 = os.path.join(HERE, "isekai_deathgame_ep2.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "%04d.png"),
                    "-i", wav, "-vf", "ass=ep2_subs.ass", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                    "-preset", "slow", "-r", str(FPS), "-af", "volume=-3dB", "-c:a", "aac", "-b:a", "192k",
                    "-ar", str(SR), "-movflags", "+faststart", "-shortest", mp4], check=True, cwd=HERE)
    shutil.rmtree(tmp)
    print("wrote", mp4, DUR)

if __name__ == "__main__":
    main()
