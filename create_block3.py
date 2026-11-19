"""
create_block3.py ― ブロック世界パート3『消えない影の正体』（高画質・12fps・縦1画面）
  朝の光 → 消えない影が跳ねて近づく → 割れて人の形 → 「その力を、使うな」 → 自分の指先が黒い（影化）
  → 胸が割れて中からパーカー（前の召喚者） → 日食 → 影ブロックが湧く → 使ってしまう → 完全な闇
  python create_block3.py [--samples 16] [--start 0] [--end 768] [--test 0,140,...]
"""
import os, sys, math, json, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, Euler
import s2_world as W, s3_toon as T, s7_world as S7
from blk3_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "20")); FPS = 12; N = int(END * FPS)
START = int(arg("--start", "0")); STOP = int(arg("--end", str(N)))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_BLK3" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
LINES = json.load(open(os.path.join(HERE, "blk3_lines.json"), encoding="utf-8"))
RSPANS = [(l[0], l[1]) for l in LINES if l[5] == "ruka"]

sc = W.reset(SAMPLES)
sc.cycles.max_bounces = 4; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.03
sc.view_settings.exposure = float(arg("--exp", "-0.5"))
print("VIEW", sc.view_settings.view_transform, sc.view_settings.look)
try: sc.view_settings.look = "Medium High Contrast"
except Exception as ex: print("look fail", ex)
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
_sb = M["shadow"].node_tree.nodes["Principled BSDF"]; _sb.inputs["Coat Weight"].default_value = 0.0; _sb.inputs["Specular IOR Level"].default_value = 0.15; _sb.inputs["Roughness"].default_value = 0.5
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
    for x in (-4, -3, -2, 2, 3, 4):                                  # パート2の壁（真ん中は拳で崩れた）
        for k in range(2): cells[(x, 8, k)] = "stone"
    for (x, y) in [(-2, 9), (-1, 10), (3, 10), (2, 7)]: cells[(x, y, 0)] = "stone"   # 崩れた壁のかけら
    return vox("terrain", cells)
build_terrain()

# ---------------------------------------------------------------- 空・太陽・日食（四角い太陽に四角い影がかぶさる）
world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True; wn = world.node_tree
bg = wn.nodes["Background"]
co = wn.nodes.new("ShaderNodeTexCoord"); sep = wn.nodes.new("ShaderNodeSeparateXYZ")
wn.links.new(co.outputs["Generated"], sep.inputs[0])
nramp = wn.nodes.new("ShaderNodeValToRGB"); el = nramp.color_ramp.elements
el[0].position, el[0].color = 0.0, (0.06, 0.02, 0.05, 1); el[1].position, el[1].color = 0.45, (0.004, 0.003, 0.01, 1)
mr = wn.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.5; mr.inputs["From Max"].default_value = 1.0
wn.links.new(sep.outputs["Z"], mr.inputs["Value"]); wn.links.new(mr.outputs[0], nramp.inputs["Fac"])
sky = wn.nodes.new("ShaderNodeTexSky")
try: sky.sky_type = "MULTIPLE_SCATTERING"
except Exception:
    try: sky.sky_type = "NISHITA"
    except Exception: pass
SUN_EL = 12.0
try: sky.sun_rotation = math.radians(180); sky.air_density = 1.2; sky.aerosol_density = 2.0; sky.sun_size = math.radians(3.0); sky.sun_elevation = math.radians(SUN_EL)
except Exception: pass
wmix = wn.nodes.new("ShaderNodeMix"); wmix.data_type = "RGBA"
wsk = wn.nodes.new("ShaderNodeMix"); wsk.data_type = "RGBA"; wsk.blend_type = "MULTIPLY"; wsk.inputs["Factor"].default_value = 1.0
wn.links.new(sky.outputs["Color"], wsk.inputs["A"]); wsk.inputs["B"].default_value = (0.5, 0.5, 0.5, 1)
wn.links.new(nramp.outputs["Color"], wmix.inputs["A"]); wn.links.new(wsk.outputs["Result"], wmix.inputs["B"])
wn.links.new(wmix.outputs["Result"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 1.0
SDIR = Vector((0.1, math.cos(math.radians(SUN_EL)), math.sin(math.radians(SUN_EL)))).normalized()
sun_m = S7.emis("sunsq", (1.0, 0.85, 0.6), 30.0)
sunq = cube("sunq", sun_m, 1.0); sunq.scale = (34, 1, 34); sunq.visible_shadow = False; sunq.location = SDIR * 500
sunq.rotation_euler = (0, 0, math.atan2(-SDIR.x, SDIR.y))
disc_m = W.mat("disc", (0.0, 0.0, 0.0), 1.0)
disc = cube("disc", disc_m, 1.0); disc.scale = (36, 1, 36); disc.visible_shadow = False; disc.rotation_euler = sunq.rotation_euler
cor_m = S7.emis("corona", (0.85, 0.9, 1.0), 6.0)
corona = cube("corona", cor_m, 1.0); corona.scale = (52, 1, 52); corona.visible_shadow = False; corona.location = SDIR * 530
corona.rotation_euler = sunq.rotation_euler
star_m = S7.emis("star", (1, 1, 0.95), 8.0); stars = []
rs = random.Random(12)
for k in range(90):
    a, e = rs.uniform(-1.6, 1.6), rs.uniform(0.12, 1.2)
    p = Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))) * 480
    s = cube("star", star_m, rs.uniform(1.0, 2.2)); s.location = p; s.visible_shadow = False; stars.append(s)
