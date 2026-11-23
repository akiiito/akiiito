"""
create_fps1.py ― 「この世界の銃、弾は1発だけ。」（FPS転生 第1話・30秒・主観）
  python create_fps1.py [--samples 20] [--res 0.75] [--start 0] [--end 720] [--test 0,100,...]
"""
import os, sys, math, json, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
import s2_world as W, fps_world as F
from fps1_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "20")); FPS = 24; N = int(END * FPS)
RS = float(arg("--res", "0.75"))
START = int(arg("--start", "0")); STOP = int(arg("--end", str(N)))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_FPS1v2" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
sc = W.reset(SAMPLES, res=(int(1080 * RS), int(1920 * RS)))
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = float(arg("--thr", "0.04"))
sc.cycles.max_bounces = 5; sc.render.use_persistent_data = True
try: sc.cycles.denoising_prefilter = "ACCURATE"; sc.cycles.denoising_quality = "HIGH"
except Exception: pass
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"; sc.view_settings.exposure = -1.45
rnd = random.Random(3)
def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def win(t, a, b, fi=0.3, fo=0.3): return ease((t - a) / fi) * (1 - ease((t - b) / fo))

# ---------------------------------------------------------------- 空・太陽・霧
world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True; wn = world.node_tree
sky = wn.nodes.new("ShaderNodeTexSky")
try: sky.sky_type = "NISHITA"; sky.sun_elevation = math.radians(4); sky.sun_rotation = math.radians(200); sky.air_density = 1.6; sky.dust_density = 4.0
except Exception: pass
wn.links.new(sky.outputs[0], wn.nodes["Background"].inputs[0]); BG = wn.nodes["Background"].inputs[1]; BG.default_value = 0.22
sun = bpy.data.lights.new("sun", "SUN"); sun.energy = 4.0; sun.color = (1.0, 0.62, 0.36); sun.angle = math.radians(1.0)
so = bpy.data.objects.new("sun", sun); bpy.context.collection.objects.link(so); so.rotation_euler = (math.radians(84), 0, math.radians(200))
fl = bpy.data.lights.new("fill", "AREA"); fl.size = 3; fl.energy = 60; fl.color = (0.5, 0.6, 1.0)
flo = bpy.data.objects.new("fill", fl); bpy.context.collection.objects.link(flo); flo.location = (-3, -2, 4); flo.rotation_euler = (0.9, 0, -0.6)
# 霧（遠くほどかすむ）：大きな箱の中の体積は重いので、材質に距離で混ぜる
FOGC = (0.42, 0.38, 0.4)
def fogify(m):
    nt = m.node_tree; N_ = nt.nodes; L = nt.links.new
    out = [n for n in N_ if n.type == "OUTPUT_MATERIAL"][0]; src = out.inputs["Surface"].links[0].from_socket
    cd = N_.new("ShaderNodeCameraData"); mul = N_.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = -0.02
    ex = N_.new("ShaderNodeMath"); ex.operation = "EXPONENT"; one = N_.new("ShaderNodeMath"); one.operation = "SUBTRACT"; one.inputs[0].default_value = 1.0
    lp = N_.new("ShaderNodeLightPath"); mm = N_.new("ShaderNodeMath"); mm.operation = "MULTIPLY"
    em = N_.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*FOGC, 1); em.inputs["Strength"].default_value = 0.035
    mx = N_.new("ShaderNodeMixShader")
    L(cd.outputs["View Distance"], mul.inputs[0]); L(mul.outputs[0], ex.inputs[0]); L(ex.outputs[0], one.inputs[1]); L(one.outputs[0], mm.inputs[0]); L(lp.outputs["Is Camera Ray"], mm.inputs[1])
    L(mm.outputs[0], mx.inputs[0]); L(src, mx.inputs[1]); L(em.outputs[0], mx.inputs[2]); L(mx.outputs[0], out.inputs["Surface"])
    return m

