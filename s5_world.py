"""
s5_world.py ― 異世界×世界の終わり：「月が落ちてくる王都の広場」
  広場の中心が原点。カメラ（召喚された自分）は y<0 側から +y を向く。正面奥（+y）の空に巨大な月。
  apocalypse() → dict(moon=, crack=[...], meteors=[...], embers=[...], rock=, rune=, hand_light=)
  毎コマ update(t, S, ...) で月の接近・流星・火の粉を動かす。
"""
import math, random
import bpy
from mathutils import Vector
import s2_world as W, s3_toon as T

SKY = ((0.85, 0.16, 0.06), (0.45, 0.08, 0.12), (0.06, 0.03, 0.1))   # 地平線＝赤、上空＝暗い紫

def emis(name, col, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*col, 1); e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], o.inputs["Surface"]); return m

def moon_mat():
    """赤く焼けた月：ノイズで溶岩っぽいまだら＋自分で光る"""
    m = bpy.data.materials.new("moon"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); e = nt.nodes.new("ShaderNodeEmission")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.5; nz.inputs["Detail"].default_value = 10
    rp = nt.nodes.new("ShaderNodeValToRGB"); el = rp.color_ramp.elements
    el[0].position, el[0].color = 0.35, (0.25, 0.05, 0.03, 1); el[1].position, el[1].color = 0.7, (1.0, 0.55, 0.2, 1)
    nt.links.new(nz.outputs["Fac"], rp.inputs["Fac"]); nt.links.new(rp.outputs["Color"], e.inputs["Color"])
    e.inputs["Strength"].default_value = 2.2; nt.links.new(e.outputs[0], o.inputs["Surface"]); return m

MOON_DIR = Vector((0.1, 1.0, 0.62)).normalized()                    # 正面やや上
MOON_DIST = 420.0

