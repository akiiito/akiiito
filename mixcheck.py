"""mixcheck.py <make_reel_xxx モジュール名> ― セリフの間、声が効果音・音楽より十分大きいかを数値で確かめる（耳で聞けないため）
  各セリフについて 声RMS / 効果音+音楽RMS を dB で出す。+6dB 未満は WARN。"""
import sys, json, importlib
import numpy as np
m = importlib.import_module(sys.argv[1]); R = m.R
voice = np.load(m.VOICE_NPY)
R.MIX = np.zeros_like(voice); m.build_sfx(); sfx = m.X.duck(R.MIX.copy(), voice) if hasattr(m, 'X') else R.MIX.copy()
L = json.load(open(m.LINES_JSON, encoding="utf-8"))
def rms(x): return float(np.sqrt(np.mean(x ** 2)) + 1e-9)
worst = 99
for l in L:
    a, b = R.n_(l[0]), R.n_(l[1]); v = voice[a:b]; s = sfx[a:b]
    act = np.abs(v).max(axis=1) > np.abs(voice).max() * 0.03          # 実際に声が出ているところだけで比べる
    from scipy.ndimage import maximum_filter1d
    act = maximum_filter1d(act.astype(np.uint8), R.n_(0.05)).astype(bool)
    v, s = v[act], s[act]
    db = 20 * np.log10(rms(v) / rms(s)); worst = min(worst, db)
    print("%5.1fs %-5s voice/sfx %+5.1f dB %s %s" % (l[0], l[5], db, "WARN" if db < 6 else "ok", l[2][:16]))
pk = 20 * np.log10(np.abs(sfx).max() / np.abs(voice).max())
print("worst %+.1f dB / sfx peak vs voice peak %+.1f dB" % (worst, pk))
