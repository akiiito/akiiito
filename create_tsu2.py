"""
create_tsu2.py ― 津波動画の「高画質版」の絵（上下2画面・8fps）。create_tsu1.py と同じ動き・タイミングで、見た目だけを作り直す
  ・のっぺりしたトゥーン塗り → 物理ベースの質感（光の回り込み・反射）と、もやのかかった空
  ・海と波：Ocean モディファイアの本物っぽい水面、波頭の白い泡、濁った浸水と浮かぶ木材
  ・日本の海沿いの町：瓦屋根の家（窓・ブロック塀）、電柱と電線、木、車、看板つきの津波避難ビル
  python create_tsu2.py [--samples 16] [--start 0] [--end 504] [--test 0,40,...]
"""
import os, sys, math, json, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import s2_world as W, s3_toon as T

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "16")); FPS = 8; N = int(63.0 * FPS)
START = int(arg("--start", "0")); STOP = int(arg("--end", str(N)))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_TSU2" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
LINES = json.load(open(os.path.join(HERE, "tsu1_lines.json"), encoding="utf-8"))
def T0(i): return LINES[i][0]
def T1(i): return LINES[i][1]

sc = W.reset(SAMPLES, res=(720, 640))
sc.cycles.max_bounces = 4; sc.view_settings.exposure = -0.75; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.02
rnd = random.Random(7)

def P(name, col, rough=0.6, noise=None, metal=0.0, spec=0.5):
    return W.mat(name, col, rough, metal, spec, noise=noise)
def obox(name, loc, size, m, rot=(0, 0, 0), bevel=0.0):
    """原点を中心に作ってから動かす（位置をメッシュに焼き込まない）"""
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0)); o = bpy.context.object; o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        md = o.modifiers.new("bv", "BEVEL"); md.width = bevel; md.segments = 2
    o.location = loc; o.rotation_euler = rot; o.data.materials.append(m); return o
def ocyl(name, loc, r, h, m, rot=(0, 0, 0), verts=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot); o = bpy.context.object
    o.name = name; o.data.materials.append(m); bpy.ops.object.shade_smooth(); return o

# ---- 材質
M = dict(asph=P("asph", (0.07, 0.07, 0.075), 0.85, noise=(30.0, 0.25)), line=P("line", (0.85, 0.85, 0.8), 0.6),
         grass=P("grass", (0.16, 0.26, 0.1), 0.9, noise=(6.0, 0.35)), sand=P("sand", (0.55, 0.48, 0.36), 0.9, noise=(20.0, 0.2)),
         conc=P("conc", (0.5, 0.5, 0.48), 0.85, noise=(12.0, 0.25)), block=P("block", (0.58, 0.57, 0.53), 0.9, noise=(25.0, 0.3)),
         tile=P("tile", (0.12, 0.13, 0.15), 0.45, noise=(40.0, 0.3)), tile2=P("tile2", (0.32, 0.17, 0.12), 0.5, noise=(40.0, 0.3)),
         tile3=P("tile3", (0.18, 0.24, 0.32), 0.4, noise=(40.0, 0.3)),
         glass=P("glass", (0.03, 0.04, 0.05), 0.08, spec=0.9), frame=P("wframe", (0.6, 0.6, 0.6), 0.4, metal=0.8),
         wood=P("wood", (0.3, 0.2, 0.12), 0.7, noise=(8.0, 0.3)), pole=P("pole", (0.45, 0.45, 0.43), 0.7, noise=(10.0, 0.2)),
         wire=P("wire", (0.02, 0.02, 0.02), 0.5), leaf=P("leaf", (0.06, 0.13, 0.05), 0.8, noise=(5.0, 0.4)),
         bark=P("bark", (0.16, 0.11, 0.08), 0.9), tire=P("tire", (0.02, 0.02, 0.02), 0.7))
