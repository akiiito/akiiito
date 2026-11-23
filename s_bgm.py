"""
s_bgm.py ― 合成でつくるBGM（著作権の心配がない自作音源）。場面ごとに展開して、最初から最後まで途切れない
  piano(f) / strings(chord, sec) / music_box(f) / ostinato(...) を組み合わせる
  hana_part1(add, DUR) … ハナの物語パート1用
"""
import numpy as np
import make_reel as R

def nf(name):
    """音名→周波数（例 'A4', 'C#5'）"""
    names = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4, "F#": -3, "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}
    n, o = name[:-1], int(name[-1]); return 440.0 * 2 ** ((names[n] + (o - 4) * 12) / 12)

def piano(f, sec=2.4, vel=1.0):
    t = R.tt(sec)
    s = sum(a * np.sin(2 * np.pi * f * k * t * (1 + 0.0004 * k * k)) * np.exp(-t * (1.4 + 0.9 * k)) for k, a in ((1, 1.0), (2, 0.45), (3, 0.22), (4, 0.1)))
    hammer = R.hp(R.noise(0.02), 2000) * 0.05
    s[:len(hammer)] += hammer
    return s * vel * np.minimum(1, t / 0.004)

def music_box(f, sec=1.6):
    t = R.tt(sec)
    return (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 3.01 * t) + 0.15 * np.sin(2 * np.pi * f * 5.4 * t)) * np.exp(-t / 0.45)

def strings(freqs, sec, cut=1400, attack=0.5, release=0.9):
    t = R.tt(sec)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t)
    out = sum(R.saw(f * vib, sec, d) for f in freqs for d in (-0.005, 0.0, 0.006))
    return R.fade(R.lp(out, cut) / (3 * len(freqs)), attack, release)

def pad(freqs, sec, cut=700):
    return strings(freqs, sec, cut, 1.0, 1.2) * 0.8

CH = {  # 和音（低音, 和音3つ）
    "C": ("C3", ("C4", "E4", "G4")), "G": ("G2", ("B3", "D4", "G4")), "Am": ("A2", ("A3", "C4", "E4")), "F": ("F2", ("A3", "C4", "F4")),
    "Em": ("E2", ("G3", "B3", "E4")), "Dm": ("D3", ("D4", "F4", "A4")), "E": ("E2", ("G#3", "B3", "E4")),
}