# ---------------------------------------------------------------- 街
conc = fogify(F.mat_concrete("conc", (0.34, 0.32, 0.3), 0.8)); asph = fogify(F.mat_concrete("asph", (0.13, 0.13, 0.14), 0.3, 6.0, streaks=False, puddles=True))
glass = fogify(F.mat_simple("glass", (0.25, 0.32, 0.36), 0.08, 0.6)); frame = fogify(F.mat_simple("frame", (0.3, 0.29, 0.27), 0.7))
F.box("ground", (0, 30, -0.05), (120, 140, 0.1), asph)
F.box("sidewalkL", (-7.5, 30, 0.08), (3, 140, 0.16), conc); F.box("sidewalkR", (7.5, 30, 0.08), (3, 140, 0.16), conc)
for k in range(7):
    F.building("bL%d" % k, -14 - rnd.uniform(0, 3), 6 + k * 14, 10, 12, rnd.uniform(12, 30), fogify(F.mat_concrete("c%d" % k, (0.26 + 0.05 * rnd.random(), 0.25, 0.23), 0.8)), glass, frame, rnd)
    if k == 1: continue
    F.building("bR%d" % k, 14 + rnd.uniform(0, 3), 6 + k * 14, 10, 12, rnd.uniform(12, 34), fogify(F.mat_concrete("d%d" % k, (0.28, 0.26 + 0.04 * rnd.random(), 0.24), 0.8)), glass, frame, rnd)
ROOF = Vector((10.5, 20.0, 16.0))                                       # 管理者が立つ屋上
F.building("bAdmin", 15.0, 20.0, 10, 12, ROOF.z, fogify(F.mat_concrete("adm", (0.27, 0.26, 0.25), 0.8)), glass, frame, rnd)
F.rubble("rub1", (-4.5, 8, 0), 2.0, 140, conc, rnd); F.rubble("rub2", (5, 18, 0), 3.0, 200, conc, rnd); F.rubble("rub3", (-1, 27, 0), 3.5, 220, conc, rnd, 0.9)
lane = fogify(F.mat_simple("lane", (0.55, 0.53, 0.48), 0.7))
for k in range(14): F.box("lane", (0.0, 3.0 + k * 4.0, 0.002), (0.18, 2.0, 0.004), lane)
pole = fogify(F.mat_simple("pole", (0.08, 0.08, 0.09), 0.5, 0.6))
for k in range(5):
    for sx in (-1, 1):
        F.cyl("pole", (sx * 5.8, 6 + k * 12, 3.0), 0.07, 6.0, pole, rot=(0, sx * (0.05 + 0.15 * (k % 2)), 0))
        F.box("lamp", (sx * 5.3, 6 + k * 12, 6.0), (1.0, 0.2, 0.12), pole)
COVER = F.box("cover", (0.2, 1.3, 0.5), (2.0, 0.35, 1.0), conc, bevel=0.05)
F.box("barrier2", (-3.3, 9.6, 0.5), (2.2, 0.4, 1.0), conc, rot=(0, 0, -0.3), bevel=0.05)
car = fogify(F.mat_simple("car", (0.12, 0.05, 0.04), 0.6, 0.4))
F.box("car", (4.8, 7.8, 0.7), (1.9, 4.4, 1.0), car, rot=(0, 0.05, 0.3), bevel=0.15); F.box("carTop", (4.8, 8.0, 1.45), (1.6, 2.2, 0.6), car, rot=(0, 0.05, 0.3), bevel=0.15)