walls = [P("w%d" % i, c, 0.85, noise=(9.0, 0.18)) for i, c in enumerate([(0.75, 0.72, 0.64), (0.62, 0.6, 0.55), (0.8, 0.78, 0.74), (0.55, 0.5, 0.42), (0.68, 0.7, 0.72)])]
carc = [P("car%d" % i, c, 0.25, spec=0.8) for i, c in enumerate([(0.6, 0.04, 0.04), (0.85, 0.85, 0.85), (0.05, 0.08, 0.2), (0.12, 0.12, 0.13), (0.7, 0.6, 0.45)])]

# ---- 地面・道路・浜・堤防
obox("land", (0, -30, -0.05), (240, 110, 0.1), M["grass"])
obox("road", (0, -10, 0.005), (6, 70, 0.01), M["asph"]); obox("road2", (0, 10, 0.005), (200, 5, 0.01), M["asph"])
for k in range(14): obox("dash", (0, -44 + k * 5, 0.012), (0.15, 2.5, 0.01), M["line"])
obox("beach", (0, 27, -0.15), (240, 10, 0.3), M["sand"])
obox("seawall", (0, 22, 0.6), (240, 0.8, 1.2), M["conc"], bevel=0.05)
# 高台（坂＋上の平地）と坂道
me = bpy.data.meshes.new("hill"); bm = bmesh.new()
pts = [(-80, -30, 0), (80, -30, 0), (80, -60, 14), (-80, -60, 14), (-80, -140, 14), (80, -140, 14)]
v = [bm.verts.new(p) for p in pts]; bm.faces.new([v[0], v[1], v[2], v[3]]); bm.faces.new([v[3], v[2], v[5], v[4]])
bm.to_mesh(me); bm.free(); hill = bpy.data.objects.new("hill", me); bpy.context.collection.objects.link(hill); me.materials.append(M["grass"])
obox("hillroad", (2.5, -45, 7.04), (3.4, 33.5, 0.06), M["asph"], rot=(math.atan2(14, 30), 0, 0))
def hill_z(y): return 0.0 if y > -30 else (min(14.0, (-30 - y) * 14 / 30))
# 木（坂と高台にたくさん）
def tree(x, y, s=1.0):
    z = hill_z(y); ocyl("trunk", (x, y, z + 1.2 * s), 0.18 * s, 2.4 * s, M["bark"], verts=8)
    for k in range(3):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rnd.uniform(1.2, 1.8) * s, location=(x + rnd.uniform(-0.6, 0.6) * s, y + rnd.uniform(-0.6, 0.6) * s, z + (2.6 + k * 0.9) * s))
        o = bpy.context.object; o.data.materials.append(M["leaf"])
        d = o.modifiers.new("d", "DISPLACE"); tx = bpy.data.textures.new("tc%d" % rnd.randint(0, 10**9), "CLOUDS"); tx.noise_scale = 0.6; d.texture = tx; d.strength = 0.5
for k in range(70):
    x = rnd.uniform(-70, 70); y = rnd.uniform(-75, -32)
    if abs(x - 2.5) < 4: continue
    tree(x, y, rnd.uniform(0.9, 1.4))
# ---- 家並み（瓦屋根・窓・ブロック塀）
def house(x, y):
    w = rnd.uniform(6.0, 7.2); d = rnd.uniform(5.5, 6.8); h = rnd.choice([3.0, 5.6, 5.8])
    wm = rnd.choice(walls); obox("hb", (x, y, h / 2), (w, d, h), wm, bevel=0.03)
    roof = rnd.choice([M["tile"], M["tile"], M["tile2"], M["tile3"]]); pitch = math.radians(rnd.uniform(22, 30))
    half = d / 2 + 0.5; rl = half / math.cos(pitch); rz = h + math.tan(pitch) * half / 2
    for s in (-1, 1):
        obox("roof", (x, y + s * half / 2, rz), (w + 1.0, rl, 0.14), roof, rot=(s * -pitch, 0, 0))
    obox("gable", (x, y, h + math.tan(pitch) * half / 2 - 0.05), (w - 0.1, 0.02, 0.02), roof)
    for s in (-1, 1):                                                       # 窓（表と裏）
        for k in range(rnd.randint(2, 3)):
            wx = x - w / 2 + (k + 0.7) * w / 3.2
            for fl in ([1.4] if h < 4 else [1.4, 4.2]):
                obox("win", (wx, y + s * (d / 2 + 0.02), fl), (1.3, 0.06, 1.0), M["glass"])
                obox("wf", (wx, y + s * (d / 2 + 0.03), fl - 0.55), (1.45, 0.1, 0.08), M["frame"])
    if rnd.random() < 0.7:                                                  # ブロック塀
        obox("bw", (x, y + d / 2 + 1.6, 0.6), (w + 1.5, 0.15, 1.2), M["block"])
    if rnd.random() < 0.35: tree(x + w / 2 + 1.2, y + d / 2 + 0.8, 0.7)
