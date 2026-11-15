"""
make_reel.py
リール用 30秒版「異世界デスゲーム」を組み立てる。
  1) レンダリング済みフレームを連結（A1 → A2 → B[1..84] → C → battle → D → タイトル静止1秒）
  2) 効果音・BGM を numpy で合成、セリフ音声を Open JTalk (pyopenjtalk) で合成
  3) 中央寄りの大きな字幕（ASS）を焼き込み、H.264 + AAC の MP4 に書き出す

  python make_reel.py            （numpy / scipy / pyopenjtalk と ffmpeg が必要）
出力: isekai_deathgame_reel.mp4 / reel_audio.wav / reel_subs.ass
"""
import os, sys, subprocess, shutil, tempfile, wave
import numpy as np
from scipy.signal import butter, lfilter, resample

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, 48000
SEGS = [("frames_A1", 1, 32), ("frames_A2", 1, 64), ("frames_B", 1, 84), ("frames_C", 1, 264),
        ("frames", 1, 120), ("frames_D", 1, 120)]
HOLD = 24                                   # freeze the title card
T_A2, T_B, T_C, T_BT, T_D = 32 / FPS, 96 / FPS, 180 / FPS, 444 / FPS, 564 / FPS
TOTAL_F = sum(b - a + 1 for _, a, b in SEGS) + HOLD
DUR = TOTAL_F / FPS
rng = np.random.default_rng(7)

def tC(f): return T_C + f / FPS             # shot-local frame -> seconds
def tB(f): return T_B + f / FPS
def tBT(f): return T_BT + f / FPS
def tD(f): return T_D + f / FPS

# ---------------------------------------------------------------- dialogue (voice + subtitle)
# (start, end, subtitle, reading for TTS, style, voice)
LINES = [
    (0.10, 1.30, "もしも、あなたが――", "もしも、あなたが", "narr", "narr"),
    (1.70, 3.90, "異世界に転生したら？", "いせかいに、てんせいしたら？", "narr", "narr"),
    (4.30, 5.25, "…ここ、どこ？", "ここ、どこ？", "hero", "hero"),
    (5.45, 6.30, "剣…！？", "けん？", "hero", "hero"),
    (6.75, 7.55, "なんか来た！", "なんかきた！", "shout", "hero"),
    (tC(8), tC(30), "え、戦うの…？", "え、たたかうの？", "hero", "hero"),
    (tC(34), tC(66), "無理無理無理！", "むりむりむり！", "shout", "hero"),
    (tC(76), tC(99), "出口だ！", "でぐちだ！", "shout", "hero"),
    (tC(103), tC(126), "閉まった…", "しまった", "hero", "hero"),
    (tC(142), tC(160), "うわっ！？", "うわああ！", "shout", "hero"),
    (tC(168), tC(196), "", "たたかわなければ、しぬ", "", "rule"),
    (tC(200), tC(222), "死にたくない…", "しにたくない", "hero", "hero"),
    (tC(225), tC(256), "…やるしかない！", "やるしかない！", "resolve", "hero"),
    (tBT(44), tBT(62), "危なっ！", "あぶな！", "shout", "hero"),
    (tBT(72), tBT(96), "うおおおっ！", "うおおおおお！", "resolve", "hero"),
    (tD(26), tD(52), "…勝った？", "かった？", "hero", "hero"),
    (tD(70), tD(96), "え、まだあるの！？", "え、まだあるの？", "shout", "hero"),
]

# ---------------------------------------------------------------- dsp helpers
def n_(sec): return int(sec * SR)
def tt(sec): return np.arange(n_(sec)) / SR
def noise(sec): return rng.uniform(-1, 1, n_(sec))
def filt(x, kind, fc, order=2):
    b, a = butter(order, np.array(fc) / (SR / 2) if np.ndim(fc) else fc / (SR / 2), kind)
    return lfilter(b, a, x)
