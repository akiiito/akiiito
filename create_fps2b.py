"""
create_fps2b.py ― FPS転生 第2話（BADルート：撃ち返した）30秒・主観・輪郭線つき
  python create_fps1.py [--samples 20] [--res 0.75] [--start 0] [--end 720] [--test 0,100,...]
"""
import os, sys, math, json, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
import s2_world as W, fps_world as F
from fps2b_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "20")); FPS = 24; N = int(END * FPS)
RS = float(arg("--res", "0.75"))
START = int(arg("--start", "0")); STOP = int(arg("--end", str(N)))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_FPS2B" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
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


# ================================================================ 第2話（BADルート）
import s3_toon as T, blk_hair as H
LINES = json.load(open(os.path.join(HERE, "fps2b_lines.json"), encoding="utf-8"))
# 輪郭線（アニメ調）
sc.render.use_freestyle = True
sc.cycles.transparent_max_bounces = 48
try: sc.render.line_thickness_mode = "ABSOLUTE"; sc.render.line_thickness = 1.4 * RS / 0.75
except Exception: pass
try:
    fs_ = bpy.context.view_layer.freestyle_settings; ls_ = fs_.linesets[0] if fs_.linesets else fs_.linesets.new("ls")
    ls_.select_by_visibility = True; ls_.select_silhouette = True; ls_.select_border = True; ls_.select_crease = True
    if ls_.linestyle is None: ls_.linestyle = bpy.data.linestyles.new("ls")
    ls_.linestyle.color = (0.04, 0.03, 0.03); ls_.linestyle.thickness = 1.6
except Exception as ex: print("freestyle", ex)
# 屋上の管理者は最初から見えている
for o in ADM_ALL:
    if o.type == "MESH": o.hide_render = False

# ---------------------------------------------------------------- ミナ
face_em = []
def pbr(root, cmap):
    for o in [root] + list(root.children_recursive):
        if o.type != "MESH": continue
        for i, m in enumerate(o.data.materials):
            if not (m and m.node_tree): continue
            if "facemat" in m.name: face_em.extend(n for n in m.node_tree.nodes if n.type == "EMISSION"); continue
            rp = [n for n in m.node_tree.nodes if n.type == "VALTORGB"]
            if not rp: continue
            key = m.name.split("_")[-1]
            c = cmap.get(key) or tuple(x ** 0.4545 for x in rp[0].color_ramp.elements[1].color[:3])
            lin = tuple(x ** 2.2 for x in c); sk = "skin" in m.name; hr = "hair" in m.name
            nm = W.mat(m.name + "_pbr", lin, 0.5 if sk else (0.36 if hr else 0.8), sss=0.25 if sk else 0.0)
            b = nm.node_tree.nodes["Principled BSDF"]
            if hr: b.inputs["Coat Weight"].default_value = 0.25; b.inputs["Sheen Weight"].default_value = 0.4
            o.data.materials[i] = fogify(nm)
def face_to(o, p, tgt):
    o.location = p; d = Vector((tgt[0] - p[0], tgt[1] - p[1], 0)).normalized()
    o.rotation_euler = (0, 0, math.atan2(-d.x, d.y))
MCOL = {"blazer": (0.2, 0.27, 0.22), "skirt": (0.12, 0.12, 0.14), "shirt": (0.85, 0.85, 0.82), "ribbon": (0.7, 0.2, 0.25), "sock": (0.08, 0.08, 0.09), "shoe": (0.1, 0.08, 0.07)}
MPOSE = {"hold": {"L": ((0.2, 0.12, 1.02), (0.1, 0.3, 1.05)), "R": ((-0.2, 0.08, 1.0), (-0.12, 0.2, 0.98))},
         "aim": {"L": ((0.22, 0.2, 1.22), (0.08, 0.42, 1.3)), "R": ((-0.2, 0.06, 1.2), (-0.06, 0.16, 1.3))}}
