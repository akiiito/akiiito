"""
create_battle.py
5秒 / 120f / 24fps / 720x1280 縦型  一人称ブロック調バトルアニメーション生成スクリプト

実行例:
  python create_battle.py --anim                 # 全フレームPNG出力 + battle_test.blend保存
  python create_battle.py --frames 1,40,84 --res 50 --samples 16   # 代表フレームの確認用
  blender -b -P create_battle.py -- --anim       # Blender本体からでも可

構成:
  0-1s  青ブロック敵が走って接近（IK脚 + 腕振り + 重心の上下動 + 制動）
  1-2s  腕を振り上げてチャージ → 青い雷撃を発射（反動つき）
  2-3s  主人公（カメラ+一人称の腕と剣）が左へ回避（予備動作→急加速→オーバーシュート）
  3-4s  踏み込み + 袈裟斬り（振りかぶり→ヒットストップ→フォロースルー）
  4-5s  敵が吹き飛び、着地して滑り、片膝をつく
"""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, Quaternion, Matrix, Euler

# ------------------------------------------------------------------ args
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = argv[1:]

def arg(name, default=None):
    if name in argv:
        i = argv.index(name)
        if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
            return argv[i + 1]
        return True
    return default

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = arg("--out", HERE)
FRAME_DIR = arg("--frame-dir", os.path.join(OUT_DIR, "frames"))
RES = int(arg("--res", 100))
SAMPLES = int(arg("--samples", 40))
FRAMES_ARG = arg("--frames", None)
DO_ANIM = bool(arg("--anim", False))
NO_SAVE = bool(arg("--no-save", False))

FPS, F_END = 24, 120
random.seed(11)

# ------------------------------------------------------------------ scene reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, F_END
COL = scene.collection
prefs = bpy.context.preferences.edit
prefs.keyframe_new_interpolation_type = 'LINEAR'

# ------------------------------------------------------------------ easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

EASE = {
    "lin": lambda t: t,
    "smooth": lambda t: t * t * (3 - 2 * t),
    "smoother": lambda t: t * t * t * (t * (6 * t - 15) + 10),
    "in": lambda t: t * t,
    "in3": lambda t: t * t * t,
    "out": lambda t: 1 - (1 - t) ** 2,
    "out3": lambda t: 1 - (1 - t) ** 3,
    "out5": lambda t: 1 - (1 - t) ** 5,
    "hold": lambda t: 0.0,
    "snap": lambda t: 1.0,
}

def lerp(a, b, t):
    return a + (b - a) * t

class Track:
    """keys: [(frame, value, ease_into_this_key), ...]  value: float / tuple"""
    def __init__(self, keys):
        self.keys = [(k[0], k[1], k[2] if len(k) > 2 else "smooth") for k in keys]

    def __call__(self, f):
        ks = self.keys
        if f <= ks[0][0]:
            return ks[0][1]
        for i in range(1, len(ks)):
            f1, v1, e = ks[i]
            if f <= f1:
                f0, v0, _ = ks[i - 1]
                t = EASE[e]((f - f0) / (f1 - f0)) if f1 > f0 else 1.0
                if isinstance(v0, (tuple, list)):
                    return tuple(lerp(a, b, t) for a, b in zip(v0, v1))
                return lerp(v0, v1, t)
        return ks[-1][1]

class PoseTimeline:
    """key poses (partial dicts) -> per-channel tracks, missing channels carry over."""
    def __init__(self, defaults, keys):
        chans = {k: [] for k in defaults}
        cur = dict(defaults)
        for item in keys:
            f, pose, ease = item
            cur = dict(cur)
            cur.update(pose)
            for c in chans:
                chans[c].append((f, cur[c], ease))
        self.tracks = {c: Track(v) for c, v in chans.items()}

    def __call__(self, f):
        return {c: t(f) for c, t in self.tracks.items()}

# ------------------------------------------------------------------ materials
def principled(name, color, rough=0.92, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.12
    if emit is not None:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    m.diffuse_color = (*color, 1)
    return m

def emissive(name, color, strength, fade_attr=False):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    if fade_attr:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name = "fade"
        nt.links.new(at.outputs["Fac"], mix.inputs["Fac"])
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(em.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
    else:
        nt.links.new(em.outputs[0], out.inputs["Surface"])
    m.diffuse_color = (*color, 1)
    return m

M = {}
# arena (purple matte)
M["floor_a"] = principled("floor_a", (0.13, 0.06, 0.24))
M["floor_b"] = principled("floor_b", (0.10, 0.05, 0.19))
M["floor_c"] = principled("floor_c", (0.16, 0.08, 0.29))
M["wall"] = principled("wall", (0.12, 0.06, 0.22))
M["wall_top"] = principled("wall_top", (0.22, 0.12, 0.36))
M["pillar"] = principled("pillar", (0.17, 0.09, 0.30))
M["stand"] = principled("stand", (0.07, 0.04, 0.12))
M["crowd"] = principled("crowd", (0.05, 0.03, 0.09))
M["banner"] = principled("banner", (0.40, 0.04, 0.22))
M["rune"] = emissive("rune", (1.0, 0.25, 0.95), 4.0)
M["rune_dim"] = emissive("rune_dim", (0.65, 0.2, 1.0), 2.0)
M["crystal"] = emissive("crystal", (0.75, 0.35, 1.0), 6.0)
M["flame"] = emissive("flame", (0.85, 0.3, 1.0), 9.0)
M["eye_red"] = emissive("eye_red", (1.0, 0.15, 0.35), 6.0)
M["portal"] = emissive("portal", (0.9, 0.25, 0.85), 2.2)
M["portal_in"] = principled("portal_in", (0.05, 0.02, 0.10), emit=(0.35, 0.05, 0.45), strength=1.0)
M["float"] = principled("float", (0.25, 0.14, 0.42))
M["dust"] = principled("dust", (0.55, 0.45, 0.70))
# enemy (blue blocks)
M["e_blue"] = principled("e_blue", (0.08, 0.32, 0.95))
M["e_dark"] = principled("e_dark", (0.03, 0.10, 0.42))
M["e_light"] = principled("e_light", (0.35, 0.65, 1.0))
M["e_eye"] = emissive("e_eye", (0.6, 1.0, 1.0), 8.0)
# player
M["sleeve"] = principled("sleeve", (0.42, 0.05, 0.09))
M["cuff"] = principled("cuff", (0.85, 0.62, 0.18))
M["glove"] = principled("glove", (0.18, 0.10, 0.07))
M["blade"] = principled("blade", (0.78, 0.80, 0.92), rough=0.8,
                        emit=(0.6, 0.9, 1.0), strength=0.0)
M["guard"] = principled("guard", (0.85, 0.62, 0.18))
M["grip"] = principled("grip", (0.15, 0.08, 0.20))
# fx
M["bolt_core"] = emissive("bolt_core", (0.85, 0.95, 1.0), 40.0)
M["bolt_glow"] = emissive("bolt_glow", (0.15, 0.45, 1.0), 5.0)
M["slash"] = emissive("slash", (0.75, 0.95, 1.0), 14.0, fade_attr=True)
M["spark"] = emissive("spark", (1.0, 0.95, 0.75), 12.0)
M["spark_b"] = emissive("spark_b", (0.4, 0.8, 1.0), 8.0)

# ------------------------------------------------------------------ geometry helpers
def bm_box(bm, size, center=(0, 0, 0), rot=None):
    sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
    c = Vector(center)
    vs = []
    for x in (-sx, sx):
        for y in (-sy, sy):
            for z in (-sz, sz):
                p = Vector((x, y, z))
                if rot is not None:
                    p = rot @ p
                vs.append(bm.verts.new(c + p))
    idx = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    for f in idx:
        bm.faces.new([vs[i] for i in f])

def bm_beam(bm, a, b, w, h=None):
    """thin box from a to b"""
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    if L < 1e-5:
        return
    q = d.normalized().to_track_quat('Y', 'Z').to_matrix()
    bm_box(bm, (w, L, h if h else w), (a + b) / 2, q)

def mesh_obj(name, bm, mat, parent=None, loc=(0, 0, 0), bevel=0.0):
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges), offset=bevel,
                        segments=1, affect='EDGES', profile=0.5, clamp_overlap=True)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if isinstance(mat, (list, tuple)):
        for m_ in mat:
            me.materials.append(m_)
    else:
        me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    COL.objects.link(ob)
    ob.parent = parent
    ob.location = loc
    return ob

