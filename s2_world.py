"""
s2_world.py ― 新シリーズ『君は写真に写らない』の共通部品（夕方の教室・人物・カメラ）
  リアル寄り：物理ベースの光、ボリューム（光の筋）、被写界深度、手持ちカメラの揺れ。
"""
import math, random
import bpy
from mathutils import Vector

def reset(samples=64, res=(720, 1280), seed=17):
    random.seed(seed)                                         # 机の配置などを毎回同じにする（途中再開でも絵が飛ばない）
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
def classroom(sun_elev=14.0, sun_az=-35.0, sun_col=(1.0, 0.55, 0.28), haze=0.006,
              sky=((1.0, 0.42, 0.16), (0.95, 0.55, 0.42), (0.12, 0.1, 0.28)), sky_str=2.5, sun_str=14.0, fill=10):
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
    sun.energy = sun_str
    w = bpy.data.worlds.new("w"); bpy.context.scene.world = w; w.use_nodes = True
    nt = w.node_tree
    co = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.0, sky[0] + (1,)                 # 地平線
    el[1].position, el[1].color = 0.55, sky[2] + (1,)                # 上空
    mid = el.new(0.12); mid.color = sky[1] + (1,)
    nt.links.new(co.outputs["Generated"], sep.inputs[0])
    mp = nt.nodes.new("ShaderNodeMapRange"); mp.inputs["From Min"].default_value = 0.5; mp.inputs["From Max"].default_value = 1.0
    nt.links.new(sep.outputs["Z"], mp.inputs["Value"]); nt.links.new(mp.outputs["Result"], ramp.inputs["Fac"])
    bg = nt.nodes["Background"]; bg.inputs["Strength"].default_value = sky_str
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
    fl = bpy.data.lights.new("fill", "AREA"); fl.energy = fill; fl.size = 4; fl.color = (1.0, 0.8, 0.65)
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
    # 後頭部〜えり足（後ろ姿で地肌が見えないように）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.104 * s, location=(0, -0.022 * s, 1.6 * s)); np = bpy.context.object
    np.scale = (0.97, 0.92, 1.08); np.data.materials.append(hm); bpy.ops.object.shade_smooth(); np.parent = o
    strands(np, s, 0.01)
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

# ---------------------------------------------------------------- 机の上の白い花瓶（亡くなった生徒の席の印）
def vase(loc, seed=3):
    rnd = random.Random(seed)
    cer = mat("vase", (0.9, 0.9, 0.88), 0.15, spec=0.6)
    prof = [(0.0, 0.0), (0.035, 0.0), (0.045, 0.02), (0.055, 0.06), (0.056, 0.09), (0.048, 0.13), (0.03, 0.17),
            (0.022, 0.2), (0.024, 0.215), (0.03, 0.225), (0.026, 0.228), (0.019, 0.215), (0.017, 0.12)]   # 外側→口→内側
    N = 40; vs = []; fs = []
    for r, z in prof:
        for i in range(N):
            a = i / N * 2 * math.pi; vs.append((r * math.cos(a), r * math.sin(a), z))
    for j in range(len(prof) - 1):
        for i in range(N):
            a, b = j * N + i, j * N + (i + 1) % N
            fs.append((a, b, b + N, a + N))
    me = bpy.data.meshes.new("vase"); me.from_pydata(vs, [], fs)
    v = bpy.data.objects.new("vase", me); bpy.context.collection.objects.link(v); v.location = loc
    bpy.context.view_layer.objects.active = v; v.select_set(True)
    v.modifiers.new("sub", "SUBSURF").levels = 1
    v.data.materials.append(cer); bpy.ops.object.shade_smooth()
    stem = mat("stem", (0.12, 0.25, 0.08), 0.6); petal = mat("petal", (0.95, 0.95, 0.92), 0.5, sss=0.4)
    leafm = mat("vleaf", (0.1, 0.22, 0.06), 0.5)
    top = loc[2] + 0.2
    for k in range(7):
        a = k / 7 * 2 * math.pi + rnd.uniform(-0.3, 0.3); tilt = rnd.uniform(0.2, 0.5); h = rnd.uniform(0.12, 0.22)
        hx, hy, hz = loc[0] + math.cos(a) * math.sin(tilt) * h, loc[1] + math.sin(a) * math.sin(tilt) * h, top + math.cos(tilt) * h
        c = cyl("stem", ((loc[0] + hx) / 2, (loc[1] + hy) / 2, (top - 0.05 + hz) / 2), 0.0035, h + 0.05, stem, verts=6)
        from mathutils import Vector
        c.rotation_euler = Vector((hx - loc[0], hy - loc[1], hz - top + 0.05)).to_track_quat('Z', 'Y').to_euler()
        for ring, (rr_, nn, up) in enumerate(((0.02, 16, 0.0), (0.014, 12, 0.006), (0.008, 8, 0.011))):   # 白い菊：細い花びらを三重に
            for j in range(nn):
                b = j / nn * 2 * math.pi + ring * 0.2
                bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=rr_,
                                                     location=(hx + math.cos(b) * rr_, hy + math.sin(b) * rr_, hz + up))
                pe = bpy.context.object; pe.scale = (1.0, 0.22, 0.18); pe.rotation_euler = (0, -0.35 - ring * 0.35, b)
                pe.data.materials.append(petal)
        if k % 2 == 0:
            bpy.ops.mesh.primitive_plane_add(size=0.06, location=(hx * 0.4 + loc[0] * 0.6, hy * 0.4 + loc[1] * 0.6, top + 0.06))
            lf = bpy.context.object; lf.scale = (1.0, 0.35, 1); lf.rotation_euler = (rnd.uniform(-0.6, 0.6), 0.3, a); lf.data.materials.append(leafm)
    return v

