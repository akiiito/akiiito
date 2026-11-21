"""
create_toki2.py ― 「その罪、時効にさせない」第2話『マッチ工場の罰金』（夜のマッチ工場 → 時が止まる → 成敗アクション → 金貨の雨 → 夜明け）
  python create_toki1.py [--samples 18] [--res 0.75] [--start 0] [--end 840] [--test 0,140,...]
  実話（1888年ロンドン・マッチ工場の少女たち）をもとにしたフィクション。会社名・人物は架空。
"""
import os, sys, math, json, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
import s2_world as W, s3_toon as T, s7_world as S7, blk_hair as H
from toki2_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "18")); FPS = 24; N = int(END * FPS)
RS = float(arg("--res", "0.75"))
START = int(arg("--start", "0")); STOP = int(arg("--end", str(N)))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_TOKI2" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
LINES = json.load(open(os.path.join(HERE, "toki2_lines.json"), encoding="utf-8"))
TT = os.path.join(HERE, "toki_tex")

sc = W.reset(SAMPLES, res=(int(1080 * RS), int(1920 * RS)))
sc.cycles.max_bounces = 5; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 2; sc.cycles.transparent_max_bounces = 8
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = float(arg("--thr", "0.04"))
try: sc.cycles.denoising_prefilter = "ACCURATE"; sc.cycles.denoising_quality = "HIGH"
except Exception: pass
sc.render.use_persistent_data = True
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = arg("--look", "AgX - Punchy")
sc.view_settings.exposure = float(arg("--exp", "0.0"))

def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def win(t, a, b, fi=0.3, fo=0.3): return ease((t - a) / fi) * (1 - ease((t - b) / fo))

# 霧（パート4の共通ノードをそのまま使う）
_src4 = open(os.path.join(HERE, "create_block4.py"), encoding="utf-8").read()
_i = _src4.index("# ---------------------------------------------------------------- 霧"); _j = _src4.index("# ---------------------------------------------------------------- ドット絵の質感", _i)
exec(_src4[_i:_j])

