"""
s6_world.py ― 異世界の花畑（夕暮れ・二つの月）。ハナの物語の舞台
  原点に自分（カメラ）。+y 方向へ花畑がつづき、y≈26 の丘に大きな一本木。-y 側の森の入口から影の魔物が出る。
  meadow() → dict(petals=[...], fireflies=[...], wolf=, wolf_eyes=)
  hana(...) → ハナ（めいモデル＋柴犬色の髪・犬耳・クリーム色のワンピース・赤いリボン）
"""
import math, random
import bpy
from mathutils import Vector
import s2_world as W, s3_toon as T

SKY = ((1.0, 0.42, 0.32), (0.5, 0.26, 0.62), (0.04, 0.05, 0.2))     # 地平線＝桃色、上空＝群青

def emis(name, col, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*col, 1); e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], o.inputs["Surface"]); return m

def recolor(mat_name, base, shade=None):
    """T.toon の色を後から変える"""
    m = bpy.data.materials[mat_name]
    if shade is None: shade = (base[0] * 0.8, base[1] * 0.76, base[2] * 0.88)
    el = [n for n in m.node_tree.nodes if n.type == "VALTORGB"][0].color_ramp.elements
    el[0].color = T.lin(shade) + (1,); el[1].color = T.lin(base) + (1,)

def flower_proto(name, col):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4, radius=0.07, location=(0, 0, 0))
    f = bpy.context.object; f.name = name; f.scale = (1, 1, 0.45)
    f.data.materials.append(T.toon(name + "_m", col)); return f

