"""
s_sfx.py ― ショート動画用の「大きくて分かりやすい」効果音（シネマ風）
  impact()   … 低音のドン＋割れる音（場面転換・見出し・カード）
  braam(sec) … 映画予告の「ブォォン」（不穏・大事件）
  stinger()  … 気づき・正体判明の「キィン！」
  swell(sec) … 逆再生っぽく吸い込んで盛り上げる（impact の直前に置く）
  tinnitus() … 衝撃のあとの耳鳴り
  whip()     … カメラを振る・振り向く「シュッ」
"""
import numpy as np
import make_reel as R

def impact(sec=2.0, sub=46.0):
    t = R.tt(sec)
    drop = np.sin(2 * np.pi * np.cumsum(sub * (1.6 - 0.6 * np.minimum(t / 0.25, 1))) / R.SR) * np.exp(-t / 0.9)
    crack = R.hp(R.noise(sec), 1500) * R.dec(sec, 0.06)
    body = R.lp(R.noise(sec), 300) * R.dec(sec, 0.35)
    return 1.0 * drop + 0.55 * crack + 0.6 * body + 0.8 * R.kick(90, 30, sec, 0.35)

def braam(sec=2.4, root=55.0):
    t = R.tt(sec)
    s = sum(R.saw(root * m, sec, d) for m in (1, 1.5, 2) for d in (-0.006, 0.0, 0.007))
    env = np.minimum(1, t / 0.06) * np.exp(-t / (sec * 0.45))
    return R.lp(s, 700) * env / 4 + 0.5 * impact(sec) * 0.6

def stinger(sec=1.6):
    t = R.tt(sec)
    ring = sum(np.sin(2 * np.pi * f * t) * np.exp(-t / 0.6) for f in (1760.0, 2217.5, 2637.0, 3520.0)) / 3
    return ring + 0.6 * R.hp(R.noise(sec), 4000) * R.dec(sec, 0.05) + 0.5 * R.kick(110, 40, sec, 0.2)

def swell(sec=1.2):
    t = R.tt(sec) / sec
    return (R.bp(R.noise(sec), 300, 6000) * 0.7 + 0.4 * R.sweep(120, 900, sec, 2.5)) * t ** 2.6

def tinnitus(sec=2.5, f=4200.0):
    t = R.tt(sec)
    return np.sin(2 * np.pi * f * t) * np.minimum(1, t / 0.05) * np.exp(-t / (sec * 0.5)) * 0.25

def whip(sec=0.35):
    t = R.tt(sec) / sec
    return R.bp(R.noise(sec), 700, 5000) * np.sin(np.pi * t) ** 3

def hit(add, t, big=1.0, pre=0.9):
    """swell → impact をまとめて置く（t が impact の瞬間）"""
    if pre > 0: add(swell(pre), t - pre, 0.55 * big)
    add(impact(), t, 0.95 * big)

def duck(sfx, voice, depth_db=14.0, hold=0.12, release=0.35):
    """声が鳴っている間だけ効果音・音楽を下げる（サイドチェイン）。セリフの合間の効果音は大きいまま"""
    from scipy.ndimage import maximum_filter1d, uniform_filter1d
    env = np.abs(voice).max(axis=1) if voice.ndim == 2 else np.abs(voice)
    env = uniform_filter1d(env, max(1, int(0.02 * R.SR)))
    on = (env > env.max() * 0.03).astype(float)
    on = maximum_filter1d(on, max(1, int(hold * R.SR)))                 # 言葉のすき間で戻りすぎない
    on = uniform_filter1d(on, max(1, int(release * R.SR)))              # なめらかに下げて戻す
    g = 10 ** (-depth_db * on / 20)
    return sfx * (g[:, None] if sfx.ndim == 2 else g)