def hana_part1(add, DUR, s_fight=5.85, s_run=6.9, s_stop=13.0, s_memory=15.9, s_end=26.3, tail=0.0):
    # ① 再会（0〜5.85）：オルゴール＋あたたかいストリングス（C-G-Am-F）
    bar = 1.45
    for i, c in enumerate(["C", "G", "Am", "F"]):
        t = 0.05 + i * bar; lo, ch = CH[c]
        add(pad([nf(n) for n in ch], bar + 0.8), t, 0.16, 0.0)
        add(piano(nf(lo), 2.0, 0.7), t, 0.10)
    mel = ["E5", "G5", "C6", "B5", "D6", "G5", "C6", "E6", "A5", "C6", "F5", "A5"]
    for i, n in enumerate(mel):
        add(music_box(nf(n)), 0.05 + i * 0.48, 0.13, 0.35 * (-1) ** i)
    # ② 逃げる（6.9〜13.0）：短調の速いストリングスの刻み＋低音（Am-F-G-E）、テンポ 150
    beat = 60 / 150
    prog = ["Am", "F", "G", "E"]
    t = s_run; k = 0
    while t < s_stop - 0.1:
        c = prog[(k // 8) % 4]; lo, ch = CH[c]
        f = nf(ch[k % 3]) * (2 if k % 2 else 1)
        add(strings([f], beat * 0.9, 2600, 0.01, 0.08), t, 0.16, 0.3 * (-1) ** k)
        if k % 8 == 0:
            add(pad([nf(lo) * 2, nf(ch[0]), nf(ch[2])], beat * 8.2, 900), t, 0.12)
            add(piano(nf(lo) / 2, 2.0, 1.0), t, 0.18)
        t += beat; k += 1
    # ③ 立ち止まる（13.0〜15.9）：息だけの静かな和音
    add(pad([nf("A3"), nf("C4"), nf("E4")], s_memory - s_stop + 0.8, 600), s_stop + 0.1, 0.09)
    # ④ 思い出（15.9〜26.3）：王道進行（F-G-Em-Am）のピアノ＋ストリングス＋メロディ（テンポ 80）
    beat = 60 / 80; bar = beat * 4
    prog = ["F", "G", "Em", "Am"]
    melody = [["A4", "C5", "F5", "E5"], ["D5", "B4", "G5", "F5"], ["E5", "G5", "B5", "A5"], ["C6", "B5", "A5", "E5"]]
    t = s_memory; i = 0
    while t < s_end - 0.2:
        c = prog[i % 4]; lo, ch = CH[c]
        add(pad([nf(n) for n in ch], bar + 1.0, 1100), t, 0.2)
        add(piano(nf(lo), 3.0, 0.9), t, 0.26)
        for j in range(4):
            tj = t + j * beat
            if tj < s_end - 0.2:
                add(piano(nf(ch[j % 3]), 1.6, 0.5), tj + beat / 2, 0.12, 0.3 * (-1) ** j)
                if i >= 1: add(piano(nf(melody[i % 4][j]), 2.2, 0.9), tj, 0.18, 0.1)
        t += bar; i += 1
    # ⑤ 残り7日（26.3〜）：低い持続音＋ぽつんと落ちるピアノ
    add(pad([nf("A2"), nf("E3"), nf("A3")], DUR + tail - s_end + 0.5, 500), s_end, 0.14)
    for j, n in enumerate(["E5", "C5", "A4", "E4", "C5", "A4"]):
        add(piano(nf(n), 2.4, 0.8), s_end + 0.6 + j * 0.75, 0.09)
    # 選択画面（DUR〜）：問いかけるような和音（F→G、答えを待つ）
    if tail > 0:
        for k, c in enumerate(["F", "G"]):
            lo, ch = CH[c]; t = DUR - 0.4 + k * (tail / 2)
            add(pad([nf(n) for n in ch], tail / 2 + 1.0, 1000), t, 0.16)
            add(piano(nf(lo), 2.5, 0.8), t, 0.18)
            for j, n in enumerate(ch): add(piano(nf(n) * 2, 1.8, 0.5), t + 0.2 + j * 0.22, 0.08)

def chip(f, sec=0.22, duty=0.3, vel=1.0):
    """ブロック世界らしいピコピコ音（矩形波）"""
    t = R.tt(sec)
    s = np.where((f * t) % 1.0 < duty, 1.0, -1.0)
    return R.lp(s, 3500) * np.exp(-t / (sec * 0.6)) * vel * np.minimum(1, t / 0.003)

def block_part1(add, DUR, s_build=15.6, s_night=19.2, tail=0.0):
    # ① 冒険（0〜15.6）：明るいピコピコ＋ピアノ（C-G-Am-F、テンポ 120）
    beat = 0.5; prog = ["C", "G", "Am", "F"]
    lead = ["E5", "G5", "C6", "G5", "D5", "G5", "B5", "G5", "C5", "E5", "A5", "E5", "F5", "A5", "C6", "A5"]
    t = 0.05; k = 0
    while t < s_build - 0.2:
        c = prog[(k // 8) % 4]; lo, ch = CH[c]
        if k % 8 == 0:
            add(pad([nf(n) for n in ch], beat * 8 + 0.6, 1200), t, 0.10)
        if k % 2 == 0: add(piano(nf(lo), 1.2, 0.8), t, 0.14)
        add(chip(nf(lead[k % 16]), 0.24, 0.3), t, 0.07, 0.25 * (-1) ** k)
        if k % 4 == 2: add(chip(nf(ch[2]) * 2, 0.12, 0.5), t + beat / 2, 0.04, -0.3)
        t += beat; k += 1
    # ② 日が沈む（15.6〜19.2）：音が減って、長い和音だけ
    add(pad([nf("A3"), nf("C4"), nf("E4")], s_night - s_build + 1.0, 800), s_build, 0.12)
    for j, n in enumerate(["E5", "C5", "A4"]):
        add(piano(nf(n), 2.0, 0.7), s_build + 0.3 + j * 0.9, 0.10)
    # ③ 夜・影ブロック（19.2〜）：低い刻み（Dm-Bb-Gm-A、テンポ 140）
    beat = 60 / 140; t = s_night; k = 0
    prog = [("D3", ("D4", "F4", "A4")), ("A#2", ("A#3", "D4", "F4")), ("G2", ("G3", "A#3", "D4")), ("A2", ("A3", "C#4", "E4"))]
    while t < DUR + tail - 0.6:
        lo, ch = prog[(k // 8) % 4]
        add(strings([nf(ch[k % 3]) / 2], beat * 0.9, 1800, 0.01, 0.08), t, 0.13, 0.3 * (-1) ** k)
        if k % 8 == 0:
            add(pad([nf(lo) * 2, nf(ch[0]), nf(ch[2])], beat * 8.2, 800), t, 0.12)
            add(piano(nf(lo) / 2, 2.0, 1.0), t, 0.16)
        t += beat; k += 1

def lofi_drums(add, t0, t1, bpm=84, gain=1.0):
    beat = 60 / bpm; t = t0; k = 0
    while t < t1:
        if k % 4 in (0, 2): add(R.lp(R.kick(80, 45, 0.35, 0.09), 900), t, 0.22 * gain)
        if k % 4 in (1, 3): add(R.hp(R.noise(0.12), 1500) * R.dec(0.12, 0.04), t, 0.07 * gain)
        add(R.hp(R.noise(0.05), 6000) * R.dec(0.05, 0.012), t + beat / 2, 0.035 * gain)
        t += beat; k += 1

def ai_matsuro(add, DUR, s_tense=28.0, s_calm=37.0, s_hope=41.1, tail=0.0):
    """ローファイ（作業用BGM風）→ 3年目の事件で緊張 → 5年目で前向きに"""
    beat = 60 / 84; bar = beat * 4
    prog = [("F", ("A3", "C4", "E4", "G4")), ("E", ("G#3", "B3", "D4", "E4")), ("Am", ("A3", "C4", "E4", "G4")), ("C", ("G3", "C4", "E4", "B4"))]
    def chords(t0, t1, gain, prog_):
        t = t0; i = 0
        while t < t1 - 0.3:
            c, notes = prog_[i % len(prog_)]; lo = CH[c][0] if c in CH else "A2"
            add(piano(nf(lo), 3.0, 0.8), t, 0.16 * gain)
            for j, n in enumerate(notes): add(piano(nf(n), 2.6, 0.6), t + j * 0.06, 0.07 * gain, 0.2 * (j - 1.5))
            add(pad([nf(n) for n in notes[:3]], bar + 0.6, 900), t, 0.06 * gain)
            t += bar; i += 1
    chords(0.0, s_tense, 2.2, prog); lofi_drums(add, 0.0, s_tense - 0.2, gain=2.0)
    # 事件：低い持続音と刻み
    add(pad([nf("D3"), nf("F3"), nf("G#3")], s_calm - s_tense + 0.6, 600), s_tense, 0.16)
    t = s_tense
    while t < s_calm:
        add(strings([nf("D3")], 0.18, 1500, 0.005, 0.05), t, 0.12); t += 60 / 140
    # 立ち直り（明るい進行）
    hope = [("F", ("F3", "A3", "C4", "E4")), ("G", ("G3", "B3", "D4", "G4")), ("Em", ("E3", "G3", "B3", "D4")), ("Am", ("A3", "C4", "E4", "G4"))]
    add(pad([nf("A3"), nf("C4"), nf("E4")], s_hope - s_calm + 0.6, 800), s_calm, 0.1)
    chords(s_hope, DUR + tail, 2.4, hope); lofi_drums(add, s_hope + bar, DUR + tail - 0.6, gain=2.0)

def disaster(add, DUR, s_quake=5.2, s_wave=29.2, s_end=55.2, tail=0.0):
    """災害もの：揺れの前は静か → 低い鼓動のような刻み → 波で厚く → 最後は静かな祈りの和音"""
    add(pad([nf("A2"), nf("E3")], s_quake + 0.5, 500), 0.0, 0.10)
    beat = 60 / 120; t = s_quake + 2.6; k = 0
    while t < s_end - 0.3:
        dense = 1.0 if t < s_wave else 1.6
        add(strings([nf("A2") * (2 if k % 2 else 1)], beat * 0.8, 1400, 0.005, 0.05), t, 0.10 * dense, 0.25 * (-1) ** k)
        if k % 8 == 0:
            add(pad([nf("A2"), nf("C3"), nf("E3"), nf("F3") if (k // 8) % 2 else nf("G3")], beat * 8.4, 700), t, 0.12 * dense)
            add(piano(nf("A1"), 2.5, 1.0), t, 0.18)
        t += beat; k += 1
    # 祈りの和音（F → C → G → Am）
    for i, c in enumerate(["F", "C", "G", "Am"]):
        lo, ch = CH[c]; t = s_end + i * 2.2
        if t > DUR + tail - 0.5: break
        add(pad([nf(n) for n in ch], 3.0, 1000), t, 0.15); add(piano(nf(lo), 3.0, 0.8), t, 0.16)
        for j, n in enumerate(ch): add(piano(nf(n) * 2, 2.2, 0.5), t + 0.25 + j * 0.3, 0.08)

def block_part2(add, DUR, hit1=11.9, cast=20.0, boss=35.6, hit2=42.3, count0=48.0, dawn=58.0, shadow=62.4, tail=0.0):
    """ブロック世界パート2：緊張の刻み → 被弾で無音に近く → バトル → ボス → 絶望 → 最後の10秒で盛り上げ → 夜明け（長調）→ 消えない影"""
    prog = [("D3", ("D4", "F4", "A4")), ("A#2", ("A#3", "D4", "F4")), ("G2", ("G3", "A#3", "D4")), ("A2", ("A3", "C#4", "E4"))]
    def ostinato(t0, t1, bpm, g, drums=False, lead=False):
        beat = 60 / bpm; t = t0; k = 0
        mel = ["D5", "F5", "A5", "F5", "A#4", "D5", "F5", "D5", "G4", "A#4", "D5", "A#4", "A4", "C#5", "E5", "A5"]
        while t < t1:
            lo, ch = prog[(k // 8) % 4]
            add(strings([nf(ch[k % 3]) / 2], beat * 0.9, 1800, 0.01, 0.08), t, 0.13 * g, 0.3 * (-1) ** k)
            if k % 8 == 0:
                add(pad([nf(lo) * 2, nf(ch[0]), nf(ch[2])], beat * 8.2, 800), t, 0.11 * g)
                add(piano(nf(lo) / 2, 2.0, 1.0), t, 0.15 * g)
            if drums:
                if k % 2 == 0: add(R.kick(100, 42, 0.3, 0.08), t, 0.3 * g)
                if k % 4 == 2: add(R.snare(), t, 0.16 * g)
                add(R.hp(R.noise(0.04), 7000) * R.dec(0.04, 0.01), t + beat / 2, 0.05 * g)
            if lead and k % 2 == 0: add(chip(nf(mel[(k // 2) % 16]), beat * 1.6, 0.3), t, 0.06 * g, 0.2)
            t += beat; k += 1
    ostinato(0.05, hit1 - 0.1, 132, 1.0)                                                   # ① 囲まれて、あたふた
    add(pad([nf("D3"), nf("A3"), nf("D4")], cast - hit1, 500), hit1 + 0.4, 0.10)            # ② 被弾：低いうなりだけ
    for j, n in enumerate(["A4", "F4", "D4"]): add(piano(nf(n), 2.4, 0.6), hit1 + 2.5 + j * 1.6, 0.08)
    add(R.riser(cast + 3.2 - (cast - 1.0)), cast - 1.0, 0.10)
    ostinato(cast + 3.2, boss - 0.2, 150, 1.0, drums=True, lead=True)                      # ③ 反撃のバトル
    for k in range(int((hit2 - boss) / 0.857)):                                             # ④ ボス：太鼓
        add(R.taiko(), boss + 0.4 + k * 0.857, 0.35)
    add(pad([nf("D2"), nf("A2"), nf("D3")], hit2 - boss, 400), boss, 0.14)
    add(pad([nf("D3"), nf("F3"), nf("A3")], count0 - hit2, 600), hit2 + 0.5, 0.11)          # ⑤ 絶望
    for j, n in enumerate(["D5", "C5", "A#4", "A4"]): add(piano(nf(n), 2.0, 0.6), hit2 + 1.0 + j * 1.2, 0.08)
    ostinato(count0, dawn - 0.4, 160, 1.15, drums=True)                                    # ⑥ 最後の10秒
    add(R.riser(dawn - count0 - 0.4), count0, 0.14)
    beat = 60 / 90; t = dawn; k = 0                                                         # ⑦ 夜明け：長調
    maj = [("D3", ("D4", "F#4", "A4")), ("A2", ("A3", "C#4", "E4")), ("B2", ("B3", "D4", "F#4")), ("G2", ("G3", "B3", "D4"))]
    while t < shadow - 0.2:
        lo, ch = maj[(k // 4) % 4]
        if k % 4 == 0:
            add(pad([nf(lo) * 2] + [nf(c) for c in ch], beat * 4.2, 1400), t, 0.13)
            add(piano(nf(lo), 2.4, 0.9), t, 0.14)
        add(piano(nf(ch[k % 3]) * 2, 1.4, 0.6), t, 0.07, 0.25 * (-1) ** k)
        t += beat; k += 1
    add(pad([nf("D3"), nf("F3"), nf("G#3")], DUR + tail - shadow, 500), shadow, 0.13)       # ⑧ 消えない影（不協和）
    for j in range(4): add(music_box(nf(["A5", "G#5", "F5", "D5"][j]), 1.6), shadow + 0.4 + j * 0.7, 0.06)

def block_part3(add, DUR, crack=10.4, black=20.4, reveal=33.0, eclipse=41.5, count0=50.0, blaze=56.4, dark=60.0, tail=0.0):
    """ブロック世界パート3：静かな朝（不穏）→ 割れて人の形 → 影化の発覚（低いうなり＋ピアノ）→ 正体（弦の悲しい和音）
       → 日食（太鼓）→ 最後の10秒で盛り上げ → 完全な闇（音が消えてオルゴールだけ）"""
    beat = 60 / 76; t = 0.05; k = 0                                                       # ① 朝：ニ短調のピアノ（ゆっくり）
    prog = [("D3", ("D4", "F4", "A4")), ("A#2", ("A#3", "D4", "F4")), ("G2", ("G3", "A#3", "D4")), ("A2", ("A3", "C#4", "E4"))]
    while t < crack - 0.3:
        lo, ch = prog[(k // 4) % 4]
        if k % 4 == 0:
            add(pad([nf(lo) * 2] + [nf(c) for c in ch], beat * 4.2, 900), t, 0.10); add(piano(nf(lo), 2.4, 0.8), t, 0.12)
        add(piano(nf(ch[k % 3]) * 2, 1.4, 0.5), t, 0.06, 0.25 * (-1) ** k)
        t += beat; k += 1
    add(pad([nf("D2"), nf("G#2"), nf("D3")], black - crack, 500), crack + 0.3, 0.13)      # ② 人の形：不協和のうなり
    for j in range(5): add(music_box(nf(["D6", "C#6", "A5", "G#5", "D5"][j]), 1.8), crack + 2.0 + j * 1.2, 0.05)
    add(pad([nf("D3"), nf("F3"), nf("A3")], reveal - black, 600), black + 0.6, 0.12)        # ③ 影化：低い弦＋ピアノ
    for j, n in enumerate(["A4", "G4", "F4", "E4", "D4", "C#4", "D4"]): add(piano(nf(n), 2.4, 0.6), black + 1.4 + j * 1.6, 0.08)
    add(strings([nf("A#2"), nf("D3"), nf("F3"), nf("A#3")], 4.4, 1200, 1.0, 1.2), reveal, 0.14)   # ④ 正体：悲しい和音
    add(strings([nf("G2"), nf("A#2"), nf("D3"), nf("G3")], 4.4, 1200, 1.0, 1.2), reveal + 4.2, 0.14)
    for j, n in enumerate(["D5", "A4", "A#4", "G4", "A4"]): add(piano(nf(n), 2.0, 0.7), reveal + 0.4 + j * 1.5, 0.08)
    for i in range(int((count0 - eclipse) / 0.79)):                                           # ⑤ 日食：太鼓
        add(R.taiko(), eclipse + 0.5 + i * 0.79, 0.3 + 0.03 * (i % 4 == 0))
    add(pad([nf("D2"), nf("A2"), nf("D3")], count0 - eclipse, 400), eclipse, 0.14)
    b = 60 / 160; t = count0; k = 0                                                         # ⑥ 最後の10秒：速い刻み
    while t < dark - 0.3:
        lo, ch = prog[(k // 8) % 4]
        add(strings([nf(ch[k % 3]) / 2], b * 0.9, 1800, 0.01, 0.08), t, 0.14, 0.3 * (-1) ** k)
        if k % 2 == 0: add(R.kick(100, 42, 0.3, 0.08), t, 0.3 * (1.3 if t > blaze else 1.0))
        if k % 4 == 2: add(R.snare(), t, 0.16)
        if k % 8 == 0: add(pad([nf(lo) * 2, nf(ch[0]), nf(ch[2])], b * 8.2, 800), t, 0.12)
        t += b; k += 1
    add(R.riser(dark - count0 - 0.3), count0, 0.15)
    add(pad([nf("D3"), nf("G#3"), nf("C4")], DUR + tail - dark, 500), dark + 0.8, 0.10)     # ⑦ 完全な闇
    for j in range(4): add(music_box(nf(["A5", "G#5", "F5", "D5"][j]), 1.8), dark + 1.2 + j * 0.8, 0.06)

def block_part4(add, DUR, burst=3.6, full=12.0, grab=17.4, glow=19.2, sun=29.0, vessel=33.8, dis=44.6, tower=51.0, tip=58.4, tail=0.0):
    """ブロック世界パート4：暴走（速い刻み）→ 影化100%（音が抜けて不協和）→ ルカが手を握る（あたたかいニ長調の弦）
       → 日食が明ける（全部の弦）→ 光の器（ピアノ）→ 消える（悲しい和音）→ 塔（低い太鼓）→ 指先（オルゴールだけ）"""
    add(pad([nf("D2"), nf("A2"), nf("D3")], burst + 0.2, 400), 0.0, 0.14)                   # ① 闇の中：低いうなり＋加速する太鼓
    for i in range(6): add(R.taiko(), 0.4 + i * 0.5, 0.22 + 0.03 * i)
    add(R.riser(burst - 0.2), 0.0, 0.14)
    prog = [("D3", ("D4", "F4", "A4")), ("A#2", ("A#3", "D4", "F4")), ("C3", ("C4", "E4", "G4")), ("A2", ("A3", "C#4", "E4"))]
    b = 60 / 160; t = burst; k = 0                                                          # ② 暴走：速い刻み
    while t < full - 0.2:
        lo, ch = prog[(k // 8) % 4]
        add(strings([nf(ch[k % 3]) / 2], b * 0.9, 1800, 0.01, 0.08), t, 0.14, 0.3 * (-1) ** k)
        if k % 2 == 0: add(R.kick(100, 42, 0.3, 0.08), t, 0.3)
        if k % 4 == 2: add(R.snare(), t, 0.16)
        if k % 8 == 0: add(pad([nf(lo) * 2, nf(ch[0]), nf(ch[2])], b * 8.2, 800), t, 0.12)
        t += b; k += 1
    add(pad([nf("D2"), nf("G#2"), nf("D3"), nf("D#3")], grab - full, 500), full, 0.14)      # ③ 100%：不協和
    for j in range(4): add(music_box(nf(["D6", "C#6", "G#5", "D5"][j]), 1.8) * 0.8, full + 1.0 + j * 1.1, 0.05)
    hope = [("D3", ("D4", "F#4", "A4")), ("A2", ("A3", "C#4", "E4")), ("B2", ("B3", "D4", "F#4")), ("G2", ("G3", "B3", "D4"))]
    beat = 60 / 72; t = grab + 0.2; k = 0                                                   # ④ 手を握る：あたたかい弦
    while t < vessel - 0.3:
        lo, ch = hope[(k // 4) % 4]
        if k % 4 == 0:
            g = 0.10 if t < sun else 0.15
            add(strings([nf(lo), nf(ch[0]), nf(ch[1]), nf(ch[2])], beat * 4.3, 1000 if t < sun else 1800, 0.8, 1.0), t, g)
            add(piano(nf(lo), 2.6, 0.8), t, 0.1)
        add(piano(nf(ch[k % 3]) * 2, 1.6, 0.5), t, 0.06, 0.25 * (-1) ** k)
        t += beat; k += 1
    mel = ["F#5", "E5", "D5", "A4", "B4", "A4", "D5", "E5"]                                 # ⑤ 日食が明ける：旋律
    for j, n in enumerate(mel): add(piano(nf(n), 2.2, 0.8), sun + 0.3 + j * beat, 0.09)
    add(strings([nf("B2"), nf("D3"), nf("F#3"), nf("B3")], 5.0, 1100, 1.0, 1.4), vessel, 0.12)   # ⑥ 光の器：短調へ
    add(strings([nf("G2"), nf("B2"), nf("D3"), nf("G3")], 5.0, 1100, 1.0, 1.4), vessel + 5.0, 0.12)
    add(strings([nf("E2"), nf("G2"), nf("B2"), nf("E3")], dis - vessel - 9.6 + 2.0, 1000, 1.0, 1.4), vessel + 10.0, 0.12)
    for j, n in enumerate(["B4", "A4", "F#4", "G4", "F#4", "E4", "D4"]): add(piano(nf(n), 2.0, 0.7), vessel + 0.4 + j * 1.5, 0.08)
    add(strings([nf("B2"), nf("D3"), nf("F#3"), nf("A3")], tower - dis + 0.4, 900, 1.5, 1.5), dis, 0.14)   # ⑦ 消える
    for j, n in enumerate(["F#5", "D5", "B4", "A4", "F#4"]): add(music_box(nf(n), 2.0), dis + 0.8 + j * 1.0, 0.05)
    add(pad([nf("D2"), nf("A2"), nf("C3")], tip - tower + 0.2, 400), tower, 0.15)            # ⑧ 塔：低い太鼓
    for i in range(int((tip - tower - 0.6) / 0.79)): add(R.taiko(), tower + 0.6 + i * 0.79, 0.26)
    add(pad([nf("D3"), nf("G#3"), nf("C4")], DUR + tail - tip, 500), tip + 1.4, 0.09)        # ⑨ 指先：オルゴールだけ
    for j in range(4): add(music_box(nf(["A5", "G#5", "F5", "D5"][j]) * (1 + 0.004 * j), 1.8), tip + 1.6 + j * 0.8, 0.06)

def block_hikari(add, DUR, grab=8.2, glow=9.0, wave=14.6, tip=24.6, hide=29.0, fin=31.8, tail=0.0):
    """単体回『触れたら影になる』：張りつめた低音＋心音 → 手を握る（あたたかい弦がそっと）
       → 光の波（全部の弦と旋律がひらく）→ 指先（音が引いてオルゴール）→ 最後の一文（短調の和音）"""
    add(pad([nf("D2"), nf("A2"), nf("D#3")], grab + 0.4, 450), 0.0, 0.13)                     # ① 来るな：不協和の低音
    for j in range(3): add(music_box(nf(["D6", "C#6", "A5"][j]), 1.8) * 0.7, 0.6 + j * 2.4, 0.04)
    hope = [("D3", ("D4", "F#4", "A4")), ("A2", ("A3", "C#4", "E4")), ("B2", ("B3", "D4", "F#4")), ("G2", ("G3", "B3", "D4"))]
    beat = 60 / 76; t = grab; k = 0                                                           # ② 手を握る：弦がそっと
    while t < wave - 0.2:
        lo, ch = hope[(k // 4) % 4]
        if k % 4 == 0:
            add(strings([nf(lo), nf(ch[0]), nf(ch[1]), nf(ch[2])], beat * 4.3, 900, 1.0, 1.0), t, 0.09)
            add(piano(nf(lo), 2.6, 0.7), t, 0.08)
        add(piano(nf(ch[k % 3]) * 2, 1.6, 0.45), t, 0.05, 0.25 * (-1) ** k)
        t += beat; k += 1
    add(R.riser(1.2), wave - 1.2, 0.12)
    t = wave; k = 0                                                                           # ③ 光の波：全部ひらく
    while t < tip - 0.3:
        lo, ch = hope[(k // 4) % 4]
        if k % 4 == 0:
            add(strings([nf(lo) / 2, nf(lo), nf(ch[0]), nf(ch[1]), nf(ch[2]), nf(ch[0]) * 2], beat * 4.4, 2200, 0.3, 1.2), t, 0.15)
            add(piano(nf(lo), 2.8, 1.0), t, 0.1)
            add(R.lp(R.kick(70, 38, 0.6, 0.1), 300), t, 0.22)
        add(piano(nf(ch[k % 3]) * 2, 1.6, 0.6), t, 0.06, 0.3 * (-1) ** k)
        t += beat; k += 1
    mel = ["F#5", "A5", "B5", "A5", "F#5", "E5", "D5", "E5", "F#5", "D5", "A4", "B4"]
    for j, n in enumerate(mel): add(piano(nf(n), 2.2, 0.85), wave + 0.4 + j * beat, 0.09)
    add(strings([nf("B2"), nf("D3"), nf("F#3"), nf("B3")], hide - tip + 0.4, 900, 1.2, 1.2), tip, 0.1)     # ④ 指先：短調へ
    for j, n in enumerate(["B5", "A5", "F#5", "D5"]): add(music_box(nf(n), 2.0), tip + 0.8 + j * 1.0, 0.05)
    add(strings([nf("G2"), nf("B2"), nf("D3"), nf("F#3")], fin - hide + 0.6, 1000, 1.0, 1.2), hide, 0.1)  # ⑤ なんでもない：Gmaj7
    for j, n in enumerate(["D5", "B4", "F#4"]): add(piano(nf(n), 2.4, 0.6), hide + 0.4 + j * 0.9, 0.07)
    add(pad([nf("E2"), nf("B2"), nf("D3"), nf("G3")], DUR + tail - fin, 600), fin, 0.12)     # ⑥ 最後の一文
    for j in range(4): add(music_box(nf(["G5", "F#5", "D5", "B4"][j]) * (1 + 0.003 * j), 2.0), fin + 0.3 + j * 0.75, 0.055)

def toki_ep1(add, DUR, stopt=12.3, report=17.0, flash=21.4, stamp=27.2, dawn=28.4, tail=0.0):
    """「その罪、時効にさせない」第1話：暗い工場（時計の秒針＋短調）→ 時が止まる（無音→鐘→裁きの低音）
       → 記者のフラッシュ（打ちこみで一気に）→ 有罪の判（特大の一撃）→ 夜明け（あたたかい長調）"""
    beat = 60 / 72
    add(pad([nf("A1"), nf("E2"), nf("C3")], stopt + 0.2, 380), 0.0, 0.14)                    # ① 暗い工場
    t = 0.0; k = 0
    while t < stopt - 0.05:                                                                  # 秒針
        add(R.lp(R.noise(0.03), 5000) * R.dec(0.03, 0.006) * (1.0 if k % 2 else 0.7), t, 0.16, 0.2 * (-1) ** k); t += 0.5; k += 1
    for j, n in enumerate(["E5", "C5", "B4", "A4", "G#4", "A4"]): add(music_box(nf(n), 1.9) * 0.8, 0.5 + j * 1.3, 0.045)
    add(strings([nf("D2"), nf("F2"), nf("G#2"), nf("B2")], stopt - 9.7, 700, 1.5, 0.3), 9.8, 0.12)      # 代わりはいくらでも：減和音
    add(pad([nf("D1"), nf("A1"), nf("D2")], flash - stopt, 300), stopt + 0.25, 0.16)        # ② 時が止まる：低い持続音
    for b in (stopt + 0.2, report - 0.2):
        bell = sum(np.sin(2 * np.pi * nf("D3") * m_ * R.tt(4.0)) * R.dec(4.0, 1.6 / (1 + i)) / (1 + i) for i, m_ in enumerate((1, 2.76, 5.4, 8.9)))
        add(bell * 0.6, b, 0.2)
    t = stopt + 2.0; k = 0
    while t < flash - 0.4:                                                                   # 裁きの鼓動（少しずつ速く）
        add(R.lp(R.kick(65, 35, 0.5, 0.12), 260), t, 0.25 + 0.1 * (t > report))
        t += beat * (2 if t < report else 1); k += 1
    add(strings([nf("D3"), nf("F3"), nf("A3"), nf("D4")], flash - report, 1200, 1.2, 0.3), report, 0.1)
    add(R.riser(1.4), flash - 1.4, 0.16)
    prog = [("E2", ("E3", "G3", "B3")), ("C2", ("C3", "E3", "G3")), ("D2", ("D3", "F#3", "A3")), ("B1", ("B2", "D#3", "F#3"))]
    b2 = 60 / 120; t = flash; k = 0                                                          # ③ 暴かれる：打ちこみ
    while t < stamp - 0.3:
        lo, ch = prog[(k // 4) % 4]
        if k % 4 == 0: add(strings([nf(lo), nf(ch[0]), nf(ch[1]), nf(ch[2]), nf(ch[0]) * 2], b2 * 4.2, 2400, 0.05, 0.4), t, 0.13)
        add(R.lp(R.kick(90, 40, 0.3, 0.08), 400), t, 0.26)
        if k % 2: add(R.lp(R.noise(0.12), 6000) * R.dec(0.12, 0.03), t, 0.1)
        t += b2; k += 1
    for j, n in enumerate(["B4", "E5", "G5", "F#5", "E5", "D5", "E5", "B4"]): add(piano(nf(n), 1.4, 0.9), flash + 0.1 + j * b2, 0.06)
    add(R.boom(3.0), stamp, 0.5)                                                             # ④ 有罪
    add(strings([nf("E2"), nf("B2"), nf("E3"), nf("G3")], dawn - stamp + 0.5, 900, 0.02, 0.6), stamp, 0.1)
    warm = [("C3", ("C4", "E4", "G4")), ("G2", ("G3", "B3", "D4")), ("A2", ("A3", "C4", "E4")), ("F2", ("F3", "A3", "C4"))]
    t = dawn; k = 0                                                                          # ⑤ 夜明け
    while t < DUR + tail - 0.2:
        lo, ch = warm[(k // 4) % 4]
        if k % 4 == 0:
            add(strings([nf(lo), nf(ch[0]), nf(ch[1]), nf(ch[2])], beat * 4.4, 1300, 1.0, 1.2), t, 0.1)
            add(piano(nf(lo), 2.6, 0.7), t, 0.07)
        add(piano(nf(ch[k % 3]) * 2, 1.6, 0.45), t, 0.045, 0.25 * (-1) ** k)
        t += beat; k += 1
    for j, n in enumerate(["E5", "G5", "C6", "B5", "G5", "A5"]): add(music_box(nf(n), 2.0), dawn + 0.6 + j * 1.0, 0.05)

def toki_ep2(add, DUR, stopt=11.6, dash=14.8, resume=22.0, stamp=27.2, dawn=28.4, tail=0.0):
    """第2話：暗い工場（短調・秒針）→ 時が止まる（鐘＋低音）→ 成敗（速い打ちこみ）→ 金貨の雨（明るい長調）→ 有罪 → 夜明け"""
    beat = 60 / 72
    add(pad([nf("A1"), nf("E2"), nf("C3")], stopt + 0.2, 380), 0.0, 0.14)
    t = 0.0; k = 0
    while t < stopt - 0.05:
        add(R.lp(R.noise(0.03), 5000) * R.dec(0.03, 0.006) * (1.0 if k % 2 else 0.7), t, 0.16, 0.2 * (-1) ** k); t += 0.5; k += 1
    for j, n in enumerate(["E5", "C5", "B4", "A4", "G#4", "A4"]): add(music_box(nf(n), 1.9) * 0.8, 0.5 + j * 1.3, 0.045)
    add(strings([nf("D2"), nf("F2"), nf("G#2"), nf("B2")], stopt - 8.9, 700, 1.5, 0.3), 9.0, 0.12)
    add(pad([nf("D1"), nf("A1"), nf("D2")], dash - stopt, 300), stopt + 0.25, 0.16)
    bell = sum(np.sin(2 * np.pi * nf("D3") * m_ * R.tt(4.0)) * R.dec(4.0, 1.6 / (1 + i)) / (1 + i) for i, m_ in enumerate((1, 2.76, 5.4, 8.9)))
    add(bell * 0.6, stopt + 0.2, 0.2)
    t = stopt + 1.6
    while t < dash - 0.3: add(R.lp(R.kick(65, 35, 0.5, 0.12), 260), t, 0.25); t += beat
    add(R.riser(0.8), dash - 0.8, 0.14)
    prog = [("D2", ("D3", "F3", "A3")), ("A#1", ("A#2", "D3", "F3")), ("C2", ("C3", "E3", "G3")), ("A1", ("A2", "C#3", "E3"))]
    b2 = 60 / 150; t = dash; k = 0                                                           # 成敗：速い打ちこみ
    while t < resume - 0.2:
        lo, ch = prog[(k // 4) % 4]
        if k % 4 == 0: add(strings([nf(lo), nf(ch[0]), nf(ch[1]), nf(ch[2]), nf(ch[0]) * 2], b2 * 4.2, 2600, 0.03, 0.3), t, 0.12)
        add(R.lp(R.kick(95, 40, 0.28, 0.07), 450), t, 0.3)
        add(R.lp(R.noise(0.08), 7000) * R.dec(0.08, 0.02), t + b2 / 2, 0.1)
        if k % 2: add(R.lp(R.noise(0.15), 5000) * R.dec(0.15, 0.05), t, 0.14)
        t += b2; k += 1
    for j, n in enumerate(["D5", "F5", "A5", "G5", "F5", "E5", "D5", "C#5", "D5", "A4", "D5", "F5", "E5", "D5", "C#5", "A4", "D5", "E5"]):
        add(piano(nf(n), 0.9, 0.9), dash + j * b2, 0.05)
    warm = [("C3", ("C4", "E4", "G4")), ("G2", ("G3", "B3", "D4")), ("A2", ("A3", "C4", "E4")), ("F2", ("F3", "A3", "C4"))]
    t = resume; k = 0                                                                        # 金貨：明るく
    while t < stamp - 0.3:
        lo, ch = warm[(k // 4) % 4]
        if k % 4 == 0: add(strings([nf(lo), nf(ch[0]), nf(ch[1]), nf(ch[2])], beat * 4.3, 1600, 0.3, 0.8), t, 0.11); add(piano(nf(lo), 2.4, 0.8), t, 0.07)
        add(piano(nf(ch[k % 3]) * 2, 1.4, 0.55), t, 0.05, 0.25 * (-1) ** k)
        t += beat / 2; k += 1
    add(R.boom(3.0), stamp, 0.5)
    add(strings([nf("C2"), nf("G2"), nf("C3"), nf("E3")], dawn - stamp + 0.5, 900, 0.02, 0.6), stamp, 0.1)
    t = dawn; k = 0
    while t < DUR + tail - 0.2:
        lo, ch = warm[(k // 4) % 4]
        if k % 4 == 0: add(strings([nf(lo), nf(ch[0]), nf(ch[1]), nf(ch[2])], beat * 4.4, 1300, 1.0, 1.2), t, 0.1); add(piano(nf(lo), 2.6, 0.7), t, 0.07)
        add(piano(nf(ch[k % 3]) * 2, 1.6, 0.45), t, 0.045, 0.25 * (-1) ** k)
        t += beat; k += 1
    for j, n in enumerate(["E5", "G5", "C6", "B5", "G5", "A5"]): add(music_box(nf(n), 2.0), dawn + 0.6 + j * 1.0, 0.05)

def block_final(add, DUR, clench=6.0, pillars=8.3, swing=9.6, slash=12.8, catch=13.9, swarm=17.0, domain=19.1, rise=21.5, fhit=22.3, sun=23.2, dawn=27.6, title=34.4, tail=0.0):
    """完結編：重い低音（巨人）→ 決意（太鼓が入る）→ 戦闘（速い打ちこみ・弦のスタッカート）→ ルカの手（あたたかい一瞬）
       → 群れ（さらに速く）→ 反転の世界（無音に近い高音）→ とどめ（全部）→ 夜明け（メインテーマ）→ 完"""
    add(pad([nf("C1"), nf("G1"), nf("C#2")], clench + 0.4, 300), 0.0, 0.16)
    for j in range(3): add(music_box(nf(["G5", "F#5", "C5"][j]), 1.8) * 0.7, 0.4 + j * 1.6, 0.04)
    t = clench; k = 0; b = 60 / 96
    while t < pillars - 0.1:
        add(R.lp(R.kick(70, 35, 0.5, 0.15), 300), t, 0.3); t += b; k += 1
    add(strings([nf("C2"), nf("D#2"), nf("G2"), nf("C3")], pillars - clench, 900, 1.0, 0.2), clench, 0.12)
    add(R.riser(1.0), pillars - 1.0, 0.15)
    prog = [("C2", ("C3", "D#3", "G3")), ("G#1", ("G#2", "C3", "D#3")), ("A#1", ("A#2", "D3", "F3")), ("G1", ("G2", "B2", "D3"))]
    def battle(t0, t1, bpm, g=1.0):
        b2 = 60 / bpm; t = t0; k = 0
        while t < t1 - 0.05:
            lo, ch = prog[(k // 4) % 4]
            if k % 4 == 0: add(strings([nf(lo), nf(ch[0]), nf(ch[1]), nf(ch[2]), nf(ch[0]) * 2], b2 * 4.1, 2800, 0.02, 0.25), t, 0.12 * g)
            add(R.lp(R.kick(95, 40, 0.26, 0.07), 450), t, 0.3 * g)
            add(R.lp(R.noise(0.06), 8000) * R.dec(0.06, 0.015), t + b2 / 2, 0.09 * g)
            if k % 2: add(R.lp(R.noise(0.14), 5000) * R.dec(0.14, 0.05), t, 0.14 * g)
            add(piano(nf(ch[k % 3]) * 2, 0.5, 0.8), t, 0.04 * g, 0.3 * (-1) ** k)
            t += b2; k += 1
    battle(pillars, catch, 160)
    add(strings([nf("D#3"), nf("G3"), nf("A#3"), nf("D4")], swarm - catch, 1400, 0.6, 0.4), catch, 0.12)    # ルカの手
    for j, n in enumerate(["G5", "A#5", "D6", "C6"]): add(music_box(nf(n), 2.0), join_t := catch + 0.9 + j * 0.7, 0.05)
    battle(swarm - 0.3, domain, 176, 1.1)
    add(pad([nf("C5"), nf("G5"), nf("D6")], rise - domain, 6000), domain, 0.05)           # 反転：高い持続音だけ
    add(R.riser(rise - domain), domain, 0.12)
    battle(rise, sun + 0.4, 176, 1.25)
    add(R.boom(3.5), fhit, 0.6)
    theme = [("C3", ("C4", "E4", "G4")), ("G2", ("G3", "B3", "D4")), ("A2", ("A3", "C4", "E4")), ("F2", ("F3", "A3", "C4"))]
    t = sun + 0.6; k = 0; b3 = 60 / 80
    while t < DUR + tail - 0.3:
        lo, ch = theme[(k // 4) % 4]
        if k % 4 == 0:
            add(strings([nf(lo) / 2, nf(lo), nf(ch[0]), nf(ch[1]), nf(ch[2])], b3 * 4.4, 2000, 0.8, 1.2), t, 0.13)
            add(piano(nf(lo), 2.8, 0.9), t, 0.08)
        add(piano(nf(ch[k % 3]) * 2, 1.6, 0.5), t, 0.05, 0.25 * (-1) ** k)
        t += b3; k += 1
    mel = ["E5", "G5", "C6", "B5", "G5", "E5", "F5", "A5", "G5", "E5", "D5", "C5", "D5", "E5", "G5", "C6"]
    for j, n in enumerate(mel): add(piano(nf(n), 2.0, 0.85), dawn + j * b3, 0.08)
    for j in range(4): add(music_box(nf(["C6", "B5", "G5", "E5"][j]), 2.2), title + 0.4 + j * 0.8, 0.06)

def fps_ep1(add, DUR, duck=8.0, edit=10.5, fire=16.6, k3=22.2, win_=23.0, loop=25.0, admin=27.4, tail=0.0):
    """FPS第1話：緊張の低音（心音）→ 銃撃戦（速い打ちこみ）→ 編集（時間が止まる高音）→ バレットカム（重い一拍ずつ）→ 勝利 → 不穏"""
    add(pad([nf("D1"), nf("A1"), nf("D#2")], duck + 0.2, 300), 0.0, 0.15)
    b = 60 / 150; t = duck; k = 0
    while t < edit - 0.1:
        add(R.lp(R.kick(95, 40, 0.26, 0.07), 450), t, 0.3); add(R.lp(R.noise(0.06), 8000) * R.dec(0.06, 0.015), t + b / 2, 0.09)
        if k % 4 == 0: add(strings([nf("D2"), nf("F2"), nf("A2"), nf("D3")], b * 4.1, 2400, 0.02, 0.25), t, 0.11)
        t += b; k += 1
    add(pad([nf("D5"), nf("A5"), nf("E6")], fire - edit, 6000), edit, 0.05)                 # 編集：時間が止まる
    add(R.riser(fire - edit - 0.3), edit + 0.3, 0.1)
    for j, kt in enumerate((fire + 0.8, fire + 1.6, fire + 2.4)): add(R.lp(R.kick(60, 30, 0.6, 0.2), 300), kt, 0.25)
    add(strings([nf("D2"), nf("A2"), nf("D3"), nf("F#3")], k3 - fire + 0.6, 1800, 0.3, 0.5), fire, 0.12)
    add(strings([nf("D2"), nf("F#2"), nf("A2"), nf("D3"), nf("F#3")], loop - win_ + 0.3, 2000, 0.05, 0.5), win_, 0.13)
    for j, n in enumerate(["D5", "F#5", "A5", "D6"]): add(piano(nf(n), 1.4, 0.9), win_ + j * 0.22, 0.07)
    add(pad([nf("C1"), nf("F#1"), nf("C2")], DUR + tail - loop, 300), loop, 0.16)
    for j in range(3): add(music_box(nf(["F#5", "C6", "F5"][j]), 2.0), admin + 0.3 + j * 0.7, 0.05)

def fps_tense(add, DUR, picks=(), ghosts=(), climax=(16.4, 22.0), alarm=23.0, final=(25.9, 28.0), tail=0.0):
    """緊迫感BGM：ずっと止まらない16分の低音オスティナート＋刻むハイハット＋心音のサブ低音＋じわじわ上がる弦。
       選択の瞬間に一撃、幻（選ばなかった方）で一瞬ブツッと抜く、クライマックスで最大、最後の2択で加速して無音に落とす"""
    bpm = 140.0; b = 60 / bpm; s16 = b / 4
    bass = ["D2", "D2", "D3", "D2", "F2", "D2", "C3", "D2"]
    gaps = [(g, g + 0.5) for g in ghosts]
    def muted(t): return any(a <= t < z for a, z in gaps) or t >= final[1]
    t = 0.0; k = 0
    while t < final[1]:
        sp = 1.0 if t < final[0] else 1.0 + 0.6 * (t - final[0]) / (final[1] - final[0])   # 最後の2択で加速
        if not muted(t):
            lvl = 0.6 + 0.4 * min(1.0, t / 8.0) + (0.25 if climax[0] <= t < climax[1] else 0.0)
            n = bass[k % len(bass)]; f = nf(n)
            x = np.sin(2 * np.pi * f * R.tt(s16 * 0.9)) * R.dec(s16 * 0.9, s16 * 0.5) + 0.4 * np.sign(np.sin(2 * np.pi * f * R.tt(s16 * 0.9))) * R.dec(s16 * 0.9, s16 * 0.3)
            add(R.lp(x, 900), t, 0.09 * lvl)
            if k % 2 == 1: add(R.hp(R.noise(0.03), 7000) * R.dec(0.03, 0.006), t, 0.05 * lvl, 0.3)
            if k % 4 == 0: add(R.lp(R.kick(70, 38, 0.3, 0.08), 260), t, 0.22 * lvl)
            if k % 16 == 8: add(R.lp(R.noise(0.18), 4000) * R.dec(0.18, 0.06), t, 0.1 * lvl)
        t += s16 / sp; k += 1
    # じわじわ上がる弦（全音ずつ上がるクラスター）
    seg = [(0.0, 5.4, ("D3", "D#3", "A3")), (5.9, 11.4, ("E3", "F3", "B3")), (11.9, climax[0], ("F#3", "G3", "C#4")),
           (climax[0], climax[1], ("D3", "A3", "D4", "F4")), (climax[1], alarm, ("D3", "F#3", "A3", "D4")), (alarm, final[1], ("C#3", "D3", "G#3", "C4"))]
    for a, z, ns in seg:
        if z > a: add(strings([nf(n) for n in ns], z - a, 1600, 0.4, 0.2), a, 0.1)
    for p in picks: add(R.boom(1.2) * 0.8, p, 0.35); add(strings([nf("D2"), nf("A2"), nf("D3")], 0.6, 2500, 0.01, 0.4), p, 0.12)
    for g in ghosts: add(R.lp(R.noise(0.5), 600) * R.dec(0.5, 0.2), g, 0.25)
    add(R.riser(climax[0] - 14.4), 14.4, 0.15)
    add(R.riser(final[1] - final[0]), final[0], 0.18)
    add(R.boom(3.0), final[1], 0.55)
    add(pad([nf("D1"), nf("A1")], DUR + tail - final[1], 200), final[1], 0.12)