def box(name, size, offset=(0, 0, 0), mat=None, parent=None, loc=(0, 0, 0), bevel=0.02, rot=None):
    bm = bmesh.new()
    bm_box(bm, size, offset, rot)
    return mesh_obj(name, bm, mat, parent, loc, bevel)

def empty(name, parent=None, loc=(0, 0, 0)):
    ob = bpy.data.objects.new(name, None)
    ob.empty_display_size = 0.15
    COL.objects.link(ob)
    ob.parent = parent
    ob.location = loc
    return ob

def light(name, kind, energy, color, loc=(0, 0, 0), size=0.2, parent=None):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = color
    if kind in ("POINT", "SPOT"):
        ld.shadow_soft_size = size
    elif kind == "AREA":
        ld.size = size
    ob = bpy.data.objects.new(name, ld)
    COL.objects.link(ob)
    ob.parent = parent
    ob.location = loc
    return ob

# ------------------------------------------------------------------ arena
ARENA_C = Vector((0, 7.0, 0))

def build_arena():
    # floor slabs
    bms = {k: bmesh.new() for k in ("floor_a", "floor_b", "floor_c")}
    T = 2.0
    for i in range(-9, 10):
        for j in range(-9, 10):
            cx, cy = i * T, ARENA_C.y + j * T
            if (Vector((cx, cy)) - ARENA_C.xy).length > 16.5:
                continue
            k = random.choice(["floor_a", "floor_a", "floor_b", "floor_c"])
            h = random.uniform(-0.015, 0.0)
            bm_box(bms[k], (T - 0.07, T - 0.07, 0.4), (cx, cy, -0.2 + h))
    for k, bm in bms.items():
        mesh_obj("Floor_" + k, bm, M[k], bevel=0.03)
    # dark gap underlay
    box("FloorBase", (40, 40, 0.1), (0, ARENA_C.y, -0.32), M["stand"], bevel=0)

    # rune rings (blocky segments)
    for r, n, w, mk in ((6.2, 64, 0.16, "rune"), (4.6, 40, 0.10, "rune_dim"), (9.5, 80, 0.12, "rune_dim")):
        bm = bmesh.new()
        for s in range(n):
            if mk == "rune_dim" and s % 2:
                continue
            a = 2 * math.pi * s / n
            p = ARENA_C + Vector((math.cos(a) * r, math.sin(a) * r, 0.005))
            seg = 2 * math.pi * r / n * 0.82
            bm_box(bm, (seg, w, 0.02), p, Matrix.Rotation(a + math.pi / 2, 3, 'Z'))
        mesh_obj("Rune_%.1f" % r, bm, M[mk], bevel=0)
    # rune glyph blocks inside ring
    bm = bmesh.new()
    for s in range(8):
        a = 2 * math.pi * s / 8 + 0.2
        p = ARENA_C + Vector((math.cos(a) * 5.4, math.sin(a) * 5.4, 0.005))
        R = Matrix.Rotation(a, 3, 'Z')
        bm_box(bm, (0.5, 0.12, 0.02), p, R)
        bm_box(bm, (0.12, 0.5, 0.02), p, R)
    mesh_obj("RuneGlyphs", bm, M["rune"], bevel=0)

    # wall ring + pillars + crystals + banners
    Rw, n = 17.0, 44
    bm_w, bm_t, bm_p, bm_c, bm_b, bm_f = (bmesh.new() for _ in range(6))
    crystal_pos = []
    for s in range(n):
        a = 2 * math.pi * s / n
        d = Vector((math.cos(a), math.sin(a), 0))
        p = ARENA_C + d * Rw
        R = Matrix.Rotation(a + math.pi / 2, 3, 'Z')
        seg = 2 * math.pi * Rw / n
        bm_box(bm_w, (seg - 0.05, 1.2, 2.6), p + Vector((0, 0, 1.3)), R)
        bm_box(bm_t, (seg - 0.05, 1.5, 0.3), p + Vector((0, 0, 2.7)), R)
        if s % 4 == 0:
            pp = ARENA_C + d * (Rw - 0.6)
            bm_box(bm_p, (1.3, 1.3, 7.0), pp + Vector((0, 0, 3.5)), R)
            bm_box(bm_p, (1.7, 1.7, 0.4), pp + Vector((0, 0, 7.1)), R)
            cp = pp + Vector((0, 0, 8.0))
            bm_box(bm_c, (0.6, 0.6, 0.6), cp, R @ Matrix.Rotation(math.radians(45), 3, 'X') @ Matrix.Rotation(math.radians(35), 3, 'Y'))
            crystal_pos.append(cp)
            # banner
            bp = ARENA_C + d * (Rw - 1.3)
            bm_box(bm_b, (1.0, 0.06, 3.0), bp + Vector((0, 0, 4.6)), R)
            bm_box(bm_c, (0.3, 0.07, 0.3), bp + Vector((0, 0, 4.9)) - d * 0.03, R @ Matrix.Rotation(math.radians(45), 3, 'Y'))
        if s % 4 == 2:
            # brazier
            bp = ARENA_C + d * (Rw - 1.6)
            bm_box(bm_p, (0.7, 0.7, 1.2), bp + Vector((0, 0, 0.6)), R)
            bm_box(bm_p, (1.0, 1.0, 0.25), bp + Vector((0, 0, 1.3)), R)
    mesh_obj("Wall", bm_w, M["wall"], bevel=0.04)
    mesh_obj("WallTop", bm_t, M["wall_top"], bevel=0.04)
    mesh_obj("Pillars", bm_p, M["pillar"], bevel=0.05)
    mesh_obj("Crystals", bm_c, M["crystal"], bevel=0)
    mesh_obj("Banners", bm_b, M["banner"], bevel=0)

    # brazier flames: animated blocky flames
    flames = []
    for s in range(n):
        if s % 4 != 2:
            continue
        a = 2 * math.pi * s / n
        d = Vector((math.cos(a), math.sin(a), 0))
        bp = ARENA_C + d * (Rw - 1.6) + Vector((0, 0, 1.45))
        fl = box("Flame_%d" % s, (0.5, 0.5, 0.7), (0, 0, 0.35), M["flame"], loc=bp, bevel=0,
                 rot=Matrix.Rotation(a, 3, 'Z'))
        flames.append(fl)
    for c in crystal_pos:
        if (c - Vector((0, 0, 0))).length < 26:
            light("CrystalLight", "POINT", 900, (0.75, 0.4, 1.0), c - (c - ARENA_C).normalized() * 1.2, 0.5)

    # stands (tiers) + crowd silhouettes with glowing eyes
    bm_s, bm_cr, bm_e = bmesh.new(), bmesh.new(), bmesh.new()
    for tier in range(4):
        r = Rw + 1.6 + tier * 1.6
        h = 3.2 + tier * 1.3
        nn = 52 + tier * 6
        for s in range(nn):
            a = 2 * math.pi * s / nn
            d = Vector((math.cos(a), math.sin(a), 0))
            R = Matrix.Rotation(a + math.pi / 2, 3, 'Z')
            seg = 2 * math.pi * r / nn
            bm_box(bm_s, (seg + 0.02, 1.6, h), ARENA_C + d * r + Vector((0, 0, h / 2)), R)
            if random.random() < 0.8:
                p = ARENA_C + d * (r - 0.2) + Vector((random.uniform(-0.3, 0.3), 0, h))
                bh = random.uniform(0.7, 1.0)
                bm_box(bm_cr, (0.55, 0.4, bh), p + Vector((0, 0, bh / 2)), R)
                bm_box(bm_cr, (0.42, 0.4, 0.42), p + Vector((0, 0, bh + 0.24)), R)
                for ex in (-0.09, 0.09):
                    ep = p + Vector((0, 0, bh + 0.27)) + (R @ Vector((ex, 0, 0))) - d * 0.21
                    bm_box(bm_e, (0.07, 0.02, 0.05), ep, R)
    mesh_obj("Stands", bm_s, M["stand"], bevel=0.03)
    mesh_obj("Crowd", bm_cr, M["crowd"], bevel=0.02)
    mesh_obj("CrowdEyes", bm_e, M["eye_red"], bevel=0)

    # giant portal ring in sky behind the enemy
    bm_r, bm_ri = bmesh.new(), bmesh.new()
    pc = Vector((0, 46, 17))
    for s in range(48):
        a = 2 * math.pi * s / 48
        R = Matrix.Rotation(a, 3, 'Y')
        p = pc + Vector((math.cos(a) * 11, 0, math.sin(a) * 11))
        bm_box(bm_r, (2.0, 0.8, 1.3), p, R)
    bm_box(bm_ri, (19, 0.3, 19), pc + Vector((0, 1.0, 0)), Matrix.Rotation(math.radians(45), 3, 'Y'))
    mesh_obj("PortalRing", bm_r, M["portal"], bevel=0)
    mesh_obj("PortalInner", bm_ri, M["portal_in"], bevel=0)

    # floating cubes (slow rotation / bob)
    floats = []
    for i in range(26):
        a = random.uniform(0, 2 * math.pi)
        r = random.uniform(20, 36)
        p = ARENA_C + Vector((math.cos(a) * r, math.sin(a) * r, random.uniform(9, 22)))
        s = random.uniform(0.8, 2.4)
        ob = box("FloatCube_%d" % i, (s, s, s), (0, 0, 0), M["float"] if i % 4 else M["crystal"], loc=p, bevel=0.06)
        ob.rotation_euler = (random.random() * 3, random.random() * 3, random.random() * 3)
        floats.append((ob, p.copy(), random.uniform(-0.4, 0.4), random.uniform(0, 6)))
    return flames, floats

