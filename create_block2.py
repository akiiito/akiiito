"""
create_block2.py ― ブロック世界パート2（高画質・12fps・縦1画面）
  オリジナルのパステル調ブロック世界を、物理ベースの光（月明かり・松明・光る手・夜明け）で描き直す。
  あたふた → 時間切れ → 背後から攻撃 → 戦うしかない → 壁・柱・ブロック弾で反撃 → 巨大な影 → 夜明けの10秒 → 消えない影
  python create_block2.py [--samples 20] [--start 0] [--end 792] [--test 0,140,...]
"""
import os, sys, math, json, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, Euler
import s2_world as W, s3_toon as T, s7_world as S7
from blk2_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "20")); FPS = 12; N = int(END * FPS)
START = int(arg("--start", "0")); STOP = int(arg("--end", str(N)))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_BLK2" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
LINES = json.load(open(os.path.join(HERE, "blk2_lines.json"), encoding="utf-8"))
RSPANS = [(l[0], l[1]) for l in LINES if l[5] == "ruka"]

sc = W.reset(SAMPLES)
sc.cycles.max_bounces = 4; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.03
sc.view_settings.exposure = float(arg("--exp", "0.0"))
rnd = random.Random(9)

def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def win(t, a, b, fi=0.3, fo=0.3): return ease((t - a) / fi) * (1 - ease((t - b) / fo))
def path(t, pts):
    if t <= pts[0][0]: return Vector(pts[0][1])
    for (ta, a), (tb, b) in zip(pts, pts[1:]):
        if t <= tb: return Vector(a).lerp(Vector(b), ease((t - ta) / (tb - ta)))
    return Vector(pts[-1][1])

# ---------------------------------------------------------------- 霧（全材質に距離で混ぜる共通ノード）
FOG = bpy.data.node_groups.new("FOG", "ShaderNodeTree")
FOG.interface.new_socket("Shader", in_out="INPUT", socket_type="NodeSocketShader")
FOG.interface.new_socket("Shader", in_out="OUTPUT", socket_type="NodeSocketShader")
gi = FOG.nodes.new("NodeGroupInput"); go = FOG.nodes.new("NodeGroupOutput")
cd = FOG.nodes.new("ShaderNodeCameraData"); dens = FOG.nodes.new("ShaderNodeValue"); dens.name = "dens"; dens.outputs[0].default_value = 0.02
mul = FOG.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
ex = FOG.nodes.new("ShaderNodeMath"); ex.operation = "EXPONENT"
neg = FOG.nodes.new("ShaderNodeMath"); neg.operation = "MULTIPLY"; neg.inputs[1].default_value = -1.0
one = FOG.nodes.new("ShaderNodeMath"); one.operation = "SUBTRACT"; one.inputs[0].default_value = 1.0
mx = FOG.nodes.new("ShaderNodeMixShader"); em = FOG.nodes.new("ShaderNodeEmission"); em.name = "fogcol"
lp = FOG.nodes.new("ShaderNodeLightPath")
mn = FOG.nodes.new("ShaderNodeMath"); mn.operation = "MULTIPLY"
L = FOG.links.new
L(cd.outputs["View Distance"], mul.inputs[0]); L(dens.outputs[0], mul.inputs[1]); L(mul.outputs[0], neg.inputs[0])
L(neg.outputs[0], ex.inputs[0]); L(ex.outputs[0], one.inputs[1])
L(one.outputs[0], mn.inputs[0]); L(lp.outputs["Is Camera Ray"], mn.inputs[1])                # 霧はカメラから見た色だけに
L(mn.outputs[0], mx.inputs[0]); L(gi.outputs[0], mx.inputs[1]); L(em.outputs[0], mx.inputs[2]); L(mx.outputs[0], go.inputs[0])
def fogify(m):
    nt = m.node_tree; out = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0]
    src = out.inputs["Surface"].links[0].from_socket
    g = nt.nodes.new("ShaderNodeGroup"); g.node_tree = FOG
    nt.links.new(src, g.inputs[0]); nt.links.new(g.outputs[0], out.inputs["Surface"])
    return m

