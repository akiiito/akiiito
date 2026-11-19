"""
s7_world.py ― オリジナルのブロック世界（1ブロック＝1m）。テクスチャは blk_tex/ の自作ドット絵
  セル (i,j,k) は [i,i+1]x[j,j+1]x[k,k+1]。地面の上面は z=0。カメラは原点付近に立ち、+y が西（夕日・影ブロックの来る方）
  world() → dict(...)   update(t, S, ...) で夕日・空・影ブロックを動かす
"""
import math, os, random
import bpy, bmesh
from mathutils import Vector
import s2_world as W, s3_toon as T

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "blk_tex")

def pixmat(name, png, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = bpy.data.images.load(os.path.join(TEX, png + ".png")); tx.interpolation = "Closest"
    # トゥーン調：拡散光を2段にして、テクスチャ色を掛ける
    df = nt.nodes.new("ShaderNodeBsdfDiffuse"); s2r = nt.nodes.new("ShaderNodeShaderToRGB")
    rp = nt.nodes.new("ShaderNodeValToRGB"); rp.color_ramp.interpolation = "CONSTANT"
    el = rp.color_ramp.elements; el[0].position, el[0].color = 0.0, (0.55, 0.55, 0.68, 1); el[1].position, el[1].color = 0.25, (1, 1, 1, 1)
    mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"; mul.inputs["Factor"].default_value = 1.0
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.0 + emit
    nt.links.new(df.outputs[0], s2r.inputs[0]); nt.links.new(s2r.outputs[0], rp.inputs[0])
    nt.links.new(rp.outputs[0], mul.inputs["A"]); nt.links.new(tx.outputs["Color"], mul.inputs["B"])
    nt.links.new(mul.outputs["Result"], em.inputs["Color"]); nt.links.new(em.outputs[0], o.inputs["Surface"])
    return m

def emis(name, col, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*col, 1); e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], o.inputs["Surface"]); return m

FACES = [((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]), ((-1, 0, 0), [(0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)]),
         ((0, 1, 0), [(1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)]), ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
         ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]), ((0, 0, -1), [(0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)])]
UVS = [(0, 0), (1, 0), (1, 1), (0, 1)]

def voxel_mesh(name, cells, mats, kinds):
    """cells: {(i,j,k): kind}  kinds: {kind: (top, side, bottom) の材質インデックス}。見える面だけ作る"""
    me = bpy.data.meshes.new(name); bm = bmesh.new(); uv = bm.loops.layers.uv.new()
    for (i, j, k), kind in cells.items():
        top, side, bot = kinds[kind]
        for n, quad in FACES:
            if (i + n[0], j + n[1], k + n[2]) in cells: continue
            vs = [bm.verts.new((i + a, j + b, k + c)) for a, b, c in quad]
            f = bm.faces.new(vs); f.material_index = top if n[2] == 1 else (bot if n[2] == -1 else side)
            for l, u in zip(f.loops, UVS): l[uv].uv = u
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    for m in mats: me.materials.append(m)
    return o

def single_block(name, mat):
    return voxel_mesh(name, {(0, 0, 0): "b"}, [mat], {"b": (0, 0, 0)})

TREE = (-2, 0)          # 叩く木（x=-2..-1, y=0..1）
PUNCH = (-2, 0, 1)      # 叩いて取るブロック
HUT = [(x, y) for x in range(2, 6) for y in range(3, 7)]

