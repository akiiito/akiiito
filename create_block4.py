"""
create_block4.py ― ブロック世界パート4『影になった手』（高画質・12fps・縦1画面）
  皆既日食の闇 → 両手を地面へ＝黒い柱の輪が突き出して影ブロックを吹き飛ばす → 影化100%・腕が勝手にルカへ
  → ルカが手を握る（金色の光で黒が引く）→ 日食が明ける → 「光の器」 → 前の召喚者が光に溶ける
  → 地平線に塔がせり上がる → ルカの指先が黒い
  python create_block4.py [--samples 16] [--start 0] [--end 768] [--test 0,140,...]
"""
import os, sys, math, json, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, Euler
import s2_world as W, s3_toon as T, s7_world as S7
from blk4_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "20")); FPS = 12; N = int(END * FPS)
START = int(arg("--start", "0")); STOP = int(arg("--end", str(N)))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_BLK4" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
LINES = json.load(open(os.path.join(HERE, "blk4_lines.json"), encoding="utf-8"))
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
SUN_EL = 38.0
try: sky.sun_rotation = math.radians(180); sky.air_density = 1.2; sky.aerosol_density = 2.0; sky.sun_size = math.radians(3.0); sky.sun_elevation = math.radians(SUN_EL)
except Exception: pass
wmix = wn.nodes.new("ShaderNodeMix"); wmix.data_type = "RGBA"
wsk = wn.nodes.new("ShaderNodeMix"); wsk.data_type = "RGBA"; wsk.blend_type = "MULTIPLY"; wsk.inputs["Factor"].default_value = 1.0
wn.links.new(sky.outputs["Color"], wsk.inputs["A"]); wsk.inputs["B"].default_value = (0.5, 0.5, 0.5, 1)
wn.links.new(nramp.outputs["Color"], wmix.inputs["A"]); wn.links.new(wsk.outputs["Result"], wmix.inputs["B"])
wn.links.new(wmix.outputs["Result"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 1.0
SDIR = Vector((-0.05, math.cos(math.radians(SUN_EL)), math.sin(math.radians(SUN_EL)))).normalized()
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
RC = Vector((-0.4, 0.9, 0))                                          # 柱の輪の中心（パート3で影ブロックが囲んだ中心）
for (x, y) in [(-2.5, 4.5), (2.0, 4.6), (-3.2, -1.5), (3.3, -1.0), (7.5, -3.6)]:
    if 2.6 < math.hypot(x - RC.x, y - RC.y) < 4.8: continue
    st = cube("tstick", stick_m, 1.0); st.scale = (0.12, 0.12, 0.8); st.location = (x, y, 0.4)

# ---------------------------------------------------------------- ルカ（腕をおろした姿／両手を前に出した姿）
RK = Vector((-1.15, 2.6, 0))
CAMP = Vector((0.3, -0.9, 1.62))
_d = (RK.xy - CAMP.xy).normalized()
RG = Vector((CAMP.x + _d.x * 0.62, CAMP.y + _d.y * 0.62, 0))           # 目の前（手を握る）
RS = Vector((-1.0, 1.0, 0))                                           # 少し離れた横
RCOL = {"blazer": (0.36, 0.56, 0.42), "skirt": (0.52, 0.38, 0.26), "sock": (0.4, 0.28, 0.2)}
face_em = []
def ruka_pbr(root):
    for o in [root] + list(root.children_recursive):
        if o.type != "MESH": continue
        for i, m in enumerate(o.data.materials):
            if not (m and m.node_tree): continue
            if "facemat" in m.name:
                face_em.extend(n for n in m.node_tree.nodes if n.type == "EMISSION"); continue
            rp = [n for n in m.node_tree.nodes if n.type == "VALTORGB"]
            if rp:
                key = m.name.split("_")[-1]
                c = RCOL.get(key) or tuple(x ** 0.4545 for x in rp[0].color_ramp.elements[1].color[:3])
                lin = tuple(x ** 2.2 for x in c)
                sk = "skin" in m.name
                nm = W.mat(m.name + "_pbr", lin, 0.55 if sk else 0.75, sss=0.2 if sk else 0.0)
                o.data.materials[i] = fogify(nm)
ruka, rtex = T.girl("ruka", tuple(RK), rot=200, hair=(0.3, 0.2, 0.16), face="mei", ponytail=True)
RH_L = (0.1, 0.28, 1.1); RH_R = (-0.1, 0.28, 1.1)
rukar, rtex2 = T.girl("rukar", tuple(RG), rot=0, hair=(0.3, 0.2, 0.16), face="mei", ponytail=True,
                      arms={"L": ((0.17, 0.12, 1.08), RH_L), "R": ((-0.17, 0.12, 1.08), RH_R)})
ruka_pbr(ruka); ruka_pbr(rukar)
for o in rukar.children_recursive:
    if o.name.startswith("rukar_hand"): o.hide_render = True; o.name = "rukar_sphere_hidden"

# ---------------------------------------------------------------- 自分の腕（パーカー）と、ブロックの手（影化）／ルカのブロックの手
cam = W.camera(tuple(CAMP), (0, 10, 1.5), lens=17, fstop=5.6)
hood = P("me_hood", (0.28, 0.29, 0.32), 0.9, noise=(40.0, 0.12))
def piece(name, r, m):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=1.0); o = bpy.context.object; o.name = name
    o.data.materials.append(m); bpy.ops.object.shade_smooth(); o.parent = cam; return o
HV = {}
def hand_mat(name, hand_empty, ecol=(0.2, 0.7, 1.0)):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; Lk = nt.links.new
    out = N["Material Output"]; skn = N["Principled BSDF"]
    skn.inputs["Roughness"].default_value = 0.55; skn.inputs["Subsurface Weight"].default_value = 0.15
    skn.inputs["Emission Color"].default_value = ecol + (1,)
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
    drk.inputs["Roughness"].default_value = 0.4; drk.inputs["Specular IOR Level"].default_value = 0.2
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
def hand_build(s, parent=None, ecol=(0.2, 0.7, 1.0), k=1.0, prefix="hand"):
    """手首を原点、指先 +Y、手の甲 +Z のブロックの手"""
    h = bpy.data.objects.new(prefix + s, None); bpy.context.collection.objects.link(h); h.parent = parent
    m = hand_mat(prefix + "m" + s, h, ecol); sx = 1 if s == "R" else -1
    def bx(nm, c, sz, rot=(0, 0, 0)):
        o = cube(nm, m, 1.0); o.scale = tuple(v * k for v in sz); o.location = tuple(v * k for v in c); o.rotation_euler = rot; o.parent = h; return o
    bx(prefix + "palm" + s, (0, 0.04, 0), (0.08, 0.08, 0.03))
    for j in range(4):
        x = -0.03 + 0.02 * j
        bx("%sfing%s%d" % (prefix, s, j), (x, 0.1 - 0.004 * abs(j - 1.5), -0.004), (0.017, 0.048 - 0.006 * abs(j - 1.5), 0.019), (-0.25, 0, 0))
    bx(prefix + "thumb" + s, (-0.05 * sx, 0.045, -0.006), (0.018, 0.045, 0.02), (0, 0, 0.5 * sx))
    return h, m
ARMS = {}
for s in "LR":
    hh, hm = hand_build(s, cam)
    ARMS[s] = dict(up=piece("up" + s, 0.055, hood), lo=piece("lo" + s, 0.05, hood), hd=hh, m=hm.name)
RHANDS = {}
for s in "LR":
    hh, hm = hand_build(s, None, ecol=(1.0, 0.72, 0.3), k=0.88, prefix="rh")
    RHANDS[s] = dict(hd=hh, m=hm.name)
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
hl = bpy.data.lights.new("handglow", "POINT"); hl.color = (1.0, 0.1, 0.12); hl.shadow_soft_size = 0.2
hlo = bpy.data.objects.new("handglow", hl); bpy.context.collection.objects.link(hlo); hlo.parent = cam; hlo.location = (0.0, -0.1, -0.8)
nf_ = bpy.data.lights.new("nightfill", "POINT"); nf_.color = (0.75, 0.7, 1.0); nf_.shadow_soft_size = 1.5
nfo = bpy.data.objects.new("nightfill", nf_); bpy.context.collection.objects.link(nfo); nfo.parent = cam; nfo.location = (0.4, 0.6, 0.6)
gl = bpy.data.lights.new("rukaglow", "POINT"); gl.color = (1.0, 0.75, 0.4); gl.shadow_soft_size = 0.15
glo = bpy.data.objects.new("rukaglow", gl); bpy.context.collection.objects.link(glo)
rl = bpy.data.lights.new("ringred", "POINT"); rl.color = (1.0, 0.12, 0.1); rl.shadow_soft_size = 1.0
rlo = bpy.data.objects.new("ringred", rl); bpy.context.collection.objects.link(rlo); rlo.location = (RC.x, RC.y, 1.2)

# ---------------------------------------------------------------- 影ブロック・前の召喚者（光で下から溶ける）
eye_m = E("eye", (1.0, 0.08, 0.06), 5.0); pupil_m = E("pupil", (0.02, 0.0, 0.0), 0.5)
def mob_obj(name, size):
    b = cube(name, M["shadow"], 1.0); b.scale = (size,) * 3
    e = cube(name + "_eye", eye_m, 1.0); e.parent = b; e.location = (0, -0.5, 0.12); e.scale = (0.42, 0.04, 0.42); e.visible_shadow = False
    p = cube(name + "_pu", pupil_m, 1.0); p.parent = b; p.location = (0, -0.52, 0.12); p.scale = (0.1, 0.04, 0.28); p.visible_shadow = False
    return b
KB = Vector((1.6, 6.6, 0)); U = 0.115
DCUT = []                                                            # 溶ける高さ（ワールドZ）
def dissolve(m):
    """材質の出力に「Z < cut は透明、境目は金色に光る」を足す"""
    nt = m.node_tree; N = nt.nodes; Lk = nt.links.new
    out = [n for n in N if n.type == "OUTPUT_MATERIAL"][0]
    src = out.inputs["Surface"].links[0].from_socket
    geo = N.new("ShaderNodeNewGeometry"); sz = N.new("ShaderNodeSeparateXYZ"); Lk(geo.outputs["Position"], sz.inputs[0])
    cut = N.new("ShaderNodeValue"); cut.outputs[0].default_value = -10.0; DCUT.append(cut.outputs[0])
    lt = N.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; Lk(sz.outputs["Z"], lt.inputs[0]); Lk(cut.outputs[0], lt.inputs[1])
    add = N.new("ShaderNodeMath"); add.operation = "ADD"; add.inputs[1].default_value = 0.07; Lk(cut.outputs[0], add.inputs[0])
    lt2 = N.new("ShaderNodeMath"); lt2.operation = "LESS_THAN"; Lk(sz.outputs["Z"], lt2.inputs[0]); Lk(add.outputs[0], lt2.inputs[1])
    band = N.new("ShaderNodeMath"); band.operation = "SUBTRACT"; Lk(lt2.outputs[0], band.inputs[0]); Lk(lt.outputs[0], band.inputs[1])
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.75, 0.35, 1); em.inputs["Strength"].default_value = 12.0
    m1 = N.new("ShaderNodeMixShader"); Lk(band.outputs[0], m1.inputs[0]); Lk(src, m1.inputs[1]); Lk(em.outputs[0], m1.inputs[2])
    tr = N.new("ShaderNodeBsdfTransparent")
    m2 = N.new("ShaderNodeMixShader"); Lk(lt.outputs[0], m2.inputs[0]); Lk(m1.outputs[0], m2.inputs[1]); Lk(tr.outputs[0], m2.inputs[2])
    Lk(m2.outputs[0], out.inputs["Surface"])
    try: m.surface_render_method = "DITHERED"
    except Exception: pass
    return m
