"""
make_reel_ep4.py ― 第四話「一万対二」のリール書き出し（frames_E4 + 合成音声/効果音/BGM + 中央寄り字幕 + 撃破カウンター）
  python make_reel_ep4.py      → isekai_deathgame_ep4.mp4
"""
import os, subprocess, shutil, tempfile, wave
import numpy as np
import make_reel as R
import reel_extras as X

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
NF, HOLD = 672, 0        # cut on the cliffhanger: no title hold (loop / next video)
DUR = (NF + HOLD) / FPS
R.DUR = DUR
R.MIX = np.zeros((R.n_(DUR) + SR, 2))
add = R.add
def t(f): return f / FPS

R.VOICE["girl"] = (5.0, 1.0, 1.2, 0.15)
R.VOICE["champ"] = (-5.0, 0.88, 1.3, 0.3)
K1, K2, GK1, K3, GK2, K4 = 72, 96, 106, 118, 140, 158
LIFT0, GIVE, SLAB0, ZAP, SW0, SW1, BREAK, LAND, MASK, REVEAL = 216, 296, 302, 372, 400, 448, 460, 508, 600, 612
R.LINES = [
    (t(4), t(36), "一万って…マジかよ！", "いちまんって、まじかよ！", "shout", "hero"),
    (t(42), t(62), "来るよ！", "くるよ！", "other", "girl"),
    (t(66), t(88), "おらぁっ！", "おらあ！", "resolve", "hero"),
    (t(101), t(116), "はぁっ！", "はあっ！", "other", "girl"),
    (t(123), t(150), "まだ来る！", "まだくる！", "shout", "hero"),
    (t(166), t(200), "キリがない…！", "きりがない！", "hero", "hero"),
    (t(204), t(236), "上に逃げる！", "うえに、にげる！", "other", "girl"),
    (t(256), t(290), "登ってくる！？", "のぼってくる！", "shout", "hero"),
    (t(297), t(336), "私の足場、\\N全部あげる！", "わたしのあしば、ぜんぶあげる！", "other", "girl"),
    (t(350), t(388), "まとめて――", "まとめて", "hero", "hero"),
    (t(394), t(444), "消えろォォ！！", "きえろおおお！", "resolve", "hero"),
    (t(466), t(500), "…あと、一人？", "あと、ひとり？", "hero", "hero"),
    (t(540), t(580), "強くなったな", "つよくなったな", "foe", "champ"),
    (t(606), t(642), "待ってたぞ…“俺”", "まってたぞ。おれ", "foe", "champ"),
    (t(648), t(672), "…俺！？", "おれ！？", "shout", "hero"),
]
KILLS = [(K1, 1), (K2, 2), (GK1, 3), (K3, 4), (GK2, 5), (K4, 7)]

def build_sfx():
    add(R.fade(R.crowd(t(SW1), 200, 2600, 4.0), 0.3, 0.3), 0, 0.16)       # ten thousand voices, until the sweep
    add(R.gong(2.6, 70), t(1), 0.5)
    for k in range(24):                                                   # they pour over the wall
        add(R.thud(0.3), t(3 + k * 2.2), 0.22, 0.8 * np.sin(k * 1.7))
    f = 40
    while f < 200:                                                        # stampede
        add(R.step(), t(f), 0.22 + 0.001 * f, 0.6 * np.sin(f)); f += 3
    for i, (kf, _) in enumerate(KILLS):
        add(R.whoosh(0.22, 800, 6000), t(kf - 4), 0.7, 0.0 if i not in (2, 4) else -0.6)
        add(R.clang(0.5, 900 + 60 * i), t(kf), 0.55); add(R.shatter(0.7), t(kf), 0.7)
        add(R.chime([880 * 2 ** (i / 12.0)], 0.01, 0.3), t(kf + 1), 0.4)
    add(R.whoosh(1.6, 200, 3000), t(166), 0.5)                            # the 360 look-around
    hb, f = R.heartbeat(), 162
    while f < 214:
        add(hb, t(f), 0.55); f += 12
    add(R.boom(1.6), t(LIFT0), 0.9); add(R.riser((250 - LIFT0) / FPS), t(LIFT0), 0.5)
    for k in range(10):
        add(R.chime([523 * 2 ** (k / 12.0), 1047 * 2 ** (k / 12.0)], 0.03, 0.4), t(LIFT0 + 2 + k * 3), 0.3)
    add(R.thud(0.5), t(250), 0.7)
    for k in range(5):                                                    # the pile grows
        add(R.thud(0.4), t(258 + 11 * k), 0.5); add(R.fade(R.crowd(0.8, 300, 2000, 3.0), 0.05, 0.3), t(258 + 11 * k), 0.25)
    for k in range(12):                                                   # slabs snap onto the blade
        add(R.chime([659 * 2 ** (k / 12.0), 1319 * 2 ** (k / 12.0)], 0.02, 0.35), t(SLAB0 + 3 * k), 0.34)
        add(R.clang(0.25, 1200 + 80 * k), t(SLAB0 + 3 * k), 0.22)
    add(R.charge((ZAP - 344) / FPS), t(344), 0.55)
    add(R.zap(1.6), t(ZAP), 1.0); add(R.boom(2.2), t(ZAP), 1.1)
    add(R.riser((SW0 - 384) / FPS), t(384), 0.5)
    add(R.whoosh((SW1 - SW0) / FPS, 150, 5000), t(SW0), 1.0)
    add(R.zap((SW1 - SW0) / FPS), t(SW0), 0.7)
    for k in range(16):                                                   # everything shatters as the blade passes
        add(R.shatter(0.8), t(SW0 + 3 * k), 0.6, 0.8 * np.sin(k * 0.9)); add(R.taiko(), t(SW0 + 3 * k), 0.4)
    add(R.boom(2.8), t(SW1), 1.2); add(R.shatter(1.8), t(SW1 + 2), 0.9)
    add(R.fade(np.sin(2 * np.pi * 2800 * R.tt(1.2)) * R.dec(1.2, 0.5), 0.01, 0.3), t(SW1 + 4), 0.05)
    add(R.shatter(1.0), t(BREAK), 0.6)
    add(R.chime([1568, 2093, 2637], 0.05, 0.9), t(SW1 + 10), 0.4)
    add(R.zap(1.0), t(LAND), 0.9); add(R.boom(2.0), t(LAND), 1.1)
    for f in (522, 534, 546, 558):                                        # slow clap
        add(R.fade(R.hp(R.snare(), 900), 0.001, 0.05), t(f), 0.5, 0.2)
    f = LAND + 14
    while f < MASK - 12:
        add(R.step(), t(f), 0.45); f += 11
    add(R.shatter(0.9), t(MASK), 0.7); add(R.clang(0.6, 1500), t(MASK), 0.4)
    add(R.gong(3.2, 62), t(REVEAL), 0.9); add(R.boom(2.2), t(REVEAL), 1.0)
    add(R.boom(1.8), t(684), 0.9); add(R.chime([587, 880, 1175], 0.12, 1.4), t(688), 0.3)

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
    drive(40, 162)
    add(R.pad([73.4, 110, 146.8, 174.6], t(LIFT0 - 162), 500, 0.3, 0.3), t(162), 0.45)
    drive(LIFT0, 296, 2 ** (2 / 12))
    add(R.pad([164.8, 246.9, 329.6, 493.9, 659.3], t(SW0 - 296), 1800, 0.5, 0.2), t(296), 0.3)     # hopeful swell
    drive(344, SW1, 2 ** (4 / 12), 0.34)
    add(R.pad([58.3, 82.4, 116.5, 164.8], t(690 - LAND), 600, 0.1, 1.0), t(LAND), 0.5)