for x in range(-56, 57, 9):
    for y in range(-26, 19, 9):
        if abs(x) < 7 or (abs(x - 9) < 7 and abs(y - 12) < 7): continue
        house(x + rnd.uniform(-0.6, 0.6), y)
# 電柱と電線（道の両側）
poles = []
for side in (-3.6, 3.6):
    for k in range(9):
        y = -28 + k * 6.0; z = hill_z(y)
        ocyl("pole", (side, y, z + 4.5), 0.13, 9.0, M["pole"], verts=10); obox("arm", (side, y, z + 8.3), (1.4, 0.1, 0.1), M["pole"])
        poles.append((side, y, z + 8.35))
for (a, b) in zip(poles, poles[1:]):
    if a[0] != b[0]: continue
    for dx in (-0.55, 0.0, 0.55):
        p0 = Vector((a[0] + dx, a[1], a[2])); p1 = Vector((b[0] + dx, b[1], b[2])); dv = p1 - p0
        o = ocyl("wire", tuple((p0 + p1) / 2 - Vector((0, 0, 0.25))), 0.012, dv.length, M["wire"], verts=4)
        o.rotation_euler = dv.to_track_quat("Z", "Y").to_euler()
# ---- 津波避難ビル（窓の帯・屋上の柵・外階段・看板）
obox("evac", (9, 12, 7.5), (8, 8, 15), M["conc"], bevel=0.05)
for k in range(1, 5):
    for s in (-1, 1): obox("band", (9 + s * 4.02, 12, k * 3.2), (0.06, 6.8, 1.2), M["glass"])
    obox("bandf", (9, 12 - 4.02, k * 3.2), (6.8, 0.06, 1.2), M["glass"])
for k in range(10): obox("stair", (13.6, 12, 1.5 * k + 0.75), (1.4, 3.0, 0.12), M["conc"])
obox("rail", (13.6 + 0.7, 12, 7.5), (0.05, 3.0, 15.2), M["frame"])
obox("roofrail", (9, 12, 15.6), (8.1, 8.1, 0.05), M["frame"])
sm = bpy.data.materials.new("signimg"); sm.use_nodes = True; nt = sm.node_tree; bsdf = nt.nodes["Principled BSDF"]
ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = bpy.data.images.load(os.path.join(HERE, "tsu_tex", "evac_sign.png"))
nt.links.new(ti.outputs["Color"], bsdf.inputs["Base Color"]); bsdf.inputs["Roughness"].default_value = 0.4
bpy.ops.mesh.primitive_plane_add(size=1, location=(4.94, 12, 10.5), rotation=(math.pi / 2, 0, -math.pi / 2)); sg = bpy.context.object
sg.scale = (4.0, 1.6, 1); sg.data.materials.append(sm)
# ---- 渋滞の車（角の丸い車体・窓・タイヤ）
def car(x, y, rot=0.0):
    cm = rnd.choice(carc)
    b = obox("car", (x, y, 0.62), (1.7, 4.2, 0.75), cm, rot=(0, 0, rot), bevel=0.18)
    c = obox("cab", (x, y - 0.3, 1.25), (1.5, 2.2, 0.6), M["glass"], rot=(0, 0, rot), bevel=0.15)
    for dx in (-0.8, 0.8):
        for dy in (-1.35, 1.35): ocyl("tire", (x + dx, y + dy, 0.33), 0.33, 0.25, M["tire"], rot=(0, math.pi / 2, 0), verts=16)