# ---------------------------------------------------------------- 敵（円の上に並ぶ）
C = Vector((0.4, 8.6, 1.66)); RR = 2.6
ANG = {"e3": math.radians(-40), "e2": math.radians(60), "e1": math.radians(180)}
def on_circle(a): return Vector((C.x + RR * math.cos(a), C.y + RR * math.sin(a), 0.0))
EN = {}
for k, a in ANG.items():
    p1 = on_circle(a); p0 = p1 + Vector((0.0, 3.5, 0)) + Vector((rnd.uniform(-1, 1), 0, 0))
    r, vis = F.soldier(k, tuple(p0), rnd)
    parts = [r] + list(r.children)
    EN[k] = dict(o=r, p0=p0, p1=p1, vis=vis, parts=parts, ph=rnd.uniform(0, 6.28))
KILL = {"e3": K1, "e2": K2, "e1": K3}
deb_m = F.mat_simple("deb", (0.05, 0.05, 0.06), 0.6); spark_m = F.mat_emit("spark", (1.0, 0.35, 0.15), 30.0)
for e in EN.values():
    e["deb"] = []
    for j in range(34):
        o = F.box("edeb", (0, 0, 0), (1, 1, 1), deb_m if j % 3 else spark_m); o.visible_shadow = False
        e["deb"].append(dict(o=o, off=Vector((rnd.uniform(-0.25, 0.25), rnd.uniform(-0.2, 0.2), rnd.uniform(0.2, 1.8))), v=Vector((rnd.uniform(-2, 2), rnd.uniform(-1, 3), rnd.uniform(0, 3))),
                             s=rnd.uniform(0.02, 0.07), w=Vector((rnd.uniform(-9, 9), rnd.uniform(-9, 9), rnd.uniform(-9, 9)))))
# 敵の銃口の光・敵の弾
mz_m = F.mat_emit("mz", (1.0, 0.6, 0.25), 60.0)
for e in EN.values():
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08); m_ = bpy.context.object; m_.data.materials.append(mz_m); m_.parent = e["o"]; m_.location = (0.12, -0.65, 1.18); m_.visible_shadow = False; e["mz"] = m_
etr_m = F.mat_emit("etr", (1.0, 0.55, 0.2), 25.0)
ETR = []
for k in range(6):
    o = F.cyl("etr", (0, 0, 0), 0.01, 0.9, etr_m, verts=8); o.visible_shadow = False; ETR.append(o)
chips = []
for k in range(40):
    o = F.box("chip", (0, 0, 0), (1, 1, 1), conc); chips.append(dict(o=o, v=Vector((rnd.uniform(-1.5, 1.5), rnd.uniform(-2.5, -0.5), rnd.uniform(1, 4))), s=rnd.uniform(0.02, 0.08),
                                                                     w=Vector((rnd.uniform(-9, 9), rnd.uniform(-9, 9), rnd.uniform(-9, 9))), t0=DUCK + 0.15 + (k % 6) * 0.35, x=rnd.uniform(-0.8, 1.0)))

# ---------------------------------------------------------------- 弾の道（銃口 → 円に入る → 円を回り続ける）
MUZ = Vector((0.18, 0.75, 1.46)); A0 = math.radians(-100); ENTRY = on_circle(A0) + Vector((0, 0, 1.66))
L0 = (ENTRY - MUZ).length
def path_pt(s):
    """弾の道の距離 s の点と向き"""
    if s < L0: d = (ENTRY - MUZ).normalized(); return MUZ + d * s, d
    a = A0 + (s - L0) / RR
    p = Vector((C.x + RR * math.cos(a), C.y + RR * math.sin(a), 1.66)); d = Vector((-math.sin(a), math.cos(a), 0)); return p, d
def s_of_angle(a): return L0 + (a - A0) * RR
S_K = {"e3": s_of_angle(ANG["e3"]), "e2": s_of_angle(ANG["e2"]), "e1": s_of_angle(ANG["e1"])}
LAP = 2 * math.pi * RR
def bullet_s(t):
    """時刻 t での弾の位置（スロー → 通常 → 回り続ける）"""
    if t < FIRE: return 0.0
    keys = [(FIRE, 0.0), (K1, S_K["e3"]), (K2, S_K["e2"]), (K3, S_K["e1"])]
    for (ta, sa), (tb, sb) in zip(keys, keys[1:]):
        if t < tb: u = (t - ta) / (tb - ta); return sa + (sb - sa) * (u * 0.65 + 0.35 * ease(u))
    return S_K["e1"] + (t - K3) * 26.0                                    # 通常速度で回り続ける