def lp(x, fc): return filt(x, "low", fc)
def hp(x, fc): return filt(x, "high", fc)
def bp(x, lo, hi): return filt(x, "band", [lo, hi])
def dec(sec, tau): return np.exp(-tt(sec) / tau)
def fade(x, a=0.01, r=0.05):
    x = x.copy()
    na, nr = min(len(x) // 2, n_(a)), min(len(x) // 2, n_(r))
    if na: x[:na] *= np.linspace(0, 1, na)
    if nr: x[-nr:] *= np.linspace(1, 0, nr)
    return x
def saw(freq, sec, det=0.0):
    t = tt(sec)
    ph = np.cumsum(np.broadcast_to(freq, t.shape)) / SR if np.ndim(freq) else freq * t
    out = 2 * ((ph * (1 + det)) % 1) - 1
    return out
def sweep(f0, f1, sec, curve=1.0):
    t = tt(sec) / sec
    f = f0 + (f1 - f0) * t ** curve
    return np.sin(2 * np.pi * np.cumsum(f) / SR)

MIX = np.zeros((n_(DUR) + SR, 2))
def add(sig, t, gain=1.0, pan=0.0):
    i = n_(max(t, 0))
    sig = sig[: len(MIX) - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    MIX[i:i + len(sig), 0] += sig * gain * l * 1.414
    MIX[i:i + len(sig), 1] += sig * gain * r * 1.414

# ---------------------------------------------------------------- sound effects
def kick(f0=110, f1=42, sec=0.45, tau=0.14):
    return sweep(f0, f1, sec, 0.35) * dec(sec, tau)
def thud(sec=0.7):
    return kick(90, 32, sec, 0.2) + 0.5 * lp(noise(sec), 300) * dec(sec, 0.12)
def taiko(): return kick(95, 50, 0.4, 0.12) + 0.25 * bp(noise(0.4), 800, 3000) * dec(0.4, 0.015)
def snare(): return 0.7 * hp(noise(0.18), 1800) * dec(0.18, 0.045) + 0.3 * kick(220, 150, 0.18, 0.04)
def step(): return 0.8 * lp(noise(0.16), 500) * dec(0.16, 0.035) + 0.5 * kick(140, 60, 0.16, 0.04)
def whoosh(sec=0.5, lo=400, hi=3000):
    env = np.sin(np.pi * tt(sec) / sec) ** 2
    return bp(noise(sec), lo, hi) * env
def clang(sec=1.2, base=520):
    t = tt(sec)
    out = sum(np.sin(2 * np.pi * base * m * t + i) * np.exp(-t / (0.5 / (1 + i * 0.5)))
              for i, m in enumerate((1, 1.56, 2.51, 3.72, 5.27, 6.76)))
    return out / 4 + 0.6 * hp(noise(sec), 3000) * dec(sec, 0.02)
def gong(sec=3.0, base=98):
    t = tt(sec)
    out = sum(np.sin(2 * np.pi * base * m * t) * np.exp(-t / (1.2 / (1 + i * 0.4)))
              for i, m in enumerate((1, 1.48, 2.0, 2.65, 3.43, 4.2)))
    return fade(out / 4, 0.004, 0.3)
def chime(notes, gap=0.07, sec=0.9):
    out = np.zeros(n_(gap * len(notes) + sec))
    for i, f in enumerate(notes):
        t = tt(sec)
        s = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.01 * t)) * np.exp(-t / 0.25)
        out[n_(i * gap): n_(i * gap) + len(s)] += s
    return out * 0.4
def zap(sec=0.9):
    t = tt(sec)
    crack = hp(noise(sec), 2500) * dec(sec, 0.07)
    fm = np.sign(np.sin(2 * np.pi * np.cumsum(90 + 700 * lp(noise(sec), 60) * 8) / SR))
    buzz = bp(fm, 300, 5000) * dec(sec, 0.22)
    return crack + 0.6 * buzz + 0.9 * kick(100, 30, sec, 0.3)
def charge(sec):
    t = tt(sec) / sec
    return (0.5 * sweep(180, 900, sec, 2.0) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 38 * tt(sec))))
            + 0.4 * bp(noise(sec), 1500, 6000) * t) * t ** 1.5
def heartbeat():
    out = np.zeros(n_(0.5))
    for off, g in ((0.0, 1.0), (0.15, 0.7)):
        k = kick(70, 38, 0.3, 0.07)
        out[n_(off): n_(off) + len(k)] += k * g
    return out
def horn(sec):
    t = tt(sec)
    s = lp(saw(311 * (1 + 0.04 * t / sec), sec) + saw(392 * (1 + 0.04 * t / sec), sec), 2200)
    return fade(s * (0.2 + 0.8 * (t / sec) ** 2), 0.03, 0.05) * 0.5
def pad(freqs, sec, cut=900, attack=0.6, release=0.8):
    out = sum(saw(f, sec, d) for f in freqs for d in (-0.004, 0.0, 0.005))
    return fade(lp(out, cut) / (3 * len(freqs)), attack, release)