def pix(name, png, rough=0.8, tint=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(os.path.join(S7.TEX, png + ".png")); tx.interpolation = "Closest"
    src = tx.outputs["Color"]
    if tint:
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1.0
        nt.links.new(src, mx.inputs["A"]); mx.inputs["B"].default_value = (*tint, 1); src = mx.outputs["Result"]
    nt.links.new(src, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough; b.inputs["Specular IOR Level"].default_value = 0.3
    bw = nt.nodes.new("ShaderNodeRGBToBW"); bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.5; bump.inputs["Distance"].default_value = 0.02
    nt.links.new(tx.outputs["Color"], bw.inputs[0]); nt.links.new(bw.outputs[0], bump.inputs["Height"]); nt.links.new(bump.outputs[0], b.inputs["Normal"])
    return fogify(m)
def P(name, col, rough=0.6, metal=0.0, emit=None, estr=0.0, sss=0.0):
    m = W.mat(name, col, rough, metal=metal, emit=emit, estr=estr, sss=sss); return fogify(m)
def E(name, col, s): return fogify(S7.emis(name, col, s))
def boxes(name, items, m):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    for c, s in items:
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r["verts"]: v.co = Vector((v.co.x * s[0], v.co.y * s[1], v.co.z * s[2])) + Vector(c)
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); me.materials.append(m); return o
def cyl(name, loc, r, depth, m, rot=(0, 0, 0), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    return o
def imgmat(name, path, rough=0.7, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(path)
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = rough
    nt.links.new(tx.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = emit
    return m
def card(name, path, w, h, rough=0.7):
    bpy.ops.mesh.primitive_plane_add(size=1.0); o = bpy.context.object; o.name = name
    o.scale = (w, h, 1); bpy.ops.object.transform_apply(scale=True)
    m = imgmat(name + "_m", path, rough); o.data.materials.append(m)
    so = o.modifiers.new("s", "SOLIDIFY"); so.thickness = 0.002
    return o, m

# ---------------------------------------------------------------- 部屋（ブロックの床・石の壁・窓・天井）
MAT = [pix("p_planks", "planks", 0.75, (0.75, 0.62, 0.5)), pix("p_stone", "stone", 0.85, (0.62, 0.62, 0.68)),
       pix("p_dark", "planks", 0.8, (0.32, 0.26, 0.22)), pix("p_log", "log_side", 0.8, (0.7, 0.6, 0.5))]
KINDS = {"floor": (0, 0, 0), "wall": (1, 1, 1), "ceil": (2, 2, 2), "post": (3, 3, 3)}
X0, X1, Y0, Y1, ZH = -6, 6, -3, 7, 4
WIN_X = (-4, -1, 2)                                                       # 奥の壁の窓（x, x+1 の2マス幅、z=1..2）
DOOR = (-6, 1)                                                            # 左の壁の扉（y=1..2, z=0..1）
cells = {}
for x in range(X0, X1):
    for y in range(Y0, Y1):
        cells[(x, y, -1)] = "floor"; cells[(x, y, ZH)] = "ceil"
for z in range(0, ZH):
    for x in range(X0 - 1, X1 + 1):
        if not (z in (1, 2) and any(wx <= x <= wx + 1 for wx in WIN_X)): cells[(x, Y1, z)] = "wall"
    for y in range(Y0, Y1):
        if not (z in (0, 1) and DOOR[1] <= y <= DOOR[1] + 1): cells[(X0 - 1, y, z)] = "wall"
        if not (0 <= y <= 2 and 0 <= z <= 2): cells[(X1, y, z)] = "wall"
for x in (-5, 0, 5):
    for z in range(0, ZH): cells[(x, Y1 - 1, z)] = "post"
room = S7.voxel_mesh("room", cells, MAT, KINDS)
# 窓の外（夜は月の青 → 夜明けの金）
win_m = bpy.data.materials.new("winsky"); win_m.use_nodes = True; _wn = win_m.node_tree.nodes; _wn.clear()
_wo = _wn.new("ShaderNodeOutputMaterial"); WIN_E = _wn.new("ShaderNodeEmission"); win_m.node_tree.links.new(WIN_E.outputs[0], _wo.inputs[0])
sky = boxes("sky", [((0, Y1 + 3, 2), (30, 0.1, 10))], win_m); sky.visible_shadow = False
for wx in WIN_X:                                                          # 窓枠と格子
    boxes("wframe", [((wx + 1.0, Y1 + 0.5, 1.0), (2.0, 0.12, 0.08)), ((wx + 1.0, Y1 + 0.5, 3.0), (2.0, 0.12, 0.08)),
                     ((wx + 1.0, Y1 + 0.5, 2.0), (2.0, 0.08, 0.05)), ((wx + 1.0, Y1 + 0.5, 2.0), (0.05, 0.08, 2.0))], P("frame", (0.12, 0.09, 0.07), 0.6))
# 月光／朝日（窓から差しこむ平行光）
sun = bpy.data.lights.new("winlight", "SUN"); sun.angle = math.radians(2.0)
suno = bpy.data.objects.new("winlight", sun); bpy.context.collection.objects.link(suno)
suno.rotation_euler = (-Vector((0.25, -1.0, -0.55)).normalized()).to_track_quat("-Z", "Y").to_euler()
# 扉（記者がなだれこむ光）
door_m = P("door", (0.25, 0.17, 0.11), 0.7)
door = boxes("door", [((0.05, 1.0, 1.0), (0.1, 2.0, 2.0))], door_m); door.location = (X0, DOOR[1], 0)
hall, hallo = None, None
hall = bpy.data.lights.new("hall", "AREA"); hall.size = 2.0; hall.color = (1.0, 0.92, 0.8)
hallo = bpy.data.objects.new("hall", hall); bpy.context.collection.objects.link(hallo); hallo.location = (X0 - 1.5, DOOR[1] + 1.0, 1.0)
hallo.rotation_euler = (Vector((1, 0, 0))).to_track_quat("-Z", "Y").to_euler()


# 右の壁の穴になるブロック（金の一撃で外へ吹き飛ぶ）
HOLE = []
for y in range(0, 3):
    for z in range(0, 3):
        o = boxes("holeblk", [((0, 0, 0), (1.0, 1.0, 1.0))], MAT[1]); o.location = (X1 + 0.5, y + 0.5, z + 0.5)
        HOLE.append(dict(o=o, p0=Vector(o.location)))
# 外（夜の路地：地面・遠くの建物・空）
OUTX = X1 + 1
boxes("street", [((OUTX + 10, 1.5, -0.5), (20, 24, 1.0))], pix("p_street", "stone", 0.9, (0.45, 0.45, 0.5)))
rb = random.Random(12)
for k in range(9):
    h = rb.uniform(4, 9); w = rb.uniform(2.5, 4)
    boxes("bld", [((OUTX + 13 + rb.uniform(-1, 4), -9 + k * 2.8, h / 2), (w, 2.4, h))], pix("p_bld", "stone", 0.9, (0.3, 0.28, 0.3)))
sky2 = boxes("sky2", [((OUTX + 22, 1.5, 6), (0.1, 60, 20))], win_m); sky2.visible_shadow = False
moon = bpy.data.lights.new("streetl", "POINT"); moon.color = (1.0, 0.75, 0.45); moon.shadow_soft_size = 0.3; moon.energy = 0.0
moono = bpy.data.objects.new("streetl", moon); bpy.context.collection.objects.link(moono); moono.location = (OUTX + 4.5, 0.0, 2.6)

# ---------------------------------------------------------------- 作業台・マッチ箱・黄リンの鍋
BY = 3.0
bench_m = pix("p_bench", "planks", 0.6, (0.62, 0.45, 0.32))
boxes("bench", [((0, BY, 0.86), (7.0, 0.9, 0.08))] + [((x, BY + dy, 0.41), (0.1, 0.1, 0.82)) for x in (-3.4, -1.1, 1.1, 3.4) for dy in (-0.38, 0.38)], bench_m)
red_m = P("boxred", (0.6, 0.08, 0.06), 0.6); yel_m = P("boxyel", (0.8, 0.62, 0.2), 0.6); stick_m = P("stick", (0.85, 0.72, 0.5), 0.7); tipm = P("tipred", (0.5, 0.05, 0.04), 0.5)
rnd = random.Random(5)
items = []
for gx in (-2.3, 0.0, 2.3):
    for i in range(7):
        x = gx - 0.75 + i * 0.2 + rnd.uniform(-0.03, 0.03); y = BY - 0.22 + rnd.uniform(-0.05, 0.08)
        if abs(x) < 0.25 and gx == 0.0: continue
        items.append(((x, y, 0.92 + 0.0), (0.1, 0.055, 0.028)))
        if rnd.random() < 0.5: items.append(((x, y, 0.95), (0.1, 0.055, 0.028)))
boxes("mboxes", items, red_m)
boxes("mboxes2", [((gx + 0.6, BY + 0.2, 0.92), (0.24, 0.16, 0.05)) for gx in (-2.3, 0.0, 2.3)], yel_m)
sticks = []
for gx in (-2.3, 0.0, 2.3):
    for k in range(30):
        sticks.append(((gx + 0.35 + rnd.uniform(-0.05, 0.05), BY + 0.25 + rnd.uniform(-0.04, 0.04), 0.91 + rnd.uniform(0, 0.03)), (0.006, 0.09, 0.006)))
boxes("sticks", sticks, stick_m)
PHOS = E("phos", (0.85, 0.95, 0.35), 3.0); PHOS_K = [n for n in PHOS.node_tree.nodes if n.type == "EMISSION"][0].inputs["Strength"]
pot_m = P("pot", (0.25, 0.25, 0.27), 0.4, metal=0.7)
FUMES = []
fume_m = bpy.data.materials.new("fume"); fume_m.use_nodes = True; _fn = fume_m.node_tree.nodes; _fl = fume_m.node_tree.links.new; _fn.clear()
_fo = _fn.new("ShaderNodeOutputMaterial"); _fe = _fn.new("ShaderNodeEmission"); _ft = _fn.new("ShaderNodeBsdfTransparent"); _fx = _fn.new("ShaderNodeMixShader")
_fe.inputs["Color"].default_value = (0.8, 0.95, 0.4, 1); _fe.inputs["Strength"].default_value = 1.2; _fx.inputs[0].default_value = 0.12
_fl(_ft.outputs[0], _fx.inputs[1]); _fl(_fe.outputs[0], _fx.inputs[2]); _fl(_fx.outputs[0], _fo.inputs["Surface"])
for gx in (-2.3, 0.0, 2.3):
    cyl("pot", (gx - 0.95, BY + 0.15, 1.0), 0.13, 0.22, pot_m); cyl("potphos", (gx - 0.95, BY + 0.15, 1.105), 0.115, 0.006, PHOS)
    for k in range(5):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=16, ring_count=8); o = bpy.context.object; o.data.materials.append(fume_m)
        o.visible_shadow = False; FUMES.append(dict(o=o, base=Vector((gx - 0.95, BY + 0.15, 1.12)), ph=rnd.uniform(0, 1), sp=rnd.uniform(0.25, 0.4)))
# 罰金表（奥の壁）
fines, _ = card("fines", os.path.join(TT, "fines.png"), 0.8, 1.1, 0.8); fines.location = (1.6, Y1 - 0.03, 2.1); fines.rotation_euler = (math.radians(90), 0, math.pi)
# 蹴られるマッチ箱
kbox = boxes("kbox", [((0, 0, 0), (0.1, 0.055, 0.028))], red_m); KB0 = Vector((0.3, BY - 0.25, 0.92))
KST = []
for k in range(14):
    o = boxes("kst", [((0, 0, 0), (0.006, 0.09, 0.006))], stick_m)
    KST.append(dict(o=o, v=Vector((rnd.uniform(-1.2, 1.2), rnd.uniform(-1.6, -0.4), rnd.uniform(0.8, 2.2))), w=Vector((rnd.uniform(-9, 9), rnd.uniform(-9, 9), rnd.uniform(-9, 9)))))
# 天井のランプ
lampm = P("lampshade", (0.1, 0.12, 0.1), 0.4, metal=0.6); bulb_m = E("bulb", (1.0, 0.72, 0.4), 18.0)
LAMPS = []
for lx in (-2.3, 0.0, 2.3):
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.26, radius2=0.06, depth=0.2, location=(lx, BY, 2.35)); s_ = bpy.context.object; s_.data.materials.append(lampm)
    bpy.ops.object.modifier_add(type="SOLIDIFY"); s_.modifiers[-1].thickness = 0.01
    cyl("cord", (lx, BY, 3.2), 0.008, 1.6, lampm)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(lx, BY, 2.27)); bpy.context.object.data.materials.append(bulb_m)
    l = bpy.data.lights.new("lamp", "SPOT"); l.spot_size = math.radians(110); l.spot_blend = 0.6; l.shadow_soft_size = 0.06; l.color = (1.0, 0.72, 0.42)
    lo = bpy.data.objects.new("lamp", l); bpy.context.collection.objects.link(lo); lo.location = (lx, BY, 2.24); LAMPS.append(l)
BULB_K = [n for n in bulb_m.node_tree.nodes if n.type == "EMISSION"][0].inputs["Strength"]
# 金貨
coin_img = os.path.join(TT, "coin.png")
COINS = []; coin_m = imgmat("coin_m", coin_img, 0.25); _cb = coin_m.node_tree.nodes["Principled BSDF"]; _cb.inputs["Metallic"].default_value = 1.0
_cb.inputs["Emission Strength"].default_value = 0.6
rc = random.Random(31)
for k in range(260):
    o = cyl("coin", (0, 0, 0), 0.055, 0.007, coin_m, verts=20); o.visible_shadow = False
    x = rc.uniform(-3.2, 3.2) if k % 3 == 0 else rc.uniform(-0.9, 0.9); y = rc.uniform(BY - 0.9, BY + 0.9); land = 0.905 if abs(y - BY) < 0.44 and abs(x) < 3.5 else 0.005
    COINS.append(dict(o=o, x=x, y=y, z0=rc.uniform(3.4, 4.6), land=land, dl=rc.uniform(0, 2.4), w=Vector((rc.uniform(-12, 12), rc.uniform(-12, 12), rc.uniform(-3, 3)))))

# ---------------------------------------------------------------- 人物
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
            nm = W.mat(m.name + "_pbr", lin, 0.5 if sk else (0.36 if hr else 0.78), sss=0.25 if sk else 0.0)
            b = nm.node_tree.nodes["Principled BSDF"]
            if hr: b.inputs["Coat Weight"].default_value = 0.25; b.inputs["Sheen Weight"].default_value = 0.4
            if key in ("blazer", "skirt", "pants"): b.inputs["Sheen Weight"].default_value = 0.6
            o.data.materials[i] = fogify(nm)
def face_to(o, p, tgt):
    o.location = p; d = Vector((tgt[0] - p[0], tgt[1] - p[1], 0)).normalized()
    o.rotation_euler = (0, 0, math.atan2(-d.x, d.y))
def fwd(o):
    a = o.rotation_euler.z; return Vector((-math.sin(a), math.cos(a), 0.0))
def side(o): f = fwd(o); return Vector((f.y, -f.x, 0.0))
def hairmat(root, nm): return [m for o in root.children if o.name.startswith(nm + "_hair") for m in o.data.materials][0]
WORK = {"blazer": (0.36, 0.33, 0.3), "skirt": (0.3, 0.26, 0.24), "shirt": (0.8, 0.76, 0.68), "ribbon": (0.45, 0.32, 0.26), "sock": (0.22, 0.18, 0.16)}
SAE_P = Vector((0.0, BY + 0.62, 0.0))
sae, stex = T.girl("sae", tuple(SAE_P), hair=(0.36, 0.16, 0.1), face="sae", ponytail=True, arm_pose="chin")
face_to(sae, SAE_P, (0.0, -1.0)); pbr(sae, WORK); H.upgrade(sae, "sae", hairmat(sae, "sae"))
others = []
for k, (x, hc, pose) in enumerate(((-2.3, (0.12, 0.09, 0.08), "down"), (2.3, (0.5, 0.36, 0.2), "chin"))):
    g, gt = T.girl("w%d" % k, (x, BY + 0.62, 0), hair=hc, face="sae", ponytail=k == 0, arm_pose=pose)
    face_to(g, (x, BY + 0.62, 0), (x * 0.6, -1.0)); pbr(g, WORK); H.upgrade(g, "w%d" % k, hairmat(g, "w%d" % k), seed=7 + k)
    others.append((g, gt))
# 工場主（シルクハット・太鼓腹・ステッキ）
OWN_P = Vector((3.4, 1.4, 0.0))
owner, otex = T.boy("owner", tuple(OWN_P), hair=(0.08, 0.07, 0.07), face="owner",
                    arms={"L": ((0.24, 0.06, 1.12), (0.16, 0.2, 1.0)), "R": ((-0.24, 0.06, 1.12), (-0.26, 0.16, 0.92))})
pbr(owner, {"blazer": (0.16, 0.2, 0.14), "pants": (0.1, 0.1, 0.1), "shirt": (0.9, 0.86, 0.76)})
blk = P("hat", (0.03, 0.03, 0.03), 0.35)
for nm_, loc, r, d in (("hat", (0, 0, 1.8), 0.085, 0.2), ("brim", (0, 0, 1.705), 0.15, 0.015)):
    cyl("owner_" + nm_, loc, r, d, blk, verts=32).parent = owner
belly = bpy.ops.mesh.primitive_uv_sphere_add(radius=0.19, location=(0, 0.06, 1.08)); bo = bpy.context.object; bo.name = "owner_belly"
bo.data.materials.append(P("vest", (0.32, 0.12, 0.08), 0.6)); bo.parent = owner; bo.scale = (1.0, 0.9, 1.1)
for p_ in bo.data.polygons: p_.use_smooth = True
musm = P("mustache", (0.06, 0.05, 0.05), 0.7)
for sx in (-1, 1):
    o = boxes("mus", [((sx * 0.035, 0, 0), (0.065, 0.018, 0.018))], musm); o.parent = owner; o.location = (0, 0.145, 1.535); o.rotation_euler.y = sx * 0.3
cane = cyl("owner_cane", (-0.27, 0.16, 0.48), 0.012, 0.92, blk); cane.parent = owner
cyl("owner_knob", (-0.27, 0.16, 0.95), 0.025, 0.04, P("brass", (0.75, 0.55, 0.25), 0.3, metal=1.0)).parent = owner
OWN_ALL = [owner] + list(owner.children_recursive)
# トキモリ（3つの姿：懐中時計／右ストレート／アッパー）
coat_m = P("coat", (0.03, 0.03, 0.035), 0.55); gold = P("gold", (1.0, 0.72, 0.3), 0.22, metal=1.0)
wface_m = E("wface", (1.0, 0.8, 0.4), 4.0); WF_K = [n for n in wface_m.node_tree.nodes if n.type == "EMISSION"][0].inputs["Strength"]
fist_m = E("fist", (1.0, 0.7, 0.3), 0.0); FIST_K = [n for n in fist_m.node_tree.nodes if n.type == "EMISSION"][0].inputs["Strength"]
TOKI_P = Vector((-0.9, 1.3, 0.0))
TCOL = {"blazer": (0.04, 0.04, 0.05), "skirt": (0.05, 0.05, 0.06), "shirt": (0.92, 0.9, 0.86), "ribbon": (0.85, 0.62, 0.2), "sock": (0.04, 0.04, 0.05), "shoe": (0.05, 0.04, 0.04)}
POSES = {"idle": {"L": ((0.2, 0.02, 1.0), (0.21, 0.06, 0.8)), "R": ((-0.2, 0.14, 1.1), (-0.1, 0.34, 1.22))},
         "punch": {"L": ((0.2, -0.06, 1.12), (0.12, 0.1, 1.2)), "R": ((-0.16, 0.28, 1.3), (-0.08, 0.54, 1.32))},
         "upper": {"L": ((0.2, -0.04, 1.05), (0.12, 0.12, 1.15)), "R": ((-0.2, 0.14, 1.52), (-0.12, 0.22, 1.86))}}
TM = {}
for k, arms in POSES.items():
    nm = "toki" if k == "idle" else "toki" + k
    r_, tx_ = T.girl(nm, tuple(TOKI_P), hair=(0.86, 0.86, 0.92), face="toki", ponytail=False, arms=arms)
    pbr(r_, TCOL); H.upgrade(r_, nm, hairmat(r_, nm), seed=11)
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.34, radius2=0.19, depth=0.78); c_ = bpy.context.object; c_.name = nm + "_coat"
    c_.data.materials.append(coat_m); c_.parent = r_; c_.location = (0, -0.01, 0.66)
    for p_ in c_.data.polygons: p_.use_smooth = True
    bpy.ops.object.modifier_add(type="SOLIDIFY"); c_.modifiers[-1].thickness = 0.012
    tr_ = cyl(nm + "_trim", (0, 0, 0), 0.343, 0.025, gold, verts=48); tr_.parent = r_; tr_.location = (0, -0.01, 0.28)
    hand = Vector(arms["R"][1])
    if k == "idle":
        w_ = cyl(nm + "_watch", (0, 0, 0), 0.05, 0.016, gold, rot=(math.pi / 2, 0, 0), verts=48); w_.parent = r_; w_.location = hand + Vector((0, 0.05, 0.04))
        f_ = cyl(nm + "_wface", (0, 0, 0), 0.042, 0.018, wface_m, rot=(math.pi / 2, 0, 0), verts=48); f_.parent = r_; f_.location = hand + Vector((0, 0.052, 0.04))
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07); g_ = bpy.context.object; g_.name = nm + "_aura"; g_.data.materials.append(fist_m)
        g_.parent = r_; g_.location = hand; g_.visible_shadow = False
    TM[k] = (r_, tx_, [r_] + list(r_.children_recursive))
