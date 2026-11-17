"""
s2_world.py ― 新シリーズ『君は写真に写らない』の共通部品（夕方の教室・人物・カメラ）
  リアル寄り：物理ベースの光、ボリューム（光の筋）、被写界深度、手持ちカメラの揺れ。
"""
import math, random
import bpy
from mathutils import Vector

def reset(samples=64, res=(720, 1280)):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    try: sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception: pass
    sc.cycles.max_bounces = 6
    sc.cycles.volume_bounces = 1
    sc.cycles.volume_step_rate = 4.0
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.fps = 24
    sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
    sc.view_settings.look = "None"
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"
    return sc

# ---------------------------------------------------------------- materials
def mat(name, col, rough=0.6, metal=0.0, spec=0.5, emit=None, estr=0.0, sss=0.0, noise=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit is not None:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = estr
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    if noise:                                         # 木目・汚れなどの微妙なムラ
        tex = nt.nodes.new("ShaderNodeTexNoise"); tex.inputs["Scale"].default_value = noise[0]
        tex.inputs["Detail"].default_value = 8; tex.inputs["Roughness"].default_value = 0.6
        if len(noise) > 2:
            map_ = nt.nodes.new("ShaderNodeMapping"); co = nt.nodes.new("ShaderNodeTexCoord")
            map_.inputs["Scale"].default_value = noise[2]
            nt.links.new(co.outputs["Object"], map_.inputs["Vector"]); nt.links.new(map_.outputs["Vector"], tex.inputs["Vector"])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (*[c * (1 - noise[1]) for c in col], 1)
        ramp.color_ramp.elements[1].color = (*[min(1, c * (1 + noise[1])) for c in col], 1)
        nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    return m

def glass():
    m = bpy.data.materials.new("glass"); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); g = nt.nodes.new("ShaderNodeBsdfTransparent")
    gl = nt.nodes.new("ShaderNodeBsdfGlossy"); g.inputs["Color"].default_value = (0.95, 0.97, 0.98, 1)
    gl.inputs["Roughness"].default_value = 0.02
    mx = nt.nodes.new("ShaderNodeMixShader"); mx.inputs["Fac"].default_value = 0.08
    nt.links.new(g.outputs[0], mx.inputs[1]); nt.links.new(gl.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o.inputs["Surface"])
    return m

