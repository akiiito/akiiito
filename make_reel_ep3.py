"""
make_reel_ep3.py ― 第三話「ルール違反」のリール書き出し（frames_E3 + 合成音声/効果音/BGM + 中央寄り字幕 + タイマーHUD）
  python make_reel_ep3.py      → isekai_deathgame_ep3.mp4
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

R.VOICE["girl"] = (5.0, 1.0, 1.2, 0.15)
R.LINES = [
    (t(4), t(40), "斬れるわけないだろ！", "きれるわけないだろ！", "shout", "hero"),
    (t(46), t(88), "私を斬って。\\Nあなたは生きて", "わたしをきって。あなたは、いきて", "other", "girl"),
    (t(92), t(112), "断る！", "ことわる！", "resolve", "hero"),
    (t(118), t(150), "…あいつがルールか", "あいつが、るーるか", "hero", "hero"),
    (t(162), t(184), "うわっ！", "うわああ！", "shout", "hero"),
    (t(206), t(238), "ルールごと――", "るーるごと", "hero", "hero"),
    (t(240), t(268), "斬るッ！！", "きる！", "resolve", "hero"),
    (t(292), t(320), "私のスキル…『足場』！", "わたしのすきる、あしば！", "other", "girl"),
    (t(326), t(352), "走れ！！", "はしれ！", "shout", "hero"),
    (t(403), t(423), "足場が！", "あしばが！", "shout", "hero"),
    (t(426), t(446), "跳べっ！", "とべ！", "resolve", "hero"),
    (t(478), t(500), "いけぇぇ！", "いけえ！", "other", "girl"),
    (t(504), t(526), "うおおおっ！", "うおおおおお！", "resolve", "hero"),
    (t(556), t(586), "…終わった？", "おわった？", "hero", "hero"),
    (t(599), t(612), "", "とおもった？", "", "rule"),
    (t(618), t(640), "は？？？", "は？", "shout", "hero"),
    (t(646), t(672), "二人なら、いける", "ふたりなら、いける", "other", "girl"),
]
LASERS = [310 + k * 12 for k in range(13)]

def build_sfx():
    add(R.fade(R.crowd(DUR), 1.0, 1.0), 0, 0.035)
    add(R.gong(2.6, 82), t(1), 0.5)
    hb, f = R.heartbeat(), 6
    while f < 236:
        add(hb, t(f), 0.5); f += 19 - min(8, f // 30)
    for k, f in enumerate((24, 72, 120, 168, 216)):               # countdown ticks
        add(R.chime([1568], 0.01, 0.25), t(f), 0.35); add(R.chime([1175], 0.01, 0.2), t(f + 4), 0.2)
    add(R.boom(2.2), t(112), 0.9); add(R.fade(R.sweep(60, 140, 1.2, 1.0), 0.2, 0.4) * 0.5, t(112), 0.5)
    add(R.charge(0.5), t(148), 0.5); add(R.zap(1.0), t(160), 1.0, 0.4); add(R.boom(1.4), t(160), 0.9)
    add(R.charge((238 - 208) / FPS), t(208), 0.5)
    add(R.whoosh(0.3, 900, 7000), t(235), 0.8)
    add(R.zap(1.5), t(239), 1.0); add(R.shatter(1.6), t(240), 1.0); add(R.boom(2.0), t(240), 1.0)
    for k in range(14):                                           # stairway pops in
        add(R.chime([523 * 2 ** (k / 12.0), 1047 * 2 ** (k / 12.0)], 0.03, 0.4), t(300 + k * 2), 0.32)
    f = 304
    while f < 468:
        if not 424 <= f <= 440:
            add(R.step(), t(f), 0.38, 0.3 if (f // 5) % 2 else -0.3)
        f += 5
    for i, f in enumerate(LASERS):
        add(R.zap(0.7), t(f), 0.55, 0.7 if i % 2 else -0.7)
    add(R.zap(1.0), t(403), 0.9); add(R.shatter(1.0), t(403), 0.7); add(R.boom(1.3), t(403), 0.8)
    add(R.whoosh(0.7, 300, 4000), t(424), 0.7); add(R.thud(0.5), t(440), 0.6)
    add(R.riser((502 - 452) / FPS), t(452), 0.6)
    add(R.whoosh(0.9, 300, 5000), t(476), 0.7)
    add(R.clang(1.6, 600), t(502), 1.0); add(R.zap(1.5), t(502), 1.0); add(R.boom(2.0), t(502), 1.1)
    add(R.shatter(1.8), t(520), 1.0); add(R.boom(2.6), t(520), 1.2)
    add(R.fade(np.sin(2 * np.pi * 2800 * R.tt(1.2)) * R.dec(1.2, 0.5), 0.01, 0.3), t(524), 0.06)
    add(R.fade(R.sweep(900, 80, 0.5, 0.6), 0.01, 0.05), t(597), 0.4)   # the "nope" drop
    add(R.gong(3.2, 62), t(612), 0.85); add(R.boom(2.2), t(612), 1.0); add(R.boom(1.6), t(616), 0.8)
    add(R.fade(R.crowd(2.6, 200, 2600, 4.0), 0.2, 0.6), t(612), 0.3)   # ten thousand voices
    add(R.chime([880, 1175, 1480, 1760, 2349], 0.06), t(644), 0.45, -0.4)
    add(R.boom(1.8), t(684), 0.9); add(R.chime([587, 880, 1175], 0.12, 1.4), t(688), 0.3)

def build_music():
    add(R.pad([73.4, 110, 146.8, 174.6], t(240), 500, 0.6, 0.4), 0, 0.4)
    beat = 0.1875
    ost = [82.4, 82.4, 98.0, 82.4, 123.5, 110.0, 98.0, 110.0]
    tt_, i = t(296), 0
    while tt_ < t(502):
        fr = tt_ * FPS
        n = ost[i % 8] * (2 ** (2 / 12) if fr > 424 else 1.0)
        add(R.fade(R.lp(R.saw(n, beat * 0.9) + R.saw(n * 2, beat * 0.9, 0.006), 750), 0.004, 0.03), tt_, 0.3)
        if i % 2 == 0: add(R.taiko(), tt_, 0.5)
        if i % 4 == 2: add(R.snare(), tt_, 0.3)
        if i % 8 in (3, 7): add(R.taiko(), tt_ + beat / 2, 0.28)
        tt_ += beat; i += 1
    add(R.pad([164.8, 246.9, 329.6, 493.9], t(502 - 296), 1600, 0.4, 0.2), t(296), 0.17)
    for k, (fr, d) in enumerate(((550, 0.25), (556, 0.25), (562, 1.4))):          # fake victory fanfare
        add(R.pad([293.7, 370.0, 440.0, 587.3], d, 2600, 0.01, 0.15 if k < 2 else 0.5), t(fr), 0.38)
        add(R.taiko(), t(fr), 0.45)
    add(R.pad([58.3, 82.4, 116.5, 164.8], t(690 - 612), 600, 0.1, 1.0), t(612), 0.5)

EXTRA_STYLES = (
    "Style: other,{f},66,&H00FFF0A0,&H00FFF0A0,&H00401000,&H96000000,-1,0,0,0,100,100,1,0,1,7,3,5,30,30,0,1\n"
    "Style: hud,{f},54,&H003C3CFF,&H003C3CFF,&H00100818,&H96000000,-1,0,0,0,100,100,1,0,1,6,2,5,30,30,0,1\n"
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
        marks = [(24, "残り 10秒"), (72, "残り 9秒"), (120, "残り 8秒"), (168, "残り 7秒"), (216, "残り 6秒"), (240, "残り --秒"), (292, None)]
        for (f0, label), (f1, _) in zip(marks, marks[1:]):
            fh.write("Dialogue: 1,%s,%s,hud,,0,0,0,,%s%s\n" % (R.ts(t(f0)), R.ts(t(f1)), pop % 250, label))
        fh.write("Dialogue: 2,%s,%s,skill,,0,0,0,,%s%s\n" % (R.ts(t(244)), R.ts(t(272)), pop % 540, "ルール破壊！"))
        fh.write("Dialogue: 2,%s,%s,skill,,0,0,0,,%s%s\n" % (R.ts(t(300)), R.ts(t(324)), pop % 540, "スキル発動【足場】"))
        fh.write("Dialogue: 1,%s,%s,hud,,0,0,0,,%s%s\n" % (R.ts(t(622)), R.ts(t(672)), pop % 250, "10000 対 2"))

def main():
    src = os.path.join(HERE, "frames_E3")
    tmp = tempfile.mkdtemp(prefix="reel3_")
    for k in range(1, NF + HOLD + 1):
        p = os.path.join(src, "%04d.png" % min(k, NF))
        assert os.path.exists(p), p
        os.symlink(p, os.path.join(tmp, "%04d.png" % k))
    build_sfx(); build_music(); R.build_voice()
    out = R.MIX[: R.n_(DUR)]
    out[-R.n_(0.6):] *= np.linspace(1, 0, R.n_(0.6))[:, None]
    out = np.tanh(out * 1.25 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.84
    wav = os.path.join(HERE, "ep3_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((out * 32767).astype("<i2").tobytes())
    build_subs(os.path.join(HERE, "ep3_subs.ass"))
    mp4 = os.path.join(HERE, "isekai_deathgame_ep3.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "%04d.png"),
                    "-i", wav, "-vf", "ass=ep3_subs.ass", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                    "-preset", "slow", "-r", str(FPS), "-af", "volume=-3dB", "-c:a", "aac", "-b:a", "192k",
                    "-ar", str(SR), "-movflags", "+faststart", "-shortest", mp4], check=True, cwd=HERE)
    shutil.rmtree(tmp)
    print("wrote", mp4, DUR)

if __name__ == "__main__":
    main()