def crowd(sec, lo=300, hi=1800, rate=1.5):
    am = 0.6 + 0.4 * lp(noise(sec), rate) * 12
    return bp(noise(sec), lo, hi) * np.clip(am, 0.1, 1.6)
def shatter(sec=1.0):
    out = hp(noise(sec), 3500) * dec(sec, 0.12) * 0.8
    for _ in range(45):
        t0, f = rng.uniform(0, 0.55), rng.uniform(1800, 7000)
        s = np.sin(2 * np.pi * f * tt(0.25)) * dec(0.25, 0.04) * rng.uniform(0.1, 0.35)
        out[n_(t0): n_(t0) + len(s)] += s[: len(out) - n_(t0)]
    return out + 0.7 * kick(120, 35, sec, 0.25)
def riser(sec):
    t = tt(sec) / sec
    return (bp(noise(sec), 500, 7000) * 0.5 + 0.4 * sweep(160, 1300, sec, 2.2)) * t ** 2.2
def boom(sec=1.6): return kick(70, 26, sec, 0.5) + 0.4 * lp(noise(sec), 180) * dec(sec, 0.4)

def build_sfx():
    # --- A1: night street, truck
    add(lp(noise(1.4), 220), 0.0, 0.12)
    add(fade(lp(noise(1.3), 140) * np.linspace(0.1, 1, n_(1.3)) ** 2, 0.02, 0.02), 0.0, 0.7, 0.4)
    add(horn(1.0), 0.25, 0.5, 0.5)
    add(boom(1.8), 1.15, 0.9)
    add(fade(np.sin(2 * np.pi * 3100 * tt(2.2)) * dec(2.2, 0.7), 0.01, 0.4), 1.2, 0.07)   # ear ring
    # --- A2: falling through the void
    add(pad([146.8, 220, 293.7, 440], 2.9, 1800, 0.8, 0.5), T_A2, 0.30)
    add(whoosh(2.4, 200, 1500), T_A2 + 0.2, 0.25)
    add(chime([587, 740, 880, 1175, 1480], 0.09), T_A2 + 0.9, 0.5)
    add(whoosh(0.5, 800, 6000), T_B - 0.35, 0.45)
    # --- arena bed: drone + crowd murmur
    add(pad([73.4, 110, 146.8, 174.6], T_BT - T_B + 0.3, 500, 1.0, 0.5), T_B, 0.42)
    add(fade(crowd(T_D - T_B + 2.0), 1.0, 1.0), T_B, 0.035)
    # --- B: awakening
    add(chime([880, 1175, 1480, 1760, 2349], 0.06), tB(29), 0.45, 0.3)        # sword appears
    add(gong(2.6, 110), tB(45), 0.5)                                          # DEATH GAME START
    add(fade(sweep(1500, 300, 0.55, 1.5), 0.05, 0.02) * 0.5, tB(60), 0.25)    # falling enemy
    add(thud(0.9), tB(74), 1.0)
    add(boom(1.2), tB(74), 0.6)
    # --- C: hesitation
    hb, t = heartbeat(), tC(20)
    while t < tC(222):                                                         # heart races, then stops
        k = (t - tC(20)) / (tC(222) - tC(20))
        add(hb, t, 0.55 + 0.35 * k)
        t += 0.78 - 0.36 * k
    for f, p in ((36, 0.2), (46, -0.2), (56, 0.2), (66, -0.2)):
        add(step(), tC(f), 0.45, p)
    add(whoosh(0.3), tC(30), 0.18, -0.6); add(whoosh(0.35), tC(45), 0.18, 0.6)
    add(whoosh(0.7), tC(71), 0.35)
    add(fade(sweep(160, 70, 0.22, 1.0), 0.005, 0.02) * 0.4 + whoosh(0.22, 300, 1500) * 0.6, tC(95), 0.5)
    add(clang(1.6, 310), tC(100), 0.85); add(thud(0.6), tC(100), 0.9)
    add(whoosh(0.5), tC(119), 0.4)
    add(charge((141 - 124) / FPS), tC(124), 0.45)
    add(zap(1.1), tC(141), 1.0, 0.3)
    add(gong(2.8, 82), tC(167), 0.6); add(boom(1.4), tC(170), 0.7)
    rat = hp(noise(1.1), 4000) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 23 * tt(1.1)))) * np.linspace(1, 0, n_(1.1))
    add(rat, tC(198), 0.06, 0.2)                                               # trembling sword
    add(clang(0.5, 900), tC(220), 0.18, 0.1)                                   # grips with both hands
    add(riser((264 - 222) / FPS + 0.05), tC(222), 0.5)
    for f, p in ((231, -0.2), (239, 0.2), (247, -0.2)):
        add(step(), tC(f), 0.6, p)
    # --- battle
    for f in (2, 7, 12, 17, 22):
        add(step(), tBT(f), 0.35 + f * 0.02)
    add(charge((40 - 29) / FPS), tBT(29), 0.5)
    add(zap(1.1), tBT(40), 1.0)
    add(whoosh(0.4, 300, 2500), tBT(45), 0.6, -0.5)
    add(step(), tBT(58), 0.6); add(step(), tBT(70), 0.7)
    add(whoosh(0.28, 900, 7000), tBT(78), 0.8)
    add(clang(1.4, 640), tBT(83), 1.0); add(boom(1.3), tBT(83), 1.0)
    add(hp(noise(0.3), 5000) * dec(0.3, 0.05), tBT(83), 0.6)
    add(thud(0.7), tBT(100), 0.9); add(thud(0.5), tBT(114), 0.6)
    # --- D: aftermath
    add(hp(noise(0.8), 3000) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 31 * tt(0.8)))) * np.linspace(0.2, 1, n_(0.8)),
        tD(1), 0.12)
    add(shatter(1.2), tD(20), 0.9)
    add(fade(crowd(2.6, 500, 3200, 3.0), 0.3, 0.9), tD(26), 0.22)              # cheer
    add(gong(3.0, 65), tD(68), 0.7); add(boom(2.0), tD(68), 0.8)
    add(boom(1.8), tD(101), 0.9); add(chime([587, 880, 1175], 0.12, 1.4), tD(104), 0.3)