sl = bpy.data.lights.new("sunl", "SUN"); sl.angle = math.radians(1.5); sl.color = (1.0, 0.82, 0.6)
slo = bpy.data.objects.new("sunl", sl); bpy.context.collection.objects.link(slo)
slo.rotation_euler = (-SDIR).to_track_quat("-Z", "Y").to_euler()
fl = bpy.data.lights.new("fill", "SUN"); fl.angle = math.radians(20); fl.color = (1.0, 0.9, 0.8)       # こちら側からのやわらかい照り返し
flo = bpy.data.objects.new("fill", fl); bpy.context.collection.objects.link(flo)
flo.rotation_euler = (-Vector((-0.3, -1.0, 0.7)).normalized()).to_track_quat("-Z", "Y").to_euler()
# 燃えつきた松明（棒だけ）
stick_m = P("stick", (0.25, 0.16, 0.1), 0.85)
for (x, y) in [(-2.5, 4.5), (2.0, 4.6), (-3.2, -1.5), (3.3, -1.0), (7.5, -3.6)]:
    st = cube("tstick", stick_m, 1.0); st.scale = (0.12, 0.12, 0.8); st.location = (x, y, 0.4)

# ---------------------------------------------------------------- ルカ
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

# ---------------------------------------------------------------- 自分の腕（パーカー）と、ブロックの手（指先から黒く＝影化）
CAMP = Vector((0.3, -0.9, 1.62))
cam = W.camera(tuple(CAMP), (0, 10, 1.5), lens=17, fstop=5.6)
hood = P("me_hood", (0.28, 0.29, 0.32), 0.9, noise=(40.0, 0.12))
def piece(name, r, m):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=1.0); o = bpy.context.object; o.name = name
    o.data.materials.append(m); bpy.ops.object.shade_smooth(); o.parent = cam; return o
HV = {}                                   # 手の材質の可変値（cast＝光る強さ、blk＝黒くなった度合い）
def hand_mat(name, hand_empty):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; Lk = nt.links.new
    out = N["Material Output"]; skn = N["Principled BSDF"]
    skn.inputs["Base Color"].default_value = (0.8, 0.58, 0.46, 1); skn.inputs["Roughness"].default_value = 0.55
    skn.inputs["Subsurface Weight"].default_value = 0.15
    skn.inputs["Emission Color"].default_value = (0.2, 0.7, 1.0, 1)
    tc = N.new("ShaderNodeTexCoord"); tc.object = hand_empty
    scl = N.new("ShaderNodeVectorMath"); scl.operation = "SCALE"; scl.inputs["Scale"].default_value = 1 / 0.0125
    snp = N.new("ShaderNodeVectorMath"); snp.operation = "SNAP"; snp.inputs[1].default_value = (1, 1, 1)
    wnz = N.new("ShaderNodeTexWhiteNoise"); wnz.noise_dimensions = "3D"
    Lk(tc.outputs["Object"], scl.inputs[0]); Lk(scl.outputs[0], snp.inputs[0]); Lk(snp.outputs[0], wnz.inputs["Vector"])
    sxyz = N.new("ShaderNodeSeparateXYZ"); Lk(tc.outputs["Object"], sxyz.inputs[0])
    tip = N.new("ShaderNodeMapRange"); tip.inputs["From Min"].default_value = 0.0; tip.inputs["From Max"].default_value = 0.13
    tip.inputs["To Min"].default_value = 0.45; tip.inputs["To Max"].default_value = 0.0; Lk(sxyz.outputs["Y"], tip.inputs["Value"])
    n55 = N.new("ShaderNodeMath"); n55.operation = "MULTIPLY"; n55.inputs[1].default_value = 0.55; Lk(wnz.outputs["Value"], n55.inputs[0])
    score = N.new("ShaderNodeMath"); score.operation = "ADD"; Lk(n55.outputs[0], score.inputs[0]); Lk(tip.outputs[0], score.inputs[1])
    blk = N.new("ShaderNodeValue"); blk.outputs[0].default_value = 0.0
    msk = N.new("ShaderNodeMath"); msk.operation = "LESS_THAN"; Lk(score.outputs[0], msk.inputs[0]); Lk(blk.outputs[0], msk.inputs[1])
    cast = N.new("ShaderNodeValue"); cast.outputs[0].default_value = 0.0
    inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0; Lk(msk.outputs[0], inv.inputs[1])
    ce = N.new("ShaderNodeMath"); ce.operation = "MULTIPLY"; Lk(cast.outputs[0], ce.inputs[0]); Lk(inv.outputs[0], ce.inputs[1])
    ce4 = N.new("ShaderNodeMath"); ce4.operation = "MULTIPLY"; ce4.inputs[1].default_value = 0.8; Lk(ce.outputs[0], ce4.inputs[0])
    Lk(ce4.outputs[0], skn.inputs["Emission Strength"])
    var = N.new("ShaderNodeMix"); var.data_type = "RGBA"; var.inputs["A"].default_value = (0.55, 0.38, 0.3, 1); var.inputs["B"].default_value = (0.45, 0.3, 0.23, 1)
    Lk(wnz.outputs["Value"], var.inputs["Factor"]); Lk(var.outputs["Result"], skn.inputs["Base Color"])
    drk = N.new("ShaderNodeBsdfPrincipled"); drk.inputs["Base Color"].default_value = (0.012, 0.01, 0.016, 1)
    drk.inputs["Roughness"].default_value = 0.25; drk.inputs["Coat Weight"].default_value = 0.6
    drk.inputs["Emission Color"].default_value = (1.0, 0.05, 0.08, 1)
    sepc = N.new("ShaderNodeSeparateColor"); Lk(wnz.outputs["Color"], sepc.inputs[0])
    red = N.new("ShaderNodeMath"); red.operation = "GREATER_THAN"; red.inputs[1].default_value = 0.8; Lk(sepc.outputs[0], red.inputs[0])
    rgl = N.new("ShaderNodeValue"); rgl.outputs[0].default_value = 3.0
    rs_ = N.new("ShaderNodeMath"); rs_.operation = "MULTIPLY"; Lk(red.outputs[0], rs_.inputs[0]); Lk(rgl.outputs[0], rs_.inputs[1])
    Lk(rs_.outputs[0], drk.inputs["Emission Strength"])
    mx = N.new("ShaderNodeMixShader"); Lk(msk.outputs[0], mx.inputs[0]); Lk(skn.outputs[0], mx.inputs[1]); Lk(drk.outputs[0], mx.inputs[2])
    Lk(mx.outputs[0], out.inputs["Surface"])
    HV[name] = dict(blk=blk.outputs[0], cast=cast.outputs[0], red=rgl.outputs[0])
    return fogify(m)