wl = bpy.data.lights.new("watchl", "POINT"); wl.color = (1.0, 0.75, 0.35); wl.shadow_soft_size = 0.05
wlo = bpy.data.objects.new("watchl", wl); bpy.context.collection.objects.link(wlo)

# ---------------------------------------------------------------- 時が止まる金の殻・ほこり・がれき
shell_m = bpy.data.materials.new("shell"); shell_m.use_nodes = True; _sn = shell_m.node_tree.nodes; _sl = shell_m.node_tree.links.new; _sn.clear()
_so = _sn.new("ShaderNodeOutputMaterial"); _se = _sn.new("ShaderNodeEmission"); _st = _sn.new("ShaderNodeBsdfTransparent"); _sx = _sn.new("ShaderNodeMixShader")
_lw = _sn.new("ShaderNodeLayerWeight"); _lw.inputs["Blend"].default_value = 0.05
_sp = _sn.new("ShaderNodeMath"); _sp.operation = "MULTIPLY"; _sl(_lw.outputs["Facing"], _sp.inputs[0]); SHELL_K = _sp.inputs[1]; SHELL_K.default_value = 0.0
_se.inputs["Color"].default_value = (1.0, 0.7, 0.3, 1); _se.inputs["Strength"].default_value = 6.0
_sl(_sp.outputs[0], _sx.inputs[0]); _sl(_st.outputs[0], _sx.inputs[1]); _sl(_se.outputs[0], _sx.inputs[2]); _sl(_sx.outputs[0], _so.inputs["Surface"])
def make_shell(name):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0); o = bpy.context.object; o.name = name; o.data.materials.append(shell_m)
    for p_ in o.data.polygons: p_.use_smooth = True
    o.visible_shadow = False
    for a in ("visible_diffuse", "visible_glossy"): setattr(o, a, False)
    return o