def meadow():
    grass = T.toon("grass", (0.36, 0.6, 0.38), (0.22, 0.4, 0.3))
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 10, 0)); g = bpy.context.object; g.name = "field"
    g.scale = (120, 140, 1); bpy.ops.object.transform_apply(scale=True)
    g.data.materials.append(grass)
    # 丘（一本木の足もと）
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.0, location=(0, 34, -6.5))
    h = bpy.context.object; h.scale = (20, 14, 8); h.data.materials.append(grass); bpy.ops.object.shade_smooth()
    # 花（パーティクルで大量に。白・桃・黄・水色）
    cols = [(1.0, 0.98, 0.95), (1.0, 0.7, 0.8), (1.0, 0.9, 0.45), (0.65, 0.85, 1.0), (1.0, 0.6, 0.65)]
    protos = [flower_proto("flower%d" % i, c) for i, c in enumerate(cols)]
    coll = bpy.data.collections.new("flowers"); bpy.context.scene.collection.children.link(coll)
    for p in protos:
        for c in p.users_collection: c.objects.unlink(p)
        coll.objects.link(p)
    for lc in bpy.context.view_layer.layer_collection.children:
        if lc.name == "flowers": lc.exclude = True
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 13, 0.03)); fp = bpy.context.object; fp.name = "flowerbed"
    fp.scale = (22, 40, 1); bpy.ops.object.transform_apply(scale=True)
    ps = fp.modifiers.new("fl", "PARTICLE_SYSTEM").particle_system.settings
    ps.type = "HAIR"; ps.count = 45000; ps.hair_length = 0.12; ps.render_type = "COLLECTION"; ps.instance_collection = coll
    ps.use_collection_pick_random = True; ps.particle_size = 2.2; ps.size_random = 0.6; ps.use_advanced_hair = True
    ps.use_rotations = True; ps.rotation_mode = "NOR"; ps.phase_factor_random = 2.0
    fp.data.materials.append(grass); fp.hide_render = False
    fp.show_instancer_for_render = False
    # 大きな一本木（丘の上）
    bark = T.toon("bark", (0.42, 0.3, 0.24)); leaf = T.toon("leaf", (0.98, 0.72, 0.8), (0.82, 0.5, 0.66))
    W.cyl("trunk", (0, 30, 3.0), 0.7, 6.5, bark, verts=16)
    rnd = random.Random(3)
    for k in range(14):
        p = Vector((rnd.uniform(-4.5, 4.5), 30 + rnd.uniform(-3, 3), rnd.uniform(6.0, 9.5)))
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rnd.uniform(2.0, 3.2), location=p)
        o = bpy.context.object; o.data.materials.append(leaf); T.link(o)
    T.link(bpy.data.objects["trunk"])
    # 遠くの浮島（空に浮かぶ岩と滝）
    rock = T.toon("isle", (0.55, 0.5, 0.58), (0.36, 0.32, 0.45)); top = T.toon("isletop", (0.45, 0.66, 0.46))
    for k, (x, y, z, s) in enumerate([]):
        bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=s, depth=s * 1.6, location=(x, y, z - s * 0.8), rotation=(math.pi, 0, 0))
        bpy.context.object.data.materials.append(rock)
        W.cyl("isletop%d" % k, (x, y, z), s, 0.8, top, verts=7)
    # 森（-y 側、魔物が出る）
    dark = T.toon("forest", (0.16, 0.2, 0.26), (0.08, 0.1, 0.16))
    rf = random.Random(8)
    for k in range(60):
        x = rf.uniform(-40, 40); y = rf.uniform(-34, -24); hgt = rf.uniform(7, 13)
        W.cyl("ftr", (x, y, hgt * 0.3), 0.3, hgt * 0.6, dark, verts=6)
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=rf.uniform(2.2, 3.4), depth=hgt, location=(x, y, hgt * 0.75))
        bpy.context.object.data.materials.append(dark)
    # 影の魔物（大きな黒い狼のシルエット＋赤い目）
    shadow = emis("shadow", (0.02, 0.0, 0.04), 1.0)
    wolf = bpy.data.objects.new("wolf", None); bpy.context.collection.objects.link(wolf)
    def blob(loc, sc, m=shadow):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0, location=loc); o = bpy.context.object
        o.scale = sc; o.data.materials.append(m); o.parent = wolf; o.visible_shadow = False; return o
    blob((0, 0, 3.2), (2.2, 4.0, 2.3)); blob((0, 3.6, 4.6), (1.6, 1.9, 1.5))
    for s in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.5, depth=1.5, location=(0.9 * s, 4.0, 6.4)); o = bpy.context.object
        o.data.materials.append(shadow); o.parent = wolf
        for ly in (-2.2, 2.2): blob((1.3 * s, ly, 1.2), (0.45, 0.45, 1.5))
    eye_m = emis("wolfeye", (1.0, 0.03, 0.02), 2.2)
    eyes = [blob((0.62 * s, 5.42, 4.35), (0.34, 0.12, 0.15), eye_m) for s in (-1, 1)]
    for o, s in zip(eyes, (-1, 1)): o.rotation_euler = (0, math.radians(-22 * s), 0)
    wolf.location = (0, -18, 0); wolf.rotation_euler = (0, 0, 0); wolf.scale = (1.9, 1.9, 1.9)
    # 空・二つの月・光
    W.sky_world(SKY, 0.9)
    mm = emis("moon1", (1.0, 0.82, 0.66), 0.85); mm2 = emis("moon2", (0.62, 0.78, 1.0), 1.4)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=48, location=(-55, 300, 120)); bpy.context.object.data.materials.append(mm)
    bpy.context.object.visible_shadow = False
    bpy.ops.mesh.primitive_uv_sphere_add(radius=22, location=(75, 320, 82)); bpy.context.object.data.materials.append(mm2)
    bpy.context.object.visible_shadow = False
    sun = bpy.data.lights.new("dusk", "SUN"); sun.energy = 4.0; sun.color = (1.0, 0.68, 0.55); sun.angle = math.radians(3)
    so = bpy.data.objects.new("dusk", sun); bpy.context.collection.objects.link(so); so.location = (0, 60, 20); W.aim(so, (0, 0, 0))
    fl = bpy.data.lights.new("fill", "AREA"); fl.energy = 70; fl.size = 8; fl.color = (0.9, 0.8, 1.0)
    fo = bpy.data.objects.new("fill", fl); bpy.context.collection.objects.link(fo); fo.location = (0, -5, 5); W.aim(fo, (0, 3, 1))
    # 舞う花びらと蛍
    pm = T.toon("petal", (1.0, 0.75, 0.85)); petals = []; fireflies = []
    rp = random.Random(17)
    for k in range(90):
        bpy.ops.mesh.primitive_plane_add(size=0.06); o = bpy.context.object; o.data.materials.append(pm)
        petals.append(dict(o=o, p=Vector((rp.uniform(-6, 6), rp.uniform(-4, 34), rp.uniform(0.2, 4))), ph=rp.uniform(0, 6.28), v=rp.uniform(0.6, 1.4)))
    ff = emis("firefly", (1.0, 0.95, 0.55), 30.0)
    for k in range(50):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.025); o = bpy.context.object; o.data.materials.append(ff)
        o.visible_shadow = False
        fireflies.append(dict(o=o, p=Vector((rp.uniform(-7, 7), rp.uniform(-3, 32), rp.uniform(0.3, 2.5))), ph=rp.uniform(0, 6.28)))
    # ハナが消えかけるときの光の粒
    sp = emis("spark", (1.0, 0.86, 0.5), 25.0); sparks = []
    for k in range(40):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.012); o = bpy.context.object; o.data.materials.append(sp)
        o.visible_shadow = False; sparks.append(dict(o=o, ph=rp.uniform(0, 6.28), r=rp.uniform(0.02, 0.12), v=rp.uniform(0.2, 0.6)))
    return dict(petals=petals, fireflies=fireflies, wolf=wolf, wolf_eyes=eyes, sparks=sparks)

