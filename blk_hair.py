"""blk_hair.py ― s3_toon.girl の髪を「1本ずつの毛束」に作りかえる（前髪・横髪・頭頂の毛流れ）。
  upgrade(root, name, mat)  … 元の前髪(cone)と横髪を消して、頭の形にそって曲がる薄い毛束を足す（root のローカル座標）
"""
import math, random
import bpy, bmesh
from mathutils import Vector

HC = Vector((0.0, 0.0, 1.44))
RX, RY, RZ = 0.125 * 0.92, 0.125 * 0.95, 0.125            # 頭の楕円体

def surf(az, el, k):
    """頭の表面を k 倍にふくらませた点（az: +Y=0 から +X へ、el: 仰角）"""
    return HC + Vector((math.sin(az) * math.cos(el) * RX * k, math.cos(az) * math.cos(el) * RY * k, math.sin(el) * RZ * k))

def strip(name, pts, widths, mat, parent, thick=0.006, twist=0.0):
    """点列にそった、先が細くなる薄い帯（頭の外向きを面の向きに）"""
    me = bpy.data.meshes.new(name); bm = bmesh.new(); rows = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        n = (p - HC).normalized()
        b = t.cross(n).normalized()
        if twist: b = (b * math.cos(twist * i / len(pts)) + n * math.sin(twist * i / len(pts))).normalized()
        w = widths[i] / 2
        # 断面をわずかに山なりにして（中央を外へ）立体感を出す
        rows.append([bm.verts.new(p - b * w), bm.verts.new(p + n * 0.002 * (w > 0.004)), bm.verts.new(p + b * w)])
    for a, c in zip(rows, rows[1:]):
        bm.faces.new((a[0], c[0], c[1], a[1])); bm.faces.new((a[1], c[1], c[2], a[2]))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); o.parent = parent
    me.materials.append(mat)
    for poly in me.polygons: poly.use_smooth = True
    so = o.modifiers.new("sol", "SOLIDIFY"); so.thickness = thick; so.offset = -1.0
    sd = o.modifiers.new("sub", "SUBSURF"); sd.levels = 1; sd.render_levels = 2
    return o

def lock(name, mat, parent, az0, el0, az1, el1, w0, k0=1.13, k1=1.06, n=16, hang=0.0, curl=0.0, out=0.0, thick=0.006):
    """頭頂側 (az0,el0) から 毛先 (az1,el1) へ頭にそって流れる毛束。hang: 毛先がさらに下へ垂れる長さ(m)"""
    pts, ws = [], []
    for i in range(n + 1):
        s = i / n; e = s ** 0.9
        az = az0 + (az1 - az0) * e; el = el0 + (el1 - el0) * e
        k = k0 + (k1 - k0) * s + out * s * s
        p = surf(az, el, k)
        if hang: p += Vector((math.sin(az) * out * 0.3, math.cos(az) * out * 0.3, -hang * max(0.0, (s - 0.35) / 0.65) ** 1.2))
        if curl: p += (HC - p).normalized() * curl * max(0.0, (s - 0.75) / 0.25) ** 2      # 毛先を内側へ巻く
        pts.append(p); ws.append(w0 * (1 - s ** 1.6) * (0.75 + 0.25 * math.sin(math.pi * min(1, s * 1.6))) + 0.0015)
    return strip(name, pts, ws, mat, parent, thick)

def upgrade(root, name, mat, seed=3):
    rnd = random.Random(seed)
    for o in list(root.children):                     # 元の前髪・横髪（円すい）を消す
        if o.name.startswith(name + "_bang") or o.name.startswith(name + "_side"):
            bpy.data.objects.remove(o, do_unlink=True)
    D = math.radians
    # 前髪：真ん中で少し分けて、目にかかる長さ。外側ほど長い
    for k, a in enumerate([-58, -46, -35, -24, -14, -5, 6, 15, 25, 36, 47, 58]):
        a_ = a + rnd.uniform(-2, 2); side = abs(a) / 58
        el1 = D(14 - 26 * side ** 1.4 + rnd.uniform(-3, 3))
        lock(name + "_bangx", mat, root, D(a_ * 0.35), D(78), D(a_ * (1.05 + 0.1 * side)), el1,
             w0=0.05 - 0.008 * side, k0=1.16, k1=1.09 + 0.02 * side, curl=0.008, thick=0.007)
    # 横髪：顔をかこむ長い束（あごの下まで）
    for sx in (-1, 1):
        for j, (a, l, w) in enumerate([(66, 0.13, 0.045), (78, 0.17, 0.05), (92, 0.12, 0.05)]):
            lock(name + "_sidex", mat, root, D(sx * (a - 12)), D(70), D(sx * (a + rnd.uniform(-3, 3))), D(-28), w0=w,
                 k0=1.16, k1=1.12, hang=l, out=0.06, curl=0.01, thick=0.007)
    # 頭頂から後ろ（結び目）への毛流れ：のっぺりした帽子をこわす
    for j in range(9):
        a = D(-70 + j * 17.5 + rnd.uniform(-4, 4))
        lock(name + "_flowx", mat, root, a * 0.2, D(84), a * 1.0 + D(180), D(18 + rnd.uniform(-6, 6)), w0=0.065,
             k0=1.17, k1=1.16, thick=0.006)
    # アホ毛（1本だけ跳ねる）
    pts = [HC + Vector((0.0, 0.03, RZ * 1.17)) + Vector((0.0, 0.028 * s, 0.035 * math.sin(math.pi * s * 0.8))) for s in [i / 10 for i in range(11)]]
    strip(name + "_ahoge", pts, [0.016 * (1 - (i / 10) ** 1.5) + 0.001 for i in range(11)], mat, root, 0.004)