# ------------------------------------------------------------------ enemy rig
E_SCALE = 0.95
H = 1.03          # hips height (standing)
L1, L2 = 0.46, 0.44
ANK = 0.09        # ankle height above sole

def build_enemy():
    J = {}
    root = empty("E_root")
    root.scale = (E_SCALE,) * 3
    J["root"] = root
    hips = empty("E_hips", root, (0, 0, H))
    J["hips"] = hips
    box("E_pelvis", (0.56, 0.32, 0.24), (0, 0, -0.02), M["e_dark"], hips)
    torso = empty("E_torso", hips, (0, 0, 0.08))
    J["torso"] = torso
    box("E_belt", (0.62, 0.38, 0.09), (0, 0, 0.04), M["e_dark"], torso)
    box("E_chest", (0.74, 0.42, 0.60), (0, 0, 0.36), M["e_blue"], torso)
    box("E_plate", (0.50, 0.06, 0.32), (0, -0.22, 0.42), M["e_light"], torso, bevel=0.015)
    box("E_core", (0.12, 0.03, 0.12), (0, -0.26, 0.42), M["e_eye"], torso, bevel=0)
    neck = empty("E_neck", torso, (0, 0, 0.66))
    J["neck"] = neck
    box("E_head", (0.48, 0.46, 0.44), (0, 0, 0.24), M["e_blue"], neck, bevel=0.03)
    box("E_visor", (0.40, 0.04, 0.12), (0, -0.235, 0.27), M["e_dark"], neck, bevel=0.01)
    for ex in (-0.1, 0.1):
        box("E_eye", (0.09, 0.03, 0.05), (ex, -0.258, 0.27), M["e_eye"], neck, bevel=0)
    box("E_crest", (0.08, 0.36, 0.14), (0, 0.02, 0.51), M["e_dark"], neck, bevel=0.015)
    for hx in (-0.2, 0.2):
        box("E_horn", (0.08, 0.08, 0.2), (hx, -0.02, 0.52), M["e_light"], neck, bevel=0.01,
            rot=Matrix.Rotation(-0.35 if hx < 0 else 0.35, 3, 'Y'))
    for side, sx in (("R", -1), ("L", 1)):
        sh = empty("E_sh" + side, torso, (sx * 0.48, 0, 0.56))
        sh.rotation_mode = 'YXZ'
        J["sh" + side] = sh
        box("E_pad" + side, (0.30, 0.34, 0.16), (sx * 0.03, 0, 0.04), M["e_dark"], sh)
        box("E_uarm" + side, (0.21, 0.23, 0.38), (0, 0, -0.17), M["e_blue"], sh)
        el = empty("E_el" + side, sh, (0, 0, -0.37))
        J["el" + side] = el
        box("E_farm" + side, (0.19, 0.21, 0.32), (0, 0, -0.15), M["e_blue"], el)
        box("E_bracer" + side, (0.22, 0.24, 0.08), (0, 0, -0.24), M["e_light"], el, bevel=0.01)
        box("E_hand" + side, (0.21, 0.23, 0.17), (0, 0, -0.38), M["e_dark"], el)
        hip = empty("E_hip" + side, hips, (sx * 0.16, 0, -0.06))
        J["hip" + side] = hip
        box("E_thigh" + side, (0.25, 0.27, 0.48), (0, 0, -0.22), M["e_blue"], hip)
        kn = empty("E_kn" + side, hip, (0, 0, -L1))
        J["kn" + side] = kn
        box("E_knee" + side, (0.26, 0.10, 0.14), (0, -0.12, 0.0), M["e_light"], kn, bevel=0.01)
        box("E_shin" + side, (0.23, 0.25, 0.44), (0, 0, -0.21), M["e_dark"], kn)
        an = empty("E_an" + side, kn, (0, 0, -L2))
        J["an" + side] = an
        box("E_foot" + side, (0.25, 0.38, 0.11), (0, -0.07, -ANK + 0.055), M["e_dark"], an)
    return J

def leg_ik(ty, tz):
    """target relative to hip joint (y fwd=-, z). returns (hip_rot_x, knee_rot_x)"""
    d = math.hypot(ty, tz)
    d = min(max(d, 0.15), L1 + L2 - 1e-4)
    k_int = math.acos(clamp((L1 * L1 + L2 * L2 - d * d) / (2 * L1 * L2), -1, 1))
    knee = math.pi - k_int
    alpha = math.atan2(-ty, -tz)              # forward angle of target from straight down
    beta = math.acos(clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1))
    thigh_fwd = alpha + beta
    return -thigh_fwd, knee

