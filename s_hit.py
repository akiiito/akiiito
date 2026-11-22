"""s_hit.py ― 気持ちいい打撃音セット（アニメの戦闘向け）。すべてモノラルの numpy 配列（SR は make_reel と同じ）
  hit(size)      : 打撃（アタック＋胴鳴り＋割れ＋超低音＋短い残響）
  suck(sec)      : 当たる直前の「吸いこみ」（逆再生の膨らみ）→ 一瞬の静けさ → hit で気持ちよく抜ける
  whoosh(sec)    : 速い風切り
  slash()        : 金属の斬撃（シャキン）
  crumble(sec)   : がれきがガラガラ崩れる
  build(n)       : ブロックがカカカッと組み上がる
  boom_big()     : とどめの大爆発（超低音のドロップ付き）
"""
import numpy as np
import make_reel as R
SR = R.SR; tt = R.tt; dec = R.dec
rng = np.random.default_rng(11)
def _pad(*xs):
    n = max(len(x) for x in xs); o = np.zeros(n)
    for x in xs: o[:len(x)] += x
    return o
def _sweep(f0, f1, sec, tau):
    t = tt(sec); f = f1 + (f0 - f1) * np.exp(-t / (sec * 0.25))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * dec(sec, tau)
def _sat(x, k=1.6): return np.tanh(x * k) / np.tanh(k)
def _room(x, amt=0.25):
    ir = rng.standard_normal(R.n_(0.35)) * dec(0.35, 0.07); ir = R.lp(ir, 3500); ir[0] = 1.0
    y = np.convolve(x, ir)[: len(x) + R.n_(0.35)]
    return _pad(x, y * amt * 0.25)
def hit(size=1.0):
    atk = R.hp(rng.standard_normal(R.n_(0.012)), 2500) * dec(0.012, 0.003) * 0.9
    body = _sweep(200 * (1.2 - 0.3 * size), 48, 0.28 + 0.1 * size, 0.07 + 0.04 * size) * 1.1
    crack = R.bp(rng.standard_normal(R.n_(0.09)), 900, 4200) * dec(0.09, 0.022) * 0.8
    sub = np.sin(2 * np.pi * 42 * tt(0.45)) * dec(0.45, 0.12) * 0.7 * size
    x = _pad(atk, body, crack, sub)
    return _room(_sat(x * 1.1, 2.2), 0.35) * 0.9
def suck(sec=0.35):
    x = R.bp(rng.standard_normal(R.n_(sec)), 300, 5000) * np.linspace(0, 1, R.n_(sec)) ** 3
    return x * 0.7
def whoosh(sec=0.22, lo=500, hi=6000):
    n = R.n_(sec); t = np.linspace(0, 1, n)
    x = rng.standard_normal(n); out = np.zeros(n); seg = max(1, n // 12)
    for k in range(12):
        a = k * seg; b = min(n, a + seg + seg // 2)
        fc = lo + (hi - lo) * (k / 11) ** 1.5
        out[a:b] += R.bp(x[a:b], fc * 0.6, min(fc * 1.6, SR / 2 - 100)) * np.hanning(b - a)
    return out * np.sin(np.pi * t) ** 0.8 * 0.9
def slash():
    t = tt(0.6); x = sum(np.sin(2 * np.pi * f * t) * dec(0.6, 0.18 / (1 + i * 0.3)) / (1 + i) for i, f in enumerate((2950, 4410, 6120, 7930)))
    return _pad(whoosh(0.16, 1500, 8000) * 0.8, np.concatenate([np.zeros(R.n_(0.1)), x * 0.35]))
def crumble(sec=1.2, n=26):
    out = np.zeros(R.n_(sec + 0.2))
    for k in range(n):
        s = R.n_(rng.uniform(0, sec) ** 1.4 / sec ** 0.4); c = R.bp(rng.standard_normal(R.n_(0.07)), rng.uniform(400, 2500), 6000) * dec(0.07, rng.uniform(0.01, 0.025))
        out[s:s + len(c)] += c[: len(out) - s] * rng.uniform(0.3, 1.0)
    return _pad(out, R.lp(rng.standard_normal(len(out)), 300) * dec(sec + 0.2, 0.3) * 0.5) * 0.8
def build(n=8, gap=0.045):
    out = np.zeros(R.n_(n * gap + 0.2))
    for k in range(n):
        f = 900 * 1.06 ** k; c = _pad(np.sin(2 * np.pi * f * tt(0.05)) * dec(0.05, 0.01), R.hp(rng.standard_normal(R.n_(0.02)), 3000) * dec(0.02, 0.003) * 0.6)
        s = R.n_(k * gap); out[s:s + len(c)] += c
    return out * 0.8
def boom_big(sec=3.0):
    drop = np.sin(2 * np.pi * np.cumsum(30 + 60 * np.exp(-tt(sec) / 0.25)) / SR) * dec(sec, 0.9)
    return _pad(hit(1.6) * 1.2, drop * 0.9, R.lp(rng.standard_normal(R.n_(sec)), 900) * dec(sec, 0.5) * 0.6, crumble(1.8, 40) * 0.6)
def strike(add, t, size=1.0, pan=0.0, pre=True):
    """吸いこみ → 打撃 → 余韻 をまとめて置く"""
    if pre: add(suck(0.3), t - 0.3, 0.35 * size, pan)
    add(hit(size), t, 0.9 * min(1.3, size), pan)