# ---------------------------------------------------------------- ドット絵の質感（物理ベース＋ドットの凹凸）
def pix(name, png, rough=0.8, emit_red=0.0, glossy=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(os.path.join(S7.TEX, png + ".png")); tx.interpolation = "Closest"
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    bw = nt.nodes.new("ShaderNodeRGBToBW"); bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35; bump.inputs["Distance"].default_value = 0.02
    nt.links.new(tx.outputs["Color"], bw.inputs[0]); nt.links.new(bw.outputs[0], bump.inputs["Height"]); nt.links.new(bump.outputs[0], b.inputs["Normal"])
    if glossy: b.inputs["Roughness"].default_value = 0.25; b.inputs["Coat Weight"].default_value = 0.6
    if emit_red:
        sep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(tx.outputs["Color"], sep.inputs[0])
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.35; mr.inputs["From Max"].default_value = 0.8
        nt.links.new(sep.outputs[0], mr.inputs["Value"])
        b.inputs["Emission Color"].default_value = (1.0, 0.05, 0.08, 1)
        nt.links.new(mr.outputs[0], b.inputs["Emission Strength"]); mr.inputs["To Max"].default_value = emit_red
    return fogify(m)
def P(name, col, rough=0.6, emit=None, estr=0.0, noise=None):
    return fogify(W.mat(name, col, rough, emit=emit, estr=estr, noise=noise))
def E(name, col, s):
    return fogify(S7.emis(name, col, s))

M = {k: pix("p_" + k, k) for k in ("grass_top", "grass_side", "dirt", "stone", "log_side", "log_top", "leaves", "planks")}
M["shadow"] = pix("p_shadow", "shadow", 0.3, emit_red=3.0, glossy=True)
mats = [M[k] for k in ("grass_top", "grass_side", "dirt", "stone", "log_side", "log_top", "leaves", "planks")]
KINDS = {"grass": (0, 1, 2), "dirt": (2, 2, 2), "stone": (3, 3, 3), "log": (5, 4, 5), "leaves": (6, 6, 6), "planks": (7, 7, 7)}

def vox(name, cells, mm=None, kinds=None):
    return S7.voxel_mesh(name, cells, mm or mats, kinds or KINDS)
def cube(name, m, size=1.0):
    """原点中心の立方体（動かす物用）"""
    o = S7.voxel_mesh(name, {(0, 0, 0): "b"}, [m], {"b": (0, 0, 0)})
    for v in o.data.vertices: v.co = (v.co - Vector((0.5, 0.5, 0.5))) * size
    return o

# ---------------------------------------------------------------- 地形（パート1と同じ地形＋隠れ穴）
hgt = None
def build_terrain():
    global hgt
    def h_(x, y):
        d = math.hypot(x, y)
        if d < 9: return 0
        h = 2.2 * math.sin(x * 0.13 + 1.0) + 2.0 * math.sin(y * 0.11) + 1.4 * math.sin((x + y) * 0.21)
        h += max(0, y - 30) * 0.18
        return int(round(max(-1, h) * min(1, (d - 9) / 8)))
    hgt = h_
    cells = {}
    for x in range(-45, 46):
        for y in range(-35, 75):
            h = h_(x, y)
            for k in range(h - 3, h):
                cells[(x, y, k)] = "grass" if k == h - 1 else ("dirt" if k >= h - 2 else "stone")
    for x in (-4, -3):                                               # 隠れる穴（2x2、深さ3）
        for y in (2, 3):
            for k in (-1, -2, -3): cells.pop((x, y, k), None)
    for (x, y) in [(-5, 2), (-5, 3), (-6, 2), (-5, 4)]:
        if rnd.random() < 0.7: cells[(x, y, 0)] = "dirt"                # 掘り出した土
    def tree(x, y, h=4):
        base = h_(x, y)
        for k in range(base, base + h): cells[(x, y, k)] = "log"
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                for dk in range(h - 1, h + 2):
                    if (abs(dx) + abs(dy) + max(0, dk - h) * 2 <= 3 and (dx, dy) != (0, 0)) or dk >= h:
                        if rnd.random() < 0.9 and (x + dx, y + dy, base + dk) not in cells:
                            cells[(x + dx, y + dy, base + dk)] = "leaves"
    for (x, y) in [(-7, 6), (-11, -3), (8, -5), (12, 9), (-5, 16), (14, 22), (-14, 20), (4, 18), (-20, 32), (20, 36),
                   (-9, -10), (6, -12), (-16, 8), (17, -2), (-24, 14), (25, 18), (-6, 40), (10, 44), (-30, 26), (30, 30)]:
        tree(x, y, rnd.randint(4, 6))
    for (x, y) in [(xx, yy) for xx in range(2, 6) for yy in range(3, 7)]:   # パート1で建てた家（板）
        for k in range(4):
            edge = x in (2, 5) or y in (3, 6)
            door = (x, y) in ((3, 3), (4, 3)) and k < 2
            if k == 3 or (edge and not door): cells[(x + 2, y - 7, k)] = "planks"
    return vox("terrain", cells)
build_terrain()

# ---------------------------------------------------------------- 空・月・星・光
world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True; wn = world.node_tree
bg = wn.nodes["Background"]
co = wn.nodes.new("ShaderNodeTexCoord"); sep = wn.nodes.new("ShaderNodeSeparateXYZ")
wn.links.new(co.outputs["Generated"], sep.inputs[0])
nramp = wn.nodes.new("ShaderNodeValToRGB"); el = nramp.color_ramp.elements
el[0].position, el[0].color = 0.0, (0.05, 0.06, 0.16, 1); el[1].position, el[1].color = 0.45, (0.005, 0.006, 0.02, 1)
nmid = el.new(0.08); nmid.color = (0.03, 0.035, 0.1, 1)
mr = wn.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.5; mr.inputs["From Max"].default_value = 1.0
wn.links.new(sep.outputs["Z"], mr.inputs["Value"]); wn.links.new(mr.outputs[0], nramp.inputs["Fac"])
sky = wn.nodes.new("ShaderNodeTexSky")
try: sky.sky_type = "MULTIPLE_SCATTERING"
except Exception:
    try: sky.sky_type = "NISHITA"
    except Exception: pass
try: sky.sun_rotation = math.radians(180); sky.air_density = 1.2; sky.aerosol_density = 3.0; sky.sun_size = math.radians(3.0)
except Exception: pass
skm = wn.nodes.new("ShaderNodeMath"); skm.operation = "MULTIPLY"
wmix = wn.nodes.new("ShaderNodeMix"); wmix.data_type = "RGBA"
wsk = wn.nodes.new("ShaderNodeMix"); wsk.data_type = "RGBA"; wsk.blend_type = "MULTIPLY"; wsk.inputs["Factor"].default_value = 1.0
wn.links.new(sky.outputs["Color"], wsk.inputs["A"]); wsk.inputs["B"].default_value = (0.4, 0.4, 0.4, 1)
wn.links.new(nramp.outputs["Color"], wmix.inputs["A"]); wn.links.new(wsk.outputs["Result"], wmix.inputs["B"])
wn.links.new(wmix.outputs["Result"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 1.0
# 四角い月（大きめ）と星
moon_m = E("moon", (0.85, 0.9, 1.0), 6.0)
moon = cube("moon", moon_m, 1.0); moon.scale = (26, 1, 26); moon.visible_shadow = False
mdir = Vector((-0.45, 0.85, 0.42)).normalized(); moon.location = mdir * 520; moon.rotation_euler = (0, 0, math.atan2(-mdir.x, mdir.y))
star_m = E("star", (1, 1, 0.95), 8.0); stars = []
rs = random.Random(12)
for k in range(110):
    a, e = rs.uniform(-1.6, 1.6), rs.uniform(0.12, 1.2)
    p = Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))) * 480
    s = cube("star", star_m, rs.uniform(1.0, 2.4)); s.location = p; s.visible_shadow = False; stars.append(s)