shell = make_shell("shell")
hit_m = bpy.data.materials.new("hitring"); hit_m.use_nodes = True; _hn = hit_m.node_tree.nodes; _hl = hit_m.node_tree.links.new; _hn.clear()
_ho = _hn.new("ShaderNodeOutputMaterial"); _he = _hn.new("ShaderNodeEmission"); _ht = _hn.new("ShaderNodeBsdfTransparent"); _hx = _hn.new("ShaderNodeMixShader")
_hlw = _hn.new("ShaderNodeLayerWeight"); _hlw.inputs["Blend"].default_value = 0.08
_hp = _hn.new("ShaderNodeMath"); _hp.operation = "MULTIPLY"; _hl(_hlw.outputs["Facing"], _hp.inputs[0]); HIT_K = _hp.inputs[1]; HIT_K.default_value = 0.0
_he.inputs["Color"].default_value = (1.0, 0.85, 0.55, 1); _he.inputs["Strength"].default_value = 10.0
_hl(_hp.outputs[0], _hx.inputs[0]); _hl(_ht.outputs[0], _hx.inputs[1]); _hl(_he.outputs[0], _hx.inputs[2]); _hl(_hx.outputs[0], _ho.inputs["Surface"])
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.0); hitb = bpy.context.object; hitb.data.materials.append(hit_m); hitb.visible_shadow = False
for a in ("visible_diffuse", "visible_glossy"): setattr(hitb, a, False)
hitl = bpy.data.lights.new("hitl", "POINT"); hitl.color = (1.0, 0.82, 0.5); hitl.shadow_soft_size = 0.2
hitlo = bpy.data.objects.new("hitl", hitl); bpy.context.collection.objects.link(hitlo)
dust_m = E("dust", (1.0, 0.85, 0.65), 3.0); gdust_m = E("gdust", (1.0, 0.75, 0.35), 12.0)
DUST = []; rd = random.Random(8)
for k in range(220):
    p = Vector((rd.uniform(-4, 5.5), rd.uniform(-1.5, 6), rd.uniform(0.2, 2.6)))
    o = boxes("dust", [((0, 0, 0), (1, 1, 1))], dust_m); o.visible_shadow = False
    DUST.append(dict(o=o, p=p, s=rd.uniform(0.004, 0.01), ph=rd.uniform(0, 6.28), v=Vector((rd.uniform(-0.04, 0.04), rd.uniform(-0.03, 0.03), rd.uniform(-0.02, 0.03)))))