MORNING = dict(sun_elev=32.0, sun_az=25.0, sun_col=(1.0, 0.93, 0.84), haze=0.004,
               sky=((0.92, 0.95, 1.0), (0.75, 0.84, 0.97), (0.28, 0.48, 0.85)), sky_str=1.6, sun_str=9.0, fill=12)

# ---------------------------------------------------------------- 旧校舎の階段と踊り場（夕方。踊り場の大きな窓から西日）
def sky_world(sky, strength):
    w = bpy.data.worlds.new("w"); bpy.context.scene.world = w; w.use_nodes = True
    nt = w.node_tree
    co = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.0, sky[0] + (1,)
    el[1].position, el[1].color = 0.55, sky[2] + (1,)
    mid = el.new(0.12); mid.color = sky[1] + (1,)
    nt.links.new(co.outputs["Generated"], sep.inputs[0])
    mp = nt.nodes.new("ShaderNodeMapRange"); mp.inputs["From Min"].default_value = 0.5; mp.inputs["From Max"].default_value = 1.0
    nt.links.new(sep.outputs["Z"], mp.inputs["Value"]); nt.links.new(mp.outputs["Result"], ramp.inputs["Fac"])
    bg = nt.nodes["Background"]; bg.inputs["Strength"].default_value = strength
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])

