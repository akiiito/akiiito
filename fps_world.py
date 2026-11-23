"""
fps_world.py ― FPS転生シリーズの共通部品（ブロックなし・実写寄りCG）
  廃墟の街（コンクリート・窓・がれき）／夕方の空／主人公の銃と手（カメラに付く）／ヘルメット兵士／光る弾の軌跡
"""
import math, random
import bpy, bmesh
from mathutils import Vector, Matrix

def mat_concrete(name, base=(0.42, 0.4, 0.37), dirt=0.5, scale=3.0, streaks=True, puddles=False):
    """汚れたコンクリート：大きなムラ＋細かいざらつき＋雨だれのすじ＋下ほど黒いすす＋（地面なら）ひびと水たまり"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links.new
    b = N["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.88
    tc = N.new("ShaderNodeTexCoord"); geo = N.new("ShaderNodeNewGeometry")
    def noise(sc_, det=8.0, vec=None):
        n = N.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = sc_; n.inputs["Detail"].default_value = det
        L(vec or geo.outputs["Position"], n.inputs["Vector"]); return n.outputs["Fac"]
    def math_(op, a_, b_=None):
        n = N.new("ShaderNodeMath"); n.operation = op
        for i, v in enumerate((a_, b_)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: L(v, n.inputs[i])
        return n.outputs[0]
    big = noise(scale * 0.35, 6.0); fine = noise(scale * 14.0, 4.0)
    # 雨だれ：X だけ細かく、Z は引きのばしたノイズ
    mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (18.0, 18.0, 0.6); L(geo.outputs["Position"], mp.inputs["Vector"])
    st = noise(4.0, 3.0, mp.outputs["Vector"]); st = math_("POWER", math_("MAXIMUM", math_("SUBTRACT", st, 0.52), 0.0), 0.7)
    sep = N.new("ShaderNodeSeparateXYZ"); L(geo.outputs["Position"], sep.inputs[0])
    soot = math_("MAXIMUM", math_("SUBTRACT", 1.0, math_("MULTIPLY", sep.outputs["Z"], 0.6)), 0.0)          # 下ほど黒い
    dark = math_("ADD", math_("MULTIPLY", math_("SUBTRACT", big, 0.45), 1.6), math_("MULTIPLY", st, 1.6 if streaks else 0.0))
    dark = math_("ADD", dark, math_("MULTIPLY", soot, 0.35 * dirt))
    ramp = N.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.0, tuple(min(1, c * 1.12) for c in base) + (1,)
    el[1].position, el[1].color = 1.0, tuple(c * 0.28 for c in base) + (1,)
    L(math_("ADD", math_("MULTIPLY", dark, 0.5), math_("MULTIPLY", fine, 0.25)), ramp.inputs["Fac"]); L(ramp.outputs["Color"], b.inputs["Base Color"])
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.45; bump.inputs["Distance"].default_value = 0.02
    hgt = math_("ADD", fine, math_("MULTIPLY", st, -0.3))
    if puddles:                                                            # ひび（ボロノイの境目）と水たまり（ツヤ）
        vor = N.new("ShaderNodeTexVoronoi"); vor.feature = "DISTANCE_TO_EDGE"; vor.inputs["Scale"].default_value = 0.9
        wob = N.new("ShaderNodeVectorMath"); wob.operation = "ADD"; L(geo.outputs["Position"], wob.inputs[0]); nzv = N.new("ShaderNodeTexNoise"); nzv.inputs["Scale"].default_value = 1.5; L(geo.outputs["Position"], nzv.inputs["Vector"]); L(nzv.outputs["Color"], wob.inputs[1]); L(wob.outputs[0], vor.inputs["Vector"])
        crack = math_("MULTIPLY", math_("LESS_THAN", vor.outputs["Distance"], 0.01), math_("GREATER_THAN", noise(0.6, 3.0), 0.5))
        hgt = math_("SUBTRACT", hgt, math_("MULTIPLY", crack, 0.8))
        pud = math_("MULTIPLY", math_("GREATER_THAN", noise(0.12, 4.0), 0.66), 0.85)
        rough = math_("ADD", math_("MULTIPLY", pud, -0.82), 0.9); L(rough, b.inputs["Roughness"])
        mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; L(pud, mix.inputs["Factor"]); L(ramp.outputs["Color"], mix.inputs["A"]); mix.inputs["B"].default_value = (0.02, 0.02, 0.022, 1)
        mix2 = N.new("ShaderNodeMix"); mix2.data_type = "RGBA"; L(crack, mix2.inputs["Factor"]); L(mix.outputs["Result"], mix2.inputs["A"]); mix2.inputs["B"].default_value = (0.005, 0.005, 0.005, 1)
        L(mix2.outputs["Result"], b.inputs["Base Color"])
    L(hgt, bump.inputs["Height"]); L(bump.outputs["Normal"], b.inputs["Normal"])
    return m
def mat_simple(name, col, rough=0.5, metal=0.0, emit=None, estr=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    if emit: b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = estr
    return m
def mat_emit(name, col, s):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*col, 1); e.inputs["Strength"].default_value = s
    nt.links.new(e.outputs[0], o.inputs[0]); return m

def box(name, c, s, m, rot=(0, 0, 0), bevel=0.0, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=c, rotation=rot); o = bpy.context.object; o.name = name; o.scale = s
    o.data.materials.append(m)
    if bevel:
        bpy.ops.object.transform_apply(scale=True); bv = o.modifiers.new("bv", "BEVEL"); bv.width = bevel; bv.segments = 2
    if parent: o.parent = parent
    return o
def cyl(name, c, r, d, m, rot=(0, 0, 0), verts=24, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=c, rotation=rot); o = bpy.context.object; o.name = name
    o.data.materials.append(m); bpy.ops.object.shade_smooth()
    if parent: o.parent = parent
    return o

_DARK = None
def _cubes(name, items, m):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    for c, sz in items:
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r["verts"]: v.co = Vector((v.co.x * sz[0], v.co.y * sz[1], v.co.z * sz[2])) + Vector(c)
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); me.materials.append(m); return o
def building(name, x, y, w, d, h, conc, glass_m, frame_m, rnd, broken=0.3):
    """窓が並ぶコンクリートの建物（一部の窓は割れて真っ暗）。窓はまとめて1つのメッシュ"""
    global _DARK
    if _DARK is None: _DARK = mat_simple("dark", (0.01, 0.01, 0.012), 0.9)
    _cubes(name, [((x, y, h / 2), (w, d, h))], conc)
    wins, darks, sills = [], [], []
    floors = int(h / 3.2)
    for fz in range(floors):
        z = 1.8 + fz * 3.2
        for (nx, ny) in ((0, -1), (-1, 0), (1, 0)):
            span = w if ny else d; n = max(1, int(span / 2.4))
            for k in range(n):
                off = -span / 2 + (k + 0.5) * span / n
                px = x + (off if ny else nx * (w / 2 + 0.01)); py = y + (ny * (d / 2 + 0.01) if ny else off)
                (darks if rnd.random() < broken else wins).append(((px, py, z), (1.4, 0.05, 1.6) if ny else (0.05, 1.4, 1.6)))
                sills.append(((px, py + ny * 0.06, z - 0.85) if ny else (px + nx * 0.06, py, z - 0.85), (1.6, 0.2, 0.1) if ny else (0.2, 1.6, 0.1)))
    if wins: _cubes(name + "_win", wins, glass_m)
    if darks: _cubes(name + "_dark", darks, _DARK)
    if sills: _cubes(name + "_sill", sills, frame_m)

def rubble(name, center, radius, n, m, rnd, smax=0.6):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    for _ in range(n):
        s = rnd.uniform(0.08, smax) ** 1.3
        r = bmesh.ops.create_cube(bm, size=1.0)
        rot = Matrix.Rotation(rnd.uniform(0, 6.28), 3, "Z") @ Matrix.Rotation(rnd.uniform(-0.6, 0.6), 3, "X")
        a = rnd.uniform(0, 6.28); d = radius * math.sqrt(rnd.random())
        c = Vector(center) + Vector((math.cos(a) * d, math.sin(a) * d, s * 0.3))
        for v in r["verts"]: v.co = rot @ Vector((v.co.x * s * rnd.uniform(0.6, 1.6), v.co.y * s, v.co.z * s * 0.6)) + c
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); me.materials.append(m); return o

def rifle(parent):
    """主人公の銃（オリジナルの近未来アサルトライフル）。原点＝グリップ、+Y が銃口、+Z が上"""
    g = bpy.data.objects.new("rifle", None); bpy.context.collection.objects.link(g); g.parent = parent
    blk = mat_simple("gunblack", (0.025, 0.026, 0.03), 0.38, 0.6, coat=0.3); tan = mat_simple("guntan", (0.36, 0.3, 0.22), 0.55)
    accent = mat_simple("gunaccent", (0.02, 0.02, 0.02), 0.3, 0.0, emit=(0.2, 0.85, 1.0), estr=3.0)
    box("rcv", (0, 0.05, 0.06), (0.06, 0.34, 0.08), blk, bevel=0.006, parent=g)
    box("hand", (0, 0.32, 0.055), (0.07, 0.24, 0.07), tan, bevel=0.01, parent=g)
    cyl("barrel", (0, 0.52, 0.065), 0.012, 0.22, blk, rot=(math.pi / 2, 0, 0), parent=g)
    cyl("muzzle", (0, 0.64, 0.065), 0.02, 0.05, blk, rot=(math.pi / 2, 0, 0), parent=g)
    box("grip", (0, -0.03, -0.04), (0.035, 0.05, 0.11), tan, rot=(-0.3, 0, 0), bevel=0.008, parent=g)
    box("mag", (0, 0.1, -0.06), (0.03, 0.06, 0.13), blk, rot=(0.2, 0, 0), bevel=0.005, parent=g)
    box("stock", (0, -0.24, 0.04), (0.05, 0.16, 0.07), tan, bevel=0.01, parent=g)
    box("rail", (0, 0.12, 0.108), (0.03, 0.3, 0.012), blk, parent=g)
    box("sight", (0, 0.06, 0.135), (0.04, 0.07, 0.045), blk, bevel=0.005, parent=g)
    box("sightglass", (0, 0.06, 0.137), (0.03, 0.072, 0.03), mat_simple("sglass", (0.05, 0.3, 0.35), 0.05, emit=(1.0, 0.2, 0.15), estr=0.5), parent=g)
    box("stripe", (0.031, 0.25, 0.055), (0.004, 0.16, 0.01), accent, parent=g)
    box("stripe2", (-0.031, 0.25, 0.055), (0.004, 0.16, 0.01), accent, parent=g)
    return g, accent

def gloves(parent):
    """銃を持つ手袋の手（簡略：前腕＋手）"""
    glv = mat_simple("glove", (0.06, 0.06, 0.065), 0.7); sleeve = mat_simple("sleeve", (0.18, 0.2, 0.17), 0.85)
    out = []
    for nm, c, rot in (("handR", (0.0, -0.02, -0.02), (0.3, 0, 0)), ("handL", (-0.01, 0.3, 0.02), (0.1, 0, 0.2))):
        h = box(nm, c, (0.075, 0.1, 0.06), glv, rot=rot, bevel=0.02, parent=parent); out.append(h)
    a1 = cyl("armR", (0.06, -0.25, -0.1), 0.045, 0.35, sleeve, rot=(1.2, 0, 0.35), parent=parent)
    a2 = cyl("armL", (-0.12, 0.12, -0.08), 0.045, 0.4, sleeve, rot=(1.3, 0, -0.55), parent=parent)
    return out

def soldier(name, loc, rnd, visor_col=(1.0, 0.15, 0.08)):
    """顔の見えないヘルメット兵士（オリジナル）。原点＝足元、-Y を向く"""
    r = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(r); r.location = loc
    arm = mat_simple(name + "_armor", (0.12, 0.13, 0.15), 0.45, 0.3, coat=0.2); cloth = mat_simple(name + "_cloth", (0.08, 0.085, 0.09), 0.85)
    visor = mat_simple(name + "_visor", (0.02, 0.02, 0.02), 0.1, emit=visor_col, estr=6.0)
    for sx in (-1, 1):
        cyl(name + "_leg", (sx * 0.11, 0, 0.45), 0.075, 0.9, cloth, parent=r)
        box(name + "_boot", (sx * 0.11, -0.04, 0.05), (0.12, 0.24, 0.1), arm, bevel=0.02, parent=r)
        box(name + "_knee", (sx * 0.11, -0.07, 0.48), (0.1, 0.06, 0.1), arm, bevel=0.015, parent=r)
    box(name + "_torso", (0, 0, 1.2), (0.42, 0.26, 0.55), cloth, bevel=0.05, parent=r)
    box(name + "_vest", (0, -0.03, 1.22), (0.46, 0.3, 0.42), arm, bevel=0.04, parent=r)
    for sx in (-1, 1):
        box(name + "_pad", (sx * 0.27, 0, 1.42), (0.14, 0.2, 0.1), arm, bevel=0.03, parent=r)
        cyl(name + "_arm", (sx * 0.24, -0.15, 1.2), 0.055, 0.4, cloth, rot=(1.2, 0, sx * 0.2), parent=r)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(0, 0, 1.68)); h = bpy.context.object; h.name = name + "_helmet"; h.scale = (1.0, 1.08, 1.0)
    h.data.materials.append(arm); bpy.ops.object.shade_smooth(); h.parent = r
    box(name + "_visor", (0, -0.13, 1.66), (0.22, 0.04, 0.06), visor, bevel=0.015, parent=r)
    g = box(name + "_gun", (0.12, -0.35, 1.18), (0.06, 0.55, 0.08), mat_simple(name + "_g", (0.03, 0.03, 0.03), 0.4, 0.5), bevel=0.01, parent=r)
    return r, visor

def tracer_curve(name, pts, col=(0.35, 0.85, 1.0), strength=30.0, width=0.012):
    """弾の軌跡（曲線に沿った細い光の帯）。pts: 制御点。返り値の bevel_factor_end で伸び具合を動かす"""
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; sp = cu.splines.new("NURBS"); sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts): p.co = (*c, 1.0)
    sp.use_endpoint_u = True; sp.order_u = min(4, len(pts)); cu.bevel_depth = width; cu.bevel_resolution = 2; cu.resolution_u = 24
    o = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(o)
    m = mat_emit(name + "_m", col, strength); cu.materials.append(m); o.visible_shadow = False
    cu.bevel_factor_mapping_start = "SPLINE"; cu.bevel_factor_mapping_end = "SPLINE"
    return o, m
