"""
create_block5.py ― ブロック世界・単体回『触れたら影になる』（35秒・1080x1920・24fps・高画質）
  影の空の下、黒く染まっていく自分の手 → 「来るな！」 → ルカが手を握る（金の光で黒が引く）
  → 光の波が地面を走り、影ブロックが金の粒になって消える → 空が晴れて夕日 → ルカの指先が黒い → 「なんでもないよ」
  python create_block5.py [--samples 24] [--res 1.0] [--start 0] [--end 840] [--test 0,140,...]
  （このファイルは create_block5_src.py から作る：python3 build_block5.py）
"""
import os, sys, math, json, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Euler, Matrix
from bpy_extras.object_utils import world_to_camera_view
import s2_world as W, s3_toon as T, s7_world as S7, blk_hair as H
from blk5_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "14")); FPS = 24; N = int(END * FPS)
RS = float(arg("--res", "0.75"))
START = int(arg("--start", "0")); STOP = int(arg("--end", str(N)))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_BLK5" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
LINES = json.load(open(os.path.join(HERE, "blk5_lines.json"), encoding="utf-8"))

sc = W.reset(SAMPLES, res=(int(1080 * RS), int(1920 * RS)))
sc.cycles.max_bounces = 4; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2; sc.cycles.transparent_max_bounces = 8
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = float(arg("--thr", "0.05"))
try: sc.cycles.denoising_prefilter = "ACCURATE"; sc.cycles.denoising_quality = "HIGH"
except Exception: pass
sc.render.use_persistent_data = True
sc.view_settings.exposure = float(arg("--exp", "-0.3"))
sc.view_settings.view_transform = arg("--vt", "AgX"); sc.view_settings.look = arg("--look", "AgX - Punchy")
rnd = random.Random(9)

def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def win(t, a, b, fi=0.3, fo=0.3): return ease((t - a) / fi) * (1 - ease((t - b) / fo))

{{fog}}
# ---------------------------------------------------------------- 光の波（地面を走る金色の輪：全部の材質に足す）
WV = bpy.data.node_groups.new("WAVE", "ShaderNodeTree")
WV.interface.new_socket("Shader", in_out="INPUT", socket_type="NodeSocketShader")
WV.interface.new_socket("Shader", in_out="OUTPUT", socket_type="NodeSocketShader")
_wn = WV.nodes; _wl = WV.links.new
_wi = _wn.new("NodeGroupInput"); _wo = _wn.new("NodeGroupOutput")
def _m(op, a, b=None):
    n = _wn.new("ShaderNodeMath"); n.operation = op
    for i, v in enumerate((a, b)):
        if v is None: continue
        if isinstance(v, (int, float)): n.inputs[i].default_value = v
        else: _wl(v, n.inputs[i])
    return n.outputs[0]
def _v(name, val):
    n = _wn.new("ShaderNodeValue"); n.name = name; n.outputs[0].default_value = val; return n.outputs[0]
_geo = _wn.new("ShaderNodeNewGeometry"); _sep = _wn.new("ShaderNodeSeparateXYZ"); _wl(_geo.outputs["Position"], _sep.inputs[0])
_dx = _m("SUBTRACT", _sep.outputs["X"], _v("wcx", 0.0)); _dy = _m("SUBTRACT", _sep.outputs["Y"], _v("wcy", 0.0))
_d = _m("SQRT", _m("ADD", _m("MULTIPLY", _dx, _dx), _m("MULTIPLY", _dy, _dy)))
_R = _v("wr", -50.0)
_u = _m("DIVIDE", _m("SUBTRACT", _d, _R), 1.8)
_band = _m("EXPONENT", _m("MULTIPLY", _m("MULTIPLY", _u, _u), -1.0))
_inside = _m("LESS_THAN", _d, _R)
_trail = _m("MULTIPLY", _m("MULTIPLY", _inside, _m("EXPONENT", _m("DIVIDE", _m("SUBTRACT", _d, _R), 5.0))), 0.45)
_hz = _m("EXPONENT", _m("MULTIPLY", _m("MAXIMUM", _sep.outputs["Z"], 0.0), -1.6))          # 地面ほど強く（木や影ブロックの上は光らせない）
_e = _m("MULTIPLY", _m("MULTIPLY", _m("ADD", _band, _trail), _v("ws", 0.0)), _hz)
_em = _wn.new("ShaderNodeEmission"); _em.inputs["Color"].default_value = (1.0, 0.48, 0.12, 1); _wl(_e, _em.inputs["Strength"])
_add = _wn.new("ShaderNodeAddShader"); _wl(_wi.outputs[0], _add.inputs[0]); _wl(_em.outputs[0], _add.inputs[1]); _wl(_add.outputs[0], _wo.inputs[0])
def wavify(m):
    nt = m.node_tree; out = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0]
    src = out.inputs["Surface"].links[0].from_socket
    g = nt.nodes.new("ShaderNodeGroup"); g.node_tree = WV
    nt.links.new(src, g.inputs[0]); nt.links.new(g.outputs[0], out.inputs["Surface"])
    return m