# ------------------------------------------------------------------ player rig (first person)
def build_player():
    cam_d = bpy.data.cameras.new("FP_Cam")
    cam_d.lens = 19
    cam_d.sensor_fit = 'VERTICAL'
    cam_d.sensor_height = 24
    cam_d.clip_start = 0.02
    cam_d.clip_end = 200
    cam = bpy.data.objects.new("FP_Cam", cam_d)
    COL.objects.link(cam)
    scene.camera = cam
    cam.rotation_mode = 'QUATERNION'

    # right hand + sword
    rh = empty("P_handR", cam)
    rh.rotation_mode = 'QUATERNION'
    box("P_fistR", (0.085, 0.10, 0.09), (0, 0, 0), M["glove"], rh, bevel=0.01)
    sword = empty("P_sword", rh)
    sword.rotation_mode = 'QUATERNION'
    box("P_grip", (0.035, 0.20, 0.035), (0, -0.02, 0), M["grip"], sword, bevel=0.005)
    box("P_pommel", (0.06, 0.05, 0.06), (0, -0.13, 0), M["guard"], sword, bevel=0.008)
    box("P_guard", (0.24, 0.045, 0.06), (0, 0.10, 0), M["guard"], sword, bevel=0.008)
    box("P_gem", (0.04, 0.03, 0.065), (0, 0.10, 0), M["e_eye"], sword, bevel=0)
    bm = bmesh.new()
    bm_box(bm, (0.07, 0.95, 0.02), (0, 0.6, 0))
    bm_box(bm, (0.045, 0.08, 0.02), (0, 1.11, 0), Matrix.Rotation(math.radians(45), 3, 'Z'))
    blade = mesh_obj("P_blade", bm, M["blade"], sword, bevel=0.006)
    # right forearm (separately oriented toward the shoulder)
    ra = empty("P_armR", cam)
    ra.rotation_mode = 'QUATERNION'
    box("P_sleeveR", (0.12, 0.62, 0.12), (0, -0.36, 0), M["sleeve"], ra, bevel=0.012)
    box("P_cuffR", (0.135, 0.07, 0.135), (0, -0.07, 0), M["cuff"], ra, bevel=0.01)
    # left hand
    lh = empty("P_handL", cam)
    lh.rotation_mode = 'QUATERNION'
    box("P_fistL", (0.09, 0.10, 0.09), (0, 0, 0), M["glove"], lh, bevel=0.01)
    la = empty("P_armL", cam)
    la.rotation_mode = 'QUATERNION'
    box("P_sleeveL", (0.12, 0.62, 0.12), (0, -0.36, 0), M["sleeve"], la, bevel=0.012)
    box("P_cuffL", (0.135, 0.07, 0.135), (0, -0.07, 0), M["cuff"], la, bevel=0.01)
    return dict(cam=cam, rh=rh, sword=sword, ra=ra, lh=lh, la=la, blade=blade)

# ------------------------------------------------------------------ animation data
# enemy root path (unscaled world)
E_RY = Track([(1, 11.2), (18, 6.6, "lin"), (27, 5.5, "out"), (37, 5.5), (40, 5.25, "in"),
              (44, 5.2, "out"), (83, 5.2), (85, 5.28, "out"), (100, 8.3, "out"), (108, 8.95, "out")])
E_RZ = Track([(1, 0), (85, 0), (92, 0.62, "out"), (100, 0.0, "in")])
E_RP = Track([(1, 0), (83, 0), (84, -0.32, "out"), (86, -0.38), (93, -0.62, "out"),
              (100, -0.12, "in"), (104, 0.18, "out"), (111, 0.0, "smooth")])
E_SPIN = Track([(1, 0), (83, 0), (84, 0.25, "out"), (100, 0.45, "out"), (112, 0.35, "smooth")])

# camera path
CAM_LOC = Track([
    (1, (0, 0, 1.62)), (40, (0, 0.05, 1.62)),
    (45, (0.08, 0.02, 1.52), "smooth"),          # anticipation: dip + slight right
    (53, (-1.65, 0.15, 1.26), "smoother"),       # burst left (dodge)
    (58, (-1.88, 0.18, 1.32), "out"),            # overshoot slide
    (66, (-1.75, 0.10, 1.55), "smooth"),         # recover
    (75, (-1.80, -0.18, 1.46), "smooth"),        # wind-up: weight back
    (83, (-0.62, 3.15, 1.38), "in"),             # lunge (accelerating into contact)
    (86, (-0.62, 3.15, 1.38), "hold"),           # hit-stop
    (93, (-0.50, 3.50, 1.35), "out3"),           # follow-through momentum
    (104, (-0.40, 3.40, 1.55), "smooth"),        # recoil / stand up
    (120, (-0.15, 3.85, 1.62), "smooth"),        # stalk forward
])
CAM_ROLL = Track([(1, 0), (44, 0.0), (46, -0.05), (52, 0.24, "out"), (58, 0.10), (66, -0.02), (75, -0.10),
                  (80, -0.12), (83, 0.06, "in"), (86, 0.06, "hold"), (91, 0.20, "out"), (104, 0.03), (120, 0.0)])
LOOK_Z = Track([(1, 1.45), (40, 1.50), (60, 1.40), (80, 1.30), (88, 1.20), (100, 0.9), (112, 0.75), (120, 0.75)])
LOOK_LAG = Track([(1, 2.0), (44, 2.0), (50, 5.0), (62, 3.0), (80, 1.0), (120, 3.0)])
LOOK_OFF = Track([(1, (0, 0, 0)), (44, (0, 0, 0)), (52, (0.7, 0, 0.0)), (62, (0.1, 0, 0)),
                  (75, (0.0, 0, 0.25)), (83, (0.0, 0, -0.1), "in"), (86, (0, 0, -0.1), "hold"),
                  (95, (0.0, 0, -0.2)), (120, (0, 0, 0))])

def V(x, y, z):
    return (x, y, z)

# right hand: (loc in camera space, blade direction)
RH = Track([
    (1, (0.165, -0.31, -0.56, -0.08, 0.50, -0.86)),
    (40, (0.165, -0.305, -0.56, -0.08, 0.50, -0.86)),
    (45, (0.15, -0.34, -0.52, -0.04, 0.55, -0.83)),            # anticipation (pull in)
    (51, (0.23, -0.29, -0.58, 0.12, 0.62, -0.78), "smooth"),   # lag (inertia to the right)
    (59, (0.14, -0.32, -0.53, -0.22, 0.50, -0.84), "smooth"),  # swing back
    (66, (0.165, -0.31, -0.56, -0.08, 0.50, -0.86), "smooth"),
    (75, (0.22, 0.00, -0.40, -0.50, 0.70, 0.50), "smooth"),    # wind-up (blade cocked back)
    (79, (0.21, 0.02, -0.46, -0.35, 0.85, -0.20), "in"),
    (83, (0.04, -0.19, -0.62, -0.85, 0.02, -0.52), "in"),     # contact
    (86, (0.02, -0.20, -0.62, -0.85, -0.06, -0.50), "lin"),   # hit-stop (tiny push)
    (89, (-0.14, -0.28, -0.50, -0.60, -0.65, -0.20), "out"),   # follow-through
    (94, (-0.16, -0.36, -0.42, -0.45, -0.60, 0.50), "out"),
    (106, (0.19, -0.31, -0.56, 0.10, 0.30, -0.95), "smooth"), # recover low guard
    (120, (0.19, -0.30, -0.56, 0.12, 0.36, -0.92), "smooth"),
])
LH = Track([
    (1, (-0.16, -0.36, -0.42)), (44, (-0.16, -0.37, -0.40)),
    (51, (-0.10, -0.22, -0.46), "out"),      # balancing hand flings into view
    (60, (-0.15, -0.34, -0.42), "smooth"),
    (75, (-0.08, -0.26, -0.50), "smooth"),   # reaching forward during wind-up
    (82, (-0.20, -0.42, -0.30), "in"),       # pulled back (counter-rotation)
    (95, (-0.20, -0.42, -0.30)),
    (110, (-0.16, -0.36, -0.42), "smooth"),
])
SHOULDER_R = Vector((0.27, -0.46, 0.15))
SHOULDER_L = Vector((-0.27, -0.46, 0.15))