def box(name, loc, size, m, bevel=0.0, parent=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        mod = o.modifiers.new("bv", "BEVEL"); mod.width = bevel; mod.segments = 3
    o.data.materials.append(m)
    if parent: o.parent = parent
    return o

def cyl(name, loc, r, h, m, rot=(0, 0, 0), verts=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o

# ---------------------------------------------------------------- classroom
def classroom(sun_elev=14.0, sun_az=-35.0, sun_col=(1.0, 0.55, 0.28), haze=0.006):
    W, D, H = 8.0, 9.0, 3.0                                   # x: windows at -W/2, y: front(board) at +D/2
    M = dict(
        floor=mat("floor", (0.32, 0.2, 0.11), 0.45, noise=(3.0, 0.25, (1, 8, 1))),
        wall=mat("wall", (0.78, 0.76, 0.7), 0.85, noise=(6.0, 0.05)),
        ceil=mat("ceil", (0.85, 0.85, 0.82), 0.9),
        board=mat("board", (0.05, 0.16, 0.1), 0.75, noise=(20.0, 0.25)),
        frame=mat("frame", (0.55, 0.57, 0.6), 0.35, 0.8),
        desk=mat("desk", (0.62, 0.43, 0.25), 0.45, noise=(4.0, 0.2, (1, 6, 1))),
        steel=mat("steel", (0.4, 0.42, 0.44), 0.35, 0.9),
        curtain=mat("curtain", (0.82, 0.78, 0.66), 0.95, sss=0.2),
        glass=glass())
    box("floor", (0, 0, -0.05), (W, D, 0.1), M["floor"])
    box("ceiling", (0, 0, H + 0.05), (W, D, 0.1), M["ceil"])
    box("wall_front", (0, D / 2 + 0.05, H / 2), (W, 0.1, H), M["wall"])
    box("wall_back", (0, -D / 2 - 0.05, H / 2), (W, 0.1, H), M["wall"])
    box("wall_in", (W / 2 + 0.05, 0, H / 2), (0.1, D, H), M["wall"])
    # window wall: low wall + pillars + top, glass panes
    x = -W / 2 - 0.05
    box("win_low", (x, 0, 0.45), (0.12, D, 0.9), M["wall"])
    box("win_top", (x, 0, H - 0.2), (0.12, D, 0.4), M["wall"])
    n = 4
    for k in range(n + 1):
        y = -D / 2 + k * D / n
        box("pillar%d" % k, (x, y, H / 2), (0.14, 0.35, H), M["wall"])
    for k in range(n * 2):
        y0 = -D / 2 + 0.18 + k * (D - 0.36) / (n * 2)
        wdt = (D - 0.36) / (n * 2)
        box("sash%d" % k, (x + 0.02, y0 + wdt / 2, 1.85), (0.03, wdt, 1.9), M["glass"])
        box("sashf%d" % k, (x + 0.02, y0 + 0.01, 1.85), (0.05, 0.03, 1.9), M["frame"])
    box("rail_lo", (x + 0.03, 0, 0.92), (0.06, D, 0.04), M["frame"])
    box("rail_hi", (x + 0.03, 0, 2.8), (0.06, D, 0.04), M["frame"])
    # curtains bunched at pillars
    for k in range(1, n):
        y = -D / 2 + k * D / n
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x + 0.25, y + 0.35, 1.85))
        c = bpy.context.object; c.scale = (0.01, 0.45, 1.0); c.rotation_euler = (0, 0, 0)
        bpy.ops.object.transform_apply(scale=True)
        bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.subdivide(number_cuts=24); bpy.ops.object.mode_set(mode="OBJECT")
        for v in c.data.vertices:                       # folds
            v.co.x += 0.06 * math.sin(v.co.y * 40.0)
        c.modifiers.new("sol", "SOLIDIFY").thickness = 0.01
        c.data.materials.append(M["curtain"]); bpy.ops.object.shade_smooth()
    # blackboard
    box("board", (0.2, D / 2 - 0.02, 1.55), (4.6, 0.04, 1.2), M["board"])
    box("board_tray", (0.2, D / 2 - 0.08, 0.93), (4.6, 0.1, 0.04), M["frame"])
    # desks 5 cols x 5 rows
    for cx in range(5):
        for ry in range(5):
            desk((-2.6 + cx * 1.25 + random.uniform(-0.05, 0.05), 2.4 - ry * 1.15 + random.uniform(-0.05, 0.05)), M,
                 rot=random.uniform(-4, 4))
    # fluorescent fixtures (off)
    for k in range(3):
        for j in range(2):
            box("lamp%d%d" % (k, j), (-1.6 + j * 3.2, -2.8 + k * 2.8, H - 0.05), (0.25, 1.3, 0.06), M["frame"])
    # sun + sky
    sun = bpy.data.lights.new("sun", "SUN"); sun.energy = 7.0; sun.color = sun_col; sun.angle = math.radians(0.6)
    so = bpy.data.objects.new("sun", sun); bpy.context.collection.objects.link(so)
    # 夕日は窓の外（-x 側）の低い位置から室内へ差し込む。sun_az は窓に対する左右の振り
    e, az = math.radians(sun_elev), math.radians(sun_az)
    so.location = (-10, 0, 3); aim(so, (-10 + math.cos(e) * math.cos(az), math.cos(e) * math.sin(az), 3 - math.sin(e)))
    sun.energy = 14.0
    w = bpy.data.worlds.new("w"); bpy.context.scene.world = w; w.use_nodes = True
    nt = w.node_tree
    co = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.0, (1.0, 0.42, 0.16, 1)          # 地平線：オレンジ
    el[1].position, el[1].color = 0.55, (0.12, 0.1, 0.28, 1)         # 上空：藍色
    mid = el.new(0.12); mid.color = (0.95, 0.55, 0.42, 1)
    nt.links.new(co.outputs["Generated"], sep.inputs[0])
    mp = nt.nodes.new("ShaderNodeMapRange"); mp.inputs["From Min"].default_value = 0.5; mp.inputs["From Max"].default_value = 1.0
    nt.links.new(sep.outputs["Z"], mp.inputs["Value"]); nt.links.new(mp.outputs["Result"], ramp.inputs["Fac"])
    bg = nt.nodes["Background"]; bg.inputs["Strength"].default_value = 2.5
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    # 窓の外：校庭と遠くの街並み（逆光のシルエット）
    town = mat("town", (0.18, 0.15, 0.2), 0.9); leaf = mat("leaf", (0.06, 0.09, 0.05), 0.9, noise=(8.0, 0.4)); grd = mat("ground", (0.35, 0.28, 0.2), 0.95)
    box("yard", (-60, 0, -4.2), (110, 240, 0.2), grd)
    rnd = random.Random(7)
    for k in range(60):
        hgt = rnd.uniform(3, 18) if rnd.random() < 0.8 else rnd.uniform(18, 35)
        box("bld%d" % k, (rnd.uniform(-170, -90), rnd.uniform(-120, 120), -4 + hgt / 2), (rnd.uniform(5, 14), rnd.uniform(5, 14), hgt * 0.8), town)
    for k in range(14):                                   # 校庭の木
        x, y = rnd.uniform(-45, -25), rnd.uniform(-30, 30)
        cyl("trunk", (x, y, -2.8), 0.2, 2.6, town, verts=8)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rnd.uniform(1.2, 1.9), location=(x, y, -1.4)); t_ = bpy.context.object
        t_.data.materials.append(leaf)
    # dusty air → god rays
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, H / 2)); v = bpy.context.object; v.name = "air"
    v.scale = (W / 2 - 0.02, D / 2 - 0.02, H / 2 - 0.02)
    vm = bpy.data.materials.new("air"); vm.use_nodes = True; nt = vm.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Density"].default_value = haze; pv.inputs["Anisotropy"].default_value = 0.6
    nt.links.new(pv.outputs[0], o.inputs["Volume"]); v.data.materials.append(vm)
    # soft bounce fill inside the room
    fl = bpy.data.lights.new("fill", "AREA"); fl.energy = 10; fl.size = 4; fl.color = (1.0, 0.8, 0.65)
    fo = bpy.data.objects.new("fill", fl); bpy.context.collection.objects.link(fo); fo.location = (1.5, -1, H - 0.2)
    return dict(W=W, D=D, H=H, M=M, sun=so)