# 朝日（四角い太陽。地平線の向こう＝ボスの背後から昇る）
sun_m = E("sunsq", (1.0, 0.7, 0.35), 25.0)
sunq = cube("sunq", sun_m, 1.0); sunq.scale = (34, 1, 34); sunq.visible_shadow = False
ml = bpy.data.lights.new("moonl", "SUN"); ml.angle = math.radians(1.5)
mlo = bpy.data.objects.new("moonl", ml); bpy.context.collection.objects.link(mlo)
# 松明（棒＋燃える頭＋暖色の点光源。ゆらぐ）
stick_m = P("stick", (0.35, 0.22, 0.12), 0.8); flame_m = E("flame", (1.0, 0.55, 0.15), 18.0)
TORCHES = [(-2.5, 4.5), (2.0, 4.6), (-3.2, -1.5), (3.3, -1.0), (7.5, -3.6)]
torch_l = []
for i, (x, y) in enumerate(TORCHES):
    st = cube("tstick", stick_m, 1.0); st.scale = (0.12, 0.12, 0.8); st.location = (x, y, 0.4)
    fl = cube("tflame", flame_m, 1.0); fl.scale = (0.16, 0.16, 0.2); fl.location = (x, y, 0.88); fl.visible_shadow = False
    l = bpy.data.lights.new("torch%d" % i, "POINT"); l.color = (1.0, 0.55, 0.22); l.shadow_soft_size = 0.15
    lo = bpy.data.objects.new("torch%d" % i, l); bpy.context.collection.objects.link(lo); lo.location = (x, y, 1.15)
    torch_l.append((l, rnd.uniform(0, 6)))

# ---------------------------------------------------------------- ルカ（トゥーンの体を物理ベースに置きかえ、顔はドット感の残るアニメ顔）
RK = Vector((-1.15, 2.6, 0))
ruka, rtex = T.girl("ruka", tuple(RK), rot=200, hair=(0.3, 0.2, 0.16), face="mei", ponytail=True)
RCOL = {"blazer": (0.36, 0.56, 0.42), "skirt": (0.52, 0.38, 0.26), "sock": (0.4, 0.28, 0.2)}
face_em = []
for o in [ruka] + list(ruka.children_recursive):
    if o.type != "MESH": continue
    for i, m in enumerate(o.data.materials):
        if not (m and m.node_tree): continue
        if "facemat" in m.name:
            face_em += [n for n in m.node_tree.nodes if n.type == "EMISSION"]; continue
        rp = [n for n in m.node_tree.nodes if n.type == "VALTORGB"]
        if rp:
            key = m.name.split("_")[-1]
            c = RCOL.get(key) or tuple(x ** 0.4545 for x in rp[0].color_ramp.elements[1].color[:3])
            lin = tuple(x ** 2.2 for x in c)
            sk = "skin" in m.name
            nm = W.mat(m.name + "_pbr", lin, 0.55 if sk else 0.75, sss=0.2 if sk else 0.0)
            o.data.materials[i] = fogify(nm)

# ---------------------------------------------------------------- 自分の腕（パーカー）と光る手
cam = W.camera((0, 0.5, 1.62), (0, 10, 1.5), lens=17, fstop=5.6)
skin = P("me_skin", (0.8, 0.6, 0.5), 0.5); skin.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.15
glow = P("me_glow", (0.6, 0.9, 1.0), 0.4, emit=(0.45, 0.9, 1.0), estr=0.0)
hood = P("me_hood", (0.28, 0.29, 0.32), 0.9, noise=(40.0, 0.12))
def piece(name, r, m):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=1.0); o = bpy.context.object; o.name = name
    o.data.materials.append(m); bpy.ops.object.shade_smooth(); o.parent = cam; return o
def ball(name, r, m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=r); o = bpy.context.object; o.name = name
    o.scale = (0.85, 1.3, 0.8); o.data.materials.append(m); bpy.ops.object.shade_smooth(); o.parent = cam; return o
ARMS = {s: dict(up=piece("up" + s, 0.055, hood), lo=piece("lo" + s, 0.05, hood), hd=ball("hd" + s, 0.042, glow)) for s in "LR"}
def between(o, p0, p1):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    o.location = (p0 + p1) / 2; o.scale = (1, 1, max(d.length, 1e-3)); o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
def set_arm(s, sh, el, hn):
    a = ARMS[s]; hn = Vector(hn); el = Vector(el)
    between(a["up"], sh, el); between(a["lo"], el, el + (hn - el) * 0.86)
    a["hd"].location = hn; a["hd"].rotation_euler = (hn - el).to_track_quat("Y", "Z").to_euler()
hl = bpy.data.lights.new("handglow", "POINT"); hl.color = (0.45, 0.85, 1.0); hl.shadow_soft_size = 0.2
hlo = bpy.data.objects.new("handglow", hl); bpy.context.collection.objects.link(hlo); hlo.parent = cam; hlo.location = (0.0, -0.2, -0.5)

# ---------------------------------------------------------------- 影ブロック（雑魚）・背後の1体・ボス
eye_m = E("eye", (1.0, 0.08, 0.06), 5.0); pupil_m = E("pupil", (0.02, 0.0, 0.0), 0.5)
def mob_obj(name, size):
    b = cube(name, M["shadow"], 1.0); b.scale = (size,) * 3
    e = cube(name + "_eye", eye_m, 1.0); e.parent = b; e.location = (0, -0.5, 0.12); e.scale = (0.42, 0.04, 0.42); e.visible_shadow = False
    p = cube(name + "_pu", pupil_m, 1.0); p.parent = b; p.location = (0, -0.52, 0.12); p.scale = (0.1, 0.04, 0.28); p.visible_shadow = False
    return b