SMAX = s_of_angle(A0 + 2 * math.pi * 6)
pts = [path_pt(SMAX * i / 1200)[0] for i in range(1201)]
cu = bpy.data.curves.new("bpath", "CURVE"); cu.dimensions = "3D"; spl = cu.splines.new("POLY"); spl.points.add(len(pts) - 1)
for p, c in zip(spl.points, pts): p.co = (*c, 1.0)
cu.bevel_depth = 0.01; cu.bevel_resolution = 2; cu.bevel_factor_mapping_start = "SPLINE"; cu.bevel_factor_mapping_end = "SPLINE"
trail = bpy.data.objects.new("trail", cu); bpy.context.collection.objects.link(trail); trail.visible_shadow = False
TR_M = F.mat_emit("trail_m", (0.35, 0.85, 1.0), 40.0); cu.materials.append(TR_M); TR_K = [n for n in TR_M.node_tree.nodes if n.type == "EMISSION"][0].inputs["Strength"]
# 予告線（描いた道：1周目だけ）
pts2 = [path_pt(s_of_angle(A0 + 2 * math.pi) * i / 400)[0] for i in range(401)]
cu2 = bpy.data.curves.new("plan", "CURVE"); cu2.dimensions = "3D"; sp2 = cu2.splines.new("POLY"); sp2.points.add(len(pts2) - 1)
for p, c in zip(sp2.points, pts2): p.co = (*c, 1.0)
cu2.bevel_depth = 0.02; cu2.bevel_factor_mapping_end = "SPLINE"
plan = bpy.data.objects.new("plan", cu2); bpy.context.collection.objects.link(plan); plan.visible_shadow = False
PL_M = F.mat_emit("plan_m", (0.4, 0.9, 1.0), 12.0); cu2.materials.append(PL_M); PL_K = [n for n in PL_M.node_tree.nodes if n.type == "EMISSION"][0].inputs["Strength"]
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03); bullet = bpy.context.object; bullet.data.materials.append(F.mat_emit("bullet_m", (0.7, 0.95, 1.0), 80.0)); bullet.visible_shadow = False
bl = bpy.data.lights.new("bl", "POINT"); bl.color = (0.4, 0.85, 1.0); bl.shadow_soft_size = 0.05
blo = bpy.data.objects.new("bl", bl); bpy.context.collection.objects.link(blo)
# 管理者（白い外套）
adm = bpy.data.objects.new("admin", None); bpy.context.collection.objects.link(adm); adm.location = ROOF
cloak = F.mat_simple("cloak", (0.85, 0.86, 0.9), 0.6)
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.45, radius2=0.18, depth=1.6, location=(0, 0, 0.8)); c_ = bpy.context.object; c_.data.materials.append(cloak); c_.parent = adm
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0, 0, 1.75)); h_ = bpy.context.object; h_.data.materials.append(cloak); h_.parent = adm; h_.scale = (1, 1, 1.15)
for sx in (-1, 1): F.box("aeye", (sx * 0.07, -0.18, 1.78), (0.06, 0.02, 0.02), F.mat_emit("aeye_m", (1.0, 0.95, 0.9), 40.0), parent=adm)
ADM_ALL = [adm] + list(adm.children)
# 主人公の銃と手
cam = W.camera((0.0, 0.0, 1.62), (0.4, 12, 1.4), lens=26, fstop=8.0)
gun, acc = F.rifle(cam); F.gloves(gun)
GUN_ALL = [gun] + list(gun.children_recursive)
mflash = bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05); mf = bpy.context.object; mf.data.materials.append(F.mat_emit("mf", (1.0, 0.85, 0.5), 80.0)); mf.parent = gun; mf.location = (0, 0.7, 0.065); mf.scale = (1.0, 2.5, 1.0); mf.visible_shadow = False
mfl = bpy.data.lights.new("mfl", "POINT"); mfl.color = (1.0, 0.8, 0.5); mflo = bpy.data.objects.new("mfl", mfl); bpy.context.collection.objects.link(mflo); mflo.parent = gun; mflo.location = (0, 0.75, 0.1)
shell = F.cyl("shell", (0, 0, 0), 0.006, 0.03, F.mat_simple("brass", (0.8, 0.6, 0.25), 0.25, 1.0), verts=10)
# 粒（舞うほこり）
dust_m = F.mat_emit("dust", (1.0, 0.85, 0.7), 2.0); DUST = []
for k in range(200):
    o = F.box("dust", (0, 0, 0), (1, 1, 1), dust_m); o.visible_shadow = False
    DUST.append(dict(o=o, p=Vector((rnd.uniform(-5, 5), rnd.uniform(1, 22), rnd.uniform(0.2, 4))), s=rnd.uniform(0.008, 0.02), ph=rnd.uniform(0, 6.28)))