# enemy poses
E_DEF = dict(hz=0.0, tp=0.0, tt=0.0, tl=0.0, np=0.0, nt=0.0,
             shRx=0.0, shRy=0.12, elR=-0.4, shLx=0.0, shLy=-0.12, elL=-0.4,
             fRy=-0.2, fRz=ANK, fLy=0.2, fLz=ANK, run=0.0)
STANCE = dict(hz=-0.10, tp=0.12, tt=0.0, tl=0.0, np=-0.08,
              shRx=-0.45, shRy=0.25, elR=-1.2, shLx=-0.35, shLy=-0.25, elL=-1.3,
              fRy=-0.25, fRz=ANK, fLy=0.25, fLz=ANK)
E_TL = PoseTimeline(E_DEF, [
    (1, dict(run=1.0, hz=-0.10, tp=0.38, elR=-1.5, elL=-1.5, np=-0.25), "smooth"),
    (18, dict(run=1.0), "smooth"),
    (25, dict(run=0.0, hz=-0.16, tp=-0.12, np=0.05, shRx=-0.2, shRy=0.35, elR=-1.0,
              shLx=0.3, shLy=-0.35, elL=-1.0, fRy=-0.40, fRz=ANK, fLy=0.30, fLz=ANK), "smooth"),  # brake
    (29, dict(STANCE), "smooth"),
    (31, dict(STANCE, tp=0.05), "smooth"),
    (36, dict(hz=-0.14, tp=-0.28, tt=-0.38, tl=0.08, np=-0.18, shRx=-2.75, shRy=0.15, elR=-0.55,
              shLx=-1.0, shLy=-0.25, elL=-0.25, fRy=-0.20, fLy=0.32), "smooth"),               # wind-up
    (37, dict(tp=-0.30, tt=-0.40, shRx=-2.85), "lin"),
    (40, dict(hz=-0.22, tp=0.30, tt=0.32, tl=-0.05, np=-0.05, shRx=-1.58, shRy=0.02, elR=-0.02,
              shLx=0.35, shLy=-0.45, elL=-0.9, fRy=-0.55, fRz=ANK, fLy=0.47, fLz=ANK), "in"),  # throw
    (44, dict(hz=-0.18, tp=0.12, tt=0.22, shRx=-1.85, elR=-0.15), "out"),                     # recoil
    (52, dict(hz=-0.17, tp=0.18, tt=0.25, shRx=-1.55, elR=-0.05), "smooth"),
    (58, dict(hz=-0.15, tp=0.15, tt=0.15, shRx=-1.20, elR=-0.4), "smooth"),
    (68, dict(STANCE, fRy=-0.40, fLy=0.33, tp=0.18, np=-0.05), "smooth"),
    (76, dict(STANCE, fRy=-0.40, fLy=0.33, tp=0.20, hz=-0.13), "smooth"),
    (82, dict(hz=-0.08, tp=-0.12, np=0.15, shRx=-1.35, shRy=-0.25, elR=-1.75,
              shLx=-1.30, shLy=0.25, elL=-1.80), "out"),                                       # late guard
    (83, dict(), "lin"),
    (84, dict(hz=-0.12, tp=-0.75, tt=0.45, tl=-0.15, np=-0.55, nt=0.2, shRx=-1.9, shRy=0.75, elR=-0.25,
              shLx=-1.3, shLy=-0.9, elL=-0.35, fRy=-0.45, fLy=0.2), "snap"),                   # impact
    (86, dict(tp=-0.78, np=-0.6), "lin"),
    (93, dict(hz=-0.02, tp=-0.45, tt=0.25, tl=0.0, np=-0.35, nt=0.1, shRx=-2.6, shRy=0.55, elR=-0.4,
              shLx=-2.4, shLy=-0.6, elL=-0.5, fRy=-0.45, fRz=0.38, fLy=-0.20, fLz=0.28), "out"),  # airborne
    (100, dict(hz=-0.30, tp=0.45, tt=0.10, np=0.15, nt=0.0, shRx=-0.9, shRy=0.45, elR=-0.6,
               shLx=-0.7, shLy=-0.5, elL=-0.7, fRy=-0.30, fRz=ANK, fLy=0.22, fLz=ANK), "in"),    # land
    (104, dict(hz=-0.36, tp=0.55, np=0.2), "out"),
    (108, dict(hz=-0.30, tp=0.48, shRx=-0.5, elR=-0.5), "smooth"),
    (111, dict(hz=-0.33, tp=0.50, fRy=0.20, fRz=0.30, fLy=-0.36, fLz=ANK + 0.02), "smooth"),
    (114, dict(hz=-0.45, tp=0.72, np=0.45, shRx=-0.35, shRy=0.12, elR=-0.15,
               shLx=-0.95, shLy=-0.2, elL=-1.0, fRy=0.44, fRz=0.12, fLy=-0.46, fLz=0.12), "in"),  # knee down
    (117, dict(hz=-0.40, tp=0.64, np=0.40), "out"),
    (120, dict(hz=-0.41, tp=0.66, np=0.44), "smooth"),
])

def foot_cycle(p):
    p %= 1.0
    c, A = 0.38, 0.456
    if p < c:
        s = p / c
        return -A + 2 * A * s, ANK
    s = (p - c) / (1 - c)
    y = A - 2 * A * EASE["smooth"](s)
    z = ANK + 0.40 * math.sin(math.pi * (s ** 0.75))
    return y, z

# ------------------------------------------------------------------ keyframing helpers
def key_loc(ob, f, loc):
    ob.location = loc
    ob.keyframe_insert("location", frame=f)

def key_rot(ob, f, eul):
    ob.rotation_euler = eul
    ob.keyframe_insert("rotation_euler", frame=f)

def key_quat(ob, f, q, prev):
    if prev.get(ob.name) is not None and prev[ob.name].dot(q) < 0:
        q = -q
    prev[ob.name] = q.copy()
    ob.rotation_quaternion = q
    ob.keyframe_insert("rotation_quaternion", frame=f)

def look_quat(frm, to, roll):
    d = (Vector(to) - Vector(frm)).normalized()
    q = d.to_track_quat('-Z', 'Y')
    return q @ Quaternion((0, 0, 1), roll)

def shake(f, start, amp, decay):
    if f < start:
        return Vector((0, 0, 0)), 0.0
    t = f - start
    a = amp * math.exp(-t / decay)
    return Vector((math.sin(t * 2.7) * a, 0, math.cos(t * 3.3) * a * 0.8)), math.sin(t * 2.1 + 1) * a * 0.6

def enemy_root_pos(f):
    return Vector((0, E_RY(f), E_RZ(f) * 1.0))

def cam_pos(f):
    p = Vector(CAM_LOC(f))
    s, _ = shake(f, 86, 0.05, 3.0)
    s2, _ = shake(f, 49, 0.018, 2.0) if f < 60 else (Vector((0, 0, 0)), 0)
    breath = Vector((0, 0, 0.008 * math.sin(f * 0.25)))
    return p + s + s2 + breath

