"""fps_lookdev.py ― FPS転生の見た目確認（1枚）。python fps_lookdev.py [--samples 24] [--res 0.5] [--out path]"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import s2_world as W, fps_world as F
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
RS = float(arg("--res", "0.5")); OUTP = arg("--out", "/tmp/fps_look.png")
sc = W.reset(int(arg("--samples", "24")), res=(int(1080 * RS), int(1920 * RS)))
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.05
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"; sc.view_settings.exposure = -1.1
rnd = random.Random(3)
# 空（夕方の物理空）と太陽
world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True; wn = world.node_tree
sky = wn.nodes.new("ShaderNodeTexSky")
try: sky.sky_type = "NISHITA"
except Exception: pass
try: sky.sun_elevation = math.radians(4); sky.sun_rotation = math.radians(200); sky.air_density = 1.6; sky.dust_density = 4.0
except Exception: pass
wn.links.new(sky.outputs[0], wn.nodes["Background"].inputs[0]); wn.nodes["Background"].inputs[1].default_value = 0.35
sun = bpy.data.lights.new("sun", "SUN"); sun.energy = 4.0; sun.color = (1.0, 0.62, 0.36); sun.angle = math.radians(1.0)
so = bpy.data.objects.new("sun", sun); bpy.context.collection.objects.link(so); so.rotation_euler = (math.radians(84), 0, math.radians(200))
# 地面・道路・建物
conc = F.mat_concrete("conc", (0.3, 0.28, 0.26), 0.8); asph = F.mat_concrete("asph", (0.16, 0.16, 0.17), 0.3, 6.0)
glass = F.mat_simple("glass", (0.25, 0.32, 0.36), 0.08, 0.6); frame = F.mat_simple("frame", (0.3, 0.29, 0.27), 0.7)
F.box("ground", (0, 30, -0.05), (120, 140, 0.1), asph)
F.box("sidewalkL", (-7.5, 30, 0.08), (3, 140, 0.16), conc); F.box("sidewalkR", (7.5, 30, 0.08), (3, 140, 0.16), conc)
for k in range(7):
    F.building("bL%d" % k, -14 - rnd.uniform(0, 3), 6 + k * 14, 10, 12, rnd.uniform(12, 30), F.mat_concrete("c%d" % k, (0.26 + 0.05 * rnd.random(), 0.25, 0.23), 0.8), glass, frame, rnd)
    F.building("bR%d" % k, 14 + rnd.uniform(0, 3), 6 + k * 14, 10, 12, rnd.uniform(12, 34), F.mat_concrete("d%d" % k, (0.28, 0.26 + 0.04 * rnd.random(), 0.24), 0.8), glass, frame, rnd)
F.rubble("rub1", (-3, 9, 0), 2.5, 160, conc, rnd); F.rubble("rub2", (4, 16, 0), 3.0, 200, conc, rnd); F.rubble("rub3", (-1, 26, 0), 3.5, 220, conc, rnd, 0.9)
F.box("barrier1", (1.5, 6, 0.5), (2.2, 0.4, 1.0), conc, rot=(0, 0, 0.2), bevel=0.05); F.box("barrier2", (-2.5, 13, 0.5), (2.2, 0.4, 1.0), conc, rot=(0, 0, -0.3), bevel=0.05)
car = F.mat_simple("car", (0.12, 0.05, 0.04), 0.6, 0.4)
F.box("car", (5, 11, 0.7), (1.9, 4.4, 1.0), car, rot=(0, 0.05, 0.3), bevel=0.15); F.box("carTop", (5, 11.2, 1.45), (1.6, 2.2, 0.6), car, rot=(0, 0.05, 0.3), bevel=0.15)
# 敵
s1, v1 = F.soldier("en1", (2.2, 14, 0), rnd); s1.rotation_euler.z = math.radians(170)
s2, v2 = F.soldier("en2", (-1.6, 19, 0), rnd); s2.rotation_euler.z = math.radians(195)
# 弾の軌跡（壁を回りこむ）
tr, _ = F.tracer_curve("trace", [(0.1, 0.6, 1.5), (1.8, 5.5, 1.6), (-1.5, 9, 1.7), (-1.0, 13, 1.7), (1.6, 15.5, 1.66), (2.2, 14.2, 1.66)], strength=40.0, width=0.006)
# カメラ・銃
cam = W.camera((0.0, 0.0, 1.62), (0.4, 12, 1.4), lens=26, fstop=4.0); cam.data.dof.use_dof = True; cam.data.dof.focus_distance = 12
g, acc = F.rifle(cam); g.location = (0.13, -0.15, -0.26); g.rotation_euler = (math.radians(-92), math.radians(-3), math.radians(4))
F.gloves(g)
fl = bpy.data.lights.new("fill", "AREA"); fl.size = 3; fl.energy = 60; fl.color = (0.5, 0.6, 1.0)
flo = bpy.data.objects.new("fill", fl); bpy.context.collection.objects.link(flo); flo.location = (-3, -2, 4); flo.rotation_euler = (0.9, 0, -0.6)
sc.render.filepath = OUTP; bpy.ops.render.render(write_still=True); print("wrote", OUTP)