def update(t, S, wind=1.0):
    for p in S["petals"]:
        x = p["p"].x + math.sin(t * 0.7 + p["ph"]) * 0.6 + t * 0.35 * wind
        z = p["p"].z + 0.3 * math.sin(t * 1.1 + p["ph"]) - ((t * 0.15 * p["v"]) % 3.0)
        p["o"].location = ((x + 6) % 12 - 6, p["p"].y, max(0.15, z % 4.2))
        p["o"].rotation_euler = (t * 2 * p["v"] + p["ph"], t * 1.3 + p["ph"], 0)
    for f in S["fireflies"]:
        f["o"].location = f["p"] + Vector((0.4 * math.sin(t * 0.6 + f["ph"]), 0.3 * math.cos(t * 0.5 + f["ph"]), 0.2 * math.sin(t * 0.9 + f["ph"])))
        f["o"].scale = (0.6 + 0.4 * math.sin(t * 3 + f["ph"]),) * 3

def hana(loc, rot=180, pull=False):
    """ハナ。pull=True は右手を後ろ（見ている人の方）へのばして手を引くポーズ"""
    name = "hana_pull" if pull else "hana"
    arms = {"R": ((-0.2, -0.16, 1.06), (-0.22, -0.42, 1.0))} if pull else None
    root, tex = T.girl(name, tuple(loc), rot=rot, hair=(0.86, 0.56, 0.3), face="mei", ponytail=False, arms=arms)
    recolor(name + "_blazer", (0.98, 0.95, 0.88)); recolor(name + "_skirt", (0.95, 0.9, 0.8)); recolor(name + "_sock", (0.98, 0.98, 0.98))
    hm = bpy.data.materials[name + "_hair"]; red = bpy.data.materials[name + "_ribbon"]
    inner = T.toon(name + "_ear_in", (1.0, 0.82, 0.8))
    for s in (-1, 1):                                                # 柴犬の耳
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.055, depth=0.12, location=(0.085 * s, -0.01, 1.6), rotation=(math.radians(-8), math.radians(18 * s), math.radians(45)))
        o = bpy.context.object; o.scale = (1, 0.55, 1); o.data.materials.append(hm); o.parent = root; T.link(o)
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.032, depth=0.08, location=(0.085 * s, 0.012, 1.595), rotation=(math.radians(-8), math.radians(18 * s), math.radians(45)))
        o = bpy.context.object; o.scale = (1, 0.3, 1); o.data.materials.append(inner); o.parent = root; T.link(o)
    for s in (-1, 1):                                                # 頭の大きな赤いリボン（昔の首輪と同じ色）
        bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.05, depth=0.09, location=(0.06 * s + 0.09, -0.06, 1.56), rotation=(0, math.radians(90 * s), 0))
        o = bpy.context.object; o.data.materials.append(red); o.parent = root; T.link(o)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=0.022, location=(0.09, -0.06, 1.56))
    o = bpy.context.object; o.data.materials.append(red); o.parent = root; T.link(o)
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.07, depth=0.32, location=(0, -0.14, 0.78), rotation=(math.radians(-140), 0, 0))
    o = bpy.context.object; o.scale = (0.8, 1, 1); o.data.materials.append(hm); o.parent = root; T.link(o)   # しっぽ
    return root, tex