def apocalypse():
    M = dict(stone=W.mat("plaza", (0.42, 0.38, 0.36), 0.85, noise=(4.0, 0.25)),
             wall=W.mat("house", (0.55, 0.47, 0.4), 0.9, noise=(3.0, 0.2)),
             roof=W.mat("roof", (0.32, 0.12, 0.1), 0.7),
             dark=W.mat("castle", (0.08, 0.06, 0.08), 0.9),
             fire=emis("fire", (1.0, 0.42, 0.1), 6.0),
             win=emis("winglow", (1.0, 0.6, 0.25), 4.0))
    # 石畳の広場（直径40）＋石の継ぎ目
    W.box("plaza", (0, 0, -0.1), (300, 300, 0.2), M["stone"])
    for k in range(-20, 21):
        W.box("seam%d" % k, (k * 0.9, 0, 0.002), (0.025, 60, 0.004), W.mat("seam", (0.2, 0.18, 0.17), 0.9))
    # 中央の噴水（壊れかけ）
    W.cyl("fountain", (0, 9, 0.35), 2.2, 0.7, M["stone"], verts=32)
    W.cyl("fountain_pillar", (0, 9, 1.4), 0.35, 2.0, M["stone"], verts=16)
    # 広場を囲む家並み（三角屋根＋灯った窓、ところどころ燃えている）
    rnd = random.Random(21)
    for k in range(46):
        a = math.radians(-80 + k * (340 / 46)) if k % 2 else math.radians(-75 + k * (330 / 46))
        r = rnd.uniform(17, 24)
        x, y = math.sin(a) * r, math.cos(a) * r
        if y < -6: continue
        h = rnd.uniform(5, 11); w = rnd.uniform(3.5, 6)
        rot = (0, 0, -a)
        W.box("h%d" % k, (x, y, h / 2), (w, 4, h), M["wall"], rot=rot)
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=w * 0.78, depth=3.2, location=(x, y, h + 1.6), rotation=(0, 0, -a + math.pi / 4))
        bpy.context.object.data.materials.append(M["roof"])
        for j in range(rnd.randint(1, 3)):
            off = rnd.uniform(-w / 3, w / 3); z = rnd.uniform(1.5, h - 1)
            W.box("wn", (x - math.sin(a) * 2.02 + math.cos(a) * off, y - math.cos(a) * 2.02 - math.sin(a) * off, z), (0.7, 0.05, 0.9), M["win"], rot=rot)
        if rnd.random() < 0.25:                                        # 燃える屋根
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rnd.uniform(1.0, 1.8), location=(x, y, h + 1.2))
            fo = bpy.context.object; fo.scale = (1, 1, 1.6); fo.data.materials.append(M["fire"]); fo.visible_shadow = False
    # 奥の王城（シルエット）：塔と城壁
    for k, (x, h, r) in enumerate([(-30, 55, 5), (-12, 70, 6), (0, 90, 7), (14, 65, 5.5), (32, 50, 4.5)]):
        W.cyl("tower%d" % k, (x, 120, h / 2 - 2), r, h, M["dark"], verts=16)
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=r * 1.25, depth=r * 3, location=(x, 120, h - 2 + r * 1.5))
        bpy.context.object.data.materials.append(M["dark"])
    W.box("castle_wall", (0, 118, 12), (90, 6, 28), M["dark"])
    # 空と月
    W.sky_world(SKY, 1.0)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0, location=tuple(MOON_DIR * MOON_DIST))
    moon = bpy.context.object; moon.name = "moon"; moon.data.materials.append(moon_mat()); moon.visible_shadow = False
    # ひび（月の手前側の面に貼る細い光の筋。最初はscale 0）
    crack = []
    cm = emis("crack", (1.0, 0.95, 0.75), 30.0)
    rc = random.Random(4)
    for k in range(9):
        bpy.ops.mesh.primitive_cube_add(size=1.0); c = bpy.context.object; c.data.materials.append(cm); c.visible_shadow = False
        c["ang"] = rc.uniform(0, 2 * math.pi); c["len"] = rc.uniform(0.35, 0.9); c["off"] = rc.uniform(-0.25, 0.25)
        crack.append(c)
    # 月明かり（赤い太陽光）と、手前の弱い補助光
    sun = bpy.data.lights.new("moonlight", "SUN"); sun.energy = 4.5; sun.color = (1.0, 0.45, 0.25); sun.angle = math.radians(4)
    so = bpy.data.objects.new("moonlight", sun); bpy.context.collection.objects.link(so)
    so.location = tuple(MOON_DIR * 50); W.aim(so, (0, 0, 0))
    fl = bpy.data.lights.new("fill", "AREA"); fl.energy = 220; fl.size = 8; fl.color = (0.85, 0.65, 0.75)
    fo = bpy.data.objects.new("fill", fl); bpy.context.collection.objects.link(fo); fo.location = (0, -6, 5); W.aim(fo, (0, 2, 1.2))
    # 流星（光る球＋尾）
    meteors = []
    mm = emis("meteor", (1.0, 0.7, 0.35), 25.0)
    rm = random.Random(9)
    for k in range(10):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=1.0); h = bpy.context.object; h.data.materials.append(mm)
        h.visible_shadow = False
        bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=1.0, depth=1.0); tl = bpy.context.object; tl.data.materials.append(mm)
        tl.visible_shadow = False
        meteors.append(dict(head=h, tail=tl, t0=rm.uniform(-2, 30), dur=rm.uniform(1.6, 3.0),
                            p0=Vector((rm.uniform(-160, 160), rm.uniform(120, 260), rm.uniform(90, 160))),
                            d=Vector((rm.uniform(-0.6, 0.6), rm.uniform(-0.5, -0.1), -1)).normalized() * rm.uniform(70, 120),
                            r=rm.uniform(1.0, 2.6)))
    # 火の粉（舞い上がる小さな光）
    embers = []
    em = emis("ember", (1.0, 0.5, 0.15), 18.0)
    re = random.Random(13)
    for k in range(70):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0); e = bpy.context.object; e.data.materials.append(em)
        e.visible_shadow = False
        embers.append(dict(o=e, p=Vector((re.uniform(-8, 8), re.uniform(-2, 16), re.uniform(0, 7))), v=re.uniform(0.5, 1.4),
                           ph=re.uniform(0, 6.28), r=re.uniform(0.012, 0.03)))
    # 飛んでくる岩
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.55); rock = bpy.context.object; rock.name = "rock"
    rr = random.Random(2)
    for v in rock.data.vertices: v.co *= rr.uniform(0.82, 1.15)
    rock.scale = (1.0, 0.85, 0.9)
    rock.data.materials.append(T.toon("rock", (0.36, 0.3, 0.28), (0.18, 0.13, 0.13))); bpy.ops.object.shade_flat(); T.link(rock)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.5); lava = bpy.context.object; lava.parent = rock
    lava.data.materials.append(emis("lava", (1.0, 0.35, 0.08), 1.5)); lava.scale = (0.98, 0.98, 0.98); lava.visible_shadow = False
    # 時間停止の魔法陣（青白く光る輪：岩のまわり／手の前）
    rune_m = emis("rune", (0.45, 0.85, 1.0), 5.0)
    def ring(name, r, w):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=w, major_segments=64, minor_segments=8); o = bpy.context.object
        o.name = name; o.data.materials.append(rune_m); o.visible_shadow = False; return o
    rune = [ring("rune_a", 1.0, 0.012), ring("rune_b", 0.8, 0.007), ring("rune_c", 0.6, 0.018)]
    hand_light = bpy.data.lights.new("handglow", "POINT"); hand_light.color = (0.45, 0.8, 1.0); hand_light.energy = 0.0
    hl = bpy.data.objects.new("handglow", hand_light); bpy.context.collection.objects.link(hl)
    return dict(moon=moon, crack=crack, meteors=meteors, embers=embers, rock=rock, rune=rune, hand_light=hl, rune_m=rune_m)