def world():
    M = {k: pixmat("m_" + k, k) for k in ("grass_top", "grass_side", "dirt", "stone", "log_side", "log_top", "leaves", "planks", "shadow")}
    mats = [M[k] for k in ("grass_top", "grass_side", "dirt", "stone", "log_side", "log_top", "leaves")]
    kinds = {"grass": (0, 1, 2), "dirt": (2, 2, 2), "stone": (3, 3, 3), "log": (5, 4, 5), "leaves": (6, 6, 6)}
    cells = {}
    rnd = random.Random(5)
    def hgt(x, y):
        d = math.hypot(x, y)
        if d < 9: return 0
        h = 2.2 * math.sin(x * 0.13 + 1.0) + 2.0 * math.sin(y * 0.11) + 1.4 * math.sin((x + y) * 0.21)
        h += max(0, y - 30) * 0.18                                         # 西の地平線に向けて丘が高くなる
        return int(round(max(-1, h) * min(1, (d - 9) / 8)))
    for x in range(-40, 41):
        for y in range(-30, 70):
            h = hgt(x, y)
            for k in range(h - 3, h):
                cells[(x, y, k)] = "grass" if k == h - 1 else ("dirt" if k >= h - 2 else "stone")
    # 木（叩く木＋まわりに数本）
    def tree(x, y, h=4):
        base = hgt(x, y)
        for k in range(base, base + h): cells[(x, y, k)] = "log"
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                for dk in range(h - 1, h + 2):
                    if abs(dx) + abs(dy) + max(0, dk - h) * 2 <= 3 and (dx, dy) != (0, 0) or dk >= h:
                        if rnd.random() < 0.92 and (x + dx, y + dy, base + dk) not in cells:
                            cells[(x + dx, y + dy, base + dk)] = "leaves"
    tree(*TREE, h=5)
    for (x, y) in [(-7, 6), (-11, -3), (8, -5), (12, 9), (-5, 16), (14, 22), (-14, 20), (4, 18), (-20, 32), (20, 36)]:
        tree(x, y, rnd.randint(4, 6))
    punch_kind = cells.pop(PUNCH)                                            # 叩くブロックは別オブジェクト
    terrain = voxel_mesh("terrain", cells, mats, kinds)
    pb = single_block("punch_block", M["log_side"]); pb.location = PUNCH
    crack = emis("crack", (0.05, 0.03, 0.02), 1.0)
    cracks = []
    for s in range(3):                                                      # ひび（3段階）
        bpy.ops.mesh.primitive_plane_add(size=1); c = bpy.context.object; c.data.materials.append(crack)
        c.rotation_euler = (math.pi / 2, 0, math.pi / 2); c.scale = (0.05, 0.3 + 0.2 * s, 1)
        c.location = (PUNCH[0] + 1.002, PUNCH[1] + 0.5 + (s - 1) * 0.18, PUNCH[2] + 0.5 + (s - 1) * 0.12)
        c.rotation_euler.rotate_axis("Z", 0); c.hide_render = True; cracks.append(c)
    # 家（板ブロック。手から飛んで組み上がる）
    hut = []
    for k in range(3):
        for (x, y) in HUT:
            edge = x in (2, 5) or y in (3, 6)
            door = (x, y) in ((3, 3), (4, 3)) and k < 2
            if edge and not door: hut.append((x, y, k))
    hut += [(x, y, 3) for (x, y) in HUT]
    hut_objs = []
    for c in hut:
        o = single_block("hut", M["planks"]); o.location = c; hut_objs.append(dict(o=o, target=Vector(c)))
    # 夕日（四角い太陽）・星・空
    sun_m = emis("sunsq", (1.0, 0.75, 0.4), 8.0)
    bpy.ops.mesh.primitive_plane_add(size=1); sun = bpy.context.object; sun.data.materials.append(sun_m); sun.visible_shadow = False
    sun.scale = (26, 26, 1)
    star_m = emis("star", (1.0, 1.0, 0.95), 6.0); stars = []
    rs = random.Random(12)
    for k in range(70):
        bpy.ops.mesh.primitive_plane_add(size=1); s = bpy.context.object; s.data.materials.append(star_m); s.visible_shadow = False
        a, e = rs.uniform(-1.2, 1.2), rs.uniform(0.25, 1.1)
        p = Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))) * 500
        s.location = p; s.rotation_euler = (-p).to_track_quat("Z", "Y").to_euler(); stars.append(dict(o=s, size=rs.uniform(1.2, 2.6)))
    W.sky_world(((1.0, 0.6, 0.3), (0.95, 0.55, 0.45), (0.3, 0.45, 0.85)), 1.0)
    light = bpy.data.lights.new("sun", "SUN"); light.energy = 3.5; light.color = (1.0, 0.75, 0.55); light.angle = math.radians(2)
    so = bpy.data.objects.new("sun", light); bpy.context.collection.objects.link(so)
    fl = bpy.data.lights.new("fill", "AREA"); fl.energy = 120; fl.size = 8; fl.color = (0.85, 0.85, 1.0)
    fo = bpy.data.objects.new("fill", fl); bpy.context.collection.objects.link(fo); fo.location = (0, -6, 6); W.aim(fo, (0, 3, 1))
    # 影ブロック（黒い立方体＋光る目）。西の丘の向こうから湧いてくる
    eye_m = emis("shadoweye", (1.0, 0.85, 0.2), 10.0); pupil_m = emis("shadowpupil", (0.05, 0.0, 0.0), 1.0)
    rm = random.Random(21); mobs = []
    for k in range(48):
        x = rm.uniform(-20, 20); y = rm.uniform(17, 34)
        g = hgt(int(x), int(y))
        size = rm.uniform(1.2, 2.4)
        b = single_block("mob", M["shadow"]); b.scale = (size,) * 3
        bpy.ops.mesh.primitive_plane_add(size=1); e = bpy.context.object; e.data.materials.append(eye_m); e.visible_shadow = False
        e.parent = b; e.location = (0.5, -0.004, 0.6); e.rotation_euler = (math.pi / 2, 0, 0); e.scale = (0.42, 0.42, 1)   # 大きな一つ目
        bpy.ops.mesh.primitive_plane_add(size=1); pu = bpy.context.object; pu.data.materials.append(pupil_m); pu.visible_shadow = False
        pu.parent = b; pu.location = (0.5, -0.008, 0.6); pu.rotation_euler = (math.pi / 2, 0, 0); pu.scale = (0.1, 0.26, 1)
        mobs.append(dict(o=b, x=x, y=y, g=g, size=size, ph=rm.uniform(0, 6.28), delay=rm.uniform(0, 2.5), speed=rm.uniform(0.6, 1.3)))
    # 手が光るときの光
    glow = bpy.data.lights.new("handglow", "POINT"); glow.color = (0.55, 0.9, 1.0); glow.energy = 0.0
    gl = bpy.data.objects.new("handglow", glow); bpy.context.collection.objects.link(gl)
    return dict(M=M, terrain=terrain, punch=pb, cracks=cracks, hut=hut_objs, sun=sun, sun_light=so, stars=stars, mobs=mobs,
                hand_light=gl, hgt=hgt, fill=fl)