# ---------------------------------------------------------------- 時間ごとの値
def slow_at(t): return win(t, EDIT, FIRE, 0.4, 0.15) * 0.9 + win(t, FIRE + 0.4, K3 + 0.3, 0.2, 0.3) * 0.7
def gt(t):
    """世界の時間（編集中はほぼ止まる）"""
    if t < EDIT: return t
    if t < FIRE: return EDIT + (t - EDIT) * 0.06
    return EDIT + (FIRE - EDIT) * 0.06 + (t - FIRE) * 0.25 if t < WIN else EDIT + (FIRE - EDIT) * 0.06 + (WIN - FIRE) * 0.25 + (t - WIN)
def enemy_pos(e, t):
    u = ease((gt(t) - 1.0) / (EDIT - 1.5)); p = e["p0"].lerp(e["p1"], u)
    return p
def gun_pose(t):
    """カメラ空間での銃の位置・回転（歩き揺れ・反動・しゃがみ）"""
    loc = Vector((0.1, -0.13, -0.24)); rot = Vector((math.radians(-92), math.radians(-3), math.radians(4)))
    bob = 0.006 * math.sin(t * 6.0) * (1 - slow_at(t)); loc += Vector((0, bob, 0))
    if DUCK <= t < EDIT: loc += Vector((0.04, -0.06, 0.02)) * ease((t - DUCK) / 0.3); rot += Vector((0.25, 0, 0.2)) * ease((t - DUCK) / 0.3) * (1 - ease((t - EDIT + 0.4) / 0.4))
    k = t - FIRE
    if 0 <= k < 0.4: rec = math.exp(-k / 0.07); loc += Vector((0, -0.03 * rec, 0.05 * rec)); rot += Vector((0.12 * rec, 0, 0))
    return loc, rot