riflem = fogify(F.mat_simple("snp", (0.05, 0.055, 0.06), 0.4, 0.6))
MM = {}
for k, arms in MPOSE.items():
    nm = "mina" if k == "hold" else "mina" + k
    r_, tx_ = T.girl(nm, (0, 0, 0), hair=(0.12, 0.1, 0.16), face="mina", ponytail=True, arms=arms)
    pbr(r_, MCOL); H.upgrade(r_, nm, [m for o in r_.children if o.name.startswith(nm + "_hair") for m in o.data.materials][0], seed=17)
    if k == "hold": F.box(nm + "_rifle", (0.0, 0.32, 1.0), (0.05, 0.95, 0.07), riflem, rot=(0.15, 0, 0.35), bevel=0.01, parent=r_)
    else:
        F.box(nm + "_rifle", (0.0, 0.62, 1.3), (0.05, 0.95, 0.07), riflem, bevel=0.01, parent=r_)
        F.cyl(nm + "_scope", (0.0, 0.5, 1.37), 0.025, 0.22, riflem, rot=(math.pi / 2, 0, 0), parent=r_)
    MM[k] = (r_, tx_, [r_] + list(r_.children_recursive))
P0 = Vector((0.0, 0.0, 1.62))
def mina_state(t):
    if t < MINA: return "hold", Vector((-6.0, 2.5, 0)), P0
    if t < 8.0: u = ease((t - MINA) / 1.3); return "hold", Vector((-4.5, 2.6, 0)).lerp(Vector((-0.35, 1.45, 0)), u), P0
    if t < AIM: return "hold", Vector((-0.35, 1.45, 0)), P0
    u = ease((t - AIM) / 0.5); return "aim", Vector((-0.35, 1.45, 0)).lerp(Vector((-0.3, 1.9, 0)), u), P0
def talking(who, t): return any(l[0] <= t <= l[1] - 0.05 for l in LINES if l[5] == who)
def expr_mina(t):
    tk = talking("mina", t) and int(t * 12) % 3 != 2
    if t < 10.4: return "shock" if tk else "shockc"
    if t < AIM: return "sadtalk" if tk else "sad"
    if t < CHOICE: return "coldtalk" if tk else "cold"
    return "tearsadtalk" if tk else "tearsad"

# ---------------------------------------------------------------- 世界が消える（距離で白い格子 → 透明）
DEL = bpy.data.node_groups.new("DEL", "ShaderNodeTree")
DEL.interface.new_socket("Shader", in_out="INPUT", socket_type="NodeSocketShader"); DEL.interface.new_socket("Shader", in_out="OUTPUT", socket_type="NodeSocketShader")
_n = DEL.nodes; _l = DEL.links.new; gi = _n.new("NodeGroupInput"); go = _n.new("NodeGroupOutput")
def _m(op, a, b=None):
    n = _n.new("ShaderNodeMath"); n.operation = op
    for i, v in enumerate((a, b)):
        if v is None: continue
        if isinstance(v, (int, float)): n.inputs[i].default_value = v
        else: _l(v, n.inputs[i])
    return n.outputs[0]
geo = _n.new("ShaderNodeNewGeometry"); sep = _n.new("ShaderNodeSeparateXYZ"); _l(geo.outputs["Position"], sep.inputs[0])
rv = _n.new("ShaderNodeValue"); rv.name = "R"; rv.outputs[0].default_value = 500.0
dx = _m("SUBTRACT", sep.outputs["X"], 0.0); dy = _m("SUBTRACT", sep.outputs["Y"], 2.0)
dist = _m("SQRT", _m("ADD", _m("MULTIPLY", dx, dx), _m("MULTIPLY", dy, dy)))
dist = _m("ADD", dist, _m("MULTIPLY", sep.outputs["Z"], 0.35))                       # 上の方から先に消える
over = _m("SUBTRACT", dist, rv.outputs[0])
band = _m("MULTIPLY", _m("GREATER_THAN", over, 0.0), _m("LESS_THAN", over, 6.0))         # 白い格子の帯
gone = _m("GREATER_THAN", over, 6.0)
def grid(axis):
    f = _m("FRACT", _m("MULTIPLY", axis, 1.0)); return _m("LESS_THAN", _m("ABSOLUTE", _m("SUBTRACT", f, 0.5)), 0.04)
