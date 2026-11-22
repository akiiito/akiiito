"""
create_block6.py ― ブロック世界・完結編『触れたら影になる世界 最終決戦』（38秒・1話完結）
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
from blk6_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "14")); FPS = 24; N = int(END * FPS)
RS = float(arg("--res", "0.75"))
START = int(arg("--start", "0")); STOP = int(arg("--end", str(int(END_OUT * FPS))))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_BLK6W" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
LINES = json.load(open(os.path.join(HERE, "blk6_lines.json"), encoding="utf-8"))

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
hood = P("me_hood", (0.08, 0.08, 0.09), 0.9, noise=(40.0, 0.12))
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
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.6, 0.22, 1); em.inputs["Strength"].default_value = 5.0
    m1 = N.new("ShaderNodeMixShader"); Lk(band.outputs[0], m1.inputs[0]); Lk(src, m1.inputs[1]); Lk(em.outputs[0], m1.inputs[2])
    tr = N.new("ShaderNodeBsdfTransparent")
    m2 = N.new("ShaderNodeMixShader"); Lk(lt.outputs[0], m2.inputs[0]); Lk(m1.outputs[0], m2.inputs[1]); Lk(tr.outputs[0], m2.inputs[2])
    Lk(m2.outputs[0], out.inputs["Surface"])
    try: m.surface_render_method = "DITHERED"
    except Exception: pass
    return m

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


# ================================================================ 完結編：最終決戦
FIGHT_SEED = random.Random(66)
U = 0.8                                                                  # 巨人のブロック1個の大きさ
def part(name, nx, ny, nz, pivot, mat=None, unit=U):
    """nx×ny×nz のブロックの塊。pivot は塊の中での回転の中心（ブロック単位、塊の左下奥=0）"""
    cells = {(i, j, k): "b" for i in range(nx) for j in range(ny) for k in range(nz)}
    o = S7.voxel_mesh(name, cells, [mat or GIANT_M], {"b": (0, 0, 0)})
    for v in o.data.vertices: v.co = (v.co - Vector(pivot)) * unit
    return o
GIANT_M = dissolve(M["shadow"].copy()); GCUT = DCUT[-1]
ARMCUT_M = dissolve(M["shadow"].copy()); ACUT = DCUT[-1]
G0 = at(13.0); G0.z = float(hgt(int(math.floor(G0.x)), int(math.floor(G0.y))))
giant = bpy.data.objects.new("giant", None); bpy.context.collection.objects.link(giant); giant.location = G0
GP = {}
def gpart(key, nx, ny, nz, pivot, loc, parent, mat=None):
    o = part("g_" + key, nx, ny, nz, pivot, mat); o.parent = parent; o.location = loc; GP[key] = o; return o
gpart("legL", 3, 3, 6, (1.5, 1.5, 6), (1.3, 0, 4.8), giant); gpart("legR", 3, 3, 6, (1.5, 1.5, 6), (-1.3, 0, 4.8), giant)
torso = gpart("torso", 7, 4, 5, (3.5, 2, 0), (0, 0, 4.6), giant)
head = gpart("head", 4, 4, 4, (2, 2, 0), (0, 0, 4.0), torso)
eye_m = E("geye", (1.0, 0.06, 0.04), 18.0)
for sx in (-1, 1):
    e = cube("geye", eye_m, 1.0); e.parent = head; e.location = (sx * 0.65, -1.62, 1.75); e.scale = (0.7, 0.08, 0.32)
mouth = cube("gmouth", E("gmouth", (1.0, 0.2, 0.05), 6.0), 1.0); mouth.parent = head; mouth.location = (0, -1.62, 0.7); mouth.scale = (1.4, 0.06, 0.12)
uaR = gpart("uaR", 2, 2, 4, (1, 1, 4), (-3.6, 0, 3.8), torso); faR = gpart("faR", 2, 2, 4, (1, 1, 4), (0, 0, -3.2), uaR); fiR = gpart("fiR", 3, 3, 3, (1.5, 1.5, 3), (0, 0, -3.0), faR)
uaL = gpart("uaL", 2, 2, 4, (1, 1, 4), (3.6, 0, 3.8), torso); faL = gpart("faL", 2, 2, 4, (1, 1, 4), (0, 0, -3.2), uaL, ARMCUT_M); fiL = gpart("fiL", 3, 3, 3, (1.5, 1.5, 3), (0, 0, -3.0), faL, ARMCUT_M)
GIANT_ALL = [giant] + list(giant.children_recursive)
gaura = bpy.data.lights.new("gaura", "POINT"); gaura.color = (1.0, 0.1, 0.06); gaura.shadow_soft_size = 3.0
gauo = bpy.data.objects.new("gaura", gaura); bpy.context.collection.objects.link(gauo)
grim = bpy.data.lights.new("grim", "AREA"); grim.size = 8.0; grim.color = (0.45, 0.55, 1.0)
grimo = bpy.data.objects.new("grim", grim); bpy.context.collection.objects.link(grimo); grimo.location = G0 + Vector((4, 9, 12)); grimo.rotation_euler = (G0 + Vector((0, 0, 6)) - grimo.location).to_track_quat("-Z", "Y").to_euler()
# 塔（遠くの影の塔）
tw = {}
for z in range(0, 46):
    for x in range(5):
        for y in range(5):
            if x in (0, 4) or y in (0, 4): tw[(x, y, z)] = "stone"
tower = vox("tower", tw); tower.location = Vector((16, 72, -2)); tower.scale = (1.4, 1.4, 1.4)
for z in range(6, 46, 7):
    w = cube("twin", E("twin", (1.0, 0.1, 0.06), 6.0), 1.0); w.location = tower.location + Vector((3.5, -0.05, z * 1.4)); w.scale = (0.8, 0.1, 1.2)
# 日食（黒い円と赤い光の輪）→ 割れて太陽
ecl_m = P("eclipse", (0.0, 0.0, 0.0), 1.0)
bpy.ops.mesh.primitive_circle_add(vertices=64, radius=1.0, fill_type="NGON"); ecl = bpy.context.object; ecl.data.materials.append(ecl_m)
cor_m = bpy.data.materials.new("corona"); cor_m.use_nodes = True; _cn = cor_m.node_tree.nodes; _cl = cor_m.node_tree.links.new; _cn.clear()
_co = _cn.new("ShaderNodeOutputMaterial"); _ce = _cn.new("ShaderNodeEmission"); _ct = _cn.new("ShaderNodeBsdfTransparent"); _cx = _cn.new("ShaderNodeMixShader")
_cg = _cn.new("ShaderNodeTexGradient"); _cg.gradient_type = "SPHERICAL"; _cc = _cn.new("ShaderNodeTexCoord"); _cl(_cc.outputs["Object"], _cg.inputs["Vector"])
_cp = _cn.new("ShaderNodeMath"); _cp.operation = "POWER"; _cp.inputs[1].default_value = 2.0; _cl(_cg.outputs["Fac"], _cp.inputs[0])
_ce.inputs["Color"].default_value = (1.0, 0.12, 0.05, 1); COR_K = _ce.inputs["Strength"]; COR_K.default_value = 30.0
_cl(_cp.outputs[0], _cx.inputs[0]); _cl(_ct.outputs[0], _cx.inputs[1]); _cl(_ce.outputs[0], _cx.inputs[2]); _cl(_cx.outputs[0], _co.inputs["Surface"])
bpy.ops.mesh.primitive_plane_add(size=2.0); cor = bpy.context.object; cor.data.materials.append(cor_m)
for o, r, d in ((ecl, 26, 499), (cor, 70, 505)):
    o.location = CAMP + SDIR * d + Vector((0, 0, 30)); o.rotation_euler = (-SDIR).to_track_quat("Z", "Y").to_euler(); o.scale = (r, r, r); o.visible_shadow = False
    for a in ("visible_diffuse", "visible_glossy"): setattr(o, a, False)
ECL_P = ecl.location.copy()
# 千本柱（地面から巨人の胸へ突き上がるブロックの柱）
pil_m = pix("p_pillar", "stone", 0.6); _pb = pil_m.node_tree.nodes["Principled BSDF"]; _pb.inputs["Emission Color"].default_value = (0.2, 0.75, 1.0, 1); _pb.inputs["Emission Strength"].default_value = 0.6
PILL = []
CHEST = G0 + Vector((0, 0, 6.6))
for k in range(46):
    u_ = FIGHT_SEED.uniform(0.15, 0.95); base = CAMP.lerp(G0, u_) + Vector((FIGHT_SEED.uniform(-2.6, 2.6), FIGHT_SEED.uniform(-0.6, 0.6), 0)); base.z = 0.0
    tgt = CHEST + Vector((FIGHT_SEED.uniform(-1.8, 1.8), FIGHT_SEED.uniform(-0.6, 0.6), FIGHT_SEED.uniform(-1.6, 1.6)))
    d = tgt - base; L = d.length * FIGHT_SEED.uniform(0.55, 1.0)
    o = S7.voxel_mesh("pillar", {(0, 0, 0): "b"}, [pil_m], {"b": (0, 0, 0)})
    for v in o.data.vertices: v.co = Vector((v.co.x - 0.5, v.co.y - 0.5, v.co.z))
    o.location = base; o.rotation_euler = d.to_track_quat("Z", "Y").to_euler(); w = FIGHT_SEED.uniform(0.35, 0.7)
    PILL.append(dict(o=o, L=L, w=w, dl=k * 0.008 + FIGHT_SEED.uniform(0, 0.08)))
# 大剣（カメラにくっつく：組み上がる小ブロック）
sw_m = E("swordglow", (0.45, 0.85, 1.0), 4.0); swb_m = pix("p_sword", "stone", 0.25); _sb = swb_m.node_tree.nodes["Principled BSDF"]
_sb.inputs["Base Color"].default_value = (0.7, 0.85, 1.0, 1); _sb.inputs["Metallic"].default_value = 0.6
sword = bpy.data.objects.new("sword", None); bpy.context.collection.objects.link(sword); sword.parent = cam
SWC = []
for k in range(40):
    z = 0.12 + k * 0.08; o = cube("swc", swb_m if k % 5 else sw_m, 1.0); o.parent = sword
    SWC.append(dict(o=o, tgt=Vector((0, 0, z)), sc=Vector((0.16 - 0.002 * k, 0.05, 0.09)), frm=Vector((FIGHT_SEED.uniform(-1.5, 1.5), FIGHT_SEED.uniform(-1.0, 1.0), FIGHT_SEED.uniform(-1.5, 0.5))), dl=k * 0.012))
guard = cube("swguard", sw_m, 1.0); guard.parent = sword; guard.location = (0, 0, 0.06); guard.scale = (0.42, 0.08, 0.06)
hilt = cube("swhilt", P("hilt", (0.08, 0.08, 0.1), 0.5), 1.0); hilt.parent = sword; hilt.location = (0, 0, -0.08); hilt.scale = (0.05, 0.05, 0.22)
SWORD_ALL = [o["o"] for o in SWC] + [guard, hilt]
# 斬撃の弧
bpy.ops.mesh.primitive_torus_add(major_radius=5.0, minor_radius=0.12, major_segments=96, minor_segments=8); arc = bpy.context.object; arc.data.materials.append(E("arc", (0.6, 0.9, 1.0), 25.0))
arc.visible_shadow = False; ARC_K = [n for n in arc.data.materials[0].node_tree.nodes if n.type == "EMISSION"][0].inputs["Strength"]
# 天穿つ拳（地面から突き上がる金と黒の巨大な拳）
gold_m = E("fistgold", (1.0, 0.7, 0.25), 6.0); FG_K = [n for n in gold_m.node_tree.nodes if n.type == "EMISSION"][0].inputs["Strength"]
dfist = {}
for i in range(6):
    for j in range(6):
        for k in range(6): dfist[(i, j, k + 20)] = "g" if (i + j + k) % 2 else "s"
for i in range(1, 5):
    for j in range(1, 5):
        for k in range(0, 20): dfist[(i, j, k)] = "g" if (i + j + k) % 3 == 0 else "s"
bigfist = S7.voxel_mesh("bigfist", dfist, [gold_m, M["shadow"]], {"g": (0, 0, 0), "s": (1, 1, 1)})
for v in bigfist.data.vertices: v.co = (v.co - Vector((3, 3, 26))) * 0.9
# 爆発の光・衝撃の玉
boom_m = bpy.data.materials.new("boomshell"); boom_m.use_nodes = True; _bn = boom_m.node_tree.nodes; _bl = boom_m.node_tree.links.new; _bn.clear()
_bo = _bn.new("ShaderNodeOutputMaterial"); _be = _bn.new("ShaderNodeEmission"); _bt = _bn.new("ShaderNodeBsdfTransparent"); _bx = _bn.new("ShaderNodeMixShader")
_bw = _bn.new("ShaderNodeLayerWeight"); _bw.inputs["Blend"].default_value = 0.1
_bp = _bn.new("ShaderNodeMath"); _bp.operation = "MULTIPLY"; _bl(_bw.outputs["Facing"], _bp.inputs[0]); BOOM_K = _bp.inputs[1]; BOOM_K.default_value = 0.0
_be.inputs["Color"].default_value = (1.0, 0.75, 0.35, 1); _be.inputs["Strength"].default_value = 12.0
_bl(_bp.outputs[0], _bx.inputs[0]); _bl(_bt.outputs[0], _bx.inputs[1]); _bl(_be.outputs[0], _bx.inputs[2]); _bl(_bx.outputs[0], _bo.inputs["Surface"])
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.0); bshell = bpy.context.object; bshell.data.materials.append(boom_m); bshell.visible_shadow = False
for a in ("visible_diffuse", "visible_glossy"): setattr(bshell, a, False)
for p_ in bshell.data.polygons: p_.use_smooth = True
hitl = bpy.data.lights.new("hitl", "POINT"); hitl.color = (1.0, 0.8, 0.5); hitl.shadow_soft_size = 1.0
hitlo = bpy.data.objects.new("hitl", hitl); bpy.context.collection.objects.link(hitlo)
# 巨人のかけら（とどめで飛び散る → 金の粒）
GDEB = []
for k in range(110):
    o = cube("gdeb", GIANT_M if k % 3 else gold_m, 1.0); s_ = FIGHT_SEED.uniform(0.3, 1.0)
    p = G0 + Vector((FIGHT_SEED.uniform(-3, 3), FIGHT_SEED.uniform(-1.5, 1.5), FIGHT_SEED.uniform(1, 11)))
    v = (p - (G0 + Vector((0, 0, 5)))).normalized() * FIGHT_SEED.uniform(6, 16) + Vector((0, 0, FIGHT_SEED.uniform(2, 9)))
    GDEB.append(dict(o=o, p=p, v=v, s=s_, w=Vector((FIGHT_SEED.uniform(-6, 6), FIGHT_SEED.uniform(-6, 6), FIGHT_SEED.uniform(-6, 6))), life=FIGHT_SEED.uniform(1.2, 3.2)))
# 地面のがれき（拳がたたきつけられたとき）
SDEB = []
for k in range(40):
    o = cube("sdeb", M["dirt"] if k % 2 else M["grass_top"], 1.0)
    SDEB.append(dict(o=o, off=Vector((FIGHT_SEED.uniform(-2, 2), FIGHT_SEED.uniform(-2, 2), 0)), v=Vector((FIGHT_SEED.uniform(-4, 4), FIGHT_SEED.uniform(-4, 4), FIGHT_SEED.uniform(3, 9))),
                     s=FIGHT_SEED.uniform(0.15, 0.5), w=Vector((FIGHT_SEED.uniform(-8, 8), FIGHT_SEED.uniform(-8, 8), FIGHT_SEED.uniform(-8, 8)))))
# 手のまわりをまわる小ブロック（力をためる）
ORB = []
for k in range(26):
    o = cube("orb", pil_m, 1.0); o.parent = cam; o.visible_shadow = False
    ORB.append(dict(o=o, a=FIGHT_SEED.uniform(0, 6.28), r=FIGHT_SEED.uniform(0.12, 0.3), h=FIGHT_SEED.uniform(-0.1, 0.12), sp=FIGHT_SEED.uniform(4, 9), s=FIGHT_SEED.uniform(0.015, 0.035)))

# ---------------------------------------------------------------- 時間ごとの値
def light_at(t): return ease((t - SUN) / 3.0)
def blk_at(t):
    if t < CLENCH: return 0.35
    if t < FHIT: return 0.35 + 0.55 * ease((t - CLENCH) / 2.0)
    return 0.9 - 0.85 * ease((t - FHIT - 1.0) / 6.0)
def gauge_at(t): return 100.0 * blk_at(t) + (9.0 if DOMAIN <= t < FHIT else 0.0) * ease((t - DOMAIN) / 1.5)
def cam_matrix(pos, look, roll):
    q = (look - pos).to_track_quat("-Z", "Y"); m = q.to_euler().to_matrix() @ Matrix.Rotation(roll, 3, "Z")
    return Matrix.Translation(pos) @ m.to_4x4()
def rhand_world(s):
    rot = rukar.rotation_euler.z; loc = Vector(RH_L if s == "L" else RH_R) - Vector((0, 0.0, 0.02))
    return rukar.location + Matrix.Rotation(rot, 3, "Z") @ loc
def fist_world(side_):
    return (GP["fiL"] if side_ == "L" else GP["fiR"]).matrix_world @ Vector((0, 0, -1.2 * U))

def giant_pose(t):
    """巨人の関節の角度（x 回転）"""
    tor = -0.08 + 0.03 * math.sin(t * 1.3); uaR_ = 0.0; faR_ = -0.2; uaL_ = -0.75; faL_ = -1.35; hd = 0.0
    if SWING - 0.5 <= t < SMASH + 1.0:                                   # 右腕をふりかぶって、たたきつける
        up = ease((t - SWING + 0.5) / 0.5); dn = ease((t - SWING - 0.25) / (SMASH - SWING - 0.25)) ** 2
        uaR_ = -2.8 * up * (1 - dn) + (-0.9) * dn; faR_ = -0.4 * (1 - dn); tor = -0.08 - 0.45 * dn
        back = ease((t - SMASH - 0.4) / 0.6); uaR_ = uaR_ * (1 - back); tor = tor * (1 - back) - 0.08 * back
    if t >= SLASH:                                                        # 左腕を失う → よろめく
        uaL_ = -0.75 + 0.6 * ease((t - SLASH) / 0.6); tor += 0.15 * win(t, SLASH, SLASH + 1.2, 0.2, 0.8)
    if SWARM - 0.4 <= t < DOMAIN:                                         # 咆哮
        hd = -0.35 * win(t, SWARM - 0.4, SWARM + 1.6, 0.3, 0.5) + 0.04 * math.sin(t * 40) * win(t, SWARM - 0.2, SWARM + 1.4, 0.1, 0.3); tor -= 0.12 * win(t, SWARM - 0.4, SWARM + 1.6, 0.3, 0.5)
    if t >= FHIT - 0.6: tor = -0.08 + 0.35 * ease((t - FHIT + 0.6) / 0.6)
    return tor, hd, uaR_, faR_, uaL_, faL_

HIT_LIST = [(PHIT, 1.0, "pill"), (SMASH, 1.1, "smash"), (SLASH, 1.0, "slash"), (WAVE, 0.8, "wave"), (WAVE + 0.5, 0.8, "wave"), (WAVE + 1.0, 0.8, "wave"), (FHIT, 1.5, "fhit"), (SUN, 1.0, "sun")]
def impact_at(t):
    best = (0.0, None, None)
    for ti, s, kind in HIT_LIST:
        if ti <= t < ti + 0.6:
            v = s * math.exp(-(t - ti) / 0.12)
            if v > best[0]: best = (v, ti, kind)
    return best
def hit_point(kind):
    if kind == "pill": return CHEST
    if kind == "smash": return SMASH_P
    if kind == "slash": return GP["uaL"].matrix_world @ Vector((0, 0, -3.0 * U))
    if kind == "wave": return WC + Vector((0, 4, 0.5))
    if kind == "fhit": return G0 + Vector((0, 0, 5.0))
    return ECL_P
SMASH_P = CAMP + Vector((0.4, 2.2, -CAMP.z)); DODGE = Vector((-2.4, -0.6, -0.15))

def shot(t):
    """(カメラ位置, 見る先, レンズ, F値, 主観か)"""
    pov = CAMP.copy(); gh = head.matrix_world @ Vector((0, -1.0, 2.0))
    if t < 3.0:
        f = model_at(t)[1]; return f + Vector((1.5 - 0.15 * t, -3.4 + 0.2 * t, 1.2)), f + Vector((0, 0, 0.95)), 34 + 2 * t, 3.2, False
    if t < 5.9: return pov, gh.lerp(fist_world("L"), 0.25), 20 + 1.5 * (t - 3), 4.0, True
    if t < PILLARS: return pov, pov + Vector((0.0, 1.0, -0.7)), 24, 2.8, True
    if t < SWING: return CAMP + Vector((12.0, 1.5, 2.6)) + Vector((-0.8 * (t - PILLARS), 0, 0)), CHEST + Vector((0, -4.5, -2.0)), 24, 8.0, False
    if t < SMASH: return pov, fist_world("R").lerp(gh, 0.2), 16, 4.0, True
    if t < SWORD:
        d = ease((t - SMASH) / 0.25); p = pov + DODGE * d
        return p, SMASH_P + Vector((0, 0, 0.6)), 18, 5.6, True
    if t < SLASH: return pov + DODGE, pov + DODGE + Vector((0.15, 1.0, -0.15)), 22, 2.8, True
    if t < CATCH:
        k = ease((t - SLASH) / 0.5); return CAMP + Vector((5.5, 5.0, 3.0)), (GP["uaL"].matrix_world @ Vector((0, 0, -3.0 * U))).lerp(model_at(t)[1] + Vector((0, 0, 0.8)), k), 26, 5.6, False
    if t < SWARM: return pov, rface(t), 22 + 4 * ease((t - CATCH) / 3.0), 2.0, True
    if t < DOMAIN: return pov, pov + Vector((0.0, 1.0, 0.05)), 18, 4.0, True
    if t < RISE: return pov, gh.lerp(pov + Vector((0, 1, -0.3)), 0.45), 20, 4.0, True
    if t < FHIT + 0.2: return CAMP + Vector((-6.0, -4.0, 0.7)), G0 + Vector((0, 0, 5.0)), 20, 8.0, False
    if t < FADEG: k = ease((t - FHIT - 0.2) / 1.5); return CAMP + Vector((-6.0, -4.0, 0.7)).lerp(Vector((-4, -9, 1.2)), k), (G0 + Vector((0, 0, 5))).lerp(ECL_P, 0.0), 18 - 2 * k, 8.0, False
    if t < DAWN: return pov, (G0 + Vector((0, 0, 7))).lerp(pov + SDIR * 20, ease((t - FADEG) / 3.0)), 20, 5.6, True
    if t < 30.3: return pov, pov + Vector((0.0, 1.0, -0.75)), 24, 2.8, True
    if t < TITLE: return pov, rface(t), 26 + 3 * ease((t - 30.3) / 4.0), 1.8, True
    k = ease((t - TITLE) / 3.5); return CAMP + Vector((1.6, -2.0, 0.1)) + Vector((0.4, -1.0, 0.6)) * k, at(3.0) + Vector((0, 0, 1.6)) + SDIR * 0.0, 20 - 2 * k, 5.6, False
def rface(t): p = model_at(t)[1]; return Vector((p.x, p.y, 1.43))

def model_at(t):
    if t < SLASH: return "down", fist_world("L") + Vector((0, 0, 1.15))
    if t < CATCH:
        u = (t - SLASH) / (CATCH - SLASH); a = fist_world("L") if False else FIST_AT_SLASH; b = RG.copy()
        p = a.lerp(b, u); p.z = a.z * (1 - u) ** 1.6 + 0.0; return "down", p
    if t < DAWN: return "reach", RG
    return "down", RF
FIST_AT_SLASH = None

def arms_at(t, cmat, pos_):
    out = {}; inv = cmat.inverted()
    hold = win(t, CATCH - 0.1, DAWN - 0.2, 0.3, 0.5)
    for s, sx in (("L", -1), ("R", 1)):
        sh = Vector((0.22 * sx, -0.55, 0.05)); el = Vector((0.2 * sx, -0.32, -0.28)); hn = Vector((0.11 * sx, -0.16, -0.42))
        cl = win(t, CLENCH - 0.2, PILLARS, 0.3, 0.1)                     # にぎりしめた拳を見る（ふるえる）
        if cl > 0:
            tr = 0.008 * math.sin(t * 37 + sx); hn = hn.lerp(Vector((0.1 * sx + tr, -0.12, -0.3)), cl); el = el.lerp(Vector((0.25 * sx, -0.32, -0.16)), cl)
        th = win(t, PILLARS - 0.05, PILLARS + 0.9, 0.08, 0.3)            # 両手を前に突き出す
        if th > 0: hn = hn.lerp(Vector((0.08 * sx, -0.5, -0.1)), th); el = el.lerp(Vector((0.18 * sx, -0.45, -0.1)), th)
        sw = win(t, SWORD - 0.1, SLASH + 0.7, 0.2, 0.3)                   # 大剣をにぎる（両手を中央に）
        if sw > 0:
            k = ease((t - SLASH + 0.15) / 0.3); hc = Vector((0.03 * sx, -0.3, -0.28)).lerp(Vector((0.35 + 0.03 * sx, -0.4, -0.38)), k)
            hn = hn.lerp(hc, sw); el = el.lerp(Vector((0.22 * sx, -0.4, -0.25)), sw)
        if hold > 0:                                                      # ルカの手をにぎる
            best = min("LR", key=lambda q: abs((inv @ rhand_world(q)).x - 0.1 * sx))
            w = rhand_world(best) + (pos_ - rhand_world(best)).xy.to_3d().normalized() * 0.1 + Vector((0, 0, 0.035))
            tgt = inv @ w; up = win(t, DOMAIN, FHIT + 0.6, 0.6, 0.6)
            tgt = tgt + Vector((0, 0.05, 0.12)) * up
            hn = hn.lerp(tgt, min(1.0, hold)); el = el.lerp(Vector((0.21 * sx, (tgt.y - 0.55) / 2 + 0.06, tgt.z / 2 - 0.02)), min(1.0, hold))
        lk = win(t, DAWN, 30.3, 0.4, 0.4)                                # 元に戻った自分の手を見る
        if lk > 0: hn = hn.lerp(Vector((0.115 * sx, -0.07, -0.36)), lk); el = el.lerp(Vector((0.27 * sx, -0.32, -0.16)), lk)
        out[s] = (sh, el, hn)
    return out

def face_cam(o, p, tgt=None):
    o.location = p; tg = tgt or CAMP; d = Vector((tg.x - p.x, tg.y - p.y, 0)).normalized()
    o.rotation_euler = (0, 0, math.atan2(-d.x, d.y))
RSP = [(l[0], l[1]) for l in LINES if l[5] == "ruka"]
def expr_at(t):
    talking = any(st <= t <= en - 0.05 for st, en in RSP); flap = talking and (int(t * 12) % 3 != 2)
    if t < SLASH: e = "shocktalk" if False else ("sadtalk" if flap else "sad")
    elif t < CATCH: e = "shockc"
    elif t < SWARM: e = "tearsmiletalk" if flap else "tearsmile"
    elif t < SUN: e = "cold" if False else "sad"
    elif t < DAWN: e = "smile"
    else: e = "blushtalk" if flap else "blushsmile"
    if (t % 3.1) < 0.12 and not talking and e in ("sad", "smile", "blushsmile"): e = {"sad": "sadblink", "smile": "blink", "blushsmile": "blink"}[e]
    return e

def place(t):
    global FIST_AT_SLASH
    # 巨人
    tor, hd, uaR_, faR_, uaL_, faL_ = giant_pose(t)
    torso.rotation_euler = (tor, 0, 0.05 * math.sin(t * 0.7)); head.rotation_euler = (hd, 0, 0.1 * math.sin(t * 0.9))
    uaR.rotation_euler = (uaR_, 0, 0.15); faR.rotation_euler = (faR_, 0, 0); uaL.rotation_euler = (uaL_, 0, -0.3); faL.rotation_euler = (faL_, 0, 0)
    bpy.context.view_layer.update()
    if FIST_AT_SLASH is None or t < SLASH:
        FIST_AT_SLASH = fist_world("L") + Vector((0, 0, 1.15))
    gone = t >= FHIT
    for o in GIANT_ALL:
        if o.type == "MESH": o.hide_render = gone
    ACUT.default_value = -10.0 if t < SLASH + 0.05 else (G0.z + 2.0 + 9.0 * ease((t - SLASH - 0.05) / 0.9))   # 斬られた左腕：下から溶ける（ここでは上へ逆に）
    faL.hide_render = gone or t > SLASH + 1.0; fiL.hide_render = faL.hide_render
    if t >= SLASH:                                                         # 斬られた前腕は外れて落ちる
        k = t - SLASH; faL.parent = None if False else faL.parent
    GCUT.default_value = -10.0
    gauo.location = G0 + Vector((0, -2.5, 7)); gaura.energy = 4000.0 * (1 - light_at(t)) * (0 if gone else 1); grim.energy = 9000.0 * (1 - light_at(t)) * (0 if gone else 1)
    # 日食
    lt = light_at(t)
    ecl.hide_render = t >= SUN + 0.3; cor.hide_render = ecl.hide_render
    COR_K.default_value = 30.0 + 300.0 * win(t, SUN - 0.4, SUN + 0.3, 0.3, 0.1)
    # 千本柱
    for p in PILL:
        k = ease((t - PILLARS - p["dl"]) / 0.35) * (1 - ease((t - SWING - 0.3) / 0.6))
        o = p["o"]; o.hide_render = k <= 0.001
        if not o.hide_render: o.scale = (p["w"], p["w"], max(0.01, p["L"] * k))
    # 大剣
    form = (t >= SWORD - 0.05) and (t < SLASH + 0.8)
    for c in SWC:
        o = c["o"]; o.hide_render = not form
        if not form: continue
        k = ease((t - SWORD - c["dl"]) / 0.45); o.location = c["frm"].lerp(c["tgt"], k); o.scale = c["sc"] * (0.3 + 0.7 * k); o.rotation_euler = (4 * (1 - k), 3 * (1 - k), 0)
    guard.hide_render = hilt.hide_render = not form
    sw_k = ease((t - SLASH + 0.15) / 0.3)
    sword.location = Vector((0.0, -0.3, -0.42)).lerp(Vector((0.32, -0.42, -0.5)), sw_k)
    bd = Vector((0.0, 0.62, -0.78)).lerp(Vector((0.85, -0.35, -0.4)), sw_k).normalized()
    sword.rotation_euler = bd.to_track_quat("Z", "Y").to_euler()
    arc.hide_render = not (SLASH - 0.05 <= t < SLASH + 0.45)
    if not arc.hide_render:
        cpt = GP["uaL"].matrix_world @ Vector((0, 0, -3.0 * U)); arc.location = cpt; arc.rotation_euler = (math.radians(70), math.radians(20), t * 3)
        sc_ = 0.6 + 0.6 * ease((t - SLASH + 0.05) / 0.2); arc.scale = (sc_, sc_, 1.0); ARC_K.default_value = 25.0 * (1 - ease((t - SLASH) / 0.45))
    # 天穿つ拳
    rk = (t - RISE) / (FHIT - RISE)
    bigfist.hide_render = not (RISE - 0.05 <= t < SUN + 1.6)
    if not bigfist.hide_render:
        z = -30.0 + 34.0 * ease(min(rk, 1.0)) ** 1.6 + (6.0 * ease((t - FHIT) / 1.2) if t > FHIT else 0)
        bigfist.location = Vector((G0.x, G0.y, z)); bigfist.rotation_euler = (0, 0, 0.3 * min(rk, 1.0))
        FG_K.default_value = 6.0 + 30.0 * win(t, FHIT - 0.1, FHIT + 0.5, 0.1, 0.4); s_ = 1.0 - ease((t - SUN - 0.6) / 1.0); bigfist.scale = (s_, s_, s_)
    # とどめの爆発・巨人のかけら
    for d in GDEB:
        o = d["o"]; dt = t - FHIT
        if dt < 0 or dt > d["life"]: o.hide_render = True; continue
        o.hide_render = False; o.location = d["p"] + d["v"] * dt + Vector((0, 0, -4.0 * dt * dt)); o.rotation_euler = d["w"] * dt
        o.scale = (d["s"] * (1 - ease((dt - d["life"] + 0.8) / 0.8)),) * 3
    # 地面のがれき（たたきつけ）
    for d in SDEB:
        o = d["o"]; dt = t - SMASH
        if dt < 0 or dt > 2.2: o.hide_render = True; continue
        o.hide_render = False; p = SMASH_P + d["off"] + d["v"] * dt + Vector((0, 0, -9.8 * dt * dt / 2)); p.z = max(p.z, d["s"] / 2); o.location = p; o.scale = (d["s"],) * 3; o.rotation_euler = d["w"] * min(dt, 1.0)
    # 衝撃の玉・光
    iv, ti, kind = impact_at(t)
    bshell.hide_render = ti is None or kind in ("sun", "slash")
    if ti is not None:
        hp = hit_point(kind); k = (t - ti) / 0.6
        big = {"fhit": 9.0, "smash": 3.5, "pill": 3.0, "slash": 2.5, "wave": 2.0}.get(kind, 2.0)
        bshell.location = hp; r = 0.3 + big * ease(k ** 0.5); bshell.scale = (r, r, r); BOOM_K.default_value = 0.45 * (1 - k) ** 3
        hitlo.location = hp; hitl.energy = 30000.0 * iv * (3.0 if kind == "fhit" else 1.0)
    else: hitl.energy = 0.0
    # 影の群れ（押しよせる → 金の波で溶ける）
    for m in mobs:
        a = m["a"]; r = m["r0"] + 6.0 - 7.0 * ease((t - SWARM) / 1.8) if t >= SWARM - 1.0 else 60.0
        p = Vector((WC.x + r * math.cos(a), WC.y + r * math.sin(a), 0)); hop = abs(math.sin(t * 5.6 + m["ph"])) * 0.25
        m["o"].location = p + Vector((0, 0, m["size"] / 2 + hop)); m["o"].rotation_euler = (0, 0, math.atan2(CAMP.x - p.x, -(CAMP.y - p.y)))
        hit = WAVE + (max(r, 0.1) / 15.0) ** (1 / 0.85) if t >= WAVE else 1e9; m["hit"] = hit
        cut = -10.0 if t < hit else -0.05 + (m["size"] + 0.3) * ease((t - hit) / 0.6)
        for c in m["cuts"]: c.default_value = cut
        for o in [m["o"]] + list(m["o"].children): o.hide_render = t < SWARM - 1.0 or t > hit + 0.8
    R_ = -50.0 if t < WAVE else 15.0 * (t - WAVE) ** 0.85
    WV.nodes["wcx"].outputs[0].default_value = WC.x; WV.nodes["wcy"].outputs[0].default_value = WC.y; WV.nodes["wr"].outputs[0].default_value = R_
    WV.nodes["ws"].outputs[0].default_value = 0.0 if t < WAVE else 5.0 * math.exp(-(t - WAVE) / 2.6)
    ring.hide_render = not (WAVE <= t < WAVE + 2.5)
    if not ring.hide_render: ring.location = (WC.x, WC.y, 0.0); ring.scale = (max(R_, 0.05),) * 2 + (2.0 + 1.5 * ease((t - WAVE) / 0.6),); RING_K.default_value = math.exp(-(t - WAVE) / 1.2)
    # ルカ
    kind_, rp_ = model_at(t)
    for k_, o in MODELS.items():
        for ch in [o] + list(o.children_recursive):
            if ch.type == "MESH" and not ch.name.startswith("rukar_sphere"): ch.hide_render = k_ != kind_
    tgt = MODELS[kind_]
    face_cam(tgt, rp_)
    if kind_ == "down" and SLASH <= t < CATCH: tgt.rotation_euler = (0.6 * math.sin(t * 9), 0.4, tgt.rotation_euler.z)
    else: tgt.rotation_euler = (0, 0, tgt.rotation_euler.z)
    # カメラ
    pos, look, lens, fst, pov = shot(t)
    iv2 = iv
    sh = 0.0
    if ti is not None: sh = 0.06 * iv2 * (1.0 if pov else 3.0)
    if SWARM - 0.4 <= t < SWARM + 1.6: sh = max(sh, 0.012)
    pos = pos + Vector((sh * math.sin(t * 61), sh * math.sin(t * 47), sh * math.sin(t * 53))) + Vector((0.005 * math.sin(t * 1.3), 0.003 * math.sin(t * 0.9), 0.005 * math.sin(t * 1.9)))
    roll = 0.0
    if SMASH <= t < SMASH + 0.4: roll = 0.25 * math.sin(math.pi * (t - SMASH) / 0.4)
    if SLASH - 0.2 <= t < SLASH + 0.2: roll = -0.3 * math.sin(math.pi * (t - SLASH + 0.2) / 0.4)
    cam.location = pos; W.aim(cam, look); cam.rotation_euler.rotate_axis("Z", roll)
    cam.data.lens = lens; cam.data.dof.aperture_fstop = fst
    cmat = cam_matrix(pos, look, roll)
    for s, (sh_, el, hn) in arms_at(t, cmat, pos).items(): set_arm(s, sh_, el, hn)
    for s in "LR":                                                         # 自分の腕は主観のときだけ
        for o in [ARMS[s]["up"], ARMS[s]["lo"]] + list(ARMS[s]["hd"].children): o.hide_render = not pov
    for c in SWC: c["o"].hide_render = c["o"].hide_render or not pov
    guard.hide_render = guard.hide_render or not pov; hilt.hide_render = hilt.hide_render or not pov
    bpy.context.view_layer.update()
    foc = (look - pos).length
    if pov and (t < 5.9 and t >= 3.0): foc = 12.0
    if pov and (CLENCH - 0.2 <= t < PILLARS or DAWN <= t < 30.3 or SWORD <= t < SLASH): foc = 0.45
    if pov and CATCH <= t < SWARM: foc = (rface(t) - pos).length
    cam.data.dof.focus_distance = max(0.3, min(60.0, foc))
    blk = blk_at(t); light = lt
    gold_h = win(t, CATCH, FHIT + 0.8, 0.5, 0.8)
    for s in "LR":
        k = ARMS[s]["m"]; HV[k]["cast"].default_value = 1.6 * gold_h; HV[k]["blk"].default_value = 0.05 + blk ** 2
        HV[k]["red"].default_value = 2.0 + 4.0 * max(0.0, blk - 0.4)
    for s in "LR":
        h = RHANDS[s]["hd"]; vis = kind_ == "reach"
        for ch in h.children: ch.hide_render = not vis
        if not vis: continue
        w = rhand_world(s); fwd_ = Vector((pos.x - w.x, pos.y - w.y, 0)).normalized()
        y = fwd_; z = Vector((0, 0, -1)); x = y.cross(z).normalized(); z = x.cross(y)
        h.location = w; h.rotation_euler = Matrix((x, y, z)).transposed().to_euler()
        k = RHANDS[s]["m"]; HV[k]["cast"].default_value = 1.6 * gold_h; HV[k]["blk"].default_value = 0.0 if t > FHIT + 1 else 0.3 * (s == "L"); HV[k]["red"].default_value = 0.0
    # 手のまわりの小ブロック
    orb_on = (CLENCH - 0.1 <= t < PILLARS + 0.3) and pov
    for o_ in ORB:
        o = o_["o"]; o.hide_render = not orb_on
        if not orb_on: continue
        a = o_["a"] + t * o_["sp"]; c_ = Vector((0.0, -0.12, -0.32)); o.location = c_ + Vector((o_["r"] * math.cos(a), o_["h"], o_["r"] * math.sin(a) * 0.5))
        o.scale = (o_["s"] * ease((t - CLENCH + 0.1) / 0.5),) * 3; o.rotation_euler = (a, a * 0.7, 0)
    hl.energy = (3.0 + 0.8 * math.sin(t * 9)) * (1 - light)
    gm = (rhand_world("L") + rhand_world("R")) / 2 if kind_ == "reach" else rp_ + Vector((0, 0, 1.0))
    glo.location = gm + Vector((0, 0, 0.12)); gl.energy = 12.0 * gold_h + 60.0 * win(t, DOMAIN, FHIT, 0.8, 0.3)
    # 空と光
    wmix.inputs["Factor"].default_value = light
    wsk.inputs["B"].default_value = (1.0 * light + 0.02,) * 3 + (1,); CLOUD_B.inputs["Emission Strength"].default_value = 0.7 * light
    sunq.hide_render = light < 0.02; halo.hide_render = light < 0.02
    sunq.location = CAMP + SDIR * 500 + Vector((0, 0, -40 * (1 - light))); HALO_E.inputs["Strength"].default_value = 6.0 * light
    sl.energy = 4.2 * light; fl.energy = 1.6 * (1 - light) + 0.25 * light
    fogcol = Vector((0.06, 0.01, 0.03)).lerp(Vector((0.62, 0.42, 0.32)), light)
    FOG.nodes["fogcol"].inputs["Color"].default_value = (*fogcol, 1); FOG.nodes["fogcol"].inputs["Strength"].default_value = 1.0
    FOG.nodes["dens"].outputs[0].default_value = 0.02 - 0.01 * light
    for n in face_em: n.inputs["Strength"].default_value = 0.95 + 0.25 * gold_h + 0.15 * light
    key.energy = 22.0; key.color = Vector((0.6, 0.65, 1.0)).lerp(Vector((1.0, 0.8, 0.62)), light)
    rimo.location = rp_ + Vector((0.25, 0.9, 1.75)); rimo.rotation_euler = (rp_ + Vector((0, 0, 1.3)) - rimo.location).to_track_quat("-Z", "Y").to_euler()
    rim.energy = 70.0 * (1 - light); emb_l.energy = 30.0 * (1 - light)
    # 粒
    for f in FR:
        o = f["o"]
        if f["kind"] == "mote":
            if t < f["t0"]: o.hide_render = True; continue
            o.hide_render = False; dt = t - f["t0"]
            o.location = f["p"] + Vector((0.12 * math.sin(t * 0.7 + f["ph"]), 0.1 * math.sin(t * 0.5 + f["ph"] * 2), f["v"] * dt + 0.1 * math.sin(t + f["ph"])))
            o.scale = (f["s"] * ease(dt / 0.5),) * 3
        elif f["kind"] == "ember":
            if t > FHIT: o.hide_render = True; continue
            o.hide_render = False
            o.location = f["p"] + Vector((0.15 * math.sin(t * 1.1 + f["ph"]), 0.1 * math.sin(t * 0.8 + f["ph"]), (f["v"] * t + f["ph"]) % 3.6 - 0.4)); o.scale = (f["s"],) * 3
        else:
            m = f["mob"]; dt = t - m.get("hit", 1e9) - f["dl"]
            if dt < 0 or dt > 3.0: o.hide_render = True; continue
            o.hide_render = False
            base = m["o"].location + Vector((f["off"].x * m["size"], f["off"].y * m["size"], (f["off"].z - 0.5) * m["size"]))
            o.location = base + Vector((0.2 * math.sin(dt * 2 + f["ph"]), 0.2 * math.cos(dt * 2 + f["ph"]), f["v"] * dt)); o.scale = (f["s"] * (1 - ease((dt - 2.0) / 1.0)),) * 3
    T.set_expr(rtex, "mei", expr_at(t)); T.set_expr(rtex2, "mei", expr_at(t)); T.set_expr(rtex3, "mei", expr_at(t))
    dash = win(t, SMASH - 0.05, SMASH + 0.3, 0.05, 0.2) + win(t, SLASH - 0.15, SLASH + 0.3, 0.05, 0.2) + win(t, RISE, FHIT, 0.2, 0.1)
    meta = dict(impact=iv, kind=kind or "", dash=min(1.0, dash), domain=win(t, DOMAIN, FHIT, 0.25, 0.15), gauge=gauge_at(t), pov=pov)
    if ti is not None:
        sv = world_to_camera_view(sc, cam, hit_point(kind)); meta["imp"] = [sv.x, sv.y, sv.z]
    return meta

W0, W1 = int(round(8.3 * FPS)), int(round(out_t(13.9) * FPS))
frames = TEST or range(max(START, W0), min(STOP, W1))
t0 = time.time()
for f in frames:
    p = os.path.join(OUT, "%04d.png" % (f + 1))
    if os.path.exists(p) and not TEST: continue
    t = story_t(f / FPS)
    meta = place(t)
    for o in bpy.data.objects:
        if any(o.name.startswith(h) for h in [x for x in arg('--hide', '').split(',') if x]): o.hide_render = True
    bpy.context.view_layer.update()
    if TEST:
        for o in bpy.data.objects:
            if o.type == 'MESH' and not o.hide_render and (o.matrix_world.translation - cam.location).length < 6: print('NEAR', o.name, tuple(round(v, 1) for v in o.matrix_world.translation), tuple(round(v, 1) for v in o.dimensions))
    sv = world_to_camera_view(sc, cam, sunq.location)
    meta.update(t=t, sun=[sv.x, sv.y, sv.z], light=light_at(t))
    json.dump(meta, open(p[:-4] + ".json", "w"))
    tmp = p[:-4] + "_tmp.png"; sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True); os.replace(tmp, p)
    print("frame %s t=%.2f %.1fs" % (p, t, time.time() - t0), flush=True); t0 = time.time()
    if TEST: print("CAM", f, tuple(round(v, 2) for v in cam.location), cam.data.lens, meta.get("pov"))