EXTRA_STYLES = (
    "Style: other,{f},66,&H00FFF0A0,&H00FFF0A0,&H00401000,&H96000000,-1,0,0,0,100,100,1,0,1,7,3,5,30,30,0,1\n"
    "Style: foe,{f},68,&H00FFFFFF,&H00FFFFFF,&H001010C0,&H96000000,-1,0,0,0,100,100,1,0,1,8,3,5,30,30,0,1\n"
    "Style: hud,{f},54,&H003C3CFF,&H003C3CFF,&H00100818,&H96000000,-1,0,0,0,100,100,1,0,1,6,2,5,30,30,0,1\n"
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
        marks = [(8, "10000 対 2")] + [(kf, "撃破 %d / 10000" % n) for kf, n in KILLS]
        for k in range(SW0, SW1, 2):
            marks.append((k, "撃破 %d / 10000" % int(7 + (9999 - 7) * ((k - SW0 + 2) / (SW1 - SW0)) ** 2)))
        marks += [(SW1, "撃破 9999 / 10000"), (LAND, None)]
        for (f0, label), (f1, _) in zip(marks, marks[1:]):
            anim = pop % 250 if f0 < SW0 or f0 >= SW1 else r"{\an5\pos(360,250)}"
            fh.write("Dialogue: 1,%s,%s,hud,,0,0,0,,%s%s\n" % (R.ts(t(f0)), R.ts(t(f1)), anim, label))
        fh.write("Dialogue: 2,%s,%s,skill,,0,0,0,,%s%s\n" % (R.ts(t(218)), R.ts(t(246)), pop % 540, "スキル発動【足場】"))
        fh.write("Dialogue: 2,%s,%s,skill,,0,0,0,,%s%s\n" % (R.ts(t(338)), R.ts(t(368)), pop % 540, "合体スキル【天断】"))
        fh.write("Dialogue: 1,%s,%s,hud,,0,0,0,,%s%s\n" % (R.ts(t(REVEAL + 4)), R.ts(t(672)), pop % 250, "残り 1"))
        X.write(fh, 4, NF)

def main():
    src = os.path.join(HERE, "frames_E4")
    tmp = tempfile.mkdtemp(prefix="reel4_")
    for k in range(1, NF + HOLD + 1):
        p = os.path.join(src, "%04d.png" % min(k, NF))
        assert os.path.exists(p), p
        os.symlink(p, os.path.join(tmp, "%04d.png" % k))
    build_sfx(); build_music(); R.build_voice()
    out = R.MIX[: R.n_(DUR)]
    out[-R.n_(0.15):] *= np.linspace(1, 0, R.n_(0.15))[:, None]
    out = np.tanh(out * 1.25 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.84
    wav = os.path.join(HERE, "ep4_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((out * 32767).astype("<i2").tobytes())
    build_subs(os.path.join(HERE, "ep4_subs.ass"))
    mp4 = os.path.join(HERE, "isekai_deathgame_ep4.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "%04d.png"),
                    "-i", wav, "-vf", "ass=ep4_subs.ass", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                    "-preset", "slow", "-r", str(FPS), "-af", "volume=-3dB", "-c:a", "aac", "-b:a", "192k",
                    "-ar", str(SR), "-movflags", "+faststart", "-shortest", mp4], check=True, cwd=HERE)
    shutil.rmtree(tmp)
    print("wrote", mp4, DUR)

if __name__ == "__main__":
    main()