for k in range(9): car(-1.4, -27 + k * 5.0)
for k in range(5): car(rnd.uniform(-50, 50), 10 + rnd.uniform(-1, 1), math.pi / 2)
# ---- 海（Ocean モディファイア）・押し寄せる波・浸水
seam = P("seawater", (0.02, 0.07, 0.08), 0.06, spec=0.6)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 190, -0.3)); sea = bpy.context.object; sea.name = "sea"
oc = sea.modifiers.new("ocean", "OCEAN"); oc.geometry_mode = "GENERATE"; oc.resolution = 7; oc.spatial_size = 60; oc.repeat_x = 10; oc.repeat_y = 6
oc.wave_scale = 0.6; oc.choppiness = 1.2; oc.wind_velocity = 14; sea.data.materials.append(seam)
# 波の壁：断面が前にせり出した形のメッシュ（高さ1、奥行き12）を、高さに合わせて伸ばす
wavem = bpy.data.materials.new("wavemat"); wavem.use_nodes = True; nt = wavem.node_tree; bsdf = nt.nodes["Principled BSDF"]
co = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6.0
add_ = nt.nodes.new("ShaderNodeMath"); add_.operation = "ADD"; rp = nt.nodes.new("ShaderNodeValToRGB")
rp.color_ramp.elements[0].position = 0.62; rp.color_ramp.elements[0].color = (0.015, 0.06, 0.06, 1); rp.color_ramp.elements[1].position = 0.9; rp.color_ramp.elements[1].color = (0.85, 0.88, 0.86, 1)
nt.links.new(co.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], add_.inputs[0]); nt.links.new(nz.outputs["Fac"], add_.inputs[1]); add_.inputs[1].default_value = 0
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 0.35; nt.links.new(nz.outputs["Fac"], mul.inputs[0]); nt.links.new(mul.outputs[0], add_.inputs[1])
nt.links.new(add_.outputs[0], rp.inputs["Fac"]); nt.links.new(rp.outputs["Color"], bsdf.inputs["Base Color"])
r2 = nt.nodes.new("ShaderNodeMapRange"); nt.links.new(add_.outputs[0], r2.inputs["Value"]); r2.inputs["To Min"].default_value = 0.08; r2.inputs["To Max"].default_value = 0.7
nt.links.new(r2.outputs["Result"], bsdf.inputs["Roughness"])
me = bpy.data.meshes.new("wave"); bm = bmesh.new()
prof = [(12.0, 0.0), (8, 0.25), (4.5, 0.55), (2.0, 0.8), (0.6, 0.95), (-0.4, 1.0), (-1.2, 0.93), (-1.5, 0.8), (-1.1, 0.68)]
NX = 160; rows = []
for i in range(NX + 1):
    x = -200 + 400 * i / NX
    rows.append([bm.verts.new((x, py, pz)) for py, pz in prof])
for i in range(NX):
    for j in range(len(prof) - 1):
        bm.faces.new([rows[i][j], rows[i + 1][j], rows[i + 1][j + 1], rows[i][j + 1]])
bm.to_mesh(me); bm.free(); wave = bpy.data.objects.new("wave", me); bpy.context.collection.objects.link(wave); me.materials.append(wavem)
sub = wave.modifiers.new("sub", "SUBSURF"); sub.levels = 2; sub.render_levels = 2
dsp = wave.modifiers.new("d", "DISPLACE"); wtex = bpy.data.textures.new("wtex", "CLOUDS"); wtex.noise_scale = 4.0; dsp.texture = wtex; dsp.strength = 0.07
for p in me.polygons: p.use_smooth = True
# 浸水：濁った水（細かい波）＋浮かぶ木材
murk = P("murk", (0.07, 0.055, 0.035), 0.08, noise=(3.0, 0.3), spec=0.7)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); flood = bpy.context.object; flood.name = "flood"
flood.scale = (400, 400, 1); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
fs = flood.modifiers.new("sub", "SUBSURF"); fs.subdivision_type = "SIMPLE"; fs.levels = fs.render_levels = 6
fd = flood.modifiers.new("d", "DISPLACE"); ftex = bpy.data.textures.new("ftex", "CLOUDS"); ftex.noise_scale = 3.0; fd.texture = ftex; fd.strength = 0.35
flood.data.materials.append(murk)
foam = P("foam", (0.8, 0.8, 0.76), 0.7)
edge = obox("edge", (0, 0, 0), (400, 2.5, 0.35), foam)
debris = []
for k in range(70):
    o = obox("debris", (0, 0, -50), (rnd.uniform(0.3, 2.5), rnd.uniform(0.2, 1.2), rnd.uniform(0.08, 0.3)), rnd.choice([M["wood"], M["wood"], walls[1], M["tile"]]))
    debris.append(dict(o=o, x=rnd.uniform(-60, 60), dy=rnd.uniform(-2, 40), ph=rnd.uniform(0, 6.3), rot=rnd.uniform(0, 6.3)))