rm = random.Random(21); mobs = []
kill_ids = []
for k in range(34):
    side = k % 3
    if side == 0: x, y = rm.uniform(-12, 12), rm.uniform(16, 30)
    elif side == 1: x, y = rm.uniform(10, 18), rm.uniform(2, 20)
    else: x, y = rm.uniform(-18, -10), rm.uniform(2, 20)
    size = rm.uniform(1.0, 1.9)
    mobs.append(dict(o=mob_obj("mob%d" % k, size), x0=x, y0=y, size=size, ph=rm.uniform(0, 6.28), sp=rm.uniform(0.7, 1.2), kill=None, tx=None))
# 撃破される10体：壁の前に並ぶ（x を散らす）
for i, tk in enumerate(KILLS):
    m = mobs[i * 3]; m["kill"] = tk; m["tx"] = -4.0 + 8.0 * i / 9 + rm.uniform(-0.3, 0.3)
attacker = mob_obj("attacker", 1.5)
# ボス：脚・胴・頭・腕のブロック人形（高さ約12m）
def boss_build():
    root = bpy.data.objects.new("boss", None); bpy.context.collection.objects.link(root)
    cells = {}
    for x in range(-3, 3):
        for y in range(-1, 2):
            for z in range(0, 12):
                if z < 4 and (x in (-1, 0)): continue                     # 脚のあいだ
                if z >= 9 and x in (-3, 2) : continue                     # 頭は細く
                cells[(x, y, z)] = "s"
    body = S7.voxel_mesh("boss_body", cells, [M["shadow"]], {"s": (0, 0, 0)}); body.parent = root
    be = cube("boss_eye", eye_m, 1.0); be.parent = root; be.location = (0, -1.06, 10.4); be.scale = (2.4, 0.1, 1.6); be.visible_shadow = False
    bp = cube("boss_pu", pupil_m, 1.0); bp.parent = root; bp.location = (0, -1.12, 10.4); bp.scale = (0.5, 0.1, 1.3); bp.visible_shadow = False
    for x in (-2.6, 1.6):                                                  # 胸の赤いひび
        cr = cube("boss_cr", eye_m, 1.0); cr.parent = root; cr.location = (x * 0.5, -1.04, 6.5 + x * 0.3); cr.scale = (0.25, 0.08, 1.8)
        cr.rotation_euler = (0, 0.5 * (1 if x > 0 else -1), 0); cr.visible_shadow = False
    arms = []
    for sx in (-1, 1):
        piv = bpy.data.objects.new("boss_sh", None); bpy.context.collection.objects.link(piv); piv.parent = root
        piv.location = (3.5 * sx, 0, 8.5)
        ac = {(0, 0, -z): "s" for z in range(1, 10)} | {(1, 0, -z): "s" for z in range(1, 10)} | {(0, 1, -z): "s" for z in range(1, 10)} | {(1, 1, -z): "s" for z in range(1, 10)}
        ac |= {(a, b, -10): "s" for a in (-1, 0, 1, 2) for b in (-1, 0, 1, 2)} | {(a, b, -11): "s" for a in (-1, 0, 1, 2) for b in (-1, 0, 1, 2)}
        am = S7.voxel_mesh("boss_arm", ac, [M["shadow"]], {"s": (0, 0, 0)}); am.parent = piv; am.location = (-1, -1, 0.5)
        arms.append(piv)
    return root, arms
boss, barms = boss_build()
# 壁（9x2）と足もとの柱（2段）と最後の巨大柱
WALL = [(x, 8, k) for k in range(2) for x in range(-4, 5)]
wall = []
for c in WALL:
    o = cube("wall", M["stone"]); wall.append(dict(o=o, c=Vector(c) + Vector((0.5, 0.5, 0.5))))
ME = Vector((0.5, 2.5, 0))                                                 # 戦うときに立つ場所（セル (0,2) の中心）
pillar = [cube("pil%d" % k, M["planks"]) for k in range(2)]
BIG = [cube("big%d" % k, M["stone"], 2.0) for k in range(8)]              # 2m角 x 8段
shots = [cube("shot%d" % i, M["planks"] if i % 2 else M["stone"], 0.7) for i in range(len(KILLS))]
# 破片（撃破・壁の崩れ・夜明けで溶ける）
frag_m = M["shadow"]; spark_m = E("spark", (1.0, 0.25, 0.1), 10.0); dawn_m = E("dawnfrag", (1.0, 0.75, 0.4), 12.0)
FR = []
def frags(t0, org, n, speed, up, size, m, life=1.6, seed=0):
    r = random.Random(seed)
    for _ in range(n):
        o = cube("frag", m, 1.0); o.visible_shadow = m is frag_m
        v = Vector((r.uniform(-1, 1), r.uniform(-1, 1), 0)).normalized() * r.uniform(0.3, 1.0) * speed + Vector((0, 0, up * r.uniform(0.6, 1.2)))
        FR.append(dict(o=o, t0=t0, p=Vector(org) + Vector((r.uniform(-.3, .3), r.uniform(-.3, .3), r.uniform(-.3, .3))), v=v,
                       s=size * r.uniform(0.5, 1.2), spin=Vector((r.uniform(-9, 9), r.uniform(-9, 9), r.uniform(-9, 9))), life=life, g=(-12 if m is not dawn_m else 3)))