def stairwell(haze=0.012, sun_elev=9.0, sun_str=16.0, night=False):
    """U字階段。1階の床 z=0、踊り場 z=1.8（y=3.4〜5.0）、踊り場の奥の壁 y=5.0 に大きな窓。
    上り1本目は x=0.1〜1.6 を +y へ、2本目は x=-1.6〜-0.1 を -y へ上る。"""
    M = dict(
        wall=mat("swall", (0.72, 0.72, 0.66), 0.85, noise=(5.0, 0.12)),
        dado=mat("dado", (0.32, 0.4, 0.36), 0.6, noise=(9.0, 0.15)),              # 古い校舎の腰壁（くすんだ緑）
        step=mat("step", (0.42, 0.4, 0.37), 0.55, noise=(14.0, 0.3)),             # 人造石の段
        nose=mat("nose", (0.25, 0.25, 0.24), 0.4, 0.6),
        rail=mat("rail", (0.3, 0.2, 0.12), 0.35),
        frame=mat("sframe", (0.5, 0.52, 0.5), 0.4, 0.7),
        ceil=mat("sceil", (0.8, 0.8, 0.77), 0.9),
        glass=glass())
    X0, X1, Y0, Y1, H = -1.7, 1.7, -1.2, 5.0, 5.4
    box("floor", (0, (Y0 + Y1) / 2 - 1, -0.05), (X1 - X0, Y1 - Y0 + 2, 0.1), M["step"])
    box("ceil", (0, (Y0 + Y1) / 2, H), (X1 - X0, Y1 - Y0, 0.1), M["ceil"])
    for sx in (X0 - 0.05, X1 + 0.05):
        box("wall", (sx, (Y0 + Y1) / 2, H / 2), (0.1, Y1 - Y0 + 2, H), M["wall"])
        box("dado", (sx + (0.06 if sx < 0 else -0.06), (Y0 + Y1) / 2, 0.55), (0.02, Y1 - Y0 + 2, 1.1), M["dado"])
    # 踊り場の奥の壁と窓（大きな窓 2.0 x 1.9、下端 z=2.6）
    wy = Y1 + 0.05; wz0, wz1, wx = 2.6, 4.5, 1.0
    box("back_lo", (0, wy, wz0 / 2), (X1 - X0, 0.12, wz0), M["wall"])
    box("back_hi", (0, wy, (wz1 + H) / 2), (X1 - X0, 0.12, H - wz1), M["wall"])
    box("back_l", ((X0 - wx) / 2, wy, (wz0 + wz1) / 2), (-wx - X0, 0.12, wz1 - wz0), M["wall"])
    box("back_r", ((X1 + wx) / 2, wy, (wz0 + wz1) / 2), (X1 - wx, 0.12, wz1 - wz0), M["wall"])
    box("pane", (0, wy, (wz0 + wz1) / 2), (2 * wx, 0.02, wz1 - wz0), M["glass"])
    for x in (-wx, 0, wx):
        box("mull", (x, wy - 0.03, (wz0 + wz1) / 2), (0.05, 0.06, wz1 - wz0), M["frame"])
    for z in (wz0, (wz0 + wz1) / 2, wz1):
        box("tran", (0, wy - 0.03, z), (2 * wx, 0.06, 0.05), M["frame"])
    box("dado_b", (0, wy - 0.07, 1.8 + 0.55), (X1 - X0, 0.02, 1.1), M["dado"])
    # 踊り場
    box("landing", (0, 4.2, 1.8 - 0.1), (X1 - X0, 1.6, 0.2), M["step"])
    # 1本目（+y へ上る）・2本目（-y へ上る）
    n, rise, run = 11, 1.8 / 11, 0.28
    for k in range(n):
        y = 3.4 - (n - k) * run
        z = (k + 1) * rise
        box("st1_%d" % k, (0.85, y + run / 2, z / 2), (1.5, run, z), M["step"])
        box("ns1_%d" % k, (0.85, y + run - 0.01, z - 0.01), (1.5, 0.03, 0.03), M["nose"])
        z2 = 1.8 + (k + 1) * rise; y2 = 3.4 - (k + 1) * run
        box("st2_%d" % k, (-0.85, y2 + run / 2, z2 - rise / 2 - 0.1), (1.5, run, rise + 0.2), M["step"])
    box("st2_slab", (-0.85, 3.4 - n * run / 2, 1.8 + 0.9 - 0.35), (1.5, n * run, 0.12), M["step"],
        rot=(math.atan2(1.8, n * run), 0, 0))
    # 中央の腰壁と木の手すり
    box("mid_wall", (0, 3.4 - n * run / 2, 1.8), (0.16, n * run, 1.0), M["dado"],
        rot=(-math.atan2(1.8, n * run), 0, 0))
    r = cyl("rail1", (0.12, 3.4 - n * run / 2, 0.9 + 0.9), 0.03, math.hypot(n * run, 1.8) + 0.2, M["rail"], rot=(math.pi / 2 - math.atan2(1.8, n * run), 0, 0), verts=12)
    # 夕日（窓の外 +y 側から低く）
    sun = bpy.data.lights.new("sun", "SUN"); sun.energy = sun_str; sun.color = (1.0, 0.5, 0.24) if not night else (0.55, 0.68, 1.0)
    sun.angle = math.radians(0.6)
    so = bpy.data.objects.new("sun", sun); bpy.context.collection.objects.link(so)
    e = math.radians(sun_elev); so.location = (0, 20, 8); aim(so, (0.25, 20 - math.cos(e), 8 - math.sin(e) - 0.0))
    if night:
        sky_world(((0.05, 0.07, 0.14), (0.03, 0.045, 0.1), (0.005, 0.008, 0.02)), 0.5)
    else:
        sky_world(((1.0, 0.42, 0.16), (0.95, 0.55, 0.42), (0.12, 0.1, 0.28)), 0.9)
    # 窓の外の遠景（逆光の街）
    town = mat("town", (0.16, 0.13, 0.18), 0.9); rnd = random.Random(11)
    for k in range(30):
        hgt = rnd.uniform(3, 20)
        box("bld%d" % k, (rnd.uniform(-60, 60), rnd.uniform(70, 140), -6 + hgt / 2), (rnd.uniform(5, 14), rnd.uniform(5, 14), hgt), town)
    # ほこりの舞う空気
    bpy.ops.mesh.primitive_cube_add(location=(0, (Y0 + Y1) / 2, H / 2)); v = bpy.context.object; v.name = "air"
    v.scale = ((X1 - X0) / 2 - 0.02, (Y1 - Y0) / 2 - 0.02, H / 2 - 0.02)
    vm = bpy.data.materials.new("air"); vm.use_nodes = True; nt = vm.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Density"].default_value = haze; pv.inputs["Anisotropy"].default_value = 0.6
    nt.links.new(pv.outputs[0], o.inputs["Volume"]); v.data.materials.append(vm)
    fl = bpy.data.lights.new("fill", "AREA"); fl.energy = 3 if not night else 0.0; fl.size = 2; fl.color = (1.0, 0.75, 0.6)
    fo = bpy.data.objects.new("fill", fl); bpy.context.collection.objects.link(fo); fo.location = (0.8, -0.8, 3.2)
    return dict(M=M, landing_z=1.8, window=(0, wy, (wz0 + wz1) / 2))