GD = []
for k in range(90):
    o = boxes("gd", [((0, 0, 0), (1, 1, 1))], gdust_m); o.visible_shadow = False
    GD.append(dict(o=o, a=rd.uniform(0, 6.28), r=rd.uniform(0.6, 1.8), z=rd.uniform(0.1, 1.9), s=rd.uniform(0.01, 0.022), dl=rd.uniform(0, 0.5)))
DEB = []                                                                 # がれき（天井／壁）
for k in range(34):
    o = boxes("deb", [((0, 0, 0), (1, 1, 1))], MAT[0] if k < 14 else MAT[1])
    DEB.append(dict(o=o, kind="ceil" if k < 14 else "wall", s=rd.uniform(0.06, 0.22), v=Vector((rd.uniform(-1, 1), rd.uniform(-1, 1), rd.uniform(-0.5, 1.5))),
                    w=Vector((rd.uniform(-8, 8), rd.uniform(-8, 8), rd.uniform(-8, 8))), off=Vector((rd.uniform(-0.6, 0.6), rd.uniform(-0.6, 0.6), rd.uniform(-0.2, 0.2)))))
for h in HOLE:
    h["v"] = Vector((rd.uniform(3.5, 7.0), rd.uniform(-1.5, 1.5), rd.uniform(0.5, 3.0))); h["w"] = Vector((rd.uniform(-5, 5), rd.uniform(-5, 5), rd.uniform(-5, 5)))

# ---------------------------------------------------------------- 補助光・カメラ
def alight(name, col, size, loc, look, e=0.0):
    l = bpy.data.lights.new(name, "AREA"); l.size = size; l.color = col; l.energy = e
    o = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return l, o
key, keyo = alight("key", (0.7, 0.75, 1.0), 1.0, (0, 0, 0), (0, 1, 0))
rim, rimo = alight("rim", (0.5, 0.7, 1.0), 1.2, (0, 0, 0), (0, 1, 0))
ownl, ownlo = alight("ownlight", (1.0, 0.6, 0.35), 0.5, (0, 0, 3), (0, 0, 0))
cam = W.camera((0, -1, 1.4), (0, 3, 1.2), lens=35, fstop=2.0)
cam.data.dof.aperture_blades = 7

# ---------------------------------------------------------------- 時間ごとの値
WALL_T = FINISH + 0.25; LAND_OUT = FINISH + 1.4; CEIL_T = UPPER + 0.4; FLOOR_T = FALL + 0.1
def stop_at(t): return 1.0 if STOPT <= t < RESUME else 0.0
def dawn_at(t): return ease((t - DAWN + 0.6) / 2.2)
DIR = Vector((1.0, 0.0, 0.0))
def owner_state(t):
    """工場主の 位置・体の傾き(x)・回転(y)・向き先"""
    p = OWN_P.copy(); rx = 0.0; ry = 0.0; look = Vector((0.4, 3.4, 0)) if t < 14.0 else TOKI_P
    if t >= PUNCH1:                                                       # 腹に一撃：くの字
        k = ease((t - PUNCH1) / 0.12); p += DIR * 0.35 * ease((t - PUNCH1) / 0.3); rx = 0.5 * k * (1 - ease((t - UPPER) / 0.1))
    if t >= UPPER:                                                        # アッパー：天井まで
        u = (t - UPPER) / (CEIL_T - UPPER)
        if t < CEIL_T: p.z = 2.25 * (1 - (1 - u) ** 2); rx = -0.6 * u
        elif t < FLOOR_T: v = (t - CEIL_T) / (FLOOR_T - CEIL_T); p.z = 2.25 - 2.7 * v * v; rx = -0.6 - 0.4 * v
        else: p.z = -0.45; rx = -0.25 * (1 - ease((t - FLOOR_T) / 0.4))
        p += DIR * 0.25 * ease((t - UPPER) / 1.0)
    if t >= FLOOR_T:                                                      # しりもち → あとずさり → よろよろ立つ
        p.z = -0.45 * (1 - ease((t - 19.0) / 0.4)); p += DIR * 0.25 * ease((t - 18.0) / 1.2)
    if t >= FINISH:                                                       # 金の一撃：壁をぶち抜いて外へ
        x0 = p.x; u = (t - FINISH) / (LAND_OUT - FINISH)
        if t < LAND_OUT:
            p.x = x0 + (OUTX + 4.0 - x0) * (1 - (1 - u) ** 1.6); p.z = 0.9 * math.sin(math.pi * min(u, 1)) * (1 - u) + 0.25 * u; ry = 7.5 * u
            rx = -0.4
        else:
            p.x = OUTX + 4.0 + 0.4 * ease((t - LAND_OUT) / 0.4); p.z = 0.12; ry = 7.5 + (2 * math.pi - 7.5 % (2 * math.pi)) * ease((t - LAND_OUT) / 0.3); rx = -1.5
        look = p + DIR
    return p, rx, ry, look