def kage_mat():
    m = bpy.data.materials.new("kage_m"); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; Lk = nt.links.new; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); scl = N.new("ShaderNodeVectorMath"); scl.operation = "SCALE"; scl.inputs["Scale"].default_value = 3.0
    snp = N.new("ShaderNodeVectorMath"); snp.operation = "SNAP"; snp.inputs[1].default_value = (1, 1, 1)
    wnz = N.new("ShaderNodeTexWhiteNoise"); wnz.noise_dimensions = "3D"
    Lk(tc.outputs["Object"], scl.inputs[0]); Lk(scl.outputs[0], snp.inputs[0]); Lk(snp.outputs[0], wnz.inputs["Vector"])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.inputs["A"].default_value = (0.0012, 0.0008, 0.0016, 1); mx.inputs["B"].default_value = (0.006, 0.002, 0.006, 1)
    Lk(wnz.outputs["Value"], mx.inputs["Factor"]); Lk(mx.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.8; b.inputs["Specular IOR Level"].default_value = 0.02
    return dissolve(fogify(m))
KM = kage_mat()
khood = dissolve(P("k_hood", (0.28, 0.29, 0.32), 0.9, noise=(40.0, 0.12)))
keye_m = dissolve(E("keye", (1.0, 0.08, 0.06), 5.0))
kstr_m = dissolve(P("strings", (0.85, 0.85, 0.82), 0.6)); kzip_m = dissolve(P("zip", (0.5, 0.5, 0.52), 0.3))
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
    for z in range(12, 16):
        for y in (-1, 0, 1): c[(-3, y, z)] = "s"; c[(2, y, z)] = "s"
        for x in (-2, -1, 0, 1): c[(x, 2, z)] = "s"
    for x in (-2, -1, 0, 1):
        for y in (-1, 0, 1): c[(x, y, 16)] = "s"
    body = S7.voxel_mesh("kage_body", c, [KM], {"s": (0, 0, 0)}); body.parent = root
    hoodie = S7.voxel_mesh("kage_hoodie", {(x, -2, z): "h" for x in (-2, -1, 0, 1) for z in range(7, 11)}, [khood], {"h": (0, 0, 0)}); hoodie.parent = root
    hoodie.scale = (0.98, 1, 0.98); hoodie.location = (-0.02, 0.05, 0.15)
    strs = []
    for x in (-0.7, 0.7):
        st = cube("kage_str", kstr_m, 1.0); st.parent = root; st.location = (x, -2.1, 9.6); st.scale = (0.18, 0.12, 1.6); strs.append(st)
    zp = cube("kage_zip", kzip_m, 1.0); zp.parent = root; zp.location = (0, -2.06, 8.5); zp.scale = (0.12, 0.1, 3.0); strs.append(zp)
    for x in (-0.9, 0.9):
        e = cube("kage_eye", keye_m, 1.0); e.parent = root; e.location = (x, -2.06, 13.8); e.scale = (0.6, 0.12, 0.38); e.visible_shadow = False
    for (x, z, r, ln) in ((-1.2, 9.0, 0.5, 2.6), (0.9, 8.4, -0.6, 2.2), (-0.2, 10.2, 1.3, 1.6), (0.4, 7.4, 0.2, 1.4)):
        cr = cube("kage_cr", keye_m, 1.0); cr.parent = root; cr.location = (x, -2.12, z); cr.scale = (0.18, 0.1, ln); cr.rotation_euler = (0, r, 0)
        cr.visible_shadow = False
    arms = []
    for sx in (-1, 1):
        piv = bpy.data.objects.new("kage_sh", None); bpy.context.collection.objects.link(piv); piv.parent = root
        piv.location = (-2.5 if sx < 0 else 2.5, -0.5, 11.5)
        am = S7.voxel_mesh("kage_arm", {(0, y, -z): "s" for y in (-1, 0) for z in range(1, 8)}, [KM], {"s": (0, 0, 0)})
        am.parent = piv; am.location = (-0.5, 0.5, 0.5); arms.append(piv)
    return root, arms
kage, karms = kage_build()
kage.location = KB

# ---------------------------------------------------------------- 囲んでいた影ブロック（パート3の最後の位置）
risers = []
rm = random.Random(31)
for k, (ang, rad) in enumerate([(10, 5.6), (50, 5.2), (-30, 10.5), (-70, 5.4), (-110, 5.8), (-150, 5.6), (180, 6.0), (130, 7.0), (45, 10.5), (30, 8.8), (-120, 8.6)]):
    a = math.radians(ang); sz = rm.uniform(1.0, 1.6)
    p = Vector((RC.x + 3.5 * math.cos(a), RC.y + 3.5 * math.sin(a), sz / 2))
    risers.append(dict(o=mob_obj("riser%d" % k, sz), p=p, size=sz, ph=rm.uniform(0, 6.28), ang=a,
                       tl=BURST + 0.05 + 0.03 * k, v=Vector((math.cos(a) * 2.5, math.sin(a) * 2.5, 8.5 + rm.uniform(-1, 1.5))),
                       spin=Vector((rm.uniform(-8, 8), rm.uniform(-8, 8), rm.uniform(-8, 8)))))
POP = 0.62                                                               # 打ち上げから砕けるまで

# ---------------------------------------------------------------- 黒い柱の輪（ブロック変形・全開）
GAP = math.radians(79.0)                                                 # 影（前の召喚者）と塔が見える切れ目
pillars = []
rp = random.Random(44)
for x in range(-6, 6):
    for y in range(-4, 7):
        cx, cy = x + 0.5, y + 0.5; d = math.hypot(cx - RC.x, cy - RC.y)
        if not (3.0 <= d <= 4.4): continue
        a = math.atan2(cy - RC.y, cx - RC.x)
        da = abs((a - GAP + math.pi) % (2 * math.pi) - math.pi)
        if da < math.radians(15): continue
        h = rp.choice((2, 3, 3, 4, 4, 5)) if da > math.radians(34) else rp.choice((1, 2))
        o = S7.voxel_mesh("pillar", {(0, 0, k): "b" for k in range(h)}, [M["shadow"]], {"b": (0, 0, 0)})
        pillars.append(dict(o=o, x=x, y=y, h=h, t0=BURST + 0.02 + 0.012 * (d - 3.0) / 1.4 * 10 + rp.uniform(0, 0.06)))

# ---------------------------------------------------------------- 塔（地平線にせり上がる）
TW = Vector((0.3, 66.0, 0)); TH = 52
tw_cells = {}
for z in range(TH):
    w = 4 if z < 34 else (3 if z < 44 else 2)
    if z % 9 == 8: w += 1
    for x in range(-w, w + 1):
        for y in range(-w, w + 1):
            if max(abs(x), abs(y)) == w or z % 9 == 8 or z == TH - 1: tw_cells[(x, y, z)] = "b"
tw_m = P("towerm", (0.012, 0.009, 0.014), 0.7); tw_m.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.05
tower = S7.voxel_mesh("tower", tw_cells, [tw_m], {"b": (0, 0, 0)})
win_m = E("towerwin", (1.0, 0.1, 0.08), 14.0); tw_parts = []
rw = random.Random(5)
for z in range(3, TH - 4, 3):
    w = 4 if z < 34 else (3 if z < 44 else 2)
    for _ in range(2):
        if rw.random() < 0.55:
            o = cube("twin", win_m, 1.0); o.scale = (0.7, 0.3, 1.2); o.parent = tower
            o.location = (rw.randint(-w + 1, w - 1) + 0.5, -w - 0.05, z + 0.6); o.visible_shadow = False; tw_parts.append(o)
crown = cube("crown", win_m, 1.0); crown.scale = (3.0, 3.0, 3.0); crown.parent = tower; crown.location = (0.5, 0.5, TH + 5); tw_parts.append(crown)
TBASE = hgt(int(TW.x), int(TW.y))

# ---------------------------------------------------------------- 破片・光の粒
frag_m = M["shadow"]; spark_m = E("spark", (1.0, 0.25, 0.1), 10.0); mote_m = E("mote", (1.0, 0.8, 0.45), 9.0)
FR = []
def frags(t0, org, n, speed, up, size, m, life=1.6, seed=0, g=-12):
    r = random.Random(seed)
    for _ in range(n):
        o = cube("frag", m, 1.0); o.visible_shadow = m is frag_m
        v = Vector((r.uniform(-1, 1), r.uniform(-1, 1), 0)).normalized() * r.uniform(0.3, 1.0) * speed + Vector((0, 0, up * r.uniform(0.6, 1.2)))
        FR.append(dict(o=o, t0=t0, p=Vector(org) + Vector((r.uniform(-.3, .3), r.uniform(-.3, .3), r.uniform(-.3, .3))), v=v,
                       s=size * r.uniform(0.5, 1.2), spin=Vector((r.uniform(-9, 9), r.uniform(-9, 9), r.uniform(-9, 9))), life=life, g=g))
for k, r in enumerate(risers):
    pp = r["p"] + r["v"] * POP + Vector((0, 0, -6 * POP * POP))
    frags(r["tl"] + POP, pp, 9, 4.0, 2.0, 0.3 * r["size"], frag_m, 1.6, 100 + k)
    frags(r["tl"] + POP, pp, 6, 5.0, 2.0, 0.07, spark_m, 0.8, 200 + k)
for k in range(10):                                                      # 柱が突き出す土
    a = 2 * math.pi * k / 10
    frags(BURST + 0.05, RC + Vector((3.7 * math.cos(a), 3.7 * math.sin(a), 0.2)), 4, 2.5, 4.0, 0.22, M["dirt"], 1.2, 300 + k)
for k in range(6):                                                       # 塔の土けむり
    frags(TOWER0 + 0.4 * k, TW + Vector((0, 0, TBASE + 1)), 6, 8.0, 6.0, 1.6, M["dirt"], 2.6, 400 + k, g=-6)
rmo = random.Random(77)
for k in range(46):                                                      # 前の召喚者から立ちのぼる光の粒
    t0 = SUN1 + 1.0 + (DIS1 - SUN1 - 1.0) * (k / 46) ** 0.6 + rmo.uniform(-0.3, 0.3)
    org = KB + Vector((rmo.uniform(-0.25, 0.25), rmo.uniform(-0.2, 0.2), rmo.uniform(0.1, 1.7)))
    o = cube("mote", mote_m, 1.0); o.visible_shadow = False
    FR.append(dict(o=o, t0=t0, p=org, v=Vector((rmo.uniform(-0.15, 0.15), rmo.uniform(-0.15, 0.15), rmo.uniform(0.5, 0.9))),
                   s=rmo.uniform(0.025, 0.05), spin=Vector((1, 2, 3)), life=2.2, g=0.0))

SHMR = [n for n in M["shadow"].node_tree.nodes if n.type == "MAP_RANGE"][0]
# ---------------------------------------------------------------- 時間ごとの値
def blk_at(t):
    if t < FULL - 0.3: return 0.99
    if t < GLOW0: return 1.06
    if t < GLOW1: return 1.06 - 0.44 * ((t - GLOW0) / (GLOW1 - GLOW0)) ** 0.8
    return 0.62
def cast_at(t):
    """自分の手の光（赤）"""
    c = 1.2 + 0.4 * math.sin(t * 9)
    c += 3.0 * math.exp(-max(0.0, t - BURST) / 0.5) * (t >= BURST - 0.3)
    c *= 1 - 0.8 * ease((t - GRAB) / 1.5)
    return c
def rglow_at(t):
    """ルカの手の光（金）"""
    g = ease((t - GLOW0 + 0.6) / 1.2) * (1 - ease((t - 25.0) / 1.5))
    g += 0.25 * ease((t - 56.0) / 1.0) * (1 - ease((t - TIP) / 0.8))
    return g
def ecl_at(t):
    if t < SUN0: return 1.0, 0.07
    k = ease((t - SUN0) / (SUN1 - SUN0))
    return 1.0 - k, 0.07 + 0.93 * k ** 1.5

RUKA_POS = [(0.0, "down", RK), (16.0, "reach", RG), (26.5, "down", RS), (52.6, "reach", RG)]
def ruka_where(t):
    return [r for r in RUKA_POS if r[0] <= t][-1]

def cam_matrix(pos, look, roll):
    q = (look - pos).to_track_quat("-Z", "Y"); e = q.to_euler(); m = e.to_matrix()
    m = m @ Matrix.Rotation(roll, 3, "Z")
    return Matrix.Translation(pos) @ m.to_4x4()

def rhand_world(s):
    """ルカ（前に出した手）の手首の位置（ワールド）"""
    rot = rukar.rotation_euler.z; loc = Vector(RH_L if s == "L" else RH_R) - Vector((0, 0.0, 0.02))
    return rukar.location + Matrix.Rotation(rot, 3, "Z") @ loc

def cam_state(t):
    pos = CAMP.copy(); roll = 0.0
    hands = lambda t: pos + Vector((0.0, 1.0, -1.25))
    ahead = lambda t: pos + Vector((-0.5, 6.0, -0.4))
    burst = lambda t: pos + Vector((-0.4, 6.0, -0.7 + 1.6 * ease((t - BURST - 0.3) / 1.0)))
    upsky = lambda t: pos + Vector((0.2, 4.0, 3.2))
    rk = lambda t: Vector((RK.x, RK.y, 1.42))
    rkm = lambda t: Vector((RK.x, RK.y, 1.15))
    rface = lambda t: (lambda w: Vector((w[2].x, w[2].y, 1.40)))(ruka_where(t))
    kh = lambda t: KB + Vector((0, 0, 1.45))
    kbody = lambda t: KB + Vector((0, 0, 1.0))
    grab = lambda t: (rhand_world("L") + rhand_world("R")) / 2 + Vector((0, 0, 0.18))
    tip = lambda t: rhand_world("L" if TIPS == "L" else "R") + (pos - rhand_world("L")).normalized() * -0.05
    sunl = lambda t: pos + SDIR * 30
    towr = lambda t: TW + Vector((0, 0, TBASE + 26 - 30 * (1 - ease((t - TOWER0) / (TOWER1 - TOWER0)))))
    SH = [(0.0, hands, 20), (1.4, ahead, 18), (BURST - 0.3, burst, 15), (4.7, upsky, 17), (5.6, rk, 24), (8.2, kh, 26),
          (10.0, hands, 20), (12.6, rkm, 22), (15.2, kh, 32), (17.2, grab, 20), (18.3, rface, 22), (20.2, grab, 20),
          (25.4, kh, 28), (28.8, sunl, 18), (33.4, kh, 26), (37.8, rface, 26), (41.0, kh, 28), (44.4, kbody, 22),
          (50.6, towr, 24), (55.0, rface, 22), (58.0, grab, 20), (59.6, tip, 20), (62.0, rface, 24)]
    i = max(j for j, s in enumerate(SH) if s[0] <= t)
    ts_, f1, l1 = SH[i]; look = f1(t); lens = l1
    if i > 0:
        _, f0, l0 = SH[i - 1]
        du = 0.45 if f1 not in (burst,) else 0.25
        if f1 is tip: du = 1.4
        k = ease((t - ts_) / du); look = f0(t).lerp(f1(t), k); lens = l0 + (l1 - l0) * k
    if f1 is tip: lens = 20 + 18 * ease((t - 59.8) / 1.6)
    if f1 is towr: lens = 24 + 6 * ease((t - TOWER0) / 4.0)
    sh = 0.0
    for a, amp, d in ((BURST, 0.14, 1.4), (FULL, 0.05, 1.0), (TOWER0, 0.05, 3.6), (TIP + 1.4, 0.02, 0.5)):
        if a <= t < a + d: sh = max(sh, amp * (1 - (t - a) / d))
    if t < BURST: sh = max(sh, 0.006 + 0.01 * t / BURST)
    if FULL <= t < GRAB: sh = max(sh, 0.012)
    pos = pos + Vector((sh * math.sin(t * 47), sh * math.sin(t * 39), sh * math.sin(t * 53)))
    pos += Vector((0.006 * math.sin(t * 1.7), 0, 0.006 * math.sin(t * 2.3)))
    return pos, look, roll, lens
TIPS = "L"

def arms_at(t, cmat):
    out = {}
    hold = win(t, GRAB - 0.25, 25.6, 0.5, 0.6) + win(t, 55.2, TIP - 0.2, 0.8, 0.6)
    inv = cmat.inverted()
    for s, sx in (("L", -1), ("R", 1)):
        sh = Vector((0.22 * sx, -0.55, 0.05)); el = Vector((0.25 * sx, -0.44, -0.24)); hn = Vector((0.15 * sx, -0.34 + 0.01 * math.sin(t * 1.3), -0.44))
        a = 0.8
        hn = hn.lerp(Vector((0.11 * sx, -0.16, -0.42)), a); el = el.lerp(Vector((0.2 * sx, -0.32, -0.28)), a)
        lh = win(t, -1.0, 1.5, 0.3, 0.4) + win(t, 10.0, 12.6, 0.4, 0.4)              # 自分の手を見る（ふるえる）
        if lh > 0:
            tr = 0.008 * math.sin(t * 31 + sx)
            hn = hn.lerp(Vector((0.115 * sx + tr, -0.07, -0.36)), lh); el = el.lerp(Vector((0.27 * sx, -0.32, -0.16)), lh)
        sl = win(t, BURST - 0.45, BURST + 1.0, 0.25, 0.8)                                 # 地面へ叩きつける
        if sl > 0:
            hn = hn.lerp(Vector((0.14 * sx, -0.5, -0.36)), sl); el = el.lerp(Vector((0.24 * sx, -0.4, -0.16)), sl)
        rc = win(t, REACH0, GRAB, 1.2, 0.4)                                               # 腕が勝手に前へ
        if rc > 0:
            tr = 0.01 * math.sin(t * 29 + sx * 2)
            hn = hn.lerp(Vector((0.1 * sx + tr, -0.18 + tr, -0.62)), rc); el = el.lerp(Vector((0.2 * sx, -0.3, -0.38)), rc)
        if hold > 0:                                                                      # ルカの手の上に
            best = min("LR", key=lambda q: abs((inv @ rhand_world(q)).x - 0.1 * sx))
            w = rhand_world(best) + Vector((0, 0, 0.04))
            tgt = inv @ w
            hn = hn.lerp(tgt, min(1.0, hold)); el = el.lerp(Vector((0.21 * sx, (tgt.y - 0.55) / 2 + 0.06, tgt.z / 2 - 0.02)), min(1.0, hold))
        out[s] = (sh, el, hn)
    return out

# ---------------------------------------------------------------- 1コマ分を置く
def face_cam(o, p):
    o.location = p; d = Vector((CAMP.x - p.x, CAMP.y - p.y, 0)).normalized()
    o.rotation_euler = (0, 0, math.atan2(-d.x, d.y))
face_cam(rukar, RG)
def place(t):
    # ルカ（カメラより先に置く：手の位置をカメラが使う）
    _, kind, rp_ = ruka_where(t)
    for o, on in ((ruka, kind == "down"), (rukar, kind == "reach")):
        for ch in [o] + list(o.children_recursive):
            if ch.type == "MESH" and not ch.name.startswith("rukar_sphere"): ch.hide_render = not on
    tgt = rukar if kind == "reach" else ruka
    face_cam(tgt, rp_)
    pos, look, roll, lens = cam_state(t)
    if kind == "down" and (BURST < t < 5.4 or SUN0 + 0.2 < t < 32.6 or TOWER0 - 0.4 < t < 55.0):
        sk = (SDIR if SUN0 < t < 33 else (TW - rp_).normalized())
        tgt.rotation_euler = (0, 0, math.atan2(-sk.x, sk.y)) if t > SUN0 else (0, 0, math.radians(-10))
    cam.location = pos; W.aim(cam, look); cam.rotation_euler.rotate_axis("Z", roll)
    cam.data.lens = lens; cam.data.dof.focus_distance = max(0.3, min(40.0, (look - pos).length))
    cmat = cam_matrix(pos, look, roll)
    cast = cast_at(t); blk = blk_at(t); rg = rglow_at(t)
    for s, (sh, el, hn) in arms_at(t, cmat).items(): set_arm(s, sh, el, hn)
    for s in "LR":
        k = ARMS[s]["m"]; HV[k]["cast"].default_value = 0.0; HV[k]["blk"].default_value = 0.05 + blk ** 2
        HV[k]["red"].default_value = 2.0 + 4.0 * max(0.0, blk - 0.4) + 4.0 * win(t, FULL, GRAB, 0.1, 0.6)
    # ルカのブロックの手（前に出した姿のときだけ）
    for s in "LR":
        h = RHANDS[s]["hd"]; vis = kind == "reach"
        for ch in h.children: ch.hide_render = not vis
        if not vis: continue
        w = rhand_world(s); fwd = Vector((pos.x - w.x, pos.y - w.y, 0)).normalized()
        y = fwd; z = Vector((0, 0, -1)); x = y.cross(z).normalized(); z = x.cross(y)
        h.location = w; h.rotation_euler = Matrix((x, y, z)).transposed().to_euler()
        k = RHANDS[s]["m"]; HV[k]["cast"].default_value = 1.3 * rg
        tipb = 0.0 if t < TIP else 0.3 * ease((t - TIP) / 2.4)
        HV[k]["blk"].default_value = tipb if s == TIPS else 0.0
        HV[k]["red"].default_value = 0.0 if t < TIP else 4.0
    hl.energy = 1.5 * cast + 30.0 * math.exp(-max(0.0, t - BURST) / 0.4) * (t >= BURST - 0.3) + 8.0 * win(t, FULL, GRAB, 0.1, 0.6)
    hl.energy *= 1 - 0.7 * ease((t - GRAB) / 2.0)
    gm = (rhand_world("L") + rhand_world("R")) / 2 if kind == "reach" else rp_ + Vector((0, 0, 1.0))
    glo.location = gm + Vector((0, 0, 0.12)); gl.energy = 9.0 * rg
    # 空：皆既日食 → 明ける
    c, light = ecl_at(t)
    wmix.inputs["Factor"].default_value = light
    wsk.inputs["B"].default_value = (0.3 * light + 0.02,) * 3 + (1,)
    off = Vector((-1.0, 0.0, 0.0)) * (1.0 - c) * 48.0 + Vector((0, 0, -1.0)) * (1.0 - c) * 10.0
    disc.location = CAMP + SDIR * 480 + off; disc.hide_render = c <= 0.0
    sunq.location = CAMP + SDIR * 500; corona.location = CAMP + SDIR * 530
    corona.hide_render = c < 0.96
    sl.energy = 3.6 * light; fl.energy = 0.9 * light + 0.12
    for s_ in stars: s_.hide_render = light > 0.15
    fogcol = Vector((0.06, 0.015, 0.045)).lerp(Vector((0.42, 0.4, 0.42)), light)
    FOG.nodes["fogcol"].inputs["Color"].default_value = (*fogcol, 1); FOG.nodes["fogcol"].inputs["Strength"].default_value = 1.0
    FOG.nodes["dens"].outputs[0].default_value = 0.004 + 0.012 * (1 - light)
    for n in face_em: n.inputs["Strength"].default_value = 1.05 + 0.3 * rg
    SHMR.inputs["To Max"].default_value = 3.0 + 14.0 * math.exp(-max(0.0, t - BURST) / 0.6) * (t >= BURST)
    nf_.energy = 18.0 * (1 - light)
    rl.energy = 400.0 * math.exp(-max(0.0, t - BURST) / 0.35) * (t >= BURST) + 25.0 * (1 - light) * (t >= BURST) + 8.0 * (t < BURST)
    # 表情
    RSP = [(l[0], l[1]) for l in LINES if l[5] == "ruka"]
    talking = any(st <= t <= en - 0.05 for st, en in RSP); flap = talking and (int(t * FPS) % 3 != 2)
    if t < 17.4: e = "talk" if flap else ("shock" if t > BURST else "shockc")
    elif t < 25.6: e = "tearsmiletalk" if flap else ("tearsmile" if t > 18.0 else "tearsad")
    elif t < 33.4: e = "smiletalk" if flap else "smile"
    elif t < 38.0: e = "shockc"
    elif t < 51.6: e = "sadtalk" if flap else "sad"
    elif t < 55.0: e = "talk" if flap else "shock"
    else: e = "smile"
    if (t % 3.3) < 0.17 and not talking and e in ("sad", "smile"): e = {"sad": "sadblink", "smile": "blink"}[e]
    T.set_expr(rtex, "mei", e); T.set_expr(rtex2, "mei", e)
    # 前の召喚者
    aL = 0.06 * math.sin(t * 1.1); aR = -0.06 * math.sin(t * 1.3)
    aR = aR + (-1.45 - aR) * win(t, 8.5, 11.6, 0.5, 0.6)
    aR = aR + (-1.6 - aR) * win(t, 15.3, 17.6, 0.3, 0.5)
    aL = aL + (-0.9 - aL) * win(t, BURST - 0.2, 6.0, 0.2, 0.6)
    pitch = 0.1 * win(t, 25.6, 28.4, 0.5, 0.6) - 0.12 * win(t, 41.4, 47.6, 0.6, 0.6)
    kage.location = KB + Vector((0, 0.3 * ease((t - BURST) / 0.6) * (t < 8.0) * (1 - ease((t - 6.0) / 2.0)), 0))
    kage.rotation_euler = (pitch, 0, math.atan2(pos.x - KB.x, -(pos.y - KB.y)))
    karms[0].rotation_euler = (aL, 0, 0); karms[1].rotation_euler = (aR, 0, 0)
    cut = -10.0 if t < DIS0 else -0.05 + 2.1 * ((t - DIS0) / (DIS1 - DIS0)) ** 0.9
    for cs in DCUT: cs.default_value = cut
    for o in [kage] + list(kage.children_recursive): o.hide_render = t > DIS1 + 0.3
    # 影ブロック：打ち上げ → 空で砕ける
    for r in risers:
        o = r["o"]; dt = t - r["tl"]
        vis = dt < POP
        o.hide_render = not vis
        for ch in o.children: ch.hide_render = not vis
        if not vis: continue
        if dt < 0:
            hop = abs(math.sin(t * 3.0 + r["ph"])) * 0.3
            o.location = r["p"] + Vector((0, 0, hop)); o.rotation_euler = (0, 0, math.atan2(pos.x - r["p"].x, -(pos.y - r["p"].y)))
        else:
            o.location = r["p"] + r["v"] * dt + Vector((0, 0, -6 * dt * dt)); o.rotation_euler = tuple(r["spin"] * dt)
    # 柱
    for p in pillars:
        k = (t - p["t0"]) / 0.22
        rise = 0.0 if k <= 0 else (1.08 * ease(k) if k < 1 else (1.08 - 0.08 * ease((k - 1) / 0.6)))
        p["o"].hide_render = k <= 0
        p["o"].location = (p["x"], p["y"], -p["h"] + p["h"] * rise)
    # 塔
    tk = ease((t - TOWER0) / (TOWER1 - TOWER0))
    tower.hide_render = t < TOWER0
    for o in tw_parts: o.hide_render = t < TOWER0
    tower.location = (TW.x, TW.y, TBASE - (TH + 10) * (1 - tk))
    crown.rotation_euler = (0, 0, t * 0.6)
    # 破片
    for f in FR:
        dt = t - f["t0"]; o = f["o"]
        if dt < 0 or dt > f["life"]: o.hide_render = True; continue
        o.hide_render = False
        p = f["p"] + f["v"] * dt + Vector((0, 0, 0.5 * f["g"] * dt * dt))
        if p.z < 0.1 and f["g"] < 0: p.z = 0.1
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