def flashlight(cam, energy=40.0, spread=28.0):
    """カメラ（手）に付けた懐中電灯"""
    sp = bpy.data.lights.new("torch", "SPOT"); sp.energy = energy; sp.spot_size = math.radians(spread); sp.spot_blend = 0.6
    sp.color = (1.0, 0.92, 0.8); sp.shadow_soft_size = 0.02
    so = bpy.data.objects.new("torch", sp); bpy.context.collection.objects.link(so)
    so.parent = cam; so.location = (0.12, -0.15, 0.05); so.rotation_euler = (math.radians(-3), math.radians(4), 0)
    return so

def phone(loc, rot_z=0.0, glow=4.0):
    """床に落ちたスマホ（画面が光る）。画面の向きは +z"""
    body = mat("phone", (0.02, 0.02, 0.025), 0.25, 0.3)
    p = box("phone", (0, 0, 0.004), (0.075, 0.155, 0.008), body, bevel=0.003)      # box() は原点に焼き込むので原点で作って動かす
    scr = mat("screen", (0.0, 0.0, 0.0), 0.1, emit=(0.75, 0.82, 1.0), estr=glow)
    s_ = box("screen", (0, 0, 0.0085), (0.068, 0.146, 0.001), scr)
    for o in (p, s_):
        o.rotation_euler = (0, 0, math.radians(rot_z)); o.location = loc
    gl = bpy.data.lights.new("phoneglow", "POINT"); gl.energy = 0.6; gl.color = (0.7, 0.8, 1.0); gl.shadow_soft_size = 0.05
    go = bpy.data.objects.new("phoneglow", gl); bpy.context.collection.objects.link(go); go.location = (loc[0], loc[1], loc[2] + 0.06)
    return p