def owner_head(t):
    p, rx, ry, look = owner_state(t)
    return p + Vector((0, 0, 1.57 * math.cos(rx))) if t < LAND_OUT else p + Vector((1.45, 0, 0.22))
TOKI_HIT = OWN_P - DIR * 0.62
MIDH = (TOKI_HIT + OWN_P) / 2 + DIR * 0.2
def toki_state(t):
    """(姿, 位置, 向き先)"""
    op = owner_state(t)[0]
    if t < DASH: return "idle", TOKI_P, OWN_P
    if t < PUNCH1: u = ease((t - DASH) / (PUNCH1 - DASH)); return "punch", TOKI_P.lerp(TOKI_HIT, u), OWN_P
    if t < UPPER - 0.18: return "punch", TOKI_HIT, OWN_P
    if t < FALL + 0.3: return "upper", TOKI_HIT + DIR * 0.3 * ease((t - UPPER + 0.18) / 0.2), OWN_P + DIR * 0.3
    if t < CHARGE: return "idle", TOKI_HIT + DIR * 0.3, op
    hit = owner_state(FINISH - 0.01)[0] - DIR * 0.62
    if t < FINISH + 0.6: return "punch", (TOKI_HIT + DIR * 0.3).lerp(hit, ease((t - CHARGE - 0.4) / 0.25)), hit + DIR
    return "idle", hit, hit + DIR
IMPACTS = [(PUNCH1, 1.0), (UPPER, 1.0), (CEIL_T, 0.7), (FLOOR_T, 0.6), (FINISH, 1.3), (WALL_T, 1.0)]
def impact_at(t):
    best = (0.0, None)
    for ti, s in IMPACTS:
        if ti <= t < ti + 0.5:
            v = s * math.exp(-(t - ti) / 0.12)
            if v > best[0]: best = (v, ti)
    return best
def impact_point(ti):
    if ti in (PUNCH1, FINISH): return owner_state(ti)[0] + Vector((0, 0, 1.1)) - DIR * 0.15
    if ti == UPPER: return owner_head(ti) - DIR * 0.1
    if ti == CEIL_T: return owner_state(ti)[0] + Vector((0, 0, 3.95))
    if ti == FLOOR_T: return owner_state(ti)[0] + Vector((0, 0, 0.1))
    return Vector((X1, owner_state(ti)[0].y, 1.0))
HH = lambda: SAE_P + Vector((0, 0, 1.4))

def shot(t):
    hf = SAE_P; tp = toki_state(t)[1]; th = lambda: tp + Vector((0, 0, 1.44)); oh = owner_head(t)
    mid = (tp + owner_state(t)[0]) / 2
    S = [
        (0.0, hf + Vector((0.14 - 0.03 * t / 3, -1.0 + 0.06 * t / 3, 1.42)), HH() + Vector((0, 0, -0.02)), 50, 1.8),
        (3.1, hf + Vector((0.6 + 0.03 * (t - 3), -0.8, 1.05)), oh + Vector((0, 0, -0.12)), 42, 2.4),
        (6.1, hf + Vector((0.06, -0.95 + 0.04 * (t - 6.1) / 3, 1.42)), HH() + Vector((0, 0, -0.02)), 52, 1.8),
        (9.0, owner.location + fwd(owner) * (0.95 - 0.02 * (t - 9)) + side(owner) * 0.2 + Vector((0, 0, 1.55)), oh, 46, 2.0),
        (10.7, Vector((0.9, -0.4, 1.5)), Vector((0.6, BY - 0.4, 0.9)), 30, 4.0),
        (STOPT, Vector((-0.4, -2.2 + 0.25 * (t - STOPT), 2.3)), Vector((0.8, 2.4, 1.0)), 18, 5.6),
        (12.5, TOKI_P + DIR * (1.15 - 0.05 * (t - 12.5)) + Vector((0, -0.55, 0.72)), th(), 30 + 8 * ease((t - 12.5) / 2.2), 2.2),
        (DASH, MIDH + Vector((0.0, -2.9, 1.2)), MIDH + Vector((0, 0, 1.05)), 24, 4.0),
        (UPPER - 0.15, owner_state(UPPER)[0] + Vector((-0.5, -2.7, 0.55)), owner_state(UPPER)[0] + Vector((0.1, 0, 1.95)), 19, 5.0),
        (FALL + 0.6, owner_state(t)[0] - DIR * 0.95 + Vector((0, -0.3, 0.85)), oh, 34, 2.4),
        (CHARGE, tp + Vector((0.75, -0.2, 1.45)), th() + Vector((0, 0, -0.04)), 44, 2.0),
        (FINISH, Vector((2.2, -2.4, 1.6)), owner_state(t)[0] + Vector((0, 0, 1.0)), 20, 5.6),
        (RESUME, hf + Vector((0.55, -1.7, 1.65)), hf + Vector((0, 0, 1.25)), 30, 3.2),
        (VERDICT, tp + DIR * 0.8 + Vector((0, -0.12, 1.45)), th() + Vector((0, 0, -0.03)), 50, 1.8),
        (STAMP, owner_state(t)[0] + Vector((1.5, -0.95, 1.6)), owner_state(t)[0] + Vector((1.5, 0, 0.14)), 32, 3.5),
        (DAWN, hf + Vector((0.12, -1.0, 1.43)), HH(), 50, 1.8),
        (FACT, Vector((0.2, -1.6 - 0.12 * (t - FACT), 1.7)), Vector((0.0, 3.2, 1.3)), 24, 4.0),
    ]
    i = max(j for j, s in enumerate(S) if s[0] <= t)
    st, pos, look, lens, fs = S[i]
    if i == 11:                                                           # 吹き飛ぶ工場主を追う（壁の外まで）
        u = ease((t - FINISH) / 1.4); pos = pos.lerp(Vector((4.6, 1.5, 1.3)), u); lens = 20 + 8 * u
    sh = 0.0; iv, ti = impact_at(t)
    if ti is not None: sh = 0.06 * iv
    if stop_at(t) == 0 or i in (7, 8, 9, 10, 11): pos = pos + Vector((0.004 * math.sin(t * 1.3), 0.003 * math.sin(t * 0.9), 0.004 * math.sin(t * 1.7)))
    pos = pos + Vector((sh * math.sin(t * 61), sh * math.sin(t * 47), sh * math.sin(t * 53)))
    if "--camover" in sys.argv:
        v = [float(x) for x in arg("--camover", "").split(",")]; pos = Vector(v[0:3]); look = Vector(v[3:6]); lens = v[6]
    return pos, look, lens, fs, i