# ---- 空（もやのかかった空）と太陽光
wd = bpy.data.worlds.new("sky"); sc.world = wd; wd.use_nodes = True; nt = wd.node_tree
sky = nt.nodes.new("ShaderNodeTexSky"); sky.sky_type = "MULTIPLE_SCATTERING"
try:
    sky.sun_elevation = math.radians(28); sky.sun_rotation = math.radians(200); sky.air_density = 2.5; sky.aerosol_density = 6.0
except Exception: pass
nt.links.new(sky.outputs["Color"], nt.nodes["Background"].inputs["Color"]); nt.nodes["Background"].inputs["Strength"].default_value = 0.35
sun = bpy.data.lights.new("sun", "SUN"); sun.energy = 2.6; sun.angle = math.radians(6); sun.color = (1.0, 0.93, 0.85)
so = bpy.data.objects.new("sun", sun); bpy.context.collection.objects.link(so); so.rotation_euler = (math.radians(55), 0, math.radians(200))
# 叫ぶ人（遠目。トゥーンの色を物理ベースに置きかえる）
yo, ytex = T.boy("stranger", (5, 20.4, 1.2), rot=170)
for o in [yo] + list(yo.children_recursive):
    if o.type != "MESH": continue
    for i, m in enumerate(o.data.materials):
        if m and m.node_tree and any(n.type == "VALTORGB" for n in m.node_tree.nodes) and "face" not in m.name:
            c = [n for n in m.node_tree.nodes if n.type == "VALTORGB"][0].color_ramp.elements[1].color
            o.data.materials[i] = W.mat(m.name + "_pbr", (c[0] ** 0.4545, c[1] ** 0.4545, c[2] ** 0.4545), 0.7)
cam = W.camera((0, 0, 1.6), (0, 10, 1.5), lens=18, fstop=8.0)
skin = P("me_skin", (0.8, 0.6, 0.5), 0.5); skin.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.15
sleeve = P("me_sleeve", (0.12, 0.17, 0.26), 0.85, noise=(40.0, 0.15))
def piece(name, r, m):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=1.0); o = bpy.context.object; o.name = name
    o.data.materials.append(m); bpy.ops.object.shade_smooth(); o.parent = cam; return o
def ball(name, r, m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=r); o = bpy.context.object; o.name = name
    o.scale = (0.85, 1.3, 0.8); o.data.materials.append(m); bpy.ops.object.shade_smooth(); o.parent = cam; return o
ARMS = {s: dict(up=piece("upper" + s, 0.05, sleeve), lo=piece("lower" + s, 0.045, sleeve), hd=ball("hand" + s, 0.04, skin)) for s in "LR"}
def between(o, p0, p1):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    o.location = (p0 + p1) / 2; o.scale = (1, 1, max(d.length, 1e-3)); o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
def set_arm(s, sh, el, hn):
    a = ARMS[s]; hn = Vector(hn); el = Vector(el)
    between(a["up"], sh, el); between(a["lo"], el, el + (hn - el) * 0.88)
    a["hd"].location = hn; a["hd"].rotation_euler = (hn - el).to_track_quat("Y", "Z").to_euler()