# ---------------------------------------------------------------- 動き
def mob_pos(m, t):
    """雑魚の位置（(x,y,z) と 見えるか）"""
    if m["kill"] is not None and t >= m["kill"]: return None
    if t >= DAWN + 0.4 + (m["ph"] % 1.0) * 1.5: return None
    k = max(0.0, t)
    hop = abs(math.sin(t * 3.0 * m["sp"] + m["ph"])) * 0.55
    x, y = m["x0"], m["y0"]
    d = Vector((x - ME.x, y - ME.y)); L0 = d.length
    lim = 9.5 if t < WALL1 else (9.2 + m["size"] / 2)
    if m["kill"] is not None and t > WALL0:                               # 撃破組は壁の前に並ぶ
        tx, ty = m["tx"], 9.4 + m["size"] / 2
        kk = ease((t - WALL0) / 2.0); x = x + (tx - x) * kk; y = y + (ty - y) * kk
    else:
        r = max(lim, L0 - 0.35 * k * m["sp"])
        if m["y0"] > 12 and t > WALL0: r = max(6.6 + m["size"] / 2 + (m["ph"] % 1) * 4, L0 - 0.35 * k * m["sp"])
        d = d.normalized() * r; x, y = ME.x + d.x, ME.y + d.y
    g = hgt(int(math.floor(x)), int(math.floor(y)))
    if CRASH - 0.2 <= t < CRASH + 0.6 and y < 13: hop = 0.9 * math.sin(math.pi * (t - CRASH + 0.2) / 0.8)   # 壁にぶつかって跳ね返る
    sink = 0.0
    if t > DAWN: sink = ease((t - DAWN) / 1.2) * m["size"]
    return Vector((x, y, g + m["size"] / 2 + hop - sink)), math.atan2(ME.x - x, -(ME.y - y))

def boss_state(t):
    """位置・腕の角度・傾き・見えるか"""
    if t < BOSS0: return None
    y = 24.0; z = -12.0 + 12.0 * ease((t - BOSS0) / (BOSS1 - BOSS0))
    if t > BOSS0: z += 0.15 * math.sin(t * 30) * (1 - ease((t - BOSS1) / 0.5))
    if t >= BOSS1: y = 24 - 14 * ease((t - BOSS1) / (JUMP + 0.5 - BOSS1))          # 歩いて近づく
    if t >= JUMP + 0.5: y = 10 - 2.5 * ease((t - JUMP - 0.5) / 1.2)                 # 拳を振る（前のめり）
    if t >= HIT2 + 0.6: y = 7.5 + 3.5 * ease((t - HIT2 - 0.6) / 3.0)               # 少し下がる
    pitch = 0.0
    if JUMP + 0.5 <= t < HIT2 + 1.0: pitch = 0.35 * win(t, JUMP + 0.5, HIT2 + 0.3, 0.6, 0.6)
    aL = aR = 0.15 * math.sin(t * 1.3)
    if JUMP < t < HIT2 + 1.2:                                                     # 右腕を振りかぶって叩きつける
        up = ease((t - JUMP) / 0.9); dn = ease((t - (HIT2 - 0.45)) / 0.45); back = ease((t - HIT2 - 0.3) / 0.9)
        aR = -2.8 * up + 1.6 * dn + 1.35 * back
    if t >= RAISE0:                                                               # 両拳を高く振り上げる
        r = ease((t - RAISE0) / (RAISE1 - RAISE0)); aL = aR = -2.9 * r + 0.08 * math.sin(t * 6) * r
    lift = 0.0; roll = 0.0
    if t >= FINAL:                                                                # 柱に突き上げられて後ろへ
        k = ease((t - FINAL) / 0.9); lift = 15.0 * k + 4.0 * ease((t - FINAL - 0.9) / 2.0); pitch = -0.9 * k; y += 6 * k
        roll = 0.3 * k
    vis = t < DAWN + 1.4
    sc_ = 1.0 - ease((t - DAWN) / 1.4) if t > DAWN else 1.0
    return dict(y=y, z=z + lift, pitch=pitch, roll=roll, aL=aL, aR=aR, vis=vis, s=sc_)