def hand_build(s):
    """手首を原点、指先 +Y、手の甲 +Z のブロックの手"""
    h = bpy.data.objects.new("hand" + s, None); bpy.context.collection.objects.link(h); h.parent = cam
    m = hand_mat("hm" + s, h); sx = 1 if s == "R" else -1
    def bx(nm, c, sz, rot=(0, 0, 0)):
        o = cube(nm, m, 1.0); o.scale = sz; o.location = c; o.rotation_euler = rot; o.parent = h; return o
    bx("palm" + s, (0, 0.04, 0), (0.08, 0.08, 0.03))
    for k in range(4):
        x = -0.03 + 0.02 * k
        bx("fing%s%d" % (s, k), (x, 0.1 - 0.004 * abs(k - 1.5), -0.004), (0.017, 0.048 - 0.006 * abs(k - 1.5), 0.019), (-0.25, 0, 0))
    bx("thumb" + s, (-0.05 * sx, 0.045, -0.006), (0.018, 0.045, 0.02), (0, 0, 0.5 * sx))
    return h, m
ARMS = {}
for s in "LR":
    hh, hm = hand_build(s)
    ARMS[s] = dict(up=piece("up" + s, 0.055, hood), lo=piece("lo" + s, 0.05, hood), hd=hh, m=hm.name)
def between(o, p0, p1):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    o.location = (p0 + p1) / 2; o.scale = (1, 1, max(d.length, 1e-3)); o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
from mathutils import Matrix
def set_arm(s, sh, el, hn, roll=0.0):
    a = ARMS[s]; hn = Vector(hn); el = Vector(el)
    between(a["up"], sh, el); between(a["lo"], el, el + (hn - el) * 0.98)
    y = (hn - el).normalized(); x = y.cross(Vector((0, 1, 0))).normalized(); z = x.cross(y)
    mt = Matrix((x, y, z)).transposed() @ Matrix.Rotation(roll, 3, "Y")
    a["hd"].location = hn; a["hd"].rotation_euler = mt.to_euler()
hl = bpy.data.lights.new("handglow", "POINT"); hl.color = (0.45, 0.85, 1.0); hl.shadow_soft_size = 0.2
hlo = bpy.data.objects.new("handglow", hl); bpy.context.collection.objects.link(hlo); hlo.parent = cam; hlo.location = (0.0, -0.1, -0.8)

# ---------------------------------------------------------------- 影ブロック・消えない影（人の形）
eye_m = E("eye", (1.0, 0.08, 0.06), 5.0); pupil_m = E("pupil", (0.02, 0.0, 0.0), 0.5)
def mob_obj(name, size):
    b = cube(name, M["shadow"], 1.0); b.scale = (size,) * 3
    e = cube(name + "_eye", eye_m, 1.0); e.parent = b; e.location = (0, -0.5, 0.12); e.scale = (0.42, 0.04, 0.42); e.visible_shadow = False
    p = cube(name + "_pu", pupil_m, 1.0); p.parent = b; p.location = (0, -0.52, 0.12); p.scale = (0.1, 0.04, 0.28); p.visible_shadow = False
    return b