def desk(xy, M, rot=0.0):
    x, y = xy
    e = bpy.data.objects.new("desk", None); bpy.context.collection.objects.link(e)
    e.location = (x, y, 0); e.rotation_euler = (0, 0, math.radians(rot))
    box("top", (0, 0, 0.72), (0.65, 0.45, 0.025), M["desk"], bevel=0.004, parent=e)
    box("shelf", (0, 0.02, 0.6), (0.6, 0.38, 0.12), M["steel"], parent=e)
    for sx in (-0.29, 0.29):
        for sy in (-0.19, 0.19):
            o = cyl("leg", (sx, sy, 0.36), 0.012, 0.72, M["steel"], verts=10); o.parent = e
    # chair
    c = bpy.data.objects.new("chair", None); bpy.context.collection.objects.link(c); c.parent = e
    c.location = (0, -0.45, 0)
    box("seat", (0, 0, 0.42), (0.4, 0.38, 0.02), M["desk"], bevel=0.004, parent=c)
    box("back", (0, -0.2, 0.72), (0.38, 0.02, 0.22), M["desk"], bevel=0.004, parent=c)
    for sx in (-0.18, 0.18):
        for sy in (-0.17, 0.17):
            o = cyl("cleg", (sx, sy, 0.21), 0.01, 0.42, M["steel"], verts=8); o.parent = c
        o = cyl("cback", (sx, -0.19, 0.6), 0.01, 0.4, M["steel"], verts=8); o.parent = c
    return e