def cam_state(t):
    """位置・見る先・ロール・レンズ"""
    base = Vector((0.0, 0.5, 1.62)); roll = 0.0; lens = 17.0
    rk_face = Vector((RK.x, RK.y, 1.42))
    look = rk_face.copy()
    pos = base.copy()
    # あたふた：穴 ↔ 群れ を素早く見比べる
    HOLE = Vector((-3.0, 3.0, -0.6)); FRONT = Vector((0, 18, 1.2)); RIGHT = Vector((12, 10, 1.2)); LEFT = Vector((-12, 9, 1.2))
    seq = [(0.0, rk_face + Vector((0, 0, 0.0))), (2.6, LEFT), (3.4, HOLE), (4.6, FRONT), (5.6, RIGHT), (6.5, HOLE), (7.1, FRONT),
           (7.6, HOLE), (8.1, RIGHT), (8.6, HOLE), (9.1, FRONT), (9.6, rk_face), (10.5, rk_face)]
    if t < TURN:
        for (ta, a), (tb, b) in zip(seq, seq[1:]):
            if ta <= t <= tb:
                du = min(0.35, tb - ta); k = ease((t - (tb - du)) / du); look = a.lerp(b, k); break
    # 振り向く → 背後から攻撃 → 倒れる
    if TURN <= t < HIT1 + 0.05:
        k = ease((t - TURN) / 0.6); ang = math.pi * k
        look = base + Vector((math.sin(ang) * -6, math.cos(ang) * 6 - 0.0, -0.1))
        if k >= 1: look = Vector((0, -6, 1.2))
    if HIT1 + 0.05 <= t < DOWN1[1] + 1.2:
        f = ease((t - HIT1) / 0.45)
        pos = base.lerp(Vector((0.2, 2.2, 0.32)), f)
        look = pos + Vector((0.6, 1.0, 3.0)).lerp(Vector((0.8, 4, 1.2)), ease((t - 14.0) / 2.0))
        roll = 1.1 * f * (1 - ease((t - 15.5) / 1.5)) + 0.15
        if t >= 16.3: look = look.lerp(rk_face, ease((t - 16.3) / 0.8))                       # 倒れたままルカを見上げる
        if t >= DOWN1[1]:
            g = ease((t - DOWN1[1]) / 1.2); pos = pos.lerp(ME + Vector((0, 0, 1.62)), g); look = look.lerp(ME + Vector((0, 12, 1.0)), g); roll *= (1 - g)
    if t >= DOWN1[1] + 1.2:
        pos = ME + Vector((0, 0, 1.62)); look = ME + Vector((0, 12, 0.6))
        if t >= WALL0 - 0.3: look = Vector((0.5, 8.5, 1.0))
        if 26.0 <= t < 27.7: look = look.lerp(rk_face, win(t, 26.0, 27.3, 0.35, 0.4))
        # 足もとに柱：2段上がる
        rise = 2.0 * ease((t - PILLAR0) / (PILLAR1 - PILLAR0))
        pos = pos + Vector((0, 0, rise))
        if t >= PILLAR1:
            tgt = None
            for i, tk in enumerate(KILLS):
                if tk - 0.55 <= t < tk + 0.1: tgt = i; break
            if tgt is not None:
                mp = mob_pos(mobs[tgt * 3], KILLS[tgt] - 0.05)
                if mp: look = look.lerp(mp[0], 0.85)
            else:
                look = Vector((0.5, 11, 0.8))
        if t >= RUMBLE: look = Vector((0.5, 20, 2.0 + 8 * ease((t - BOSS0) / (BOSS1 - BOSS0))))
        if t >= JUMP:                                                                         # 飛び降りてルカの前へ
            j = ease((t - JUMP) / 0.45); p2 = Vector((RK.x + 0.6, RK.y + 0.9, 1.62))
            pos = pos.lerp(p2, j) + Vector((0, 0, 0.6 * math.sin(math.pi * min(1, (t - JUMP) / 0.45))))
            bs = boss_state(t); look = Vector((0.0, bs["y"] - 2, 7.0 - 3.0 * ease((t - (HIT2 - 0.6)) / 0.5)))
        if t >= HIT2:                                                                         # 拳を受けて吹き飛ぶ
            f = ease((t - HIT2) / 0.5); p2 = Vector((RK.x + 0.6, RK.y + 0.9, 1.62))
            pos = p2.lerp(Vector((0.0, -2.2, 0.3)), f)
            look = pos + Vector((-0.6, 1.0, 3.5)); roll = -1.0 * f * (1 - ease((t - 45.0) / 1.6)) - 0.1
            if t >= 43.5: look = look.lerp(rk_face, win(t, 43.5, 46.6, 0.6, 0.5))
            if t >= DOWN2[1]:
                g = ease((t - DOWN2[1]) / 1.4); pos = pos.lerp(Vector((0.0, -1.6, 1.62)), g); roll *= (1 - g)
                look = look.lerp(Vector((0.0, 11, 7.0)), g)
        if t >= DOWN2[1] + 1.4:
            bs = boss_state(t); look = Vector((0.0, bs["y"], 8.5 + 2.5 * ease((t - RAISE0) / 2.0)))
            if t >= FINAL: look = Vector((0.0, bs["y"], min(30, bs["z"] + 9)))
            if t >= DAWN - 0.3: look = look.lerp(Vector((0, 80, 7)), ease((t - DAWN + 0.3) / 1.0))
            if t >= 59.2: look = look.lerp(rk_face, ease((t - 59.2) / 0.7))
            if t >= SHADOW - 0.2:
                k = ease((t - SHADOW + 0.2) / 0.8); look = look.lerp(SHADOW_P + Vector((0, 0, 0.8)), k); lens = 17 + 25 * ease((t - SHADOW - 0.6) / 1.6)
    # 揺れ（被弾・壁・地鳴り・最後の一手）と手持ちの揺れ
    sh = 0.0
    for a, amp, d in ((HIT1, 0.12, 0.6), (CRASH, 0.03, 0.5), (HIT2, 0.15, 0.7), (FINAL + 0.1, 0.1, 0.9), (DAWN, 0.03, 0.8)):
        if a <= t < a + d: sh = max(sh, amp * (1 - (t - a) / d))
    if RUMBLE <= t < BOSS1: sh = max(sh, 0.035)
    if t < TURN: sh = max(sh, 0.008)
    pos = pos + Vector((sh * math.sin(t * 47), sh * math.sin(t * 39), sh * math.sin(t * 53)))
    pos += Vector((0.006 * math.sin(t * 1.7), 0, 0.006 * math.sin(t * 2.3)))
    return pos, look, roll, lens

SHADOW_P = None
def find_shadow_p():
    x, y = 7, 16
    return Vector((x + 0.5, y + 0.5, hgt(x, y) + 0.75))
SHADOW_P = find_shadow_p()
last = mob_obj("lastshadow", 1.4)

def cast_level(t):
    c = win(t, CAST0, WALL1 + 0.3, 0.8, 0.5) * 0.9 + win(t, PILLAR0 - 0.2, KILLS[-1] + 0.4, 0.2, 0.4)
    c = max(c, ease((t - 50.0) / 6.0) * 1.6 * (1 - ease((t - FINAL - 0.4) / 1.2)))
    return min(2.0, c)