SHADOW_P = Vector((7.5, 16.5, hgt(7, 16) + 0.75))
KP = Vector((0.6, 5.2, 0)); KB = Vector((1.6, 6.6, 0))
last = mob_obj("lastshadow", 1.4)
U = 0.115
def kage_mat():
    m = bpy.data.materials.new("kage_m"); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; Lk = nt.links.new; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); scl = N.new("ShaderNodeVectorMath"); scl.operation = "SCALE"; scl.inputs["Scale"].default_value = 3.0
    snp = N.new("ShaderNodeVectorMath"); snp.operation = "SNAP"; snp.inputs[1].default_value = (1, 1, 1)
    wnz = N.new("ShaderNodeTexWhiteNoise"); wnz.noise_dimensions = "3D"
    Lk(tc.outputs["Object"], scl.inputs[0]); Lk(scl.outputs[0], snp.inputs[0]); Lk(snp.outputs[0], wnz.inputs["Vector"])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.inputs["A"].default_value = (0.0012, 0.0008, 0.0016, 1); mx.inputs["B"].default_value = (0.006, 0.002, 0.006, 1)
    Lk(wnz.outputs["Value"], mx.inputs["Factor"]); Lk(mx.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.8; b.inputs["Specular IOR Level"].default_value = 0.02
    return fogify(m)
KM = kage_mat()
def kage_build():
    root = bpy.data.objects.new("kage", None); bpy.context.collection.objects.link(root); root.scale = (U,) * 3
    c = {}
    for x in (-2, -1, 0, 1):
        for y in (-1, 0):
            for z in range(0, 6):
                if x in (-1, 0) and z < 5: continue
                c[(x, y, z)] = "s"
            for z in range(6, 12): c[(x, y, z)] = "s"
    for x in (-2, -1, 0, 1):
        for y in (-2, -1, 0, 1):
            for z in range(12, 16): c[(x, y, z)] = "s"
    for z in range(12, 16):                                              # フード
        for y in (-1, 0, 1): c[(-3, y, z)] = "s"; c[(2, y, z)] = "s"
        for x in (-2, -1, 0, 1): c[(x, 2, z)] = "s"
    for x in (-2, -1, 0, 1):
        for y in (-1, 0, 1): c[(x, y, 16)] = "s"
    body = S7.voxel_mesh("kage_body", c, [KM], {"s": (0, 0, 0)}); body.parent = root
    chest = S7.voxel_mesh("kage_chest", {(x, -2, z): "s" for x in (-2, -1, 0, 1) for z in range(7, 11)}, [KM], {"s": (0, 0, 0)}); chest.parent = root
    hoodie = S7.voxel_mesh("kage_hoodie", {(x, -2, z): "h" for x in (-2, -1, 0, 1) for z in range(7, 11)}, [hood], {"h": (0, 0, 0)}); hoodie.parent = root
    hoodie.scale = (0.98, 1, 0.98); hoodie.location = (-0.02, 0.05, 0.15)
    str_m = P("strings", (0.85, 0.85, 0.82), 0.6)
    strs = []
    for x in (-0.7, 0.7):
        st = cube("kage_str", str_m, 1.0); st.parent = root; st.location = (x, -2.1, 9.6); st.scale = (0.18, 0.12, 1.6); strs.append(st)
    zp = cube("kage_zip", P("zip", (0.5, 0.5, 0.52), 0.3), 1.0); zp.parent = root; zp.location = (0, -2.06, 8.5); zp.scale = (0.12, 0.1, 3.0); strs.append(zp)
    eyes = []
    for x in (-0.9, 0.9):
        e = cube("kage_eye", eye_m, 1.0); e.parent = root; e.location = (x, -2.06, 13.8); e.scale = (0.6, 0.12, 0.38); e.visible_shadow = False; eyes.append(e)
    cracks = []
    for (x, z, r, ln) in ((-1.2, 9.0, 0.5, 2.6), (0.9, 8.4, -0.6, 2.2), (-0.2, 10.2, 1.3, 1.6), (0.4, 7.4, 0.2, 1.4)):
        cr = cube("kage_cr", eye_m, 1.0); cr.parent = root; cr.location = (x, -2.12, z); cr.scale = (0.18, 0.1, ln); cr.rotation_euler = (0, r, 0)
        cr.visible_shadow = False; cracks.append(cr)
    arms = []
    for sx in (-1, 1):
        piv = bpy.data.objects.new("kage_sh", None); bpy.context.collection.objects.link(piv); piv.parent = root
        piv.location = (-2.5 if sx < 0 else 2.5, -0.5, 11.5)
        am = S7.voxel_mesh("kage_arm", {(0, y, -z): "s" for y in (-1, 0) for z in range(1, 8)}, [KM], {"s": (0, 0, 0)})
        am.parent = piv; am.location = (-0.5, 0.5, 0.5); arms.append(piv)
    return root, body, chest, hoodie, strs, eyes, cracks, arms
kage, kbody, kchest, khoodie, kstrs, keyes, kcracks, karms = kage_build()
KPARTS = [kbody, kchest, khoodie] + kstrs + keyes + kcracks + [o for a in karms for o in a.children]

# 地面から湧く影ブロック（カメラが見回す順に湧く）
SWEEP0, SWEEP1 = RISE0, RISE0 + 2.4
SW_A0, SW_A1 = 90.0, 90.0 - 338.0                                       # 北 → 東 → 南 → 西 → ルカ
rm = random.Random(31); risers = []
for k, (ang, rad) in enumerate([(10, 5.6), (50, 5.2), (-30, 10.5), (-70, 5.4), (-110, 5.8), (-150, 5.6), (180, 6.0), (130, 7.0), (45, 10.5), (30, 8.8), (-120, 8.6)]):
    cx, cy = -0.4, 0.9
    x, y = cx + rad * math.cos(math.radians(ang)), cy + rad * math.sin(math.radians(ang))
    a = ang if ang <= 90 else ang - 360
    f = (90 - a) / 338.0
    risers.append(dict(o=mob_obj("riser%d" % k, rm.uniform(1.0, 1.6)), x0=x, y0=y, cx=cx, cy=cy, t0=SWEEP0 + f * (SWEEP1 - SWEEP0) - 0.25, ph=rm.uniform(0, 6.28)))
for r in risers: r["size"] = r["o"].scale[0]

# 破片
frag_m = M["shadow"]; spark_m = E("spark", (1.0, 0.25, 0.1), 10.0)
FR = []
def frags(t0, org, n, speed, up, size, m, life=1.6, seed=0):
    r = random.Random(seed)
    for _ in range(n):
        o = cube("frag", m, 1.0); o.visible_shadow = m is frag_m
        v = Vector((r.uniform(-1, 1), r.uniform(-1, 1), 0)).normalized() * r.uniform(0.3, 1.0) * speed + Vector((0, 0, up * r.uniform(0.6, 1.2)))
        FR.append(dict(o=o, t0=t0, p=Vector(org) + Vector((r.uniform(-.3, .3), r.uniform(-.3, .3), r.uniform(-.3, .3))), v=v,
                       s=size * r.uniform(0.5, 1.2), spin=Vector((r.uniform(-9, 9), r.uniform(-9, 9), r.uniform(-9, 9))), life=life, g=-12))
frags(CRACK, KP + Vector((0, 0, 0.7)), 16, 3.5, 4.0, 0.3, frag_m, 1.8, 1)
frags(CRACK, KP + Vector((0, 0, 0.7)), 10, 4.5, 4.0, 0.08, spark_m, 0.8, 2)
frags(REVEAL, KP + Vector((0, -0.3, 1.0)), 10, 1.8, 2.0, 0.08, frag_m, 1.4, 3)
frags(REVEAL, KP + Vector((0, -0.3, 1.0)), 8, 2.5, 2.0, 0.04, spark_m, 0.7, 4)
for k, r in enumerate(risers):
    frags(r["t0"] + 0.1, Vector((r["x0"], r["y0"], 0.2)), 5, 2.0, 4.0, 0.25, M["dirt"], 1.2, 10 + k)

# ---------------------------------------------------------------- 時間ごとの値
def blk_at(t):
    """影化（0〜1）。前回から指先はうっすら黒かった（気づいていないだけ）"""
    if t < BLACK1: return 0.10
    if t < BLACK1 + 0.6: return 0.10 + 0.13 * ease((t - BLACK1) / 0.6)
    if t < 50.4: return 0.23
    if t < 52.6: return 0.23 + 0.22 * (t - 50.4) / 2.2
    if t < BLAZE + 0.4: return 0.45
    if t < DARK - 0.2: return 0.45 + 0.54 * ((t - BLAZE - 0.4) / (DARK - 0.2 - BLAZE - 0.4)) ** 1.4
    return 0.99
def cast_at(t):
    c = win(t, 3.2, 9.4, 0.6, 0.6) * 0.8
    if 50.4 < t < 53.0: c = max(c, 0.9 * (0.5 + 0.5 * math.sin(t * 23)) * win(t, 50.4, 52.8, 0.2, 0.3))   # 迷い：光がちらつく
    c = max(c, 2.0 * ease((t - BLAZE - 0.3) / 1.0) * (1 - 0.85 * ease((t - DARK - 0.2) / 1.0)))
    return c
def ecl_at(t):
    """日食の進み（0〜1）と明るさ"""
    c = 0.0 if t < ECLIPSE0 else min(1.0, ((t - ECLIPSE0) / (DARK - ECLIPSE0)) ** 1.25)
    light = 1.0 - 0.92 * c ** 1.3
    if t >= DARK: light = 0.0
    elif t > DARK - 0.6: light *= 1 - ease((t - DARK + 0.6) / 0.6)
    return c, light

def path_hop(t):
    pts = [SHADOW_P.xy, Vector((5.0, 13.6)), Vector((2.6, 11.0)), Vector((0.5, 9.2)), Vector((0.5, 7.2)), KP.xy]
    segs = [(a, b, (b - a).length) for a, b in zip(pts, pts[1:])]
    tot = sum(s[2] for s in segs)
    n = 6; k = (t - APPROACH0) / (APPROACH1 - APPROACH0) * n
    if k <= 0: d = 0.0; ph = 0.0
    elif k >= n: d = tot; ph = 0.0
    else:
        i = int(k); f = k - i; d = tot * (i + ease(f)) / n; ph = math.sin(math.pi * f)
    for a, b, L_ in segs:
        if d <= L_: p = a.lerp(b, d / L_); break
        d -= L_
    else: p = pts[-1]
    g = hgt(int(math.floor(p.x)), int(math.floor(p.y)))
    return Vector((p.x, p.y, g + 0.7 + 0.9 * ph))

def kage_state(t):
    """人の形の位置・立ち上がり・腕"""
    p = KP.copy()
    if t > RISE0 + 0.4: p = KP.lerp(KB, ease((t - RISE0 - 0.4) / 2.0))
    st = 0.35 + 0.65 * ease((t - CRACK) / (STAND1 - CRACK))
    aL = 0.06 * math.sin(t * 1.1); aR = -0.06 * math.sin(t * 1.3)
    aR = aR + (-1.45 - aR) * win(t, POINT0 + 0.3, POINT1, 0.5, 0.6)
    aR = aR + (-1.1 - aR) * win(t, 29.0, 32.4, 0.5, 0.5)
    aR = aR + (-2.7 - aR) * win(t, 42.4, 45.4, 0.6, 0.6)
    pitch = 0.08 * win(t, 34.0, 37.8, 0.6, 0.6) - 0.12 * win(t, ECLIPSE0 + 0.4, 44.0, 0.6, 0.6)
    return p, st, aL, aR, pitch

def kage_head(t):
    p, st, *_ = kage_state(t); return p + Vector((0, 0, 1.62 * st))

def cam_state(t):
    """位置・見る先・ロール・レンズ"""
    pos = CAMP.copy(); roll = 0.0
    rk_face = Vector((RK.x, RK.y, 1.42))
    hands = lambda t: pos + Vector((0.0, 1.0, -1.25))
    def sweep(t):
        a = math.radians(SW_A0 + (SW_A1 - SW_A0) * ease((t - SWEEP0) / (SWEEP1 - SWEEP0)))
        return pos + Vector((math.cos(a), math.sin(a), -0.04)) * 6
    def cube_look(t):
        if t < CRACK: return path_hop(t) + Vector((0, 0, 0.2))
        return kage_head(t) - Vector((0, 0, 0.3))
    kh = lambda t: kage_head(t)
    chest = lambda t: kage_head(t) - Vector((0, 0, 0.55))
    sunl = lambda t: pos + SDIR * 30
    blaze = lambda t: pos + Vector((0, 6, 0.6))
    ruk = lambda t: rk_face
    SH = [(0.0, cube_look, 44), (1.6, cube_look, 34), (2.6, cube_look, 20), (7.8, ruk, 22), (9.6, cube_look, 20),
          (11.0, kh, 24), (15.0, kh, 30), (HANDS0, hands, 22), (22.3, ruk, 24), (24.9, hands, 22), (28.3, kh, 26),
          (CRACKS0 - 0.2, chest, 36), (35.6, kh, 30), (38.3, ruk, 24), (ECLIPSE0 - 0.1, sunl, 18), (43.6, kh, 22),
          (SWEEP0, sweep, 17), (SWEEP1, ruk, 20), (49.9, hands, 22), (53.3, ruk, 26), (BLAZE - 0.2, blaze, 17), (61.0, kh, 26)]
    i = max(j for j, s in enumerate(SH) if s[0] <= t)
    ts_, f1, l1 = SH[i]
    look = f1(t); lens = l1
    if i > 0:
        _, f0, l0 = SH[i - 1]
        du = 0.0 if f1 is sweep or f0 is sweep and False else 0.45
        if f0 is sweep: du = 0.6
        if du > 0:
            k = ease((t - ts_) / du); look = f0(t).lerp(f1(t), k); lens = l0 + (l1 - l0) * k
    if i == 1: lens = 44 + (34 - 44) * ease((t - 1.6) / 1.0)
    # 揺れ
    sh = 0.0
    for a, amp, d in ((CRACK, 0.06, 0.7), (BLACK1, 0.02, 0.4), (REVEAL, 0.04, 0.5), (ECLIPSE0, 0.03, 2.5), (DARK, 0.12, 1.2)):
        if a <= t < a + d: sh = max(sh, amp * (1 - (t - a) / d))
    if RISE0 <= t < SWEEP1 + 0.4: sh = max(sh, 0.02)
    if BLAZE <= t < DARK: sh = max(sh, 0.01 + 0.04 * (t - BLAZE) / (DARK - BLAZE))
    if t >= DARK: roll = 0.12 * ease((t - DARK) / 0.8)
    pos = pos + Vector((sh * math.sin(t * 47), sh * math.sin(t * 39), sh * math.sin(t * 53)))
    pos += Vector((0.006 * math.sin(t * 1.7), 0, 0.006 * math.sin(t * 2.3)))
    return pos, look, roll, lens

def arms_at(t, cast):
    out = {}
    hshot = lambda a, b: win(t, a, b, 0.5, 0.45)
    look_hands = max(hshot(HANDS0, 22.3), hshot(24.9, 28.3), hshot(49.9, 53.3))
    for s, sx in (("L", -1), ("R", 1)):
        sh = Vector((0.22 * sx, -0.55, 0.05)); el = Vector((0.25 * sx, -0.44, -0.24)); hn = Vector((0.15 * sx, -0.34 + 0.01 * math.sin(t * 1.3), -0.44))
        a = min(1, cast)
        hn = hn.lerp(Vector((0.11 * sx, -0.16, -0.42)), a); el = el.lerp(Vector((0.2 * sx, -0.32, -0.28)), a)
        if look_hands > 0:                                                  # 自分の手を見る（ふるえる）
            tr = 0.004 * math.sin(t * 31 + sx) * (1 + 2 * (t > BLACK1))
            hn = hn.lerp(Vector((0.115 * sx + tr, -0.07, -0.36)), look_hands); el = el.lerp(Vector((0.27 * sx, -0.32, -0.16)), look_hands)
        bz = ease((t - BLAZE - 0.2) / 0.8)
        if bz > 0:                                                          # 使ってしまう：両手を前へ突き出す
            tr = 0.012 * math.sin(t * 37 + sx * 2)
            hn = hn.lerp(Vector((0.13 * sx + tr, -0.04 + tr, -0.5)), bz); el = el.lerp(Vector((0.22 * sx, -0.28, -0.3)), bz)
        out[s] = (sh, el, hn)
    return out

# ---------------------------------------------------------------- 1コマ分を置く
def place(t):
    pos, look, roll, lens = cam_state(t)
    cam.location = pos; W.aim(cam, look); cam.rotation_euler.rotate_axis("Z", roll)
    cam.data.lens = lens; cam.data.dof.focus_distance = max(0.3, min(40.0, (look - pos).length))
    cast = cast_at(t); blk = blk_at(t)
    for s, (sh, el, hn) in arms_at(t, cast).items(): set_arm(s, sh, el, hn)
    for k in HV:
        HV[k]["cast"].default_value = cast; HV[k]["blk"].default_value = 0.05 + 1.0 * blk
        HV[k]["red"].default_value = 2.0 + 4.0 * max(0.0, blk - 0.4) + (3.0 if t >= DARK else 0.0)
    hcol = Vector((0.45, 0.85, 1.0)).lerp(Vector((1.0, 0.1, 0.12)), ease((blk - 0.3) / 0.6))
    hl.color = tuple(hcol); hl.energy = 6.0 * cast + (6.0 if t >= DARK else 0.0) + (60.0 * math.exp(-((t - DARK) / 0.3) ** 2) if t > DARK - 1 else 0)
    # 空：朝 → 日食
    c, light = ecl_at(t)
    wmix.inputs["Factor"].default_value = light
    wsk.inputs["B"].default_value = (0.3 * light + 0.02,) * 3 + (1,)
    bg.inputs["Strength"].default_value = 1.0 if t < DARK else 0.5
    off = Vector((1.0, 0.0, 0.0)) * (1.0 - c) * 48.0 + Vector((0, 0, 1.0)) * (1.0 - c) * 14.0
    disc.location = SDIR * 480 + off; disc.hide_render = c <= 0.0
    corona.hide_render = c < 0.96; corona.scale = (52 * (0.7 + 0.3 * ease((c - 0.96) / 0.04)),) * 2 + (1,)
    corona.scale = (corona.scale[0], 1, corona.scale[0])
    sun_m.node_tree.nodes  # （太陽の明るさは材質のまま）
    sl.energy = 3.6 * light; fl.energy = 0.9 * light
    for s in stars: s.hide_render = light > 0.12
    fogcol = Vector((0.06, 0.015, 0.045)).lerp(Vector((0.42, 0.4, 0.42)), light)
    if t >= DARK: fogcol = Vector((0.01, 0.005, 0.012))
    FOG.nodes["fogcol"].inputs["Color"].default_value = (*fogcol, 1); FOG.nodes["fogcol"].inputs["Strength"].default_value = 1.0
    FOG.nodes["dens"].outputs[0].default_value = 0.004 + 0.014 * (1 - light)
    for n in face_em: n.inputs["Strength"].default_value = 0.25 + 0.75 * light + 0.3 * min(1, cast)
    # ルカ
    to_me = Vector((pos.x - RK.x, pos.y - RK.y, 0))
    if to_me.length > 0.01:
        to_me.normalize(); ruka.rotation_euler = (0, 0, math.atan2(-to_me.x, to_me.y))
    if ECLIPSE0 + 0.3 < t < 44.0 or (CRACK < t < 11.6): ruka.rotation_euler = (0, 0, math.radians(-10))   # 空・影の方を見る
    RSP = [(l[0], l[1]) for l in LINES if l[5] == "ruka"]
    talking = any(st <= t <= en - 0.05 for st, en in RSP); flap = talking and (int(t * FPS) % 3 != 2)
    if t < 3.2: e = "talk" if flap else "shockc"
    elif t < 21.6: e = "talk" if flap else ("shock" if t > CRACK else "shockc")
    elif t < 24.8: e = "talk" if flap else "shock"
    elif t < 38.2: e = "sad" if t < REVEAL else "shockc"
    elif t < 41.2: e = "talk" if flap else "shock"
    elif t < 49.8: e = "talk" if flap else "shock"
    else: e = "tearsadtalk" if flap else "tearsad"
    if (t % 3.3) < 0.17 and not talking and e in ("sad",): e = "sadblink"
    T.set_expr(rtex, "mei", e)
    # 消えない影：跳ねて近づく（ブロック）→ 割れて人の形
    cube_vis = t < CRACK
    last.hide_render = not cube_vis
    for ch in last.children: ch.hide_render = not cube_vis
    if cube_vis:
        p = path_hop(t)
        if APPROACH1 < t < CRACK: p = p + Vector((0.03 * math.sin(t * 40), 0, 0)) * ease((t - APPROACH1) / 2.0)
        last.location = p; last.rotation_euler = (0, 0, math.atan2(pos.x - p.x, -(pos.y - p.y)))
    kvis = t >= CRACK
    for o in KPARTS: o.hide_render = not kvis
    if kvis:
        p, st, aL, aR, pitch = kage_state(t)
        kage.location = p; kage.scale = (U, U, U * st)
        kage.rotation_euler = (pitch, 0, math.atan2(pos.x - p.x, -(pos.y - p.y)))
        karms[0].rotation_euler = (aL, 0, 0); karms[1].rotation_euler = (aR, 0, 0)
        kchest.hide_render = t >= REVEAL
        khoodie.hide_render = t < REVEAL
        for o in kstrs: o.hide_render = t < REVEAL
        for i, cr in enumerate(kcracks):
            g = ease((t - CRACKS0 - 0.18 * i) / 0.25)
            cr.hide_render = g <= 0; cr.scale = (0.18, 0.1, max(1e-3, cr.scale[2] if False else [2.6, 2.2, 1.6, 1.4][i] * g))
    # 地面から湧く影ブロック
    for r in risers:
        o = r["o"]; k = ease((t - r["t0"]) / 0.7); vis = t >= r["t0"]
        o.hide_render = not vis
        for ch in o.children: ch.hide_render = not vis
        if not vis: continue
        d = Vector((r["x0"] - r["cx"], r["y0"] - r["cy"])); L0 = d.length
        rad = max(3.4, L0 - 0.16 * max(0.0, t - r["t0"] - 0.8))
        d = d.normalized() * rad; x, y = r["cx"] + d.x, r["cy"] + d.y
        hop = abs(math.sin(t * 3.0 + r["ph"])) * 0.4 * ease((t - r["t0"] - 0.8) / 0.4)
        z = hgt(int(math.floor(x)), int(math.floor(y))) - r["size"] / 2 - 0.1 + (r["size"] + 0.1) * k + hop
        o.location = (x, y, z); o.rotation_euler = (0, 0, math.atan2(pos.x - x, -(pos.y - y)))
    # 破片
    for f in FR:
        dt = t - f["t0"]; o = f["o"]
        if dt < 0 or dt > f["life"]: o.hide_render = True; continue
        o.hide_render = False
        p = f["p"] + f["v"] * dt + Vector((0, 0, 0.5 * f["g"] * dt * dt))
        if p.z < 0.1: p.z = 0.1
        o.location = p; o.rotation_euler = tuple(f["spin"] * dt)
        s = f["s"] * (1 - max(0, dt - f["life"] * 0.6) / (f["life"] * 0.4)); o.scale = (max(s, 1e-3),) * 3

HIDE = [x for x in arg("--hide", "").split(",") if x]
frames = TEST or range(START, STOP)
t0 = time.time()
for f in frames:
    p = os.path.join(OUT, "%04d.png" % (f + 1))
    if os.path.exists(p) and not TEST: continue
    t = f / FPS
    place(t)
    for o in bpy.data.objects:
        if any(o.name.startswith(h) for h in HIDE): o.hide_render = True
    tmp = p[:-4] + "_tmp.png"; sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True); os.replace(tmp, p)
    print("frame %s t=%.2f %.1fs" % (p, t, time.time() - t0), flush=True); t0 = time.time()