# ---------------------------------------------------------------- people (skin-modifier skeleton → smooth body)
def person(name, loc, height=1.7, female=False, shirt=(0.9, 0.9, 0.88), bottom=(0.06, 0.07, 0.12), hair=(0.03, 0.025, 0.02),
           skin=(0.8, 0.6, 0.48), long_hair=False, rot=0.0):
    s = height / 1.7
    J = {  # joint name: (x, y, z, radius)
        "pelvis": (0, 0, 0.95, 0.15), "spine": (0, 0, 1.15, 0.14), "chest": (0, 0, 1.33, 0.16), "neck": (0, 0, 1.5, 0.055),
        "head": (0, 0, 1.6, 0.1), "crown": (0, 0, 1.68, 0.09),
        "shL": (0.19, 0, 1.43, 0.06), "elL": (0.23, 0.02, 1.17, 0.045), "haL": (0.25, 0.04, 0.93, 0.04),
        "shR": (-0.19, 0, 1.43, 0.06), "elR": (-0.23, 0.02, 1.17, 0.045), "haR": (-0.25, 0.04, 0.93, 0.04),
        "hipL": (0.09, 0, 0.9, 0.08), "knL": (0.1, 0.01, 0.5, 0.06), "anL": (0.1, 0, 0.08, 0.045), "toL": (0.1, 0.12, 0.03, 0.04),
        "hipR": (-0.09, 0, 0.9, 0.08), "knR": (-0.1, 0.01, 0.5, 0.06), "anR": (-0.1, 0, 0.08, 0.045), "toR": (-0.1, 0.12, 0.03, 0.04),
    }
    if female:
        J["pelvis"] = (0, 0, 0.95, 0.16); J["chest"] = (0, 0, 1.33, 0.145); J["neck"] = (0, 0, 1.5, 0.045)
    E = [("pelvis", "spine"), ("spine", "chest"), ("chest", "neck"), ("neck", "head"), ("head", "crown"),
         ("chest", "shL"), ("shL", "elL"), ("elL", "haL"), ("chest", "shR"), ("shR", "elR"), ("elR", "haR"),
         ("pelvis", "hipL"), ("hipL", "knL"), ("knL", "anL"), ("anL", "toL"),
         ("pelvis", "hipR"), ("hipR", "knR"), ("knR", "anR"), ("anR", "toR")]
    names = list(J)
    me = bpy.data.meshes.new(name)
    me.from_pydata([(J[k][0] * s, J[k][1] * s, J[k][2] * s) for k in names], [(names.index(a), names.index(b)) for a, b in E], [])
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    sk = o.modifiers.new("skin", "SKIN")
    for i, k in enumerate(names):
        r = J[k][3] * s
        me.skin_vertices[0].data[i].radius = (r, r * (0.85 if k in ("chest", "spine", "pelvis") else 1.0))
    me.skin_vertices[0].data[0].use_root = True
    o.modifiers.new("sub", "SUBSURF").levels = 2; o.modifiers["sub"].render_levels = 2
    bpy.context.view_layer.objects.active = o; bpy.ops.object.shade_smooth()
    # clothes by height bands (vertex-height material split is complex; use separate shells)
    o.data.materials.append(mat(name + "_shirt", shirt, 0.8, sss=0.05))
    head = bpy.data.objects.new(name + "_headgrp", None); bpy.context.collection.objects.link(head); head.parent = o
    sm = mat(name + "_skin", skin, 0.5, sss=0.3)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.105 * s, location=(0, 0.005 * s, 1.62 * s)); hd = bpy.context.object
    hd.scale = (0.92, 1.0, 1.18); hd.data.materials.append(sm); bpy.ops.object.shade_smooth(); hd.parent = o
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.108 * s, location=(0, -0.01 * s, 1.655 * s)); hr = bpy.context.object
    hr.scale = (0.97, 1.02, 1.08); hm = hair_mat(name, hair); hr.data.materials.append(hm); bpy.ops.object.shade_smooth(); hr.parent = o
    strands(hr, s, 0.012)                                  # 毛束の凹凸
    # 前髪（顔の上半分にかかる）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11 * s, location=(0, 0.02 * s, 1.675 * s)); fr = bpy.context.object
    fr.scale = (0.98, 1.0, 0.62); fr.data.materials.append(hm); bpy.ops.object.shade_smooth(); fr.parent = o
    strands(fr, s, 0.01)
    for side in (-1, 1):                                  # hands
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04 * s, location=(0.25 * side * s, 0.04 * s, 0.9 * s)); h = bpy.context.object
        h.scale = (0.7, 1.0, 1.3); h.data.materials.append(sm); bpy.ops.object.shade_smooth(); h.parent = o
    lower = bpy.data.objects.new(name + "_low", None)
    # trousers / skirt shell
    if female:
        bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.3 * s, radius2=0.16 * s, depth=0.42 * s, location=(0, 0, 0.8 * s))
        sk_ = bpy.context.object; sk_.data.materials.append(mat(name + "_skirt", bottom, 0.85)); sk_.parent = o
        bpy.ops.object.shade_smooth()
    else:
        for side in (-1, 1):
            c = cyl(name + "_leg", (0.1 * side * s, 0.005 * s, 0.5 * s), 0.07 * s, 0.86 * s, mat(name + "_pants", bottom, 0.8))
            c.parent = o
    if long_hair:                                          # 背中まで流れる黒髪
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(0, -0.045 * s, 1.47 * s)); lh = bpy.context.object
        lh.scale = (0.125 * s, 0.07 * s, 0.25 * s)
        bpy.ops.object.transform_apply(scale=True)
        for v in lh.data.vertices:                         # 下に行くほど薄く広がる
            t = max(0.0, (1.47 * s - (v.co.z + 1.47 * s)) / (0.25 * s)) if False else max(0.0, -v.co.z / (0.25 * s))
            v.co.x *= 1.0 + 0.25 * t; v.co.y *= 1.0 - 0.45 * t
        lh.data.materials.append(hm); bpy.ops.object.shade_smooth(); lh.parent = o
        strands(lh, s, 0.014)
    o.location = loc; o.rotation_euler = (0, 0, math.radians(rot))
    return o