def build_music():
    beat = 0.2                                                                 # 150 bpm eighths
    # tension pulse under the hesitation
    t = tC(24)
    while t < tC(220):
        add(taiko(), t, 0.22); t += 0.8
    # battle: bass ostinato + drums, with a hit-stop hole at the sword impact
    ost = [73.4, 73.4, 87.3, 73.4, 98.0, 73.4, 110.0, 98.0]
    t, i, hit = T_BT, 0, tBT(83)
    while t < T_D - 0.15:
        if not (hit - 0.02 < t < hit + 0.22):
            add(fade(lp(saw(ost[i % 8], beat * 0.9) + saw(ost[i % 8] * 2, beat * 0.9, 0.006), 700), 0.004, 0.03), t, 0.30)
            if i % 2 == 0: add(taiko(), t, 0.55)
            if i % 4 == 2: add(snare(), t, 0.32)
            if i % 8 in (3, 7): add(taiko(), t + beat / 2, 0.3)
        t += beat; i += 1
    add(pad([146.8, 220, 293.7], 3.3, 1400, 0.3, 0.3), T_BT, 0.2)
    add(pad([174.6, 233.1, 293.7], 1.6, 1600, 0.1, 0.3), tBT(84), 0.22)
    # victory fanfare (D major) then the ominous turn
    for k, (fr, d) in enumerate(((26, 0.25), (32, 0.25), (38, 1.3))):
        ch = [293.7, 370.0, 440.0, 587.3] if k < 2 else [293.7, 370.0, 440.0, 587.3, 740.0]
        add(pad(ch, d, 2600, 0.01, 0.15 if k < 2 else 0.6), tD(fr), 0.4)
        add(taiko(), tD(fr), 0.5)
    add(pad([58.3, 82.4, 116.5, 164.8], 2.2, 600, 0.3, 0.8), tD(66), 0.5)
    add(pad([73.4, 110, 146.8, 220], 1.6, 900, 0.3, 1.0), tD(101), 0.3)

# ---------------------------------------------------------------- voice (Open JTalk)
VOICE = {   # half_tone shift, base speed, gain, reverb
    "hero": (1.0, 1.12, 1.25, 0.0),
    "narr": (-3.0, 0.98, 1.15, 0.15),
    "rule": (-9.0, 0.82, 1.3, 0.5),
}
def reverb(x, amt):
    if amt <= 0: return x
    out = np.concatenate([x, np.zeros(n_(1.2))])
    for d, g in ((0.031, 0.5), (0.047, 0.42), (0.071, 0.36), (0.113, 0.3), (0.19, 0.22), (0.31, 0.15)):
        out[n_(d): n_(d) + len(x)] += x * g * amt * 2
    return out