def shot(t):
    """(位置, 見る先, レンズ, 主観か)"""
    P0 = Vector((0.0, 0.0, 1.62))
    if t < DUCK: return P0 + Vector((0.01 * math.sin(t * 0.8), 0, 0.01 * math.sin(t * 1.3))), Vector((0.4, 8.6, 1.45)), 26 + 8 * ease((t - 3.0) / 4.0), True
    if t < EDIT: k = ease((t - DUCK) / 0.3) * (1 - ease((t - EDIT + 0.5) / 0.5)); return P0 + Vector((0, 0, -0.62 * k)), Vector((0.4, 8.6, 1.45 - 0.9 * k)), 30, True
    if t < DRAW: return P0, Vector((0.4, 8.6, 1.5)), 30 - 4 * ease((t - EDIT) / 1.5), True
    if t < FIRE - 0.15:
        k = ease((t - DRAW) / 3.0); return Vector((0.4 - 1.5 * k, 0.5 - 1.5 * k, 12.0)), C + Vector((0, 0.4, -1.6)), 30, False
    if t < FIRE + 0.4: return P0, Vector((0.4, 8.6, 1.5)), 26, True
    if t < K3 + 0.4:                                                      # バレットカム
        s = bullet_s(t); p, d = path_pt(s); side_ = Vector((-d.y, d.x, 0)) * 0.25
        return p - d * 0.9 + side_ + Vector((0, 0, 0.22)), p + d * 2.0 + Vector((0, 0, -0.05)), 22, False
    if t < LOOP: return P0, Vector((0.4, 8.6, 1.5)), 26, True
    if t < ADMIN: return P0, Vector((0.4, 8.6, 1.7)), 26 + 6 * ease((t - LOOP) / 2.0), True
    k = ease((t - ADMIN) / 0.6); return P0, Vector((0.4, 8.6, 1.7)).lerp(ROOF + Vector((0, 0, 1.2)), k), 26 + 84 * ease((t - ADMIN - 0.4) / 1.2), True

IMP = [(K1, 1.2, "e3"), (K2, 1.2, "e2"), (K3, 1.4, "e1"), (FIRE, 0.8, "fire")]
def impact_at(t):
    best = (0.0, None, None)
    for ti, s, k in IMP:
        if ti <= t < ti + 0.5:
            v = s * math.exp(-(t - ti) / 0.1)
            if v > best[0]: best = (v, ti, k)
    return best