def hair_mat(name, col):
    m = mat(name + "_hair", col, 0.32, spec=0.6, sss=0.0)          # 艶のある黒髪（縁が夕日で光る）
    b = m.node_tree.nodes["Principled BSDF"]
    try:
        b.inputs["Anisotropic"].default_value = 0.8; b.inputs["Sheen Weight"].default_value = 0.4
        b.inputs["Sheen Tint"].default_value = (1.0, 0.7, 0.5, 1)
    except Exception: pass
    return m

def strands(ob, s, depth):
    """縦に伸ばしたノイズで押し出し、毛束っぽい筋を作る"""
    sub = ob.modifiers.new("sub", "SUBSURF"); sub.levels = 2; sub.render_levels = 3
    tx = bpy.data.textures.new(ob.name + "_str", "STUCCI"); tx.noise_scale = 0.012 * s; tx.turbulence = 3.0
    d = ob.modifiers.new("str", "DISPLACE"); d.texture = tx; d.strength = depth * s; d.mid_level = 0.5
    em = bpy.data.objects.new(ob.name + "_tc", None); bpy.context.collection.objects.link(em); em.scale = (1, 1, 14)
    d.texture_coords = "OBJECT"; d.texture_coords_object = em

def add_hair(scalp, m, long_hair, s):
    """パーティクルの髪（逆光で毛先が光る＝リアルさの決め手）"""
    ps = scalp.modifiers.new("hair", "PARTICLE_SYSTEM").particle_system.settings
    ps.type = "HAIR"; ps.count = 1800; ps.hair_length = (0.42 if long_hair else 0.09) * s
    ps.use_advanced_hair = False; ps.emit_from = "FACE"
    ps.child_type = "INTERPOLATED"; ps.rendered_child_count = 40; ps.child_percent = 20
    ps.clump_factor = 0.4; ps.roughness_1 = 0.004; ps.roughness_endpoint = 0.01
    ps.root_radius = 0.6; ps.tip_radius = 0.2; ps.radius_scale = 0.008 * s
    ps.effector_weights.gravity = 1.0
    ps.normal_factor = 0.15 if long_hair else 0.3
    ps.factor_random = 0.02
    ps.object_align_factor[2] = -0.25 if long_hair else -0.05     # 下へ流す
    ps.material_slot = m.name
    scalp.data.materials.append(m)
    # 顔側（+y の下半分）には生やさない
    vg = scalp.vertex_groups.new(name="scalp")
    for v in scalp.data.vertices:
        if not (v.co.y > 0.02 * s and v.co.z < 0.02 * s): vg.add([v.index], 1.0, "REPLACE")
    scalp.particle_systems[0].vertex_group_density = "scalp"

# ---------------------------------------------------------------- camera
def camera(loc, look, lens=35, fstop=2.0, focus=None):
    cd = bpy.data.cameras.new("cam"); cd.lens = lens; cd.sensor_width = 24
    c = bpy.data.objects.new("cam", cd); bpy.context.collection.objects.link(c); bpy.context.scene.camera = c
    c.location = loc; aim(c, look)
    cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop
    cd.dof.focus_distance = focus if focus else (Vector(look) - Vector(loc)).length
    return c

def aim(o, target):
    d = Vector(target) - o.location
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

def handheld(c, f, amp=0.006, rot_amp=0.004, seed=0):
    """一人称の手持ちの揺れ（ゆっくりしたノイズ）"""
    r = lambda k, sp: (math.sin(f * sp + k * 1.7 + seed) + 0.5 * math.sin(f * sp * 2.3 + k * 4.1 + seed)) / 1.5
    return (amp * r(1, 0.07), amp * r(2, 0.05), amp * 0.6 * r(3, 0.06)), (rot_amp * r(4, 0.06), rot_amp * 0.6 * r(5, 0.045), rot_amp * r(6, 0.05))