def enemy_yaw(f):
    """enemy turns to face the player with a few frames of lag; locked after the hit."""
    ff = min(f, 83)
    c = cam_pos(max(1, ff - 4))
    e = enemy_root_pos(ff)
    return math.atan2(c.x - e.x, -(c.y - e.y)) + E_SPIN(f)

def animate(J, P, flames, floats):
    prevq = {}
    for f in range(1, F_END + 1):
        # ---------------- enemy
        pose = E_TL(f)
        ry = E_RY(f)
        w = pose["run"]
        phase = (11.2 - ry) / 2.4
        yaw = enemy_yaw(f)
        root = J["root"]
        key_loc(root, f, (0, ry, E_RZ(f)))
        key_rot(root, f, (E_RP(f), 0, yaw))

        # run overlay
        yL, zL = foot_cycle(phase)
        yR, zR = foot_cycle(phase + 0.5)
        nL = yL / 0.456
        hz = pose["hz"] + w * (0.05 * math.cos(4 * math.pi * (phase - 0.05)))
        fRy, fRz = lerp(pose["fRy"], yR, w), lerp(pose["fRz"], zR, w)
        fLy, fLz = lerp(pose["fLy"], yL, w), lerp(pose["fLz"], zL, w)
        shRx = pose["shRx"] + w * (nL * 0.95)
        shLx = pose["shLx"] + w * (-nL * 0.95)
        tt = pose["tt"] + w * (0.16 * nL)
        tl = pose["tl"]
        # breathing after kneel / idle micro motion
        br = math.sin(f * 0.45) * (0.035 if f > 112 else 0.012)
        tp = pose["tp"] + br
        # impact shake on enemy during hit-stop
        if 83 <= f <= 86:
            tt += 0.05 * math.sin(f * 9)

        key_loc(J["hips"], f, (0, 0, H + hz))
        key_rot(J["torso"], f, (tp, tl, tt))
        key_rot(J["neck"], f, (pose["np"] - 0.4 * (tp - 0.2) * (1 - w) * 0.3, 0, pose["nt"] - tt * 0.4))
        key_rot(J["shR"], f, (shRx, pose["shRy"], 0))
        key_rot(J["shL"], f, (shLx, pose["shLy"], 0))
        key_rot(J["elR"], f, (pose["elR"], 0, 0))
        key_rot(J["elL"], f, (pose["elL"], 0, 0))
        hipz = H + hz - 0.06
        for side, fy, fz in (("R", fRy, fRz), ("L", fLy, fLz)):
            hr, kr = leg_ik(fy, fz - hipz)
            key_rot(J["hip" + side], f, (hr, 0, 0))
            key_rot(J["kn" + side], f, (kr, 0, 0))
            key_rot(J["an" + side], f, (-(hr + kr) - E_RP(f) * 0.7, 0, 0))

        # ---------------- camera
        cp = cam_pos(f)
        lag = LOOK_LAG(f)
        tgt = enemy_root_pos(max(1, f - lag))
        tgt.z = LOOK_Z(f) + E_RZ(max(1, f - lag))
        tgt += Vector(LOOK_OFF(f))
        _, sroll = shake(f, 86, 0.05, 3.0)
        cam = P["cam"]
        key_loc(cam, f, cp)
        key_quat(cam, f, look_quat(cp, tgt, CAM_ROLL(f) + sroll), prevq)

        # ---------------- first-person hands
        r = RH(f)
        hloc = Vector(r[:3]) + Vector((0, 0.006 * math.sin(f * 0.25 + 1), 0))
        bdir = Vector(r[3:]).normalized()
        key_loc(P["rh"], f, hloc)
        key_quat(P["rh"], f, bdir.to_track_quat('Y', 'Z'), prevq)
        key_loc(P["ra"], f, hloc)
        key_quat(P["ra"], f, (hloc - SHOULDER_R).normalized().to_track_quat('Y', 'Z'), prevq)
        l = Vector(LH(f))
        key_loc(P["lh"], f, l)
        key_quat(P["lh"], f, (l - SHOULDER_L).normalized().to_track_quat('Y', 'Z'), prevq)
        key_loc(P["la"], f, l)
        key_quat(P["la"], f, (l - SHOULDER_L).normalized().to_track_quat('Y', 'Z'), prevq)

        # ---------------- environment life
        for i, fl in enumerate(flames):
            rnd = random.Random(f * 31 + i)
            fl.scale = (1 + rnd.uniform(-0.12, 0.12), 1 + rnd.uniform(-0.12, 0.12), 1 + rnd.uniform(-0.25, 0.3))
            fl.keyframe_insert("scale", frame=f)
    for ob, p, spd, ph in floats:
        for f in (1, F_END):
            ob.location = p + Vector((0, 0, 0.4 * math.sin(ph + f * 0.03)))
            ob.keyframe_insert("location", frame=f)
            ob.rotation_euler.z += spd * (1 if f == F_END else 0)
            ob.keyframe_insert("rotation_euler", frame=f)

    # enemy hit flash (white emission on enemy materials)
    for mk in ("e_blue", "e_dark", "e_light"):
        b = M[mk].node_tree.nodes.get("Principled BSDF")
        b.inputs["Emission Color"].default_value = (1, 1, 1, 1)
        for f, v in ((1, 0), (82, 0), (83, 1.0), (85, 0.6), (88, 0.0)):
            b.inputs["Emission Strength"].default_value = v
            b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
    # blade glow during slash
    b = M["blade"].node_tree.nodes.get("Principled BSDF")
    for f, v in ((1, 0), (76, 0), (80, 2.0), (83, 4.0), (90, 0.5), (98, 0.0)):
        b.inputs["Emission Strength"].default_value = v
        b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)

# ------------------------------------------------------------------ effects (per-frame meshes)
def vis_only(ob, frames):
    prefs.keyframe_new_interpolation_type = 'CONSTANT'
    fr = set(frames)
    lo, hi = min(fr) - 1, max(fr) + 1
    for f in range(max(0, lo), hi + 1):
        h = f not in fr
        ob.hide_render = h
        ob.hide_viewport = h
        ob.keyframe_insert("hide_render", frame=f)
        ob.keyframe_insert("hide_viewport", frame=f)
    prefs.keyframe_new_interpolation_type = 'LINEAR'

def jag_path(a, b, n, amp, rnd):
    a, b = Vector(a), Vector(b)
    d = b - a
    u = d.orthogonal().normalized()
    v = d.normalized().cross(u)
    pts = []
    for i in range(n + 1):
        t = i / n
        env = math.sin(math.pi * t) ** 0.6
        off = (u * rnd.uniform(-1, 1) + v * rnd.uniform(-1, 1)) * amp * env
        pts.append(a + d * t + off)
    return pts

def add_bolt(bm_core, bm_glow, a, b, rnd, amp=0.16, w=0.03, branches=3):
    L = (Vector(b) - Vector(a)).length
    n = max(4, int(L / 0.22))
    pts = jag_path(a, b, n, amp, rnd)
    for p, q in zip(pts, pts[1:]):
        bm_beam(bm_core, p, q, w)
        bm_beam(bm_glow, p, q, w * 2.4)
    for _ in range(branches):
        if len(pts) < 4:
            break
        i = rnd.randrange(1, len(pts) - 2)
        s = pts[i]
        dirv = (Vector(b) - Vector(a)).normalized()
        rv = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
        e = s + (dirv * 0.4 + rv * 0.6).normalized() * rnd.uniform(0.3, 0.8)
        bp = jag_path(s, e, 4, 0.08, rnd)
        for p, q in zip(bp, bp[1:]):
            bm_beam(bm_core, p, q, w * 0.6)
            bm_beam(bm_glow, p, q, w * 2.0)