lines = _m("MINIMUM", _m("ADD", _m("ADD", grid(sep.outputs["X"]), grid(sep.outputs["Y"])), grid(sep.outputs["Z"])), 1.0)
em = _n.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.85, 0.95, 1.0, 1)
_l(_m("ADD", _m("MULTIPLY", lines, 6.0), 1.2), em.inputs["Strength"])
mx = _n.new("ShaderNodeMixShader"); _l(band, mx.inputs[0]); _l(gi.outputs[0], mx.inputs[1]); _l(em.outputs[0], mx.inputs[2])
tr = _n.new("ShaderNodeBsdfTransparent"); mx2 = _n.new("ShaderNodeMixShader"); _l(gone, mx2.inputs[0]); _l(mx.outputs[0], mx2.inputs[1]); _l(tr.outputs[0], mx2.inputs[2])
_l(mx2.outputs[0], go.inputs[0])
for m in list(bpy.data.materials):
    if not m.node_tree or m.name.startswith(("gun", "glove", "sleeve", "brass", "mf", "sglass", "dust")): continue
    outs = [n for n in m.node_tree.nodes if n.type == "OUTPUT_MATERIAL"]
    if not outs or not outs[0].inputs["Surface"].links: continue
    src = outs[0].inputs["Surface"].links[0].from_socket; g = m.node_tree.nodes.new("ShaderNodeGroup"); g.node_tree = DEL
    m.node_tree.links.new(src, g.inputs[0]); m.node_tree.links.new(g.outputs[0], outs[0].inputs["Surface"])
    try: m.surface_render_method = "DITHERED"
    except Exception: pass
def del_r(t): return 500.0 if t < DELETE else max(5.0, 140.0 * math.exp(-(t - DELETE) / 5.2) - 2.0)
# 白い空へ
wmx = wn.nodes.new("ShaderNodeMix"); wmx.data_type = "RGBA"; wn.links.new(sky.outputs[0], wmx.inputs["A"]); wmx.inputs["B"].default_value = (0.9, 0.96, 1.0, 1)
wn.links.new(wmx.outputs["Result"], wn.nodes["Background"].inputs[0])
# 管理者のかけら
ADEB = []
for k in range(60):
    o = F.box("adeb", (0, 0, 0), (1, 1, 1), F.mat_emit("adm_deb", (0.9, 0.95, 1.0), 6.0) if k % 2 else cloak)
    ADEB.append(dict(o=o, off=Vector((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), rnd.uniform(0.2, 1.9))), v=Vector((rnd.uniform(-3, 3), rnd.uniform(-1, 3), rnd.uniform(0, 4))),
                     s=rnd.uniform(0.04, 0.14), w=Vector((rnd.uniform(-9, 9), rnd.uniform(-9, 9), rnd.uniform(-9, 9)))))
tracer = F.cyl("tracer", (0, 0, 0), 0.02, 1.4, F.mat_emit("tr2", (0.5, 0.9, 1.0), 60.0), verts=8); tracer.visible_shadow = False
GLOVE = bpy.data.materials.get("glove"); GB = GLOVE.node_tree.nodes["Principled BSDF"] if GLOVE else None

# ---------------------------------------------------------------- 時間ごとの値
def shot(t):
    mk, mp, _ = mina_state(t); mh = mp + Vector((0, 0, 1.42))
    if t < HIT: return P0, ROOF + Vector((0, 0, 1.3)), 70, True
    if t < 3.1: return P0 + Vector((0.3, 0.5, 0)), ROOF + Vector((0, 0, 1.0)), 110, False
    if t < MINA: return P0, Vector((0.6, 30, 3.0 + 2.0 * ease((t - DELETE) / 1.5))), 24, True
    if t < 8.4: k = ease((t - MINA) / 1.0); return P0, Vector((0.6, 30, 3.0)).lerp(mh, k), 24 + 10 * k, True
    if t < 10.4: return P0, P0 + Vector((0.05, 1.0, -0.35)), 26, True
    if t < 13.0: return P0, mh + Vector((0, 0, -0.02)), 40, True
    if t < 14.7: return P0, Vector((0.6, 20, 1.6)), 22, True
    if t < 18.3: return P0, P0 + Vector((0.05, 1.0, -0.35)), 26, True
    if t < 19.6: return P0, mh + Vector((0.05, 0, -0.08)), 36, True
    if t < CHOICE: return P0, Vector((0.6, 25, 14.0)), 22, True
    return P0, mh + Vector((0, 0, -0.03)), 44 + 4 * ease((t - CHOICE) / 4.0), True
def gun_pose(t):
    loc = Vector((0.1, -0.13, -0.24)); rot = Vector((math.radians(-92), math.radians(-3), math.radians(4)))
    down = 0.0
    loc += Vector((-0.04, 0.06, 0.04)) * down; rot += Vector((0.35, 0.0, 0.25)) * down
    k = t - FIRE
    if 0 <= k < 0.4: rec = math.exp(-k / 0.07); loc += Vector((0, -0.03 * rec, 0.05 * rec)); rot += Vector((0.12 * rec, 0, 0))
    return loc, rot