# スマホ
phm = P("phone", (0.02, 0.02, 0.025), 0.3, spec=0.8); ph = obox("phone", (0, 0, 0), (0.075, 0.012, 0.15), phm, bevel=0.006); ph.parent = cam
scrm = W.mat("phscr", (0.2, 0.3, 0.4), 0.2, emit=(0.5, 0.62, 0.75), estr=1.5)
phs = obox("phscr", (0, -0.007, 0), (0.066, 0.002, 0.135), scrm); phs.parent = ph
recm = W.mat("rec", (1, 0.1, 0.1), 0.5, emit=(1, 0.1, 0.1), estr=6.0)
rec = obox("rec", (-0.022, -0.009, 0.055), (0.012, 0.002, 0.012), recm); rec.parent = ph

def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def lerpv(a, b, k): return Vector(a).lerp(Vector(b), k)
def path(t, pts):
    """[(時刻, (x,y,z))…] を時間で補間"""
    if t <= pts[0][0]: return Vector(pts[0][1])
    for (ta, a), (tb, b) in zip(pts, pts[1:]):
        if t <= tb: return lerpv(a, b, ease((t - ta) / (tb - ta)))
    return Vector(pts[-1][1])

QUAKE0, QUAKE1 = T0(1), T0(2) - 0.2
W1_0, W1_1, W1_2 = T0(6), 38.0, 45.0        # 1回目の波：水平線に出る→浜→町の奥
W2_0, W2_2 = T0(11), 56.0                  # 2回目（もっと大きい）
def wave_state(t):
    if t < W1_0: return 400.0, 0.0, -0.2
    if t < W2_0:
        if t < W1_1: y = 260 - (260 - 26) * ease((t - W1_0) / (W1_1 - W1_0)) ** 0.8; h = 9.0
        else: y = 26 - 54 * ease((t - W1_1) / (W1_2 - W1_1)); h = 7.0
        flood = 0.0 if y > 22 else 4.2 * min(1, (22 - y) / 10)
        return y, h, flood
    k = ease((t - W2_0) / (W2_2 - W2_0)); y = 260 - (260 + 30) * k; h = 11.0
    return y, h, 4.2 + (1.6 if y < 22 else 0) * min(1, (22 - y) / 10)

def pane(t, side):
    A = side == "A"
    run = 0.0
    if A:
        pos = path(t, [(T0(2) + 0.3, (0, 0, 0)), (T0(5) - 0.3, (2.5, -29, 0)), (33.0, (2.5, -58, 14)), (63, (2.5, -60, 14))])
        run = 1.0 if T0(2) + 0.3 < t < 33.0 else 0.0
        look = pos + Vector((0, -10, 1.5)) if t < 33.6 else Vector((0, 14, -2))
        if T0(5) - 1.0 < t < T1(5): look = pos + Vector((-4, -8, 0.5))             # 渋滞の車を横目に
        if t >= T0(12) + 0.5: k = ease((t - T0(12) - 0.5) / 3.0); pos = pos.lerp(Vector((2.5, -62, 40)), k); look = Vector((0, 0, 0)).lerp(Vector((0, 10, 0)), k)
    else:
        pos = path(t, [(T0(3), (0, 0, 0)), (T1(4), (1.5, 24.5, 0)), (36.3, (1.5, 24.5, 0)), (39.0, (8.0, 16.6, 0)), (39.8, (15.0, 15.5, 0)), (41.0, (15.0, 13.0, 9.0)), (T1(9), (15.0, 9.5, 15)), (63, (15.0, 9.5, 15))])
        run = 1.0 if 36.3 < t < T1(9) else (0.35 if T0(3) < t < T1(4) else 0.0)
        look = pos + Vector((0, 10, 1.4))
        if T0(7) - 0.3 <= t < T1(7): look = Vector((5, 20.4, 2.8))                     # 叫ぶ人の方を見る
        if T1(7) <= t < 36.3: look = Vector((0, 120, 6))                                # 振り返ると、波
        if 36.3 <= t < 39.8: look = pos + Vector((4, -6, 1.2))
        if 39.8 <= t < T1(9): look = pos + Vector((2, 6, 0.8))                         # 階段を上りながら海側を見る
        if t >= T1(9): look = Vector((0, 4, 0.0))                                        # 屋上から水につかった町を見下ろす
        if t >= T0(12) + 0.5: k = ease((t - T0(12) - 0.5) / 3.0); pos = pos.lerp(Vector((10, -8, 40)), k); look = look.lerp(Vector((0, 10, 0)), k)
    z = (hill_z(pos.y) if pos.z < 14.5 and A else pos.z) if A else pos.z
    eye = Vector((pos.x, pos.y, (z if A else pos.z) + 1.6))
    ph_ = t * 2.6 * math.pi
    if run > 0: eye += Vector((0.03 * math.sin(ph_ * 0.5), 0, 0.05 * run * abs(math.sin(ph_))))
    if QUAKE0 <= t < QUAKE1:
        a = 0.06 * math.sin(math.pi * (t - QUAKE0) / (QUAKE1 - QUAKE0))
        eye += Vector((a * math.sin(t * 41), a * math.sin(t * 37), a * 0.5 * math.sin(t * 53)))
    return eye, look, run, (not A) and T0(3) <= t < 36.3