def arms_at(t, cast):
    out = {}
    for s, sx in (("L", -1), ("R", 1)):
        sh = Vector((0.22 * sx, -0.55, 0.05)); el = Vector((0.25 * sx, -0.44, -0.24)); hn = Vector((0.15 * sx, -0.32 + 0.01 * math.sin(t * 1.3), -0.46))
        panic = win(t, CHOICE0, TIMEUP, 0.3, 0.3)
        hn += Vector((0.03 * math.sin(t * 9 + sx), 0.0, 0.05 * panic * math.sin(t * 7 + sx)))
        a = min(1, cast)
        hn = hn.lerp(Vector((0.1 * sx, -0.12, -0.42)), a); el = el.lerp(Vector((0.2 * sx, -0.3, -0.3)), a)
        # 撃つ：右手を突き出す
        for tk in KILLS:
            x = (t - (tk - 0.4)) / 0.22
            if 0 <= x <= 1 and s == "R": hn = hn.lerp(Vector((0.05, -0.02, -0.7)), math.sin(x * math.pi))
        if FINAL - 0.3 <= t < FINAL + 0.6:
            x = ease((t - FINAL + 0.3) / 0.3) * (1 - ease((t - FINAL - 0.3) / 0.3)); hn = hn.lerp(Vector((0.04 * sx, 0.05, -0.75)), x)
        if (HIT1 < t < DOWN1[1] + 0.8) or (HIT2 < t < DOWN2[1] + 0.8):
            hn = hn + Vector((0.1 * sx, 0, -0.25))
        out[s] = (sh, el, hn)
    return out

def build_frags():
    for i, tk in enumerate(KILLS):
        mp = mob_pos(mobs[i * 3], tk - 0.01)
        if mp:
            frags(tk, mp[0], 8, 4.0, 5.0, 0.35 * mobs[i * 3]["size"], frag_m, 1.5, i)
            frags(tk, mp[0], 6, 5.0, 4.0, 0.12, spark_m, 0.7, 100 + i)
    for k in range(10):                                                     # 拳で壁の真ん中が崩れる
        frags(HIT2 - 0.35, Vector((rnd.uniform(-1.5, 2.5), 8.5, rnd.uniform(0.3, 1.8))), 1, 6.0, 6.0, 0.6, M["stone"], 2.5, 300 + k)
    frags(HIT1, Vector((0, -0.4, 1.4)), 10, 3.5, 3.0, 0.2, frag_m, 1.0, 400)
    for k in range(4):                                                      # 夜明け：ボスが光の粒になって溶ける
        frags(DAWN + 0.2 * k, Vector((0.5, 16 + 4 * k, 18 - 2 * k)), 12, 3.0, 1.0, 0.5, dawn_m, 2.4, 500 + k)
build_frags()
WALL_BREAK = {i for i, w in enumerate(wall) if -1 <= w["c"].x - 0.5 <= 1}

