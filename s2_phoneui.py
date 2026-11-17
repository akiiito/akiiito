"""
s2_phoneui.py ― 3Dで描いたスマホの画面に、別に作ったUI画像を遠近を合わせて貼る
  python3 s2_phoneui.py base.png quad.json ui.png out.png [blur]
quad.json: 画面の四隅の画素座標 [左上, 右上, 右下, 左下]
"""
import json, sys
import numpy as np
from PIL import Image, ImageFilter

def coeffs(dst, src):
    """dst（出力画像の点）→ src（UI画像の点）への射影変換の係数（PIL の PERSPECTIVE 用）"""
    A, b = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    return np.linalg.solve(np.array(A, float), np.array(b, float)).tolist()

def main(base, quad, ui, out, blur=0.8):
    bg = Image.open(base).convert("RGBA"); u = Image.open(ui).convert("RGBA")
    q = json.load(open(quad)); w, h = u.size
    c = coeffs(q, [(0, 0), (w, 0), (w, h), (0, h)])
    warped = u.transform(bg.size, Image.PERSPECTIVE, c, Image.BICUBIC)
    mask = Image.new("L", u.size, 255).transform(bg.size, Image.PERSPECTIVE, c, Image.BICUBIC)
    warped.putalpha(mask)
    if blur: warped = warped.filter(ImageFilter.GaussianBlur(blur))
    Image.alpha_composite(bg, warped).convert("RGB").save(out)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5]) if len(sys.argv) > 5 else 0.8)