def sky_at(t, night):
    """night: 0（夕方）→1（夜）"""
    def mix(a, b): return tuple(x + (y - x) * night for x, y in zip(a, b))
    return (mix((1.0, 0.6, 0.3), (0.12, 0.1, 0.3)), mix((0.95, 0.5, 0.45), (0.06, 0.06, 0.2)), mix((0.3, 0.45, 0.85), (0.01, 0.01, 0.05)))

def update(t, S, night, sun_elev, mob_k):
    nt = bpy.context.scene.world.node_tree
    ramp = [n for n in nt.nodes if n.type == "VALTORGB"][0]
    cols = sky_at(t, night)
    els = sorted(ramp.color_ramp.elements, key=lambda e: e.position)
    for e, c in zip(els, cols): e.color = c + (1,)
    nt.nodes["Background"].inputs["Strength"].default_value = 1.0 - 0.55 * night
    e = math.radians(sun_elev)
    d = Vector((0.25, math.cos(e), math.sin(e))).normalized()
    S["sun"].location = d * 420; S["sun"].rotation_euler = (-d).to_track_quat("Z", "Y").to_euler()
    S["sun_light"].location = d * 50; W.aim(S["sun_light"], (0, 0, 0))
    S["sun_light"].data.energy = 3.5 * max(0.0, 1 - night * 1.15)
    S["sun_light"].data.color = (1.0, 0.75 - 0.3 * night, 0.55 - 0.3 * night)
    S["fill"].energy = 120 - 80 * night
    for s in S["stars"]:
        s["o"].scale = (s["size"] * night ** 2 + 1e-4,) * 3
    for m in S["mobs"]:
        k = max(0.0, mob_k - m["delay"] * 0.25)
        rise = min(1.0, k * 1.5)
        hop = abs(math.sin(t * 3.0 * m["speed"] + m["ph"])) * 0.6 * min(1, k)
        y = m["y"] - k * 1.1 * m["speed"]
        z = m["g"] - m["size"] * (1 - rise) + hop
        m["o"].location = (m["x"] - m["size"] / 2, y, z)
        m["o"].rotation_euler = (0, 0, 0)