def side_of(pos, look):
    d = (look - pos); return Vector((d.y, -d.x, 0)).normalized()
def talking(who, t): return any(l[0] <= t <= l[1] - 0.05 for l in LINES if l[5] == who)
def flap(t): return int(t * 12) % 3 != 2
def expr_sae(t):
    tk = talking("sae", t) and flap(t)
    if t < 6.1: e = "sadtalk" if tk else "sad"
    elif t < RESUME: e = "tearsadtalk" if tk else "tearsad"
    elif t < DAWN: e = "smiletalk" if tk else ("shockc" if t < RESUME + 0.4 else "smile")
    else: e = "tearsmiletalk" if tk else "tearsmile"
    if (t % 3.3) < 0.12 and not tk and e in ("sad", "smile") and not stop_at(t): e = "blink" if e == "smile" else "sadblink"
    return e
def expr_owner(t):
    tk = talking("owner", t) and flap(t)
    if t < 14.0: return "coldtalk" if tk else "cold"
    if t < PUNCH1: return "shockc"
    if t < CEIL_T + 0.1: return "hurt"
    if t < 18.0: return "dizzy"
    if t < FINISH: return "shock" if tk else "shockc"
    if t < LAND_OUT + 0.2: return "hurt"
    return "dizzy"
def expr_toki(t):
    tk = talking("toki", t) and flap(t)
    if DASH <= t < FINISH + 0.4: return "coldtalk" if int(t * 10) % 2 else "cold"
    e = "coldtalk" if tk else "cold"
    if STAMP + 0.4 < t: e = "base"
    if (t % 3.7) < 0.12 and not tk: e = "blink"
    return e

