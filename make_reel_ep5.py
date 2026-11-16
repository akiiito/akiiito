"""
make_reel_ep5.py ― 第五話「俺 対 俺」のリール書き出し（frames_E5 + 合成音声/効果音/BGM + 中央寄り字幕 + HUD）
  python make_reel_ep5.py      → isekai_deathgame_ep5.mp4
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
R.VOICE["champ"] = (-5.0, 0.88, 1.3, 0.3)
CL = [44, 60, 74, 88]
CHG, BEAM, THROWS, CAGE, TRUTH, MEM0, MEMX = 116, 150, [178, 184, 190], 204, 216, 236, 262
RED0, SWING, BLOCK, CAGEX, JOIN, SHAT, XS, DISS, CATCH, SKY = 286, 344, 356, 404, 436, 478, 512, 612, 636, 652
R.LINES = [
    (t(2), t(34), "お前の技は、\\N全部知ってる", "おまえのわざは、ぜんぶしってる", "foe", "champ"),
    (t(47), t(60), "速っ！", "はやっ！", "shout", "hero"),
    (t(92), t(114), "動きが同じ…！？", "うごきがおなじ！", "hero", "hero"),
    (t(120), t(146), "なら雷刃で！", "なら、らいじんで！", "resolve", "hero"),
    (t(152), t(172), "それも俺の技だ", "それもおれのわざだ", "foe", "champ"),
    (t(174), t(198), "これなら！", "これなら！", "other", "girl"),
    (t(205), t(217), "きゃっ！", "きゃあ！", "other", "girl"),
    (t(219), t(262), "優勝者は、次の\\N“最後の一人”になる", "ゆうしょうしゃは、つぎの、さいごのひとりになる", "foe", "champ"),
    (t(266), t(302), "俺は…あいつを\\N守れなかった", "おれは、あいつを、まもれなかった", "foe", "champ"),
    (t(308), t(344), "だから、ここで終われ", "だから、ここでおわれ", "foe", "champ"),
    (t(358), t(382), "重っ…！", "おもっ！", "shout", "hero"),
    (t(386), t(403), "折れる…！", "おれる！", "hero", "hero"),
    (t(406), t(435), "一人で戦わないで！", "ひとりで、たたかわないで！", "other", "girl"),
    (t(440), t(477), "俺は、一人じゃない！", "おれは、ひとりじゃない！", "resolve", "hero"),
    (t(484), t(512), "うおおおっ！！", "うおおおおお！", "resolve", "hero"),
    (t(530), t(566), "…そうか。二人なら", "そうか。ふたりなら", "foe", "champ"),
    (t(570), t(612), "核は、あの眼の奥だ。\\N行け", "かくは、あのめのおくだ。いけ", "foe", "champ"),
    (t(656), t(674), "全部、終わらせる", "ぜんぶ、おわらせる", "resolve", "hero"),
]

def build_sfx():
    add(R.gong(2.6, 70), t(1), 0.45)
    for k in range(3):
        add(R.step(), t(36 + 3 * k), 0.5)
    add(R.whoosh(0.4, 500, 6000), t(36), 0.7)
    for i, c in enumerate(CL):
        add(R.whoosh(0.2, 800, 6000), t(c - 4), 0.6, 0.5 if i % 2 else -0.5)
        add(R.clang(0.8, 700 + 90 * i), t(c), 0.9, 0.4 if i % 2 else -0.4); add(R.thud(0.3), t(c), 0.5)
    add(R.whoosh(0.5, 300, 4000), t(100), 0.5)
    add(R.charge((BEAM - CHG) / FPS), t(CHG), 0.6)
    add(R.zap(0.8), t(BEAM), 1.0); add(R.zap(0.7), t(BEAM + 6), 0.8, 0.5); add(R.riser(14 / FPS), t(BEAM), 0.6)
    add(R.boom(2.2), t(BEAM + 14), 1.2); add(R.shatter(1.0), t(BEAM + 15), 0.6)
    for k, f0 in enumerate(THROWS):
        add(R.chime([523 * 2 ** (k / 6.0)], 0.02, 0.3), t(f0 - 3), 0.3, -0.5)
        add(R.whoosh(0.3, 400, 5000), t(f0), 0.6, -0.4)
        add(R.clang(0.4, 1000), t(f0 + 8), 0.6, 0.3); add(R.shatter(0.6), t(f0 + 8), 0.6, 0.3)
    add(R.clang(1.0, 300), t(CAGE), 0.9, -0.5); add(R.boom(1.2), t(CAGE), 0.7)
    for f in range(240, CAGEX - 8, 9):
        add(R.thud(0.25), t(f), 0.3, -0.6)
    add(R.chime([1047, 1319, 1568], 0.08, 1.2), t(MEM0), 0.3, 0.4)
    add(R.shatter(1.4), t(MEMX), 0.45, 0.4)
    hb, f = R.heartbeat(), 222
    while f < RED0:
        add(hb, t(f), 0.5); f += 18
    for k in range(10):
        add(R.clang(0.3, 300 + 40 * k), t(RED0 + 6 + 3 * k), 0.4); add(R.chime([220 * 2 ** (k / 12.0)], 0.02, 0.3), t(RED0 + 6 + 3 * k), 0.3)
    add(R.riser((BLOCK - 320) / FPS), t(320), 0.6)
    add(R.whoosh(0.5, 150, 3000), t(SWING), 1.0)
    add(R.clang(2.0, 260), t(BLOCK), 1.1); add(R.boom(2.4), t(BLOCK), 1.2); add(R.zap(1.0), t(BLOCK), 0.7)
    f = BLOCK + 8
    while f < SHAT:                                                      # grinding + heartbeat speeding up
        add(R.zap(0.35), t(f), 0.3, 0.6 * np.sin(f)); add(hb, t(f), 0.5); f += max(6, 16 - (f - BLOCK) // 12)
    for f in (388, 396, 402):
        add(R.fade(R.hp(R.snare(), 2500), 0.001, 0.03), t(f), 0.4)          # the blade cracking
    add(R.shatter(1.2), t(CAGEX), 0.9, -0.5); add(R.boom(1.4), t(CAGEX), 0.8, -0.3)
    for k in range(5):
        add(R.step(), t(CAGEX + 8 + 5 * k), 0.4, -0.5 + 0.1 * k)
    add(R.clang(1.2, 900), t(JOIN), 0.9); add(R.chime([880, 1175, 1480, 1760], 0.05, 1.0), t(JOIN), 0.45)
    add(R.riser((SHAT - JOIN - 4) / FPS), t(JOIN + 4), 0.7)
    add(R.shatter(1.8), t(SHAT), 1.1); add(R.boom(2.4), t(SHAT), 1.2)
    f = SHAT + 8
    while f < XS - 2:
        add(R.step(), t(f), 0.5, 0.3 if (f // 4) % 2 else -0.3); f += 4
    add(R.whoosh(0.3, 800, 7000), t(XS - 5), 0.9)
    add(R.clang(1.4, 600), t(XS), 1.0, -0.3); add(R.clang(1.4, 800), t(XS + 1), 1.0, 0.3); add(R.zap(1.2), t(XS), 0.9); add(R.boom(2.6), t(XS), 1.2)
    add(R.fade(np.sin(2 * np.pi * 2800 * R.tt(1.2)) * R.dec(1.2, 0.5), 0.01, 0.3), t(XS + 4), 0.05)
    add(R.thud(0.5), t(XS + 18), 0.6)
    add(R.chime([1568, 1976, 2349, 3136], 0.07, 1.6), t(DISS), 0.4); add(R.shatter(1.6), t(DISS), 0.35)
    add(R.whoosh(0.9, 600, 5000), t(DISS + 2), 0.4)
    add(R.clang(0.7, 1100), t(CATCH), 0.7, -0.4); add(R.chime([880, 1175, 1480, 1760, 2349], 0.06), t(CATCH + 2), 0.5)
    add(R.fade(R.sweep(900, 60, 0.5, 0.6), 0.01, 0.05), t(SKY - 2), 0.4)
    add(R.gong(3.2, 62), t(SKY + 7), 0.9); add(R.boom(2.4), t(SKY + 7), 1.1)
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
    add(R.pad([73.4, 110, 146.8], t(36), 500, 0.3, 0.2), 0, 0.4)
    drive(36, BEAM + 14)
    add(R.pad([73.4, 87.3, 110, 146.8, 174.6], t(RED0 - TRUTH + 20), 700, 0.6, 0.8), t(TRUTH - 10), 0.5)     # the truth: sad minor
    add(R.pad([55, 82.4, 110, 164.8], t(SHAT - RED0), 500, 0.5, 0.1), t(RED0), 0.45)
    drive(BLOCK, JOIN, 2 ** (-2 / 12), 0.22)
    add(R.pad([164.8, 246.9, 329.6, 493.9, 659.3], t(XS - JOIN), 1800, 0.3, 0.2), t(JOIN), 0.32)
    drive(JOIN, XS, 2 ** (4 / 12), 0.36)
    add(R.pad([146.8, 220, 293.7, 370, 440], t(SKY - XS - 16), 1400, 0.8, 1.0), t(XS + 16), 0.36)             # farewell: major
    add(R.pad([58.3, 82.4, 116.5, 164.8], t(690 - SKY), 600, 0.1, 1.0), t(SKY), 0.5)

EXTRA_STYLES = (
    "Style: other,{f},66,&H00FFF0A0,&H00FFF0A0,&H00401000,&H96000000,-1,0,0,0,100,100,1,0,1,7,3,5,30,30,0,1\n"
    "Style: foe,{f},68,&H00FFFFFF,&H00FFFFFF,&H001010C0,&H96000000,-1,0,0,0,100,100,1,0,1,8,3,5,30,30,0,1\n"
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
        marks = [(46, "一致率 100%"), (104, None)]
        marks2 = [(BLOCK + 4, "剣の耐久 80%"), (370, "剣の耐久 55%"), (384, "剣の耐久 31%"), (396, "剣の耐久 12%"), (420, "剣の耐久 5%"), (JOIN, None)]
        for mk in (marks, marks2):
            for (f0, label), (f1, _) in zip(mk, mk[1:]):
                fh.write("Dialogue: 1,%s,%s,hud,,0,0,0,,%s%s\n" % (R.ts(t(f0)), R.ts(t(f1)), pop % 250, label))
        fh.write("Dialogue: 2,%s,%s,skill,,0,0,0,,%s%s\n" % (R.ts(t(JOIN + 2)), R.ts(t(JOIN + 30)), pop % 540, "共鳴！"))
        fh.write("Dialogue: 2,%s,%s,skill,,0,0,0,,%s%s\n" % (R.ts(t(CATCH + 2)), R.ts(t(SKY + 2)), pop % 540, "スキル獲得【二刀流】"))

def main():
    src = os.path.join(HERE, "frames_E5")
    tmp = tempfile.mkdtemp(prefix="reel5_")
    for k in range(1, NF + HOLD + 1):
        p = os.path.join(src, "%04d.png" % min(k, NF))
        assert os.path.exists(p), p
        os.symlink(p, os.path.join(tmp, "%04d.png" % k))
    build_sfx(); build_music(); R.build_voice()
    out = R.MIX[: R.n_(DUR)]
    out[-R.n_(0.6):] *= np.linspace(1, 0, R.n_(0.6))[:, None]
    out = np.tanh(out * 1.25 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.84
    wav = os.path.join(HERE, "ep5_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((out * 32767).astype("<i2").tobytes())
    build_subs(os.path.join(HERE, "ep5_subs.ass"))
    mp4 = os.path.join(HERE, "isekai_deathgame_ep5.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "%04d.png"),
                    "-i", wav, "-vf", "ass=ep5_subs.ass", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                    "-preset", "slow", "-r", str(FPS), "-af", "volume=-3dB", "-c:a", "aac", "-b:a", "192k",
                    "-ar", str(SR), "-movflags", "+faststart", "-shortest", mp4], check=True, cwd=HERE)
    shutil.rmtree(tmp)
    print("wrote", mp4, DUR)

if __name__ == "__main__":
    main()
