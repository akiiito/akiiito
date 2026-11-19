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