def place(t):
    st = stop_at(t); dn = dawn_at(t)
    tf = t if t < STOPT else (STOPT if t < RESUME else t - (RESUME - STOPT))
    night = 1.0 - dn
    sun.color = Vector((0.45, 0.6, 1.0)).lerp(Vector((1.0, 0.66, 0.38)), dn)[:]; sun.energy = 0.6 * night + 5.5 * dn
    WIN_E.inputs["Color"].default_value = (*Vector((0.05, 0.08, 0.2)).lerp(Vector((1.0, 0.62, 0.32)), dn), 1); WIN_E.inputs["Strength"].default_value = 1.0 + 5.0 * dn
    for l in LAMPS: l.energy = (55.0 + 4.0 * math.sin(tf * 7.0)) * (1 - 0.6 * dn)
    BULB_K.default_value = 18.0 * (1 - 0.6 * dn); PHOS_K.default_value = 3.0 * (1 - 0.6 * dn)
    moon.energy = 140.0 * (t > WALL_T) * (1 - 0.5 * dn)
    FOG.nodes["fogcol"].inputs["Color"].default_value = (*Vector((0.025, 0.03, 0.04)).lerp(Vector((0.55, 0.38, 0.26)), dn), 1)
    FOG.nodes["dens"].outputs[0].default_value = 0.05 - 0.025 * dn
    for n in face_em: n.inputs["Strength"].default_value = 0.9 + 0.2 * dn
    door.rotation_euler.z = 0.0; hall.energy = 0.0
    # 煙（黄リンの湯気）
    for f in FUMES:
        u = (tf * f["sp"] + f["ph"]) % 1.0; o = f["o"]
        o.location = f["base"] + Vector((0.05 * math.sin(u * 7 + f["ph"] * 9), 0.04 * math.cos(u * 5), 0.7 * u)); r = 0.05 + 0.14 * u; o.scale = (r, r, r * 1.2)
    # 蹴られるマッチ箱
    kt = t - KICKBOX
    if kt < 0: kbox.location = KB0; kbox.rotation_euler = (0, 0, 0)
    else:
        kt_ = min(kt, 0.7) if t < STOPT else min(STOPT - KICKBOX, 0.7)
        kbox.location = KB0 + Vector((-0.8 * kt_, -1.6 * kt_, 1.4 * kt_ - 4.9 * kt_ * kt_)); kbox.location.z = max(kbox.location.z, 0.015)
        kbox.rotation_euler = (9 * kt_, 4 * kt_, 6 * kt_)
    for s_ in KST:
        o = s_["o"]
        if kt < 0: o.hide_render = True; continue
        o.hide_render = False; kt_ = min(kt, 0.9) if t < STOPT else min(STOPT - KICKBOX, 0.9)
        p = KB0 + s_["v"] * kt_ + Vector((0, 0, -4.9 * kt_ * kt_)); p.z = max(p.z, 0.006); o.location = p; o.rotation_euler = s_["w"] * kt_
    # 人物：工場主
    op, rx, ry, olook = owner_state(t)
    face_to(owner, op, olook); owner.location = op
    owner.rotation_euler = (rx, ry, owner.rotation_euler.z)
    # トキモリ
    pose, tp, tlook = toki_state(t)
    vis = t >= STOPT + 0.45
    for k, (r_, tx_, allo) in TM.items():
        on = vis and k == pose
        for o in allo:
            if o.type == "MESH": o.hide_render = not on
        if k == pose: face_to(r_, tp, tlook)
        T.set_expr(tx_, "toki", expr_toki(t))
    tr_ = TM[pose][0]
    hand = tr_.matrix_world @ Vector(POSES[pose]["R"][1])
    wlo.location = hand + Vector((0, 0, 0.05)); wl.energy = (3.0 + 40.0 * math.exp(-max(0.0, t - STOPT) / 0.4) * (t >= STOPT)) * vis
    charge = ease((t - CHARGE) / 0.6) * (1 - ease((t - FINISH - 0.4) / 0.4))
    FIST_K.default_value = 1.5 * ease((t - DASH) / 0.2) * (t < FALL + 0.3) + 25.0 * charge
    wl.energy += 120.0 * charge
    WF_K.default_value = 4.0 + 20.0 * math.exp(-max(0.0, t - STOPT) / 0.3) * (t >= STOPT) + 14.0 * math.exp(-max(0.0, t - STAMP) / 0.25) * (t >= STAMP)
    # 時を止める金の殻
    u = (t - STOPT) / 0.9; shell.hide_render = not (0 <= u < 1.0)
    if not shell.hide_render: shell.location = TOKI_P + Vector((0, 0, 1.2)); r = 0.2 + 9.0 * ease(u); shell.scale = (r, r, r); SHELL_K.default_value = 0.55 * (1 - u)
    # 当たった瞬間の光の玉
    iv, ti = impact_at(t)
    hitb.hide_render = ti is None
    if ti is not None:
        ip = impact_point(ti); k = (t - ti) / 0.5; hitb.location = ip; r = 0.1 + 0.75 * ease(k ** 0.5); hitb.scale = (r, r, r); HIT_K.default_value = 0.9 * (1 - k) ** 2
        hitlo.location = ip; hitl.energy = 900.0 * iv
    else: hitl.energy = 0.0
    # がれき
    for d in DEB:
        o = d["o"]
        t0 = CEIL_T if d["kind"] == "ceil" else WALL_T
        dt = t - t0
        if dt < 0 or dt > 3.5: o.hide_render = True; continue
        o.hide_render = False
        if d["kind"] == "ceil":
            base = owner_state(CEIL_T)[0] + Vector((0, 0, 3.95)) + d["off"]; p = base + Vector((d["v"].x * 0.6 * dt, d["v"].y * 0.6 * dt, -4.9 * dt * dt))
        else:
            base = Vector((X1 + 0.3, owner_state(WALL_T)[0].y, 1.0)) + d["off"] * 1.5; v = Vector((abs(d["v"].x) * 4 + 2, d["v"].y * 2, d["v"].z * 2))
            p = base + v * dt + Vector((0, 0, -4.9 * dt * dt))
        p.z = max(p.z, d["s"] / 2 - (0.5 if p.x > X1 + 1 else 0.0)); o.location = p; o.scale = (d["s"],) * 3; o.rotation_euler = d["w"] * min(dt, 0.8)
    for h in HOLE:
        o = h["o"]; dt = t - WALL_T
        if dt < 0: o.location = h["p0"]; o.rotation_euler = (0, 0, 0); o.hide_render = False; continue
        p = h["p0"] + h["v"] * dt + Vector((0, 0, -4.9 * dt * dt)); p.z = max(p.z, 0.0); o.location = p; o.rotation_euler = h["w"] * min(dt, 1.0)
        o.scale = (0.9,) * 3
    # 金貨の雨
    for c in COINS:
        o = c["o"]; dt = t - RESUME - c["dl"]
        if dt < 0: o.hide_render = True; continue
        o.hide_render = False; z = c["z0"] - 4.9 * dt * dt
        if z <= c["land"]: z = c["land"] + 0.0025; o.rotation_euler = (0, 0, c["w"].z); o.location = (c["x"], c["y"], z); continue
        o.location = (c["x"], c["y"], z); o.rotation_euler = c["w"] * dt
    # 粒
    for d in DUST:
        o = d["o"]; p = d["p"] + d["v"] * tf + Vector((0.03 * math.sin(tf * 0.7 + d["ph"]), 0.03 * math.cos(tf * 0.5 + d["ph"]), 0.02 * math.sin(tf + d["ph"])))
        o.location = p; s = d["s"] * (1.4 if st else 1.0); o.scale = (s, s, s)
    for g in GD:
        k = (t - STOPT - g["dl"]) / 0.7; o = g["o"]; o.hide_render = not (0 <= k < 1.15)
        if o.hide_render: continue
        r = g["r"] * (1 - ease(k)); a = g["a"] + 2.5 * k
        o.location = TOKI_P + Vector((r * math.cos(a), r * math.sin(a), g["z"] + (1.0 - g["z"]) * 0.3 * ease(k))); o.scale = (g["s"] * (1 - ease((k - 0.9) / 0.25)),) * 3
    # カメラ・補助光
    pos, look, lens, fs, si = shot(t)
    keyo.location = pos + side_of(pos, look) * -1.1 + Vector((0, 0, 0.6)); keyo.rotation_euler = (look - keyo.location).to_track_quat("-Z", "Y").to_euler()
    key.energy = 9.0 * (1.6 if si == 14 else 1.0); key.color = Vector((0.7, 0.75, 1.0)).lerp(Vector((1.0, 0.82, 0.65)), dn)[:]
    rimo.location = look + (look - pos).normalized() * 1.0 + Vector((0.4, 0, 0.5)); rimo.rotation_euler = (look - rimo.location).to_track_quat("-Z", "Y").to_euler()
    rim.energy = 30.0 * (1 - dn) + (25.0 if si in (6, 10, 13) else 0.0); rim.color = (0.55, 0.7, 1.0) if si not in (6, 10, 13) else (1.0, 0.75, 0.4)
    ownlo.location = op + Vector((0.2, -0.5, 2.6)); ownlo.rotation_euler = (op + Vector((0, 0, 1.2)) - ownlo.location).to_track_quat("-Z", "Y").to_euler()
    ownl.energy = 60.0 * (1 - dn)
    cam.location = pos; W.aim(cam, look); cam.data.lens = lens; cam.data.dof.aperture_fstop = fs
    bpy.context.view_layer.update()
    cam.data.dof.focus_distance = max(0.25, (look - pos).length)
    T.set_expr(stex, "sae", expr_sae(t)); T.set_expr(otex, "owner", expr_owner(t))
    for g, gt in others: T.set_expr(gt, "sae", "sad" if t < RESUME else "smile")
    dash = ease((t - DASH) / 0.1) * (1 - ease((t - PUNCH1 - 0.1) / 0.15)) + ease((t - FINISH) / 0.1) * (1 - ease((t - FINISH - 0.9) / 0.3))
    meta = dict(stop=st, dawn=dn, flash=0.0, shot=si, impact=iv, dash=dash)
    if ti is not None:
        sv = world_to_camera_view(sc, cam, impact_point(ti)); meta["imp"] = [sv.x, sv.y, sv.z]
    return meta

frames = TEST or range(START, STOP)
t0 = time.time()
for f in frames:
    p = os.path.join(OUT, "%04d.png" % (f + 1))
    if os.path.exists(p) and not TEST: continue
    t = f / FPS
    meta = place(t)
    bpy.context.view_layer.update()
    wc = Vector((-0.5, Y1 + 2.0, 2.2)); sv = world_to_camera_view(sc, cam, wc)
    meta.update(t=t, sun=[sv.x, sv.y, sv.z], light=0.25 + 0.75 * meta["dawn"])
    json.dump(meta, open(p[:-4] + ".json", "w"))
    tmp = p[:-4] + "_tmp.png"; sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True); os.replace(tmp, p)
    print("frame %s t=%.2f %.1fs" % (p, t, time.time() - t0), flush=True); t0 = time.time()
