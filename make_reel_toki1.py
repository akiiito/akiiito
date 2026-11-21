"""
make_reel_toki1.py ― 「その罪、時効にさせない」第1話『光る絵の具』（35秒・1080x1920・24fps）
  1) --voice で声（toki1_voice.npy / toki1_lines.json）
  2) create_toki1.py → post_toki1.py で絵
  3) 引数なしで 絵＋声＋効果音＋BGM＋字幕 → toki_ep1.mp4
"""
import os, sys, json, subprocess, wave
import numpy as np
import make_reel as R
from toki_lines import TOKI1 as LINES0
from toki1_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SR = 24, R.SR
DUR = END; TAIL = 0.6
R.DUR = DUR; R.MIX = np.zeros((R.n_(DUR) + SR, 2)); add = R.add
R.VV_CAST.update({
    "hana": (1878365376, 1878365376, 0.0, 1.0, 1.1),      # コハク
    "toki": (888753763, 888753763, 0.0, 0.95, 1.05),      # まお（おちつき）
    "boss": (1310138976, 1310138976, 0.0, 0.95, 1.15),    # 阿井田 茂
})
R.VOICE.update({k: (0, 0, 1.1, 0.04) for k in ("hana", "toki", "boss")})
R.SPK_REF_TEXT[:] = ["今日の放課後、少しだけ話せる", "写真、見せてくれる", "ううん、なんでもない", "また明日ね", "窓の外、きれいだね"]
R.LINES = list(LINES0)
R.RETAKE_MIN, R.RETAKES = 0.63, 10
R.VV_READ += [("筆先", "ふでさき"), ("舐めろ", "なめろ"), ("時効", "じこう"), ("報告書", "ほうこくしょ")]
VOICE_NPY = os.path.join(HERE, "toki1_voice.npy"); LINES_JSON = os.path.join(HERE, "toki1_lines.json")

def main():
    if "--voice" in sys.argv:
        R.build_voice()
        np.save(VOICE_NPY, R.MIX)
        json.dump([list(l) for l in R.LINES], open(LINES_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("wrote", VOICE_NPY, LINES_JSON); return

if __name__ == "__main__":
    main()