# ---------------------------------------------------------------- 1コマ分を置く
def place(t):
    pos, look, roll, lens = cam_state(t)
    cam.location = pos; W.aim(cam, look); cam.rotation_euler.rotate_axis("Z", roll)
    cam.data.lens = lens; cam.data.dof.focus_distance = max(1.0, min(40.0, (look - pos).length))
    cast = cast_level(t)
    for s, (sh, el, hn) in arms_at(t, cast).items(): set_arm(s, sh, el, hn)
    glow.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 4.0 * cast
    hl.energy = 45.0 * cast + (300.0 * math.exp(-((t - FINAL) / 0.25) ** 2) if t > FINAL - 1 else 0)
    hide_arms = (HIT1 + 0.1 < t < DOWN1[1] - 0.2) or (HIT2 + 0.1 < t < DOWN2[1] - 0.2)
    for s in "LR":
        for o in ARMS[s].values(): o.hide_render = hide_arms
        ARMS[s]["hd"].data.materials[0] = glow if cast > 0.25 else skin
    # 空：夜 → 夜明け
    dawn = ease((t - (DAWN - 1.5)) / 3.0)
    wmix.inputs["Factor"].default_value = dawn
    elev = -6.0 + 9.0 * ease((t - (DAWN - 1.5)) / 4.0)
    try: sky.sun_elevation = math.radians(elev)
    except Exception: pass
    wsk.inputs["B"].default_value = (0.25 + 0.25 * dawn,) * 3 + (1,)
    sdir = Vector((0.0, math.cos(math.radians(max(elev, -3))), math.sin(math.radians(elev)))).normalized()
    sunq.location = sdir * 500; sunq.rotation_euler = (0, 0, 0); sunq.hide_render = elev < -2.5
    mlo.rotation_euler = (-(sdir if dawn > 0.5 else mdir)).to_track_quat("-Z", "Y").to_euler()
    ml.energy = 0.35 + 3.5 * dawn; ml.color = (0.55 + 0.45 * dawn, 0.65 + 0.15 * dawn, 1.0 - 0.45 * dawn)
    moon.hide_render = dawn > 0.95
    for s in stars: s.hide_render = dawn > 0.6
    fogcol = Vector((0.03, 0.035, 0.08)).lerp(Vector((0.85, 0.55, 0.35)), dawn)
    FOG.nodes["fogcol"].inputs["Color"].default_value = (*fogcol, 1); FOG.nodes["fogcol"].inputs["Strength"].default_value = 1.0
    FOG.nodes["dens"].outputs[0].default_value = 0.022 - 0.015 * dawn
    for i, (l, ph) in enumerate(torch_l):
        l.energy = (55 + 12 * math.sin(t * 13 + ph) + 8 * math.sin(t * 29 + ph * 2)) * (1 - 0.6 * dawn)
    for n in face_em: n.inputs["Strength"].default_value = 0.45 + 0.55 * dawn + 0.3 * min(1, cast)
    # ルカ：基本は自分の方を見る
    to_me = Vector((pos.x - RK.x, pos.y - RK.y, 0))
    if to_me.length > 0.01:
        to_me.normalize(); ruka.rotation_euler = (0, 0, math.atan2(-to_me.x, to_me.y))
    if BOSS0 + 1 < t < JUMP: ruka.rotation_euler = (0, 0, math.radians(0))           # ボスを見上げる
    talking = any(st <= t <= en - 0.05 for st, en in RSPANS); flap = talking and (int(t * FPS) % 3 != 2)
    if t < HIT1 + 1: e = "talk" if flap else "shockc"
    elif t < WALL0: e = "talk" if flap else "shock"
    elif t < BOSS0: e = "smiletalk" if flap else ("shock" if t < 28.4 else "smile")
    elif t < DAWN: e = ("tearsadtalk" if flap else "tearsad") if HIT2 < t < 50 else ("talk" if flap else "shockc")
    elif t < SHADOW: e = "tearsmiletalk" if flap else "tearsmile"
    else: e = "talk" if flap else "shockc"
    if (t % 3.1) < 0.17 and not talking and e in ("smile", "base"): e = "blink"
    T.set_expr(rtex, "mei", e)
    # 雑魚
    for m in mobs:
        r = mob_pos(m, t)
        o = m["o"]; o.hide_render = r is None
        for c in o.children: c.hide_render = r is None
        if r: o.location = r[0]; o.rotation_euler = (0, 0, r[1])
    # 背後の1体：飛びかかる → はね返って消える
    if TURN <= t < HIT1 + 0.7:
        k = ease((t - TURN - 0.2) / (HIT1 - TURN - 0.2))
        p = Vector((0.3, -7, 0.75)).lerp(Vector((0.0, -0.3, 1.45)), k) + Vector((0, 0, 1.6 * math.sin(math.pi * k)))
        if t > HIT1: p = Vector((0.0, -0.3, 1.45)).lerp(Vector((0.5, -4, 0.75)), ease((t - HIT1) / 0.6))
        attacker.location = p; attacker.rotation_euler = (0, 0, math.pi); vis = True
    else: vis = False
    attacker.hide_render = not vis
    for c in attacker.children: c.hide_render = not vis
    # 壁
    bpy.context.view_layer.update()
    src = cam.matrix_world @ Vector((0.08, -0.1, -0.6))
    for i, w in enumerate(wall):
        st = WALL0 + (WALL1 - WALL0 - 0.35) * i / len(wall)
        k = ease((t - st) / 0.35); o = w["o"]
        o.hide_render = k <= 0
        c = src.lerp(w["c"], k) + Vector((0, 0, 1.0 * math.sin(k * math.pi)))
        o.scale = (0.3 + 0.7 * k,) * 3; o.location = c; o.rotation_euler = ((1 - k) * 4, (1 - k) * 3, 0)
        if i in WALL_BREAK and t >= HIT2 - 0.35: o.hide_render = True
    # 足もとの柱
    for k_, o in enumerate(pillar):
        h = 2.0 * ease((t - PILLAR0) / (PILLAR1 - PILLAR0))
        o.hide_render = t < PILLAR0 or t > JUMP + 6
        sz = max(0.01, min(1.0, h - k_)); o.scale = (1, 1, sz); o.location = (ME.x, ME.y, k_ + 0.5 * sz)
    # ブロック弾
    for i, (o, tk) in enumerate(zip(shots, KILLS)):
        t0 = tk - 0.38; k = (t - t0) / 0.38
        o.hide_render = not (0 <= k < 1)
        if 0 <= k < 1:
            mp = mob_pos(mobs[i * 3], tk - 0.01)
            tgt = mp[0] if mp else Vector((0, 10, 1))
            o.location = src.lerp(tgt, k) + Vector((0, 0, 0.8 * math.sin(k * math.pi))); o.rotation_euler = (k * 9, k * 7, 0)
    # ボス
    bs = boss_state(t)
    hidden = bs is None or not bs["vis"]
    for o in [boss] + list(boss.children_recursive): o.hide_render = hidden
    if bs:
        boss.location = (0.5, bs["y"], bs["z"]); boss.rotation_euler = (bs["pitch"], bs["roll"], 0); boss.scale = (max(bs["s"], 1e-3),) * 3
        barms[0].rotation_euler = (bs["aL"], 0, 0); barms[1].rotation_euler = (bs["aR"], 0, 0)
    # 最後の巨大柱（ボスの真下から突き上がる）
    for k_, o in enumerate(BIG):
        h = 16.0 * ease((t - FINAL) / 0.5)
        top = h - 2 * k_
        o.hide_render = t < FINAL or top <= 0 or t > DAWN + 1.4
        o.location = (0.5, 11.0, top - 1.0)
        o.scale = (1,) * 3 if t < DAWN else (max(1e-3, 1 - ease((t - DAWN) / 1.4)),) * 3
    # 破片
    for f in FR:
        dt = t - f["t0"]; o = f["o"]
        if dt < 0 or dt > f["life"]: o.hide_render = True; continue
        o.hide_render = False
        p = f["p"] + f["v"] * dt + Vector((0, 0, 0.5 * f["g"] * dt * dt))
        gz = 0.1 if f["g"] < 0 else -99
        if p.z < gz: p.z = gz
        o.location = p; o.rotation_euler = tuple(f["spin"] * dt)
        s = f["s"] * (1 - max(0, dt - f["life"] * 0.6) / (f["life"] * 0.4)); o.scale = (max(s, 1e-3),) * 3
    # 消えない影
    vis = t >= DAWN - 3
    last.hide_render = not vis
    for c in last.children: c.hide_render = not vis
    last.location = SHADOW_P; last.rotation_euler = (0, 0, math.atan2(pos.x - SHADOW_P.x, -(pos.y - SHADOW_P.y)))

frames = TEST or range(START, STOP)
t0 = time.time()
for f in frames:
    p = os.path.join(OUT, "%04d.png" % (f + 1))
    if os.path.exists(p) and not TEST: continue
    t = f / FPS
    place(t)
    tmp = p[:-4] + "_tmp.png"; sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True); os.replace(tmp, p)
    print("frame %s t=%.2f %.1fs" % (p, t, time.time() - t0), flush=True); t0 = time.time()