def knight_gear(root, name="kai"):
    """陽太モデルに騎士の装備：銀の胸当て・肩当て・赤いマント・背中の剣"""
    silver = T.toon(name + "_silver", (0.82, 0.84, 0.9), (0.45, 0.48, 0.58))
    red = T.toon(name + "_cape", (0.75, 0.12, 0.12), (0.45, 0.05, 0.08))
    gold = T.toon(name + "_gold", (0.95, 0.78, 0.3), (0.6, 0.42, 0.15))
    def add(o): o.parent = root; T.link(o); return o
    add(W.box(name + "_plate", (0, 0.035, 1.2), (0.3, 0.2, 0.32), silver, bevel=0.05))
    for s in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.085, location=(0.19 * s, 0, 1.38))
        o = bpy.context.object; o.scale = (1.2, 1.0, 0.7); o.data.materials.append(silver); bpy.ops.object.shade_smooth(); add(o)
    add(W.box(name + "_belt", (0, 0.0, 0.95), (0.3, 0.2, 0.05), gold))
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -0.13, 0.92), rotation=(math.radians(84), 0, 0))
    c = bpy.context.object; c.scale = (0.42, 0.95, 1); c.data.materials.append(red); add(c)
    add(W.cyl(name + "_sword", (0.12, -0.16, 1.15), 0.025, 1.0, silver, rot=(0, math.radians(-25), 0), verts=8))
    add(W.cyl(name + "_hilt", (-0.08, -0.16, 1.58), 0.03, 0.18, gold, rot=(0, math.radians(-25), 0), verts=8))

def update(t, S, cam_pos, moon_r, moon_pull, crack_k, rune_k, rock_pos, hands_world):
    """t秒の空・月・流星・火の粉・岩・魔法陣"""
    moon = S["moon"]; d = MOON_DIST - moon_pull
    moon.location = tuple(MOON_DIR * d); moon.scale = (moon_r,) * 3
    toward = -MOON_DIR
    up = Vector((0, 0, 1)); side = toward.cross(up).normalized(); up2 = side.cross(toward).normalized()
    for c in S["crack"]:
        L = c["len"] * moon_r * crack_k
        ctr = moon.location + toward * moon_r * 1.05 + (side * math.cos(c["ang"]) + up2 * math.sin(c["ang"])) * moon_r * (0.3 + 0.6 * c["len"]) * 0.5 * crack_k
        c.location = ctr
        c.scale = (max(L * 0.6, 1e-3), moon_r * 0.02 * (1 if crack_k > 0 else 0) + 1e-4, moon_r * 0.02 * (1 if crack_k > 0 else 0) + 1e-4)
        c.rotation_euler = (side * math.cos(c["ang"]) + up2 * math.sin(c["ang"])).to_track_quat("X", "Z").to_euler()
    for m in S["meteors"]:
        k = ((t - m["t0"]) % 6.0) / m["dur"]
        vis = 0 <= k <= 1
        p = m["p0"] + m["d"] * k
        m["head"].location = p; m["head"].scale = (m["r"],) * 3 if vis else (1e-4,) * 3
        dirn = m["d"].normalized(); L = m["r"] * 14
        m["tail"].location = p - dirn * L / 2; m["tail"].scale = (m["r"] * 0.9, m["r"] * 0.9, L) if vis else (1e-4,) * 3
        m["tail"].rotation_euler = dirn.to_track_quat("Z", "Y").to_euler()
    for e in S["embers"]:
        z = (e["p"].z + t * e["v"]) % 8.0
        e["o"].location = (e["p"].x + 0.4 * math.sin(t * 0.8 + e["ph"]), e["p"].y + 0.3 * math.cos(t * 0.6 + e["ph"]), z)
        e["o"].scale = (e["r"],) * 3
    S["rock"].location = rock_pos
    S["rock"].rotation_euler = (t * 2.0, t * 1.3, 0) if rune_k < 0.5 else S["rock"].rotation_euler
    for i, o in enumerate(S["rune"]):
        o.location = rock_pos
        o.scale = (rune_k * (1.0 + 0.05 * math.sin(t * 6 + i)),) * 3 if rune_k > 0 else (1e-4,) * 3
        o.rotation_euler = ((cam_pos - Vector(rock_pos)).to_track_quat("Z", "Y").to_euler().x, 0, t * (1.5 - i))
        o.rotation_euler = (cam_pos - Vector(rock_pos)).to_track_quat("Z", "Y").to_euler()
        o.rotation_euler.rotate_axis("Z", t * (1.2 - i * 0.9))