def place(t):
    # 世界の消失
    R_ = del_r(t); DEL.nodes["R"].outputs[0].default_value = R_
    wmx.inputs["Factor"].default_value = ease((t - DELETE - 1.0) / 14.0) * 0.85
    # 管理者：撃たれて砕ける
    for o in ADM_ALL:
        if o.type == "MESH": o.hide_render = t >= HIT + 0.08
    for d in ADEB:
        dt = t - HIT; o = d["o"]
        if dt < 0 or dt > 3.0: o.hide_render = True; continue
        o.hide_render = False; o.location = ROOF + d["off"] + d["v"] * dt + Vector((0, 0, -4.9 * dt * dt)); o.scale = (d["s"],) * 3; o.rotation_euler = d["w"] * dt
    k = (t - FIRE) / (HIT - FIRE); tracer.hide_render = not (0 <= k < 1)
    if not tracer.hide_render:
        a = cam.matrix_world @ Vector((0.1, -0.1, -0.6)); b = ROOF + Vector((0, 0, 1.3)); p = a.lerp(b, k); d_ = (b - a).normalized()
        tracer.location = p; tracer.rotation_euler = d_.to_track_quat("Z", "Y").to_euler()
    # 敵（止まった NPC）
    for e in EN.values():
        e["o"].location = e["p1"]; e["o"].rotation_euler = (0, 0, math.atan2(e["p1"].x, -e["p1"].y) + math.pi)
        e["mz"].hide_render = True
        for dd in e["deb"]: dd["o"].hide_render = True
    for o in ETR: o.hide_render = True
    for c in chips: c["o"].hide_render = True
    # ミナ
    mk, mp, ml = mina_state(t); vis = t >= MINA - 0.1
    for k_, (r_, tx_, allo) in MM.items():
        on = vis and k_ == mk
        for o in allo:
            if o.type == "MESH": o.hide_render = not on
        if k_ == mk: face_to(r_, mp, ml)
        if mk == "hold" and k_ == mk and MINA <= t < 8.0: r_.location.z = 0.05 * abs(math.sin(t * 12))
        T.set_expr(tx_, "mina", expr_mina(t))
    # 手袋が白くなる
    if GB:
        w = ease((t - 15.6) / 2.2); GB.inputs["Base Color"].default_value = (*Vector((0.06, 0.06, 0.065)).lerp(Vector((0.9, 0.93, 0.95)), w), 1)
        GB.inputs["Emission Color"].default_value = (0.8, 0.9, 1.0, 1); GB.inputs["Emission Strength"].default_value = 1.5 * w
    # ほこり
    for dd in DUST:
        o = dd["o"]; o.location = dd["p"] + Vector((0.3 * math.sin(t * 0.3 + dd["ph"]), 0.2 * math.cos(t * 0.25 + dd["ph"]), 0.15 * math.sin(t * 0.5 + dd["ph"]))); o.scale = (dd["s"],) * 3
    # カメラ・銃
    pos, look, lens, pov = shot(t)
    sh = 0.03 * math.exp(-max(0.0, t - HIT) / 0.2) * (t >= HIT) + 0.006 * (t > DELETE)
    pos = pos + Vector((sh * math.sin(t * 61), sh * math.sin(t * 47), sh * math.sin(t * 53)))
    cam.location = pos; W.aim(cam, look); cam.data.lens = lens
    for o in GUN_ALL:
        if o.type == "MESH": o.hide_render = not pov
    gl_, gr_ = gun_pose(t); gun.location = gl_; gun.rotation_euler = tuple(gr_)
    fk = t - FIRE; mf.hide_render = not (pov and 0 <= fk < 0.06); mfl.energy = 300.0 if (0 <= fk < 0.06) else 0.0
    shell.hide_render = True
    iv = 1.2 * math.exp(-max(0.0, t - HIT) / 0.1) * (HIT <= t < HIT + 0.5)
    meta = dict(impact=iv, kind="hit" if iv > 0 else "", edit=0.0, pov=pov, dash=0.0)
    if iv > 0:
        bpy.context.view_layer.update(); sv = world_to_camera_view(sc, cam, ROOF + Vector((0, 0, 1.3))); meta["imp"] = [sv.x, sv.y, sv.z]
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