def place(t):
    g = gt(t)
    # 敵
    for k, e in EN.items():
        kt = KILL[k]; dead = t >= kt
        p = enemy_pos(e, t); o = e["o"]; o.location = p + Vector((0, 0, 0.03 * abs(math.sin(g * 5 + e["ph"])) * (g < EDIT)))
        d = Vector((0, -1, 0)) if True else None; o.rotation_euler = (-0.25 * ease((t - kt) / 0.12) * (t < kt + 0.25), 0, math.atan2(o.location.x - 0.0, -(o.location.y - 0.0)) + math.pi)
        for ch in e["parts"]:
            if ch.type == "MESH": ch.hide_render = t >= kt + 0.18
        e["mz"].hide_render = not (DUCK <= t < EDIT and int(g * 14 + e["ph"] * 3) % 4 == 0) or dead
        for dd in e["deb"]:
            dt = (t - kt - 0.12) * (0.35 if t < WIN else 1.0); ob = dd["o"]
            if dt < 0 or dt > 2.5: ob.hide_render = True; continue
            ob.hide_render = False; ob.location = e["o"].location + dd["off"] + dd["v"] * dt + Vector((0, 0, -3.0 * dt * dt)); ob.scale = (dd["s"] * (1 - ease((dt - 1.6) / 0.9)),) * 3; ob.rotation_euler = dd["w"] * dt
    # 敵の弾（しゃがんでいる間）
    for i, o in enumerate(ETR):
        k = ((g - DUCK) * 2.4 + i / len(ETR)) % 1.0
        on = DUCK <= t < EDIT
        o.hide_render = not on
        if not on: continue
        e = list(EN.values())[i % 3]; a = e["o"].location + Vector((0, 0, 1.2)); b = Vector((0.2 + 0.3 * math.sin(i * 7), 1.35, 0.7 + 0.25 * math.cos(i * 3)))
        p = a.lerp(b, k); d = (b - a).normalized(); o.location = p; o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    for c in chips:
        dt = (g - c["t0"]) % 2.1 if t < EDIT else 9; ob = c["o"]
        if t < DUCK or dt > 0.9 or t >= EDIT: ob.hide_render = True; continue
        ob.hide_render = False; ob.location = Vector((c["x"], 1.1, 0.9)) + c["v"] * dt + Vector((0, 0, -4.9 * dt * dt)); ob.scale = (c["s"],) * 3; ob.rotation_euler = c["w"] * dt
    # 予告線・弾・軌跡
    plan.hide_render = not (DRAW - 0.3 <= t < K3 + 0.5)
    cu2.bevel_factor_end = ease((t - DRAW) / 2.6); PL_K.default_value = 12.0 * (1 - 0.6 * ease((t - FIRE) / 0.5))
    s = bullet_s(t); fired = t >= FIRE
    bullet.hide_render = not fired; trail.hide_render = not fired
    if fired:
        p, d = path_pt(s); bullet.location = p; blo.location = p; bl.energy = 60.0
        tail = 7.0 if t < WIN else 14.0
        cu.bevel_factor_start = max(0.0, (s - tail) / SMAX); cu.bevel_factor_end = min(1.0, s / SMAX)
    else: bl.energy = 0.0
    # 管理者
    for o in ADM_ALL:
        if o.type == "MESH": o.hide_render = t < ADMIN - 0.1
    # ほこり
    for dd in DUST:
        o = dd["o"]; o.location = dd["p"] + Vector((0.3 * math.sin(g * 0.3 + dd["ph"]), 0.2 * math.cos(g * 0.25 + dd["ph"]), 0.15 * math.sin(g * 0.5 + dd["ph"]))); o.scale = (dd["s"],) * 3
    # カメラと銃
    pos, look, lens, pov = shot(t)
    iv, ti, ik = impact_at(t)
    sh = 0.0
    if ti is not None: sh = (0.02 if pov else 0.05) * iv
    if DUCK <= t < EDIT: sh = max(sh, 0.008)
    pos = pos + Vector((sh * math.sin(t * 61), sh * math.sin(t * 47), sh * math.sin(t * 53)))
    cam.location = pos; W.aim(cam, look); cam.data.lens = lens
    for o in GUN_ALL:
        if o.type == "MESH": o.hide_render = not pov
    gl_, gr_ = gun_pose(t); gun.location = gl_; gun.rotation_euler = tuple(gr_)
    fk = t - FIRE
    mf.hide_render = not (pov and 0 <= fk < 0.06); mfl.energy = 300.0 if (0 <= fk < 0.06) else 0.0
    shell.hide_render = not (pov and 0 <= fk < 0.6)
    if not shell.hide_render:
        bpy.context.view_layer.update(); base = gun.matrix_world @ Vector((0.03, 0.05, 0.08))
        r_ = cam.matrix_world.to_3x3() @ Vector((1, 0.6, -0.3)); shell.location = base + r_ * fk * 1.6 + Vector((0, 0, -4.9 * fk * fk)); shell.rotation_euler = (fk * 30, fk * 20, 0)
    TR_K.default_value = 40.0 + 30.0 * slow_at(t)
    edit = win(t, EDIT, FIRE + 0.1, 0.4, 0.1)
    meta = dict(impact=iv, kind=ik or "", edit=edit, slow=slow_at(t), pov=pov, dash=win(t, FIRE, K3 + 0.3, 0.05, 0.3) if not pov else 0.0)
    if ti is not None and ik != "fire":
        bpy.context.view_layer.update(); sv = world_to_camera_view(sc, cam, EN[ik]["o"].location + Vector((0, 0, 1.66))); meta["imp"] = [sv.x, sv.y, sv.z]
    return meta

frames = TEST or range(START, STOP)
t0 = time.time()
for f in frames:
    p = os.path.join(OUT, "%04d.png" % (f + 1))
    if os.path.exists(p) and not TEST: continue
    t = f / FPS
    meta = place(t)
    bpy.context.view_layer.update()
    meta.update(t=t)
    json.dump(meta, open(p[:-4] + ".json", "w"))
    tmp = p[:-4] + "_tmp.png"; sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True); os.replace(tmp, p)
    print("frame %s t=%.2f %.1fs" % (p, t, time.time() - t0), flush=True); t0 = time.time()