# ---------------------------------------------------------------- ドット絵の質感（物理ベース＋ドットの凹凸＋光の波）
def pix(name, png, rough=0.8, emit_red=0.0, glossy=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(os.path.join(S7.TEX, png + ".png")); tx.interpolation = "Closest"
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough; b.inputs["Specular IOR Level"].default_value = 0.35
    bw = nt.nodes.new("ShaderNodeRGBToBW"); bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.45; bump.inputs["Distance"].default_value = 0.02
    nt.links.new(tx.outputs["Color"], bw.inputs[0]); nt.links.new(bw.outputs[0], bump.inputs["Height"]); nt.links.new(bump.outputs[0], b.inputs["Normal"])
    if png == "leaves":                                                   # 葉は光を透かす（夕日の逆光で光る）
        b.inputs["Subsurface Weight"].default_value = 0.0
        tl = nt.nodes.new("ShaderNodeBsdfTranslucent"); nt.links.new(tx.outputs["Color"], tl.inputs["Color"])
        mx = nt.nodes.new("ShaderNodeMixShader"); mx.inputs[0].default_value = 0.3
        out = nt.nodes["Material Output"]; nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(tl.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs["Surface"])
    if glossy: b.inputs["Roughness"].default_value = 0.25; b.inputs["Coat Weight"].default_value = 0.6
    if emit_red:
        sep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(tx.outputs["Color"], sep.inputs[0])
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.35; mr.inputs["From Max"].default_value = 0.8
        nt.links.new(sep.outputs[0], mr.inputs["Value"])
        b.inputs["Emission Color"].default_value = (1.0, 0.05, 0.08, 1)
        nt.links.new(mr.outputs[0], b.inputs["Emission Strength"]); mr.inputs["To Max"].default_value = emit_red
    return fogify(wavify(m))
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
    o = S7.voxel_mesh(name, {(0, 0, 0): "b"}, [m], {"b": (0, 0, 0)})
    for v in o.data.vertices: v.co = (v.co - Vector((0.5, 0.5, 0.5))) * size
    return o
def boxes(name, items, m):
    """小さな直方体をまとめて1つのメッシュに（草・花・雲）。items: [(中心, 大きさ)]"""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    for c, s in items:
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r["verts"]: v.co = Vector((v.co.x * s[0], v.co.y * s[1], v.co.z * s[2])) + Vector(c)
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); me.materials.append(m); return o

{{terrain}}
build_terrain()
# 草むらと小さな花（地面の質感を上げる）
rg_ = random.Random(21)
tuft_m = fogify(wavify(W.mat("tuft", (0.16, 0.42, 0.1), 0.7)))
tufts = []
for _ in range(900):
    x, y = rg_.uniform(-12, 12), rg_.uniform(-6, 22)
    if hgt(int(math.floor(x)), int(math.floor(y))) != 0: continue
    if math.hypot(x - 0.3, y + 0.9) < 0.45: continue
    h = rg_.uniform(0.06, 0.18)
    tufts.append(((x, y, h / 2), (0.035, 0.035, h)))
boxes("tufts", tufts, tuft_m)
for col, n in (((0.95, 0.85, 0.2), 70), ((0.95, 0.95, 0.95), 60), ((0.85, 0.2, 0.25), 40)):
    fm = fogify(wavify(W.mat("flower", col, 0.6)))
    fl_ = []
    for _ in range(n):
        x, y = rg_.uniform(-10, 10), rg_.uniform(-4, 18)
        if hgt(int(math.floor(x)), int(math.floor(y))) != 0 or math.hypot(x - 0.3, y + 0.9) < 0.6: continue
        h = rg_.uniform(0.1, 0.2)
        fl_.append(((x, y, h), (0.05, 0.05, 0.05)))
    boxes("flowers", fl_, fm)
stem_m = fogify(W.mat("stem", (0.1, 0.3, 0.06), 0.8))

# ---------------------------------------------------------------- 空：影の空 → 晴れて夕日（四角い太陽・ブロックの雲）
world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True; wn = world.node_tree
bg = wn.nodes["Background"]
co = wn.nodes.new("ShaderNodeTexCoord"); sep = wn.nodes.new("ShaderNodeSeparateXYZ")
wn.links.new(co.outputs["Generated"], sep.inputs[0])
nramp = wn.nodes.new("ShaderNodeValToRGB"); el = nramp.color_ramp.elements
el[0].position, el[0].color = 0.0, (0.07, 0.012, 0.03, 1); el[1].position, el[1].color = 0.4, (0.006, 0.004, 0.014, 1)
mr = wn.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.5; mr.inputs["From Max"].default_value = 1.0
wn.links.new(sep.outputs["Z"], mr.inputs["Value"]); wn.links.new(mr.outputs[0], nramp.inputs["Fac"])
SUN_EL = 13.0
SDIR = Vector((-0.06, math.cos(math.radians(SUN_EL)), math.sin(math.radians(SUN_EL)))).normalized()
# アニメ調の夕焼け：地平線オレンジ → 桃色 → 上は青紫。太陽の方向ほど明るく黄金色
sramp = wn.nodes.new("ShaderNodeValToRGB"); se = sramp.color_ramp.elements
se[0].position, se[0].color = 0.0, (1.0, 0.36, 0.12, 1)
se[1].position, se[1].color = 1.0, (0.08, 0.09, 0.32, 1)
for pos_, col_ in ((0.08, (1.0, 0.5, 0.2, 1)), (0.22, (0.95, 0.42, 0.42, 1)), (0.45, (0.42, 0.28, 0.55, 1))):
    e_ = se.new(pos_); e_.color = col_