def build_voice():
    import pyopenjtalk
    spans = []
    for st, en, _, say, _, who in LINES:
        ht, spd, gain, rv = VOICE[who]
        slot = en - st + 0.25
        for _try in range(4):
            x, sr = pyopenjtalk.tts(say, speed=spd, half_tone=ht)
            x = np.asarray(x, dtype=np.float64) / 32768.0
            nz = np.where(np.abs(x) > 0.01)[0]
            x = x[max(nz[0] - 200, 0): nz[-1] + 2000] if len(nz) else x
            ln = len(x) / sr
            if ln > slot: spd *= max(1.06, ln / slot)          # too long for its slot: speak faster
            elif ln < 0.45 and spd > 0.7: spd *= 0.8           # clipped-sounding one-word shout: slow down
            else: break
        if sr != SR: x = resample(x, int(len(x) * SR / sr))
        x = np.tanh(hp(x, 90) * 2.2) / 1.2                    # a bit of drive so it cuts through
        x = reverb(fade(x, 0.005, 0.03), rv)
        add(x, st, gain)
        spans.append((st, st + len(x) / SR))
        print("voice %-5s %5.2fs len %.2fs  %s" % (who, st, len(x) / SR, say))
    return spans

# ---------------------------------------------------------------- subtitles (ASS, centre-weighted)
FONT = "IPAPGothic"
ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: hero,{f},66,&H00FFFFFF,&H00FFFFFF,&H00301018,&H96000000,-1,0,0,0,100,100,1,0,1,7,3,5,30,30,0,1
Style: narr,{f},62,&H00FFFFFF,&H00FFFFFF,&H00301018,&H96000000,-1,0,0,0,100,100,2,0,1,7,3,5,30,30,0,1
Style: shout,{f},78,&H0040E6FF,&H0040E6FF,&H00200818,&H96000000,-1,0,0,0,100,100,1,0,1,8,3,5,30,30,0,1
Style: resolve,{f},80,&H00FFFFFF,&H00FFFFFF,&H003C14DC,&H96000000,-1,0,0,0,100,100,1,0,1,8,3,5,30,30,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
SUB_Y = 790          # a little below the middle: clear of the Reels UI (top bar / bottom caption area)
def ts(s):
    cs = int(round(s * 100))
    return "%d:%02d:%02d.%02d" % (cs // 360000, cs // 6000 % 60, cs // 100 % 60, cs % 100)
def build_subs(path):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(ASS_HEAD.replace("{f}", FONT))
        for st, en, text, _, style, _ in LINES:
            if not text: continue
            pop = r"{\an5\pos(360,%d)\fscx70\fscy70\t(0,90,\fscx108\fscy108)\t(90,160,\fscx100\fscy100)\fad(0,90)}" % SUB_Y
            if style == "shout":
                pop = pop[:-1] + r"\frz-3}"
            fh.write("Dialogue: 0,%s,%s,%s,,0,0,0,,%s%s\n" % (ts(st), ts(en), style, pop, text))

# ---------------------------------------------------------------- main
def main():
    for d, a, b in SEGS:
        for i in range(a, b + 1):
            assert os.path.exists(os.path.join(HERE, d, "%04d.png" % i)), "missing frame %s/%04d" % (d, i)
    tmp = tempfile.mkdtemp(prefix="reel_")
    k, last = 0, None
    for d, a, b in SEGS:
        for i in range(a, b + 1):
            k += 1
            last = os.path.join(HERE, d, "%04d.png" % i)
            os.symlink(last, os.path.join(tmp, "%04d.png" % k))
    for _ in range(HOLD):
        k += 1
        os.symlink(last, os.path.join(tmp, "%04d.png" % k))
    assert k == TOTAL_F

    build_sfx(); build_music()
    spans = build_voice()
    out = MIX[: n_(DUR)]
    out[-n_(0.6):] *= np.linspace(1, 0, n_(0.6))[:, None]
    out = np.tanh(out * 1.5 / max(1e-9, np.percentile(np.abs(out), 99.9))) * 0.93
    wav = os.path.join(HERE, "reel_audio.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((out * 32767).astype("<i2").tobytes())
    ass = os.path.join(HERE, "reel_subs.ass")
    build_subs(ass)
    mp4 = os.path.join(HERE, "isekai_deathgame_reel.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "%04d.png"),
           "-i", wav, "-vf", "ass=reel_subs.ass", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
           "-preset", "slow", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
           "-movflags", "+faststart", "-shortest", mp4]
    subprocess.run(cmd, check=True, cwd=HERE)
    shutil.rmtree(tmp)
    print("wrote", mp4, "frames", TOTAL_F, "dur", DUR)

if __name__ == "__main__":
    main()