def place(t, side):
    eye, look, run, phone = pane(t, side)
    cam.location = eye; W.aim(cam, look)
    y, h, fl = wave_state(t)
    wave.location = (0, y, -0.3); wave.scale = (1, max(0.4, h / 9.0), max(h, 0.1) + 0.3)
    if y > 300: wave.location = (0, 2000, 0)
    flood.location = (0, y + 200, fl - 0.05); flood.hide_render = fl <= 0.01
    edge.location = (0, y - 0.8, fl + 0.05); edge.hide_render = fl <= 0.01
    oc.time = t * 0.8; wtex.noise_basis = "BLENDER_ORIGINAL"; dsp.mid_level = 0.5 + 0.05 * math.sin(t)
    for dbr in debris:
        dbr["o"].hide_render = fl <= 0.01
        dbr["o"].location = (dbr["x"], y + 3 + dbr["dy"] + 0.4 * math.sin(t * 0.7 + dbr["ph"]), fl + 0.06)
        dbr["o"].rotation_euler = (0.1 * math.sin(t + dbr["ph"]), 0.1 * math.cos(t * 1.3 + dbr["ph"]), dbr["rot"] + 0.2 * t)
    for o in [yo] + list(yo.children_recursive): o.hide_render = not (side == "B" and T0(6) < t < 40)
    T.set_expr(ytex, "yota", "talk" if (T0(7) <= t < T1(7) and int(t * 8) % 3 != 2) else "shockc")
    ph.hide_render = not phone
    for c in ph.children: c.hide_render = not phone
    ph.location = (0.07, -0.12, -0.42); ph.rotation_euler = (math.radians(-80), 0, 0)
    sw = math.sin(t * 2.6 * math.pi) * run
    for s, sx in (("L", -1), ("R", 1)):
        hn = Vector((0.15 * sx, -0.34 + 0.1 * sw * sx, -0.45))
        if s == "R" and phone: hn = Vector((0.08, -0.2, -0.42))
        set_arm(s, Vector((0.22 * sx, -0.55, 0.05)), Vector((0.24 * sx, -0.46, -0.26)), hn)


frames = TEST or range(START, STOP)
t0 = time.time()
for f in frames:
    p = os.path.join(OUT, "done_%04d.txt" % (f + 1))
    if os.path.exists(p) and not TEST: continue
    t = f / FPS
    for side in "AB":
        place(t, side)
        hp = os.path.join(OUT, "%s_%04d.png" % (side, f + 1)); tmp = hp[:-4] + "_tmp.png"
        sc.render.filepath = tmp; bpy.ops.render.render(write_still=True); os.replace(tmp, hp)
    open(p, "w").write("ok")
    print("frame %s t=%.2f %.1fs" % (p, t, time.time() - t0), flush=True); t0 = time.time()