def world_of(name):
    return bpy.data.objects[name].matrix_world.copy()

def build_effects(J, P):
    hand_local = Vector((0, 0, -0.40))
    elR = J["elR"]
    # ---- charge orb on the enemy hand
    orb = box("FX_orb", (0.22, 0.22, 0.22), (0, 0, 0), M["bolt_core"], elR, (0, 0, -0.42), bevel=0)
    orb_g = box("FX_orb_glow", (0.4, 0.4, 0.4), (0, 0, 0), M["bolt_glow"], orb, bevel=0)
    orb.rotation_mode = 'XYZ'
    for f in range(1, F_END + 1):
        if f < 29:
            s = 0.001
        elif f <= 40:
            s = 0.25 + 0.95 * ((f - 29) / 11) ** 1.3 + 0.1 * math.sin(f * 2.3)
        elif f <= 46:
            s = 1.1 * (1 - (f - 40) / 6) + 0.001
        else:
            s = 0.001
        orb.scale = (s, s, s)
        orb.keyframe_insert("scale", frame=f)
        orb.rotation_euler = (f * 0.5, f * 0.37, f * 0.21)
        orb.keyframe_insert("rotation_euler", frame=f)
    lh = light("FX_handLight", "POINT", 0, (0.3, 0.6, 1.0), (0, 0, -0.42), 0.15, elR)
    for f, v in ((1, 0), (29, 0), (39, 120), (40, 350), (46, 80), (58, 0)):
        lh.data.energy = v
        lh.data.keyframe_insert("energy", frame=f)

    # ---- charge arcs (frames 30-40) & lightning beam (40-57)
    scene.frame_set(40)
    release_cam = P["cam"].matrix_world.translation.copy()
    tip_light = light("FX_tipLight", "POINT", 0, (0.35, 0.65, 1.0), (0, 0, 0), 0.3)
    for f in range(30, 58):
        scene.frame_set(f)
        hp = elR.matrix_world @ hand_local
        rnd = random.Random(1000 + f)
        bc, bg = bmesh.new(), bmesh.new()
        if f < 40:
            k = (f - 30) / 10
            for _ in range(3 + int(k * 4)):
                rv = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
                add_bolt(bc, bg, hp, hp + rv * rnd.uniform(0.25, 0.55 + k * 0.4), rnd, amp=0.06, w=0.015, branches=0)
            tip = None
        else:
            # tip travels from hand to just past where the player stood at release
            target = release_cam + Vector((0.55, 0, -0.12))
            dirv = (target - hp).normalized()
            t = (f - 40) / 10.0
            far = (target - hp).length + 8.0
            dist = (target - hp).length * EASE["in"](min(t, 1.0)) if t <= 1.0 else \
                (target - hp).length + (far - (target - hp).length) * min(1.0, (t - 1.0) * 3.0)
            tip = hp + dirv * max(dist, 0.3)
            fade = 1.0 if f < 52 else max(0.0, 1 - (f - 52) / 6)
            wcore = 0.035 * (0.4 + 0.6 * fade) * (1.0 + 0.3 * rnd.random())
            add_bolt(bc, bg, hp, tip, rnd, amp=0.20 * (1 + 0.5 * (1 - fade)), w=wcore, branches=4 if fade > 0.5 else 2)
            if f % 2 == 0 and fade > 0.3:  # second strand
                add_bolt(bc, bg, hp, tip, random.Random(f * 7), amp=0.28, w=wcore * 0.6, branches=1)
            if t < 1.0:  # leading orb
                bm_box(bc, (0.13, 0.13, 0.13), tip, Matrix.Rotation(f * 0.7, 3, Vector((1, 1, 0)).normalized()))
                bm_box(bg, (0.26, 0.26, 0.26), tip, Matrix.Rotation(f * 0.5, 3, Vector((0, 1, 1)).normalized()))
        oc = mesh_obj("FX_boltCore_%03d" % f, bc, M["bolt_core"])
        og = mesh_obj("FX_boltGlow_%03d" % f, bg, M["bolt_glow"])
        for o in (oc, og):
            o.visible_shadow = False
            vis_only(o, [f])
        if tip is not None:
            lp = tip if (tip - release_cam).length > 1.0 else (release_cam + Vector((0.6, 0.3, 0)))
            tip_light.location = lp
            tip_light.keyframe_insert("location", frame=f)
            tip_light.data.energy = 1200 * (1.0 if f < 52 else max(0, 1 - (f - 52) / 6)) * (0.7 + 0.3 * rnd.random())
            tip_light.data.keyframe_insert("energy", frame=f)
    for f in (29, 58):
        tip_light.data.energy = 0
        tip_light.data.keyframe_insert("energy", frame=f)

    # ---- slash trail (sub-frame samples of the blade)
    blade = P["sword"]
    def blade_pts(fr, sub):
        scene.frame_set(fr, subframe=sub)
        m = blade.matrix_world
        return m @ Vector((0, 0.35, 0)), m @ Vector((0, 1.18, 0))
    for f in range(79, 92):
        bm = bmesh.new()
        samples = []
        span = 3.5 if f <= 86 else max(0.5, 3.5 - (f - 86) * 0.6)
        N = 14
        for i in range(N + 1):
            tf = f - span + span * i / N
            if tf < 78:
                continue
            fi = int(math.floor(tf))
            samples.append((blade_pts(fi, tf - fi), i / N))
        if len(samples) < 2:
            bm.free()
            continue
        lay = bm.verts.layers.float.new("fade")
        verts = []
        for (a, b), t in samples:
            verts.append((bm.verts.new(a), bm.verts.new(b), t))
        life = 1.0 if f <= 86 else max(0.0, 1 - (f - 86) / 6)
        for (va, vb, t) in verts:
            va[lay] = (t ** 1.5) * life * 0.9
            vb[lay] = (t ** 1.2) * life
        for (a0, b0, _), (a1, b1, _) in zip(verts, verts[1:]):
            bm.faces.new((a0, b0, b1, a1))
        me = bpy.data.meshes.new("FX_slash_%03d" % f)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(M["slash"])
        ob = bpy.data.objects.new("FX_slash_%03d" % f, me)
        COL.objects.link(ob)
        ob.visible_shadow = False
        vis_only(ob, [f])

    # ---- hit sparks at contact
    scene.frame_set(83)
    torso = J["torso"]
    hit_p = torso.matrix_world @ Vector((0.05, -0.30, 0.42))
    cam_p = P["cam"].matrix_world.translation
    to_cam = (cam_p - hit_p).normalized()
    rnd = random.Random(5)
    dirs = []
    for i in range(22):
        v = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
        v = (v + to_cam * 0.3 + Vector((-0.5, 0, -0.4)) * 0.4).normalized()
        dirs.append((v, rnd.uniform(0.6, 1.4)))
    hl = light("FX_hitLight", "POINT", 0, (0.9, 0.95, 1.0), hit_p + to_cam * 0.4, 0.3)
    for f, v in ((1, 0), (82, 0), (83, 900), (86, 500), (90, 100), (95, 0)):
        hl.data.energy = v
        hl.data.keyframe_insert("energy", frame=f)
    for f in range(83, 93):
        t = (f - 83) / 9
        bs, bb = bmesh.new(), bmesh.new()
        for v, sp in dirs:
            r0 = 0.15 + 1.5 * sp * EASE["out"](t)
            r1 = r0 + 0.45 * sp * (1 - t)
            bm_beam(bs if sp > 1.0 else bb, hit_p + v * r0, hit_p + v * r1, 0.035 * (1 - t) + 0.008)
        if f <= 87:
            s = 0.16 * (1 - (f - 83) / 5) + 0.05
            bm_box(bs, (s, s, s), hit_p, Matrix.Rotation(0.6 + f, 3, Vector((1, 0.5, 0.2)).normalized()))
            # slash-shaped flash plane
            sl = Matrix.Rotation(math.radians(40), 3, to_cam)
            bm_box(bb, (1.4 * (1 - t * 0.5), 0.07 * (1 - t), 0.01), hit_p, sl @ to_cam.to_track_quat('Z', 'Y').to_matrix())
        o1 = mesh_obj("FX_spark_%03d" % f, bs, M["spark"])
        o2 = mesh_obj("FX_sparkB_%03d" % f, bb, M["spark_b"])
        for o in (o1, o2):
            o.visible_shadow = False
            vis_only(o, [f])

    # ---- dust puffs on landing and knee drop
    def puffs(prefix, f0, center_fn, count, seed, spread=0.8, size=0.25):
        r = random.Random(seed)
        for i in range(count):
            scene.frame_set(f0)
            c = center_fn()
            d = Vector((r.uniform(-1, 1), r.uniform(-0.3, 1.0), 0)).normalized()
            s0 = r.uniform(0.6, 1.0) * size
            ob = box("%s_%d" % (prefix, i), (1, 1, 1), (0, 0, 0), M["dust"], bevel=0.08)
            ob.visible_shadow = False
            ob.rotation_euler = (r.random(), r.random(), r.random())
            for f in range(f0 - 1, f0 + 16):
                t = clamp((f - f0) / 14)
                if f < f0:
                    sc = 0.001
                else:
                    sc = s0 * (0.4 + 1.2 * EASE["out"](t)) * (1 - t ** 2) + 0.001
                ob.location = c + d * spread * EASE["out"](t) + Vector((0, 0, 0.08 + 0.35 * EASE["out"](t) * r.uniform(0.5, 1)))
                ob.scale = (sc, sc, sc)
                ob.keyframe_insert("location", frame=f)
                ob.keyframe_insert("scale", frame=f)
            ob.scale = (0.001,) * 3
            ob.keyframe_insert("scale", frame=1)
    puffs("FX_dustLand", 100, lambda: J["root"].matrix_world.translation.copy(), 16, 3, 1.0, 0.28)
    puffs("FX_dustKnee", 114, lambda: J["knR"].matrix_world.translation.copy() * Vector((1, 1, 0)), 10, 4, 0.6, 0.2)
    puffs("FX_dustDodge", 53, lambda: P["cam"].matrix_world.translation * Vector((1, 1, 0)) + Vector((0.3, 0.9, 0)), 8, 6, 0.5, 0.18)