smr = wn.nodes.new("ShaderNodeMapRange"); smr.inputs["From Min"].default_value = 0.0; smr.inputs["From Max"].default_value = 0.75
wn.links.new(sep.outputs["Z"], smr.inputs["Value"]); wn.links.new(smr.outputs[0], sramp.inputs["Fac"])
sdot = wn.nodes.new("ShaderNodeVectorMath"); sdot.operation = "DOT_PRODUCT"; sdot.inputs[1].default_value = (-0.06, 0.974, 0.225)
wn.links.new(co.outputs["Generated"], sdot.inputs[0])
sclp = wn.nodes.new("ShaderNodeMath"); sclp.operation = "MAXIMUM"; sclp.inputs[1].default_value = 0.0; wn.links.new(sdot.outputs["Value"], sclp.inputs[0])
spw = wn.nodes.new("ShaderNodeMath"); spw.operation = "POWER"; spw.inputs[1].default_value = 6.0; wn.links.new(sclp.outputs[0], spw.inputs[0])
spw2 = wn.nodes.new("ShaderNodeMath"); spw2.operation = "POWER"; spw2.inputs[1].default_value = 60.0; wn.links.new(sclp.outputs[0], spw2.inputs[0])
sg = wn.nodes.new("ShaderNodeMath"); sg.operation = "MULTIPLY_ADD"; sg.inputs[1].default_value = 0.9
wn.links.new(spw.outputs[0], sg.inputs[0]); wn.links.new(spw2.outputs[0], sg.inputs[2])
sgc = wn.nodes.new("ShaderNodeMix"); sgc.data_type = "RGBA"; sgc.blend_type = "ADD"
wn.links.new(sg.outputs[0], sgc.inputs["Factor"]); wn.links.new(sramp.outputs["Color"], sgc.inputs["A"]); sgc.inputs["B"].default_value = (1.0, 0.62, 0.25, 1)
wmix = wn.nodes.new("ShaderNodeMix"); wmix.data_type = "RGBA"
wsk = wn.nodes.new("ShaderNodeMix"); wsk.data_type = "RGBA"; wsk.blend_type = "MULTIPLY"; wsk.inputs["Factor"].default_value = 1.0
wn.links.new(sgc.outputs["Result"], wsk.inputs["A"]); wsk.inputs["B"].default_value = (0.5, 0.5, 0.5, 1)
wn.links.new(nramp.outputs["Color"], wmix.inputs["A"]); wn.links.new(wsk.outputs["Result"], wmix.inputs["B"])
wn.links.new(wmix.outputs["Result"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 1.0
CAMP = Vector((0.3, -0.9, 1.62))
sun_m = S7.emis("sunsq", (1.0, 0.62, 0.3), 40.0)
sunq = cube("sunq", sun_m, 1.0); sunq.scale = (30, 1, 30); sunq.visible_shadow = False; sunq.location = CAMP + SDIR * 500
sunq.rotation_euler = (0, 0, math.atan2(-SDIR.x, SDIR.y))
halo_m = bpy.data.materials.new("halo"); halo_m.use_nodes = True                    # 太陽のまわりのにじみ（中心ほど明るい）
_hn = halo_m.node_tree.nodes; _hl = halo_m.node_tree.links.new; _hn.clear()
_ho = _hn.new("ShaderNodeOutputMaterial"); _he = _hn.new("ShaderNodeEmission"); _ht = _hn.new("ShaderNodeBsdfTransparent")
_hx = _hn.new("ShaderNodeMixShader"); _hc = _hn.new("ShaderNodeTexCoord"); _hg = _hn.new("ShaderNodeTexGradient"); _hg.gradient_type = "SPHERICAL"
_hmp = _hn.new("ShaderNodeMapping"); _hmp.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
_hl(_hc.outputs["Object"], _hmp.inputs["Vector"]); _hl(_hmp.outputs["Vector"], _hg.inputs["Vector"])
_hpw = _hn.new("ShaderNodeMath"); _hpw.operation = "POWER"; _hpw.inputs[1].default_value = 3.0; _hl(_hg.outputs["Fac"], _hpw.inputs[0])
_he.inputs["Color"].default_value = (1.0, 0.55, 0.25, 1); _he.inputs["Strength"].default_value = 6.0
_hl(_hpw.outputs[0], _hx.inputs[0]); _hl(_ht.outputs[0], _hx.inputs[1]); _hl(_he.outputs[0], _hx.inputs[2]); _hl(_hx.outputs[0], _ho.inputs["Surface"])
bpy.ops.mesh.primitive_plane_add(size=2.0); halo = bpy.context.object; halo.name = "halo"; halo.data.materials.append(halo_m)
halo.scale = (110, 110, 1); halo.location = CAMP + SDIR * 520; halo.rotation_euler = (-SDIR).to_track_quat("Z", "Y").to_euler(); halo.visible_shadow = False
for a in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"): setattr(halo, a, False)
HALO_E = _he
# ブロックの雲（夕日で下から染まる）
cloud_m = W.mat("cloud", (0.95, 0.8, 0.8), 0.9, emit=(1.0, 0.5, 0.42), estr=0.0); CLOUD_B = cloud_m.node_tree.nodes["Principled BSDF"]; CLOUD_B.inputs["Specular IOR Level"].default_value = 0.1
rc_ = random.Random(3); clouds = []
for k in range(16):
    cx, cy = rc_.uniform(-160, 160), rc_.uniform(120, 360); cz = rc_.uniform(45, 80)
    if abs(cx - SDIR.x / SDIR.y * cy) < 45: cx += 90 if cx > 0 else -90
    cells = {}
    for _ in range(rc_.randint(5, 9)):
        ox, oy = rc_.randint(-4, 4), rc_.randint(-2, 2)
        for x in range(ox - rc_.randint(2, 4), ox + rc_.randint(2, 4)):
            for y in range(oy - rc_.randint(1, 2), oy + rc_.randint(1, 2)): cells[(x, y, 0)] = "c"
    o = S7.voxel_mesh("cloud", cells, [cloud_m], {"c": (0, 0, 0)}); o.scale = (4.0, 4.0, 2.2); o.location = (cx, cy, cz)
    o.visible_shadow = False; clouds.append(o)
sl = bpy.data.lights.new("sunl", "SUN"); sl.angle = math.radians(1.2); sl.color = (1.0, 0.66, 0.4)
slo = bpy.data.objects.new("sunl", sl); bpy.context.collection.objects.link(slo)
slo.rotation_euler = (-SDIR).to_track_quat("-Z", "Y").to_euler()
fl = bpy.data.lights.new("fill", "SUN"); fl.angle = math.radians(30); fl.color = (0.55, 0.6, 1.0)
flo = bpy.data.objects.new("fill", fl); bpy.context.collection.objects.link(flo)
flo.rotation_euler = (-Vector((-0.4, -1.0, 0.8)).normalized()).to_track_quat("-Z", "Y").to_euler()

# ---------------------------------------------------------------- ルカ（腕をおろした姿／両手を前に出した姿／手を後ろに隠した姿）
_d = Vector((-0.08, 1.0)).normalized()
def at(dist): return Vector((CAMP.x + _d.x * dist, CAMP.y + _d.y * dist, 0))
RF = at(1.3)                     # 少し離れて立つ
RG = at(0.62)                    # 目の前（手を握る）
RB = at(0.78)                    # 一歩下がって、手を後ろに
WC = (CAMP + RG) / 2             # 光の波の中心
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
                sk = "skin" in m.name; hr = "hair" in m.name
                nm = W.mat(m.name + "_pbr", lin, 0.5 if sk else (0.38 if hr else 0.75), sss=0.25 if sk else 0.0)
                b = nm.node_tree.nodes["Principled BSDF"]
                if hr: b.inputs["Coat Weight"].default_value = 0.25; b.inputs["Sheen Weight"].default_value = 0.4
                if key in ("blazer", "skirt"): b.inputs["Sheen Weight"].default_value = 0.6
                o.data.materials[i] = fogify(nm)
HAIR = (0.3, 0.2, 0.16)
ruka, rtex = T.girl("ruka", tuple(RF), rot=0, hair=HAIR, face="mei", ponytail=True)
RH_L = (0.1, 0.28, 1.1); RH_R = (-0.1, 0.28, 1.1)
rukar, rtex2 = T.girl("rukar", tuple(RG), rot=0, hair=HAIR, face="mei", ponytail=True,
                      arms={"L": ((0.17, 0.12, 1.08), RH_L), "R": ((-0.17, 0.12, 1.08), RH_R)})
rukab, rtex3 = T.girl("rukab", tuple(RB), rot=0, hair=HAIR, face="mei", ponytail=True,
                      arms={"L": ((0.19, -0.06, 1.04), (0.07, -0.13, 0.9)), "R": ((-0.19, -0.06, 1.04), (-0.07, -0.13, 0.9))})
for r_, nm_ in ((ruka, "ruka"), (rukar, "rukar"), (rukab, "rukab")):
    ruka_pbr(r_)
    hm_ = [m for o in r_.children if o.name.startswith(nm_ + "_hair") for m in o.data.materials][0]
    H.upgrade(r_, nm_, hm_)
for o in rukar.children_recursive:
    if o.name.startswith("rukar_hand"): o.hide_render = True; o.name = "rukar_sphere_hidden"
MODELS = {"down": ruka, "reach": rukar, "back": rukab}

# ---------------------------------------------------------------- 自分の腕（パーカー）と、ブロックの手（影化）／ルカのブロックの手
cam = W.camera(tuple(CAMP), (0, 10, 1.5), lens=24, fstop=2.0)
cam.data.dof.aperture_blades = 7; cam.data.dof.aperture_ratio = 1.0
{{hands}}
ARMS = {}
for s in "LR":
    hh, hm = hand_build(s, cam)
    ARMS[s] = dict(up=piece("up" + s, 0.055, hood), lo=piece("lo" + s, 0.05, hood), hd=hh, m=hm.name)
RHANDS = {}
for s in "LR":
    hh, hm = hand_build(s, None, ecol=(1.0, 0.72, 0.3), k=0.88, prefix="rh")
    RHANDS[s] = dict(hd=hh, m=hm.name)
{{setarm}}
def plight(name, kind, col, size, parent=None, loc=(0, 0, 0)):
    l = bpy.data.lights.new(name, kind); l.color = col
    if kind == "AREA": l.size = size
    else: l.shadow_soft_size = size
    o = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(o); o.parent = parent; o.location = loc; return l, o
hl, hlo = plight("handglow", "POINT", (1.0, 0.1, 0.12), 0.2, cam, (0.0, -0.1, -0.8))
key, keyo = plight("key", "AREA", (0.6, 0.65, 1.0), 1.2, cam, (-0.9, 0.7, 0.3))          # 顔を照らす（左上のやわらかい光）
gl, glo = plight("rukaglow", "POINT", (1.0, 0.72, 0.38), 0.12)
rim, rimo = plight("rim", "AREA", (1.0, 0.25, 0.45), 1.5)                                  # ルカの背中から：髪の縁を光らせる
emb_l, emb_lo = plight("emberfill", "POINT", (1.0, 0.2, 0.15), 3.0, None, (0.0, 5.0, 0.6))

# ---------------------------------------------------------------- 影ブロック（光の波で下から金色に溶ける）
eye_src = E("eye", (1.0, 0.08, 0.06), 6.0); pupil_src = E("pupil", (0.02, 0.0, 0.0), 0.5)
{{dissolve}}
mobs = []
rmb = random.Random(31)
for k, (ang, rad) in enumerate([(62, 4.6), (85, 6.4), (104, 4.2), (122, 7.4), (45, 7.8), (140, 5.2), (75, 10.0), (96, 12.5),
                                 (30, 5.6), (155, 8.8), (112, 15.0), (58, 13.0)]):
    a = math.radians(ang); sz = rmb.uniform(0.9, 1.5)
    cut = None; DCUT.clear()
    bm_ = dissolve(M["shadow"].copy()); em_ = dissolve(eye_src.copy()); pm_ = dissolve(pupil_src.copy())
    b = cube("mob%d" % k, bm_, 1.0); b.scale = (sz,) * 3
    e = cube("mob%d_eye" % k, em_, 1.0); e.parent = b; e.location = (0, -0.5, 0.12); e.scale = (0.42, 0.04, 0.42); e.visible_shadow = False
    p = cube("mob%d_pu" % k, pm_, 1.0); p.parent = b; p.location = (0, -0.52, 0.12); p.scale = (0.1, 0.04, 0.28); p.visible_shadow = False
    mobs.append(dict(o=b, a=a, r0=rad, size=sz, ph=rmb.uniform(0, 6.28), cuts=list(DCUT)))

# ---------------------------------------------------------------- 光の輪（立ち上がる光の壁）・粒
ring_m = bpy.data.materials.new("ring"); ring_m.use_nodes = True; _rn = ring_m.node_tree.nodes; _rl = ring_m.node_tree.links.new; _rn.clear()
_ro = _rn.new("ShaderNodeOutputMaterial"); _re = _rn.new("ShaderNodeEmission"); _rt = _rn.new("ShaderNodeBsdfTransparent"); _rx = _rn.new("ShaderNodeMixShader")
_rc = _rn.new("ShaderNodeTexCoord"); _rs = _rn.new("ShaderNodeSeparateXYZ"); _rl(_rc.outputs["Generated"], _rs.inputs[0])
_rp = _rn.new("ShaderNodeMath"); _rp.operation = "POWER"; _rp.inputs[1].default_value = 2.5
_ri = _rn.new("ShaderNodeMath"); _ri.operation = "SUBTRACT"; _ri.inputs[0].default_value = 1.0; _rl(_rs.outputs["Z"], _ri.inputs[1]); _rl(_ri.outputs[0], _rp.inputs[0])
_rk = _rn.new("ShaderNodeMath"); _rk.operation = "MULTIPLY"; _rl(_rp.outputs[0], _rk.inputs[0]); _rk.inputs[1].default_value = 1.0
_re.inputs["Color"].default_value = (1.0, 0.55, 0.18, 1); _re.inputs["Strength"].default_value = 5.0
_rl(_rk.outputs[0], _rx.inputs[0]); _rl(_rt.outputs[0], _rx.inputs[1]); _rl(_re.outputs[0], _rx.inputs[2]); _rl(_rx.outputs[0], _ro.inputs["Surface"])
RING_K = _rk.inputs[1]
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=1.0, depth=1.0, end_fill_type="NOTHING", location=(0, 0, 0.5))
ring = bpy.context.object; ring.name = "ring"; ring.data.materials.append(ring_m); ring.visible_shadow = False
bpy.ops.object.transform_apply(location=True)
for a in ("visible_diffuse", "visible_glossy"): setattr(ring, a, False)

mote_m = E("mote", (1.0, 0.78, 0.42), 14.0); ember_m = E("ember", (1.0, 0.22, 0.1), 10.0)
FR = []
rmo = random.Random(77)
for k in range(240):                                                     # 光のあとに漂う金の粒
    d = rmo.uniform(0.35, 9.0) ** 1.0; a = rmo.uniform(-0.4, math.pi + 0.4)
    p = CAMP + Vector((math.cos(a) * d, math.sin(a) * d, rmo.uniform(-1.5, 2.2)))
    o = cube("mote", mote_m, 1.0); o.visible_shadow = False
    FR.append(dict(o=o, kind="mote", p=p, s=rmo.uniform(0.006, 0.018) * (1 + 0.15 * d), ph=rmo.uniform(0, 6.28), v=rmo.uniform(0.05, 0.16),
                   t0=WAVE + 0.15 + d / 14.0))
for k in range(80):                                                      # 影の空の下の、赤い火の粉
    d = rmo.uniform(0.4, 8.0); a = rmo.uniform(-0.3, math.pi + 0.3)
    p = CAMP + Vector((math.cos(a) * d, math.sin(a) * d, rmo.uniform(-1.6, 1.8)))
    o = cube("ember", ember_m, 1.0); o.visible_shadow = False
    FR.append(dict(o=o, kind="ember", p=p, s=rmo.uniform(0.006, 0.014) * (1 + 0.15 * d), ph=rmo.uniform(0, 6.28), v=rmo.uniform(0.1, 0.3),
                   t0=WAVE + d / 14.0))
for m in mobs:                                                           # 影ブロックが溶けて立ちのぼる粒
    for j in range(16):
        o = cube("mmote", mote_m, 1.0); o.visible_shadow = False
        FR.append(dict(o=o, kind="mmote", mob=m, off=Vector((rmo.uniform(-0.5, 0.5), rmo.uniform(-0.5, 0.5), rmo.uniform(0.0, 1.0))),
                       s=rmo.uniform(0.02, 0.045), ph=rmo.uniform(0, 6.28), v=rmo.uniform(0.6, 1.2), dl=rmo.uniform(0.0, 0.8)))

# ---------------------------------------------------------------- 時間ごとの値
def wave_r(t): return -50.0 if t < WAVE else 15.0 * (t - WAVE) ** 0.85
def light_at(t): return ease((t - SKY0) / (SKY1 - SKY0))
def blk_at(t):
    if t < GLOW0: return 0.9 + 0.07 * ease(t / 2.5)
    if t < GLOW1: return 0.97 - 0.89 * ((t - GLOW0) / (GLOW1 - GLOW0)) ** 0.8
    return 0.08
def rglow_at(t):
    return ease((t - GLOW0 + 0.8) / 1.0) * (1 - ease((t - WAVE - 0.6) / 2.0)) + 0.35 * win(t, WAVE - 0.4, WAVE + 1.2, 0.3, 1.0)

def model_at(t):
    if t < 7.85: return "down", RF
    if t < HIDE: return "reach", at(0.95 - 0.33 * ease((t - 7.85) / 0.45))
    return "back", RB

def cam_matrix(pos, look, roll):
    q = (look - pos).to_track_quat("-Z", "Y"); e = q.to_euler(); m = e.to_matrix()
    m = m @ Matrix.Rotation(roll, 3, "Z")
    return Matrix.Translation(pos) @ m.to_4x4()

def rhand_world(s):
    rot = rukar.rotation_euler.z; loc = Vector(RH_L if s == "L" else RH_R) - Vector((0, 0.0, 0.02))
    return rukar.location + Matrix.Rotation(rot, 3, "Z") @ loc

TIPS = "L"
def cam_state(t):
    pos = CAMP.copy(); roll = 0.0
    hands = lambda t: pos + Vector((0.0, 1.0, -0.6))
    rface = lambda t: (lambda p: Vector((p.x, p.y, 1.43 + 0.07 * light_at(t))))(model_at(t)[1])
    rbody = lambda t: (lambda p: Vector((p.x, p.y, 1.22)))(model_at(t)[1])
    hmid = lambda t: (rhand_world("L") + rhand_world("R")) / 2 + Vector((0, 0, 0.05))
    grab = lambda t: (lambda h, f: h.lerp(f, 0.42))(hmid(t), rface(t))                 # 握った手と顔が両方入る
    tip = lambda t: rhand_world(TIPS) + (pos - rhand_world(TIPS)).xy.to_3d().normalized() * 0.08 + Vector((0, 0, 0.02))
    floor = lambda t: Vector((WC.x - 0.8, WC.y + 2.2, 0.0)) + Vector((0, 1.5, 0.8)) * ease((t - WAVE) / 1.0)
    ahead = lambda t: pos + Vector((-3.4 + 1.6 * ease((t - WAVE - 2.4) / 3.5), 7.0, -0.9 + 1.5 * ease((t - WAVE - 2.2) / 3.5)))
    # (開始, 見る先, レンズ, F値)
    SH = [(0.0, hands, 22, 2.8), (3.0, rface, 46, 2.0), (7.7, grab, 19, 2.8), (11.3, rface, 24, 1.8), (14.0, floor, 17, 5.6), (15.5, ahead, 17, 5.6),
          (20.3, rface, 24, 1.8), (24.2, grab, 19, 2.8), (25.4, tip, 24, 4.5), (28.85, rface, 24, 1.8), (31.6, rbody, 22, 2.2)]
    i = max(j for j, s in enumerate(SH) if s[0] <= t)
    ts_, f1, l1, fs1 = SH[i]; look = f1(t); lens = l1; fst = fs1
    if i > 0:
        _, f0, l0, fs0 = SH[i - 1]
        du = {ahead: 1.0, tip: 0.8, rbody: 1.4}.get(f1, 0.4)
        k = ease((t - ts_) / du); look = f0(t).lerp(f1(t), k); lens = l0 + (l1 - l0) * k; fst = fs0 + (fs1 - fs0) * k
    if f1 is tip: lens = 24 + 22 * ease((t - 25.5) / 2.2)
    if f1 is rface: lens += 3 * ease((t - ts_) / 3.0)                     # ゆっくり寄る
    if f1 is rbody: lens -= 2 * ease((t - ts_) / 3.0)
    sh = 0.0
    for a, amp, d in ((0.25, 0.012, 2.6), (WAVE, 0.05, 1.6), (TIP + 1.2, 0.008, 0.6)):
        if a <= t < a + d: sh = max(sh, amp * (1 - (t - a) / d))
    pos = pos + Vector((sh * math.sin(t * 47), sh * math.sin(t * 39), sh * math.sin(t * 53)))
    pos += Vector((0.005 * math.sin(t * 1.3), 0.003 * math.sin(t * 0.9), 0.005 * math.sin(t * 1.9)))   # 息づかい
    if "--sundbg" in sys.argv: look = pos + SDIR * 10; lens = 16
    if "--camover" in sys.argv:
        v = [float(x) for x in arg("--camover", "").split(",")]; pos = Vector(v[0:3]); look = Vector(v[3:6]); lens = v[6]; fst = 22
    return pos, look, roll, lens, fst

def arms_at(t, cmat, pos_):
    out = {}
    hold = win(t, GRAB - 0.3, 24.9, 0.4, 0.7)
    inv = cmat.inverted()
    for s, sx in (("L", -1), ("R", 1)):
        sh = Vector((0.22 * sx, -0.55, 0.05)); el = Vector((0.25 * sx, -0.44, -0.24)); hn = Vector((0.15 * sx, -0.34 + 0.01 * math.sin(t * 1.3), -0.44))
        hn = hn.lerp(Vector((0.11 * sx, -0.16, -0.42)), 0.8); el = el.lerp(Vector((0.2 * sx, -0.32, -0.28)), 0.8)
        lh = win(t, -1.0, 3.2, 0.3, 0.4)                                                  # 黒くなっていく自分の手を見る（ふるえる）
        if lh > 0:
            tr = 0.006 * math.sin(t * 31 + sx)
            hn = hn.lerp(Vector((0.115 * sx + tr, -0.07, -0.36)), lh); el = el.lerp(Vector((0.27 * sx, -0.32, -0.16)), lh)
        if hold > 0:                                                                      # ルカの手の上に
            best = min("LR", key=lambda q: abs((inv @ rhand_world(q)).x - 0.1 * sx))
            w = rhand_world(best) + (pos_ - rhand_world(best)).xy.to_3d().normalized() * 0.1 + Vector((0, 0, 0.035))
            tgt = inv @ w
            hn = hn.lerp(tgt, min(1.0, hold)); el = el.lerp(Vector((0.21 * sx, (tgt.y - 0.55) / 2 + 0.06, tgt.z / 2 - 0.02)), min(1.0, hold))
        dn = ease((t - 25.0) / 0.8)                                                       # 手を離して、下ろす
        if dn > 0: hn = hn.lerp(Vector((0.2 * sx, -0.6, -0.3)), dn); el = el.lerp(Vector((0.25 * sx, -0.6, -0.1)), dn)
        out[s] = (sh, el, hn)
    return out

def face_cam(o, p):
    o.location = p; d = Vector((CAMP.x - p.x, CAMP.y - p.y, 0)).normalized()
    o.rotation_euler = (0, 0, math.atan2(-d.x, d.y))
face_cam(rukar, RG)
RSP = [(l[0], l[1]) for l in LINES if l[5] == "ruka"]
def expr_at(t):
    talking = any(st <= t <= en - 0.05 for st, en in RSP); flap = talking and (int(t * 12) % 3 != 2)
    if t < 3.2: e = "sad"
    elif t < 5.15: e = "sadtalk" if flap else "sad"
    elif t < 8.2: e = "tearsadtalk" if flap else "tearsad"
    elif t < 14.2: e = "tearsmiletalk" if flap else "tearsmile"
    elif t < 20.3: e = "smile"
    elif t < 24.2: e = "blushtalk" if flap else "blushsmile"
    elif t < HIDE: e = "shockc"
    elif t < 32.4: e = "smiletalk" if flap else "smile"
    else: e = "sad"
    if (t % 3.1) < 0.12 and not talking and e in ("sad", "smile", "blushsmile"): e = {"sad": "sadblink", "smile": "blink", "blushsmile": "blink"}[e]
    return e

def FOCUS(t, look, pos):
    if t < 3.0: return (cam_hand_mid() - pos).length                    # 自分の手にピント（ルカはぼける）
    if (look - pos).length > 4: return 6.0
    if 7.7 <= t < 11.3 or 24.2 <= t < 25.4: return ((rhand_world("L") + rhand_world("R")) / 2 - pos).length
    return (look - pos).length
def cam_hand_mid(): return (ARMS["L"]["hd"].matrix_world.translation + ARMS["R"]["hd"].matrix_world.translation) / 2
def place(t):
    kind, rp_ = model_at(t)
    for k_, o in MODELS.items():
        for ch in [o] + list(o.children_recursive):
            if ch.type == "MESH" and not ch.name.startswith("rukar_sphere"): ch.hide_render = k_ != kind
    tgt = MODELS[kind]; face_cam(tgt, rp_)
    pos, look, roll, lens, fst = cam_state(t)
    cam.location = pos; W.aim(cam, look); cam.rotation_euler.rotate_axis("Z", roll)
    cam.data.lens = lens; cam.data.dof.aperture_fstop = fst
    cmat = cam_matrix(pos, look, roll)
    blk = blk_at(t); rg = rglow_at(t); light = light_at(t)
    for s, (sh, el, hn) in arms_at(t, cmat, pos).items(): set_arm(s, sh, el, hn)
    bpy.context.view_layer.update()
    cam.data.dof.focus_distance = max(0.3, min(40.0, FOCUS(t, look, pos)))
    for s in "LR":
        k = ARMS[s]["m"]; HV[k]["cast"].default_value = 0.0; HV[k]["blk"].default_value = 0.05 + blk ** 2
        HV[k]["red"].default_value = 2.0 + 4.0 * max(0.0, blk - 0.4)
    for s in "LR":                                                        # ルカのブロックの手（前に出した姿のときだけ）
        h = RHANDS[s]["hd"]; vis = kind == "reach"
        for ch in h.children: ch.hide_render = not vis
        if not vis: continue
        w = rhand_world(s); fwd = Vector((pos.x - w.x, pos.y - w.y, 0)).normalized()
        y = fwd; z = Vector((0, 0, -1)); x = y.cross(z).normalized(); z = x.cross(y)
        h.location = w; h.rotation_euler = Matrix((x, y, z)).transposed().to_euler()
        k = RHANDS[s]["m"]; HV[k]["cast"].default_value = 1.3 * rg
        tipb = 0.0 if t < TIP else 0.34 * ease((t - TIP) / 3.0)
        HV[k]["blk"].default_value = tipb if s == TIPS else 0.0
        HV[k]["red"].default_value = 0.0 if t < TIP else 3.0 + 1.5 * math.sin(t * 5)
    hl.energy = (3.0 + 0.8 * math.sin(t * 9)) * (1 - ease((t - GLOW0) / 3.0))
    gm = (rhand_world("L") + rhand_world("R")) / 2 if kind == "reach" else rp_ + Vector((0, 0, 1.0))
    glo.location = gm + Vector((0, 0, 0.12)); gl.energy = 10.0 * rg + 80.0 * math.exp(-max(0.0, t - WAVE) / 0.25) * (t >= WAVE)
    # 空
    wmix.inputs["Factor"].default_value = light
    wsk.inputs["B"].default_value = (1.0 * light + 0.02,) * 3 + (1,); CLOUD_B.inputs["Emission Strength"].default_value = 0.7 * light
    sunq.hide_render = light < 0.02; halo.hide_render = light < 0.02
    sunq.location = CAMP + SDIR * 500 + Vector((0, 0, -40 * (1 - light)))
    HALO_E.inputs["Strength"].default_value = 6.0 * light
    sl.energy = 4.2 * light; fl.energy = 0.35 * (1 - light) + 0.25 * light
    fogcol = Vector((0.05, 0.012, 0.035)).lerp(Vector((0.62, 0.42, 0.32)), light)
    FOG.nodes["fogcol"].inputs["Color"].default_value = (*fogcol, 1); FOG.nodes["fogcol"].inputs["Strength"].default_value = 1.0
    FOG.nodes["dens"].outputs[0].default_value = 0.022 - 0.012 * light
    for n in face_em: n.inputs["Strength"].default_value = 0.95 + 0.25 * rg + 0.15 * light
    key.energy = 22.0; key.color = Vector((0.6, 0.65, 1.0)).lerp(Vector((1.0, 0.8, 0.62)), light)
    rimo.location = rp_ + Vector((0.25, 0.9, 1.75)); rimo.rotation_euler = (rp_ + Vector((0, 0, 1.3)) - rimo.location).to_track_quat("-Z", "Y").to_euler()
    rim.energy = 70.0 * (1 - light); emb_l.energy = 30.0 * (1 - light)
    # 光の波
    R_ = wave_r(t)
    WV.nodes["wcx"].outputs[0].default_value = WC.x; WV.nodes["wcy"].outputs[0].default_value = WC.y
    WV.nodes["wr"].outputs[0].default_value = R_
    WV.nodes["ws"].outputs[0].default_value = 0.0 if t < WAVE else 5.0 * math.exp(-(t - WAVE) / 2.6)
    ring.hide_render = not (WAVE <= t < WAVE + 3.0)
    if not ring.hide_render:
        ring.location = (WC.x, WC.y, 0.0); ring.scale = (max(R_, 0.05), max(R_, 0.05), 1.8 + 1.2 * ease((t - WAVE) / 0.6))
        RING_K.default_value = math.exp(-(t - WAVE) / 1.4)
    # 影ブロック：にじり寄る → 波が来たら金色に溶ける
    for m in mobs:
        r = m["r0"] - 0.06 * min(t, WAVE); a = m["a"]
        p = Vector((WC.x + r * math.cos(a), WC.y + r * math.sin(a), 0))
        hop = abs(math.sin(t * 2.6 + m["ph"])) * 0.12
        m["o"].location = p + Vector((0, 0, m["size"] / 2 + hop))
        m["o"].rotation_euler = (0, 0, math.atan2(CAMP.x - p.x, -(CAMP.y - p.y)))
        hit = WAVE + (r / 15.0) ** (1 / 0.85) if t >= WAVE else 1e9
        m["hit"] = hit
        cut = -10.0 if t < hit else -0.05 + (m["size"] + 0.3) * ease((t - hit) / 0.9)
        for c in m["cuts"]: c.default_value = cut
        for o in [m["o"]] + list(m["o"].children): o.hide_render = t > hit + 1.0
    # 粒
    for f in FR:
        o = f["o"]
        if f["kind"] == "mote":
            if t < f["t0"]: o.hide_render = True; continue
            o.hide_render = False; dt = t - f["t0"]
            o.location = f["p"] + Vector((0.12 * math.sin(t * 0.7 + f["ph"]), 0.1 * math.sin(t * 0.5 + f["ph"] * 2), f["v"] * dt + 0.1 * math.sin(t + f["ph"])))
            o.scale = (f["s"] * ease(dt / 0.5),) * 3; o.rotation_euler = (t * 0.7 + f["ph"], t * 0.5, f["ph"])
        elif f["kind"] == "ember":
            if t > f["t0"]: o.hide_render = True; continue
            o.hide_render = False
            o.location = f["p"] + Vector((0.15 * math.sin(t * 1.1 + f["ph"]), 0.1 * math.sin(t * 0.8 + f["ph"]), (f["v"] * t + f["ph"]) % 3.6 - 0.4))
            o.scale = (f["s"],) * 3; o.rotation_euler = (t + f["ph"], t * 0.6, 0)
        else:
            m = f["mob"]; dt = t - m.get("hit", 1e9) - f["dl"]
            if dt < 0 or dt > 3.0: o.hide_render = True; continue
            o.hide_render = False
            base = m["o"].location + Vector((f["off"].x * m["size"], f["off"].y * m["size"], (f["off"].z - 0.5) * m["size"]))
            o.location = base + Vector((0.2 * math.sin(dt * 2 + f["ph"]), 0.2 * math.cos(dt * 2 + f["ph"]), f["v"] * dt))
            o.scale = (f["s"] * (1 - ease((dt - 2.0) / 1.0)),) * 3; o.rotation_euler = (dt * 3, dt * 2, f["ph"])
    T.set_expr(rtex, "mei", expr_at(t)); T.set_expr(rtex2, "mei", expr_at(t)); T.set_expr(rtex3, "mei", expr_at(t))
    return kind

HIDE_ = [x for x in arg("--hide", "").split(",") if x]
frames = TEST or range(START, STOP)
t0 = time.time()
for f in frames:
    p = os.path.join(OUT, "%04d.png" % (f + 1))
    if os.path.exists(p) and not TEST: continue
    t = f / FPS
    place(t)
    for o in bpy.data.objects:
        if any(o.name.startswith(h) for h in HIDE_): o.hide_render = True
    bpy.context.view_layer.update()
    sv = world_to_camera_view(sc, cam, sunq.location)                    # 光の筋（後処理）のための太陽の画面位置
    json.dump(dict(t=t, sun=[sv.x, sv.y, sv.z], light=light_at(t)), open(p[:-4] + ".json", "w"))
    tmp = p[:-4] + "_tmp.png"; sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True); os.replace(tmp, p)
    print("frame %s t=%.2f %.1fs" % (p, t, time.time() - t0), flush=True); t0 = time.time()
