"""
s4_rooftop.py ― 夕焼けの屋上（POVシリーズの舞台）
  階段室（扉つき）が y=-4 付近、フェンスが y=+5。夕日は +y 側の低い位置（フェンスの向こう）＝逆光。
  rooftop() → dict(door=扉オブジェクト, hut_y=扉の位置)
"""
import math, random
import bpy
import s2_world as W

SUNSET_SKY = ((1.0, 0.36, 0.1), (0.98, 0.5, 0.36), (0.16, 0.12, 0.34))

def rooftop(sun_elev=7.0, sun_str=6.0, sky_str=0.85):
    M = dict(conc=W.mat("conc", (0.55, 0.52, 0.5), 0.9, noise=(5.0, 0.2)),
             tile=W.mat("tile", (0.42, 0.4, 0.4), 0.8, noise=(12.0, 0.15)),
             wall=W.mat("hutwall", (0.72, 0.7, 0.66), 0.85, noise=(6.0, 0.05)),
             door=W.mat("door", (0.32, 0.4, 0.45), 0.4, 0.6),
             fence=W.mat("fence", (0.2, 0.24, 0.24), 0.4, 0.8),
             town=W.mat("town2", (0.05, 0.035, 0.06), 0.95),
             win=W.mat("townwin", (1.0, 0.75, 0.4), 0.5, emit=(1.0, 0.7, 0.35), estr=3.0),
             dark=W.mat("hutdark", (0.05, 0.05, 0.06), 0.9))
    # 屋上の床（12 x 10）と低い縁
    W.box("roof", (0, 0.5, -0.1), (12, 10, 0.2), M["conc"])
    for k in range(13):
        W.box("joint%d" % k, (-6 + k, 0.5, 0.003), (0.03, 10, 0.006), M["tile"])
    for k in range(11):
        W.box("jointy%d" % k, (0, -4.5 + k, 0.003), (12, 0.03, 0.006), M["tile"])
    W.box("lip_far", (0, 5.55, 0.15), (12, 0.2, 0.3), M["conc"])
    W.box("lip_l", (-6.05, 0.5, 0.15), (0.2, 10, 0.3), M["conc"])
    W.box("lip_r", (6.05, 0.5, 0.15), (0.2, 10, 0.3), M["conc"])
    # フェンス（向こう側と左右）：柱＋横棒＋細い縦線
    def fence_line(name, p0, p1, n_post, n_wire):
        x0, y0 = p0; x1, y1 = p1
        for k in range(n_post + 1):
            f = k / n_post; W.cyl("%s_post%d" % (name, k), (x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, 1.1), 0.035, 2.2, M["fence"], verts=8)
        L = math.hypot(x1 - x0, y1 - y0); ang = math.atan2(y1 - y0, x1 - x0)
        for z in (0.3, 1.2, 2.15):
            W.cyl("%s_rail%.1f" % (name, z), ((x0 + x1) / 2, (y0 + y1) / 2, z), 0.02, L, M["fence"], rot=(0, math.pi / 2, ang), verts=6)
        for k in range(n_wire + 1):
            f = k / n_wire; W.cyl("%s_w%d" % (name, k), (x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, 1.2), 0.006, 1.85, M["fence"], verts=4)
    fence_line("ff", (-5.9, 5.4), (5.9, 5.4), 6, 90)
    fence_line("fl", (-5.9, -4.4), (-5.9, 5.4), 5, 70)
    fence_line("fr", (5.9, -4.4), (5.9, 5.4), 5, 70)
    # 階段室（扉の向こうは暗い）
    hut_y = -4.0
    W.box("hut_back", (0, hut_y - 2.0, 1.4), (3.0, 0.15, 2.8), M["wall"])
    W.box("hut_l", (-1.5, hut_y - 1.0, 1.4), (0.15, 2.0, 2.8), M["wall"])
    W.box("hut_r", (1.5, hut_y - 1.0, 1.4), (0.15, 2.0, 2.8), M["wall"])
    W.box("hut_top", (0, hut_y - 1.0, 2.85), (3.2, 2.2, 0.15), M["wall"])
    W.box("hut_front_l", (-0.95, hut_y, 1.4), (1.1, 0.15, 2.8), M["wall"])
    W.box("hut_front_r", (0.95, hut_y, 1.4), (1.1, 0.15, 2.8), M["wall"])
    W.box("hut_front_t", (0, hut_y, 2.5), (0.8, 0.15, 0.6), M["wall"])
    W.box("hut_floor", (0, hut_y - 1.0, 0.0), (2.9, 2.0, 0.05), M["dark"])
    # 扉：左端（x=-0.4）を蝶番にして外へ開く
    door = bpy.data.objects.new("door_pivot", None); bpy.context.collection.objects.link(door)
    door.location = (-0.4, hut_y + 0.02, 0)
    W.box("door", (0.4, 0, 1.1), (0.8, 0.05, 2.2), M["door"], parent=door)
    # 下に広がる街（逆光のシルエット＋窓の灯り）
    rnd = random.Random(11)
    for k in range(140):
        x = rnd.uniform(-160, 160); y = rnd.uniform(14, 220)
        if abs(x) < 10 and y < 20: continue
        hgt = rnd.uniform(4, 22) if rnd.random() < 0.85 else rnd.uniform(22, 50)
        if abs(x) < 45: hgt = min(hgt, 14 + y * 0.02)          # 夕日のまわりは低く（夕日が見えるように）
        sx, sy = rnd.uniform(6, 16), rnd.uniform(6, 16)
        W.box("tb%d" % k, (x, y, -14 + hgt / 2), (sx, sy, hgt), M["town"])
        if rnd.random() < 0.5:
            W.box("tw%d" % k, (x, y - sy / 2 - 0.05, -14 + hgt * rnd.uniform(0.3, 0.8)), (sx * 0.6, 0.05, 0.6), M["win"])
    W.box("ground", (0, 0, -14.1), (600, 600, 0.2), W.mat("gnd", (0.12, 0.09, 0.1), 0.95))
    # 空と夕日（大きな発光円盤を地平線の少し上に置く＝ようたの真後ろに来る）
    W.sky_world(SUNSET_SKY, sky_str)
    sm = W.mat("sundisc", (1.0, 0.85, 0.5), 0.5, emit=(1.0, 0.72, 0.38), estr=12.0)
    e = math.radians(sun_elev)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=11, location=(4, 300 * math.cos(e), 300 * math.sin(e) - 2))
    bpy.context.object.data.materials.append(sm); bpy.context.object.visible_shadow = False
    sun = bpy.data.lights.new("sun", "SUN"); sun.energy = sun_str; sun.color = (1.0, 0.58, 0.3); sun.angle = math.radians(1.0)
    so = bpy.data.objects.new("sun", sun); bpy.context.collection.objects.link(so)
    so.location = (0, 20, 5); W.aim(so, (0, 20 - math.cos(e), 5 - math.sin(e)))
    # 正面（カメラ側）からの柔らかい空の照り返し：顔が真っ黒にならないように
    fl = bpy.data.lights.new("fill", "AREA"); fl.energy = 120; fl.size = 6; fl.color = (0.95, 0.75, 0.75)
    fo = bpy.data.objects.new("fill", fl); bpy.context.collection.objects.link(fo); fo.location = (0, -2, 4); W.aim(fo, (0, 3, 1))
    return dict(door=door, hut_y=hut_y, M=M)