# ------------------------------------------------------------------ world / lights / render
def setup_world_render():
    w = bpy.data.worlds.new("World")
    scene.world = w
    nt = w.node_tree
    bg = nt.nodes.get("Background")
    # vertical gradient sky: dark violet top -> magenta haze horizon
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[0].color = (0.22, 0.05, 0.25, 1)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (0.02, 0.01, 0.05, 1)
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.0

    sun = light("Sun", "SUN", 2.2, (0.85, 0.78, 1.0))
    sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
    sun.data.angle = math.radians(12)
    rim = light("RimLight", "AREA", 6000, (0.45, 0.55, 1.0), (0, 22, 9), 12)
    rim.rotation_euler = (math.radians(-70), 0, 0)
    rim.rotation_mode = 'XYZ'
    rim.rotation_euler = Vector((0, -1, -0.4)).to_track_quat('-Z', 'Y').to_euler()
    fill = light("FillLight", "AREA", 1500, (0.9, 0.6, 1.0), (-4, -4, 6), 8)
    fill.rotation_euler = (Vector((4, 10, -5))).to_track_quat('-Z', 'Y').to_euler()

    r = scene.render
    r.engine = 'CYCLES'
    r.resolution_x, r.resolution_y = 720, 1280
    r.resolution_percentage = RES
    r.use_motion_blur = True
    r.motion_blur_shutter = 0.45
    r.image_settings.file_format = 'PNG'
    c = scene.cycles
    c.device = 'CPU'
    c.samples = SAMPLES
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.04
    c.use_denoising = True
    c.denoiser = 'OPENIMAGEDENOISE'
    c.max_bounces = 4
    c.diffuse_bounces = 2
    c.glossy_bounces = 1
    c.transmission_bounces = 0
    c.volume_bounces = 0
    c.transparent_max_bounces = 6
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.blur_glossy = 1.0
    scene.view_settings.view_transform = 'AgX'
    try:
        scene.view_settings.look = 'AgX - Punchy'
    except Exception:
        pass
    scene.view_settings.exposure = -0.15

    # compositor: bloom glow for lightning / slash
    try:
        tree = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
        tree.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
        rl = tree.nodes.new("CompositorNodeRLayers")
        gl = tree.nodes.new("CompositorNodeGlare")
        gl.inputs["Type"].default_value = 'Bloom'
        gl.inputs["Quality"].default_value = 'High'
        gl.inputs["Threshold"].default_value = 1.0
        gl.inputs["Strength"].default_value = 0.4
        gl.inputs["Size"].default_value = 0.45
        out = tree.nodes.new("NodeGroupOutput")
        tree.links.new(rl.outputs["Image"], gl.inputs["Image"])
        tree.links.new(gl.outputs["Image"], out.inputs[0])
        scene.render.compositor_device = 'CPU'
        scene.compositing_node_group = tree
        r.use_compositing = True
    except Exception as ex:
        print("compositor setup skipped:", ex)

# ------------------------------------------------------------------ main
def main():
    flames, floats = build_arena()
    J = build_enemy()
    P = build_player()
    setup_world_render()
    animate(J, P, flames, floats)
    build_effects(J, P)
    return J, P

def render_out(J, P):
    scene.frame_set(1)
    if not NO_SAVE and not arg("--side", False):
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, "battle_test.blend"))
        print("saved", os.path.join(OUT_DIR, "battle_test.blend"))
    os.makedirs(FRAME_DIR, exist_ok=True)
    frames = []
    if FRAMES_ARG and FRAMES_ARG is not True:
        frames = [int(x) for x in FRAMES_ARG.split(",")]
    elif DO_ANIM:
        frames = list(range(1, F_END + 1))
    import time
    side = None
    if arg("--side", False):
        cd = bpy.data.cameras.new("Side"); cd.lens = 35
        side = bpy.data.objects.new("Side", cd); COL.objects.link(side); scene.camera = side
        for o in P["cam"].children_recursive:
            o.hide_render = True
    for f in frames:
        t0 = time.time()
        scene.frame_set(f)
        if side:
            mw = J["root"].matrix_world
            e = mw.translation
            xa = (mw.to_3x3() @ Vector((1, 0, 0))).normalized()
            xa.z = 0
            side.location = e + xa.normalized() * 4.5 + Vector((0, 0, 0.9))
            for o in bpy.data.objects:
                if o.name.startswith("FX_dust"):
                    o.hide_render = True
            side.rotation_euler = (e + Vector((0, 0, 0.8)) - side.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = os.path.join(FRAME_DIR, "%04d.png" % f)
        bpy.ops.render.render(write_still=True)
        print("frame %d  %.1fs" % (f, time.time() - t0), flush=True)

render_out(*main())
