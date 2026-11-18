"""
s3_toon.py ― 『恋は心理学で落とせる？』のアニメ調キャラクター（トゥーン陰影＋輪郭線＋顔デカール）
背景は s2_world の教室（Cycles の写実寄り）を使い、人物だけセル調にする（アニメ映画の「描き込んだ背景＋セルの人物」）。
"""
import math, os, random
import bpy
from mathutils import Vector
import s2_world as W

HERE = os.path.dirname(os.path.abspath(__file__))
ASSET = os.path.join(HERE, "s3_assets")

def chars_collection():
    c = bpy.data.collections.get("chars")
    if not c:
        c = bpy.data.collections.new("chars"); bpy.context.scene.collection.children.link(c)
    return c

def decals_collection():
    c = bpy.data.collections.get("decals")
    if not c:
        c = bpy.data.collections.new("decals"); bpy.context.scene.collection.children.link(c)
    return c

def link(o, col=None):
    for col in list(o.users_collection):
        col.objects.unlink(o)
    (col or chars_collection()).objects.link(o)
    return o

def lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

def toon(name, base, shade=None, rim=0.0):
    """光の当たり方を2段のベタ塗りにする（色は画面で見える sRGB で指定。影色は自動でやや暗く青寄りに）"""
    if shade is None:
        shade = (base[0] * 0.78, base[1] * 0.74, base[2] * 0.86)
    base, shade = lin(base), lin(shade)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    df = nt.nodes.new("ShaderNodeBsdfDiffuse")
    s2r = nt.nodes.new("ShaderNodeShaderToRGB")
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.0, shade + (1,)
    el[1].position, el[1].color = 0.3, base + (1,)
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(df.outputs[0], s2r.inputs[0]); nt.links.new(s2r.outputs[0], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m

def decal_mat(name, path):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(path); tex.extension = "CLIP"
    em = nt.nodes.new("ShaderNodeEmission"); tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tex.outputs["Color"], em.inputs[0]); nt.links.new(tex.outputs["Alpha"], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs["Surface"])
    m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
    return m, tex

def sph(name, loc, r, scale, m, parent, seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(m)
    bpy.ops.object.shade_smooth(); o.parent = parent; link(o); return o

def cone(name, loc, r1, r2, depth, rot, m, parent, verts=16):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.data.materials.append(m); bpy.ops.object.shade_smooth()
    o.parent = parent; link(o); return o

def skin_body(name, J, E, mats, parent):
    names = list(J)
    me = bpy.data.meshes.new(name)
    me.from_pydata([J[k][:3] for k in names], [(names.index(a), names.index(b)) for a, b in E], [])
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    o.modifiers.new("skin", "SKIN")
    for i, k in enumerate(names):
        r = J[k][3]; me.skin_vertices[0].data[i].radius = (r, r * 0.85 if k in ("chest", "spine", "pelvis") else r)
    me.skin_vertices[0].data[0].use_root = True
    sub = o.modifiers.new("sub", "SUBSURF"); sub.levels = sub.render_levels = 2
    o.data.materials.append(mats); bpy.context.view_layer.objects.active = o; bpy.ops.object.shade_smooth()
    o.parent = parent; link(o); return o

def girl(name, loc, rot=0.0, hair=(0.16, 0.12, 0.18), face="mei", ponytail=True, expr="base", arm_pose="down"):
    """アニメ調の女子高生（身長およそ1.58m、頭はやや大きめ）。顔は face_<face>_<expr>.png を貼る"""
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root); link(root)
    skin = toon(name + "_skin", (1.0, 0.91, 0.86), (0.96, 0.78, 0.74))
    navy = toon(name + "_blazer", (0.2, 0.23, 0.4), (0.13, 0.14, 0.28))
    shirt = toon(name + "_shirt", (0.97, 0.97, 0.97), (0.78, 0.8, 0.9))
    skirt = toon(name + "_skirt", (0.24, 0.27, 0.42), (0.15, 0.17, 0.3))
    red = toon(name + "_ribbon", (0.9, 0.2, 0.26), (0.66, 0.12, 0.2))
    sock = toon(name + "_sock", (0.16, 0.16, 0.24), (0.1, 0.1, 0.16))
    shoe = toon(name + "_shoe", (0.35, 0.22, 0.15))
    hm = toon(name + "_hair", hair, tuple(c * 0.55 for c in hair))
    # 上半身（ブレザー）と腕
    ha = {"down": ((0.17, 0.02, 1.0), (0.2, 0.05, 0.8)), "chin": ((0.17, 0.18, 1.08), (0.06, 0.12, 1.27)),
          "wave": ((0.3, 0.06, 1.28), (0.42, 0.1, 1.45))}[arm_pose]
    J = {"pelvis": (0, 0, 0.86, 0.12), "spine": (0, 0, 1.0, 0.105), "chest": (0, 0, 1.15, 0.12), "neck": (0, 0, 1.3, 0.04),
         "shL": (0.15, 0, 1.24, 0.05), "elL": (0.17, 0.02, 1.02, 0.036), "haL": (0.19, 0.05, 0.82, 0.03),
         "shR": (-0.15, 0, 1.24, 0.05), "elR": (-ha[0][0], ha[0][1], ha[0][2], 0.036), "haR": (-ha[1][0], ha[1][1], ha[1][2], 0.03)}
    E = [("pelvis", "spine"), ("spine", "chest"), ("chest", "neck"), ("chest", "shL"), ("shL", "elL"), ("elL", "haL"),
         ("chest", "shR"), ("shR", "elR"), ("elR", "haR")]
    skin_body(name + "_body", J, E, navy, root)
    # 白いシャツの襟と赤いリボン
    cone(name + "_collar", (0, 0.06, 1.25), 0.06, 0.0, 0.1, (math.radians(-100), 0, 0), shirt, root, 3)
    cone(name + "_ribbonL", (0.022, 0.105, 1.21), 0.02, 0.0, 0.04, (0, math.radians(90), 0), red, root, 3)
    cone(name + "_ribbonR", (-0.022, 0.105, 1.21), 0.02, 0.0, 0.04, (0, math.radians(-90), 0), red, root, 3)
    for side in (-1, 1):                                                 # 手（腕の先）
        p = (0.19, 0.05, 0.8) if side > 0 else (-ha[1][0], ha[1][1], ha[1][2] - 0.02)
        sph(name + "_hand", p, 0.032, (0.8, 1, 1.2), skin, root, 16)
    # プリーツスカート（半径を波打たせる）
    bpy.ops.mesh.primitive_cone_add(vertices=96, radius1=0.25, radius2=0.13, depth=0.3, location=(0, 0, 0.74), end_fill_type="NOTHING")
    sk = bpy.context.object; sk.name = name + "_skirt"
    for v in sk.data.vertices:
        a = math.atan2(v.co.y, v.co.x); k = 1.0 + 0.06 * abs(math.sin(a * 12)) * (0.5 - v.co.z / 0.3)
        v.co.x *= k; v.co.y *= k
    sk.modifiers.new("sol", "SOLIDIFY").thickness = 0.008
    sk.data.materials.append(skirt); sk.parent = root; link(sk)
    # 脚・紺ソックス・ローファー
    for side in (-1, 1):
        x = 0.07 * side
        W.cyl(name + "_leg", (x, 0, 0.5), 0.05, 0.56, skin).parent = root
        W.cyl(name + "_sock", (x, 0, 0.27), 0.054, 0.38, sock).parent = root
        sh = W.box(name + "_shoe", (x, 0.035, 0.03), (0.08, 0.2, 0.06), shoe, bevel=0.02); sh.parent = root
    for o in list(root.children):
        if o.users_collection[0] not in (chars_collection(), decals_collection()): link(o)
    # 頭（あごを少しとがらせる）
    hc = (0, 0.0, 1.44)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.125, location=hc); hd = bpy.context.object
    hd.name = name + "_head"
    for v in hd.data.vertices:
        if v.co.z < 0:
            t = -v.co.z / 0.125
            v.co.x *= 1 - 0.32 * t * t; v.co.y *= 1 - 0.12 * t * t
            if v.co.y > 0: v.co.z -= 0.012 * t
    hd.scale = (0.92, 0.95, 1.0); hd.data.materials.append(skin); bpy.ops.object.shade_smooth(); hd.parent = root; link(hd)
    W.cyl(name + "_neck", (0, 0, 1.31), 0.026, 0.1, skin).parent = root
    # 顔デカール（顔の前の曲面に貼る）
    bpy.ops.mesh.primitive_plane_add(size=1, location=(hc[0], hc[1] + 0.14, hc[2] - 0.005), rotation=(math.radians(90), 0, 0))
    fp = bpy.context.object; fp.name = name + "_face"; fp.scale = (0.205, 0.154, 1)
    bpy.ops.object.transform_apply(scale=True, location=False, rotation=False)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.subdivide(number_cuts=16); bpy.ops.object.mode_set(mode="OBJECT")
    sw = fp.modifiers.new("wrap", "SHRINKWRAP"); sw.target = hd; sw.wrap_method = "PROJECT"; sw.use_negative_direction = True
    sw.use_project_y = True; sw.offset = 0.0015
    fm, tex = decal_mat(name + "_facemat", os.path.join(ASSET, "face_%s_%s.png" % (face, expr)))
    fp.data.materials.append(fm); fp.parent = root; link(fp, decals_collection())
    fp.visible_shadow = False
    # 髪：後頭部の帽子、前髪の束、横の髪、ポニーテール
    cap = sph(name + "_hair", (0, -0.03, hc[2] + 0.02), 0.134, (0.97, 0.97, 1.0), hm, root)
    for k in range(7):                                                # 前髪
        a = math.radians(-48 + k * 16); x = math.sin(a) * 0.1; y = 0.1 * math.cos(a) * 0.95
        cone(name + "_bang", (x * 0.92, y + 0.012, hc[2] + 0.028), 0.03, 0.004, 0.12,
             (math.radians(180 - 18), math.radians(-a * 0.5 / 1.0 * 57.3 / 57.3) * 0.5, -a * 0.3), hm, root, 10)
    for side in (-1, 1):                                              # もみあげの長い髪
        cone(name + "_side", (0.105 * side, 0.03, hc[2] - 0.07), 0.028, 0.004, 0.2, (math.radians(185), math.radians(-6 * side), 0), hm, root, 10)
    if ponytail:
        sph(name + "_tie", (0, -0.12, hc[2] + 0.06), 0.03, (1, 1, 1), red, root, 16)
        pt = cone(name + "_tail", (0, -0.17, hc[2] - 0.08), 0.07, 0.01, 0.34, (math.radians(155), 0, 0), hm, root, 20)
        bend = pt.modifiers.new("bend", "SIMPLE_DEFORM"); bend.deform_method = "BEND"; bend.angle = math.radians(35); bend.deform_axis = "X"
    root.location = loc; root.rotation_euler = (0, 0, math.radians(rot))
    return root, tex

def boy(name, loc, rot=0.0, hair=(0.5, 0.34, 0.24), face="yota", expr="base"):
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root); link(root)
    skin = toon(name + "_skin", (1.0, 0.9, 0.83), (0.95, 0.76, 0.7))
    navy = toon(name + "_blazer", (0.2, 0.23, 0.4), (0.13, 0.14, 0.28))
    pants = toon(name + "_pants", (0.28, 0.29, 0.36))
    shirt = toon(name + "_shirt", (0.97, 0.97, 0.97), (0.78, 0.8, 0.9))
    hm = toon(name + "_hair", hair, tuple(c * 0.55 for c in hair))
    J = {"pelvis": (0, 0, 0.92, 0.13), "spine": (0, 0, 1.08, 0.12), "chest": (0, 0, 1.25, 0.14), "neck": (0, 0, 1.42, 0.045),
         "shL": (0.18, 0, 1.36, 0.055), "elL": (0.2, 0.02, 1.11, 0.04), "haL": (0.22, 0.05, 0.88, 0.033),
         "shR": (-0.18, 0, 1.36, 0.055), "elR": (-0.2, 0.02, 1.11, 0.04), "haR": (-0.22, 0.05, 0.88, 0.033),
         "hipL": (0.08, 0, 0.86, 0.075), "knL": (0.09, 0.01, 0.48, 0.06), "anL": (0.09, 0, 0.08, 0.05),
         "hipR": (-0.08, 0, 0.86, 0.075), "knR": (-0.09, 0.01, 0.48, 0.06), "anR": (-0.09, 0, 0.08, 0.05)}
    E = [("pelvis", "spine"), ("spine", "chest"), ("chest", "neck"), ("chest", "shL"), ("shL", "elL"), ("elL", "haL"),
         ("chest", "shR"), ("shR", "elR"), ("elR", "haR"), ("pelvis", "hipL"), ("hipL", "knL"), ("knL", "anL"),
         ("pelvis", "hipR"), ("hipR", "knR"), ("knR", "anR")]
    b = skin_body(name + "_body", J, E, navy, root)
    for side in (-1, 1):
        W.cyl(name + "_legs", (0.085 * side, 0, 0.47), 0.068, 0.86, pants).parent = root
        sph(name + "_hand", (0.22 * side, 0.05, 0.86), 0.036, (0.8, 1, 1.2), skin, root, 16)
        W.box(name + "_shoe", (0.09 * side, 0.04, 0.035), (0.1, 0.24, 0.07), toon(name + "_shoe", (0.2, 0.16, 0.14)), bevel=0.02).parent = root
    cone(name + "_collar", (0, 0.07, 1.37), 0.065, 0.0, 0.11, (math.radians(-100), 0, 0), shirt, root, 3)
    for o in list(root.children):
        if o.users_collection[0] not in (chars_collection(), decals_collection()): link(o)
    hc = (0, 0, 1.57)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.125, location=hc); hd = bpy.context.object
    hd.name = name + "_head"
    for v in hd.data.vertices:
        if v.co.z < 0:
            t = -v.co.z / 0.125; v.co.x *= 1 - 0.25 * t * t; v.co.y *= 1 - 0.1 * t * t
    hd.scale = (0.94, 0.97, 1.02); hd.data.materials.append(skin); bpy.ops.object.shade_smooth(); hd.parent = root; link(hd)
    W.cyl(name + "_neck", (0, 0, 1.44), 0.034, 0.1, skin).parent = root
    bpy.ops.mesh.primitive_plane_add(size=1, location=(hc[0], hc[1] + 0.14, hc[2] - 0.005), rotation=(math.radians(90), 0, 0))
    fp = bpy.context.object; fp.name = name + "_face"; fp.scale = (0.205, 0.154, 1)
    bpy.ops.object.transform_apply(scale=True, location=False, rotation=False)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.subdivide(number_cuts=16); bpy.ops.object.mode_set(mode="OBJECT")
    sw = fp.modifiers.new("wrap", "SHRINKWRAP"); sw.target = hd; sw.wrap_method = "PROJECT"; sw.use_negative_direction = True
    sw.use_project_y = True; sw.offset = 0.0015
    fm, tex = decal_mat(name + "_facemat", os.path.join(ASSET, "face_%s_%s.png" % (face, expr)))
    fp.data.materials.append(fm); fp.parent = root; link(fp, decals_collection()); fp.visible_shadow = False
    cap = sph(name + "_hair", (0, -0.03, hc[2] + 0.02), 0.136, (0.98, 0.97, 0.99), hm, root)
    rnd = random.Random(5)
    for k in range(18):                                               # ぼさっとした毛束
        a = rnd.uniform(0, 2 * math.pi); el = rnd.uniform(0.2, 1.2)
        d = Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)))
        if d.y > 0.5 and d.z < 0.5: continue
        p = Vector(hc) + d * 0.13
        o = cone(name + "_tuft", tuple(p), 0.035, 0.003, 0.065, (0, 0, 0), hm, root, 8)
        o.rotation_euler = (d + Vector((0, 0, -0.6))).to_track_quat("Z", "Y").to_euler()
    for k in range(7):                                                # 目にかかる前髪
        a = math.radians(-54 + k * 18); x = math.sin(a) * 0.1; y = 0.1 * math.cos(a) * 0.95
        cone(name + "_bang", (x, y + 0.015, hc[2] + 0.04), 0.03, 0.004, 0.14, (math.radians(165), 0, -a * 0.3), hm, root, 10)
    root.location = loc; root.rotation_euler = (0, 0, math.radians(rot))
    return root, tex

def outlines(thickness=2.2):
    sc = bpy.context.scene; sc.render.use_freestyle = True; sc.render.line_thickness_mode = "ABSOLUTE"
    sc.render.line_thickness = thickness
    vl = sc.view_layers[0]; fs = vl.freestyle_settings
    ls = fs.linesets[0] if fs.linesets else fs.linesets.new("chars")
    ls.select_by_collection = True; ls.collection = chars_collection()
    ls.select_by_visibility = True; ls.select_silhouette = True; ls.select_border = True; ls.select_crease = False
    if ls.linestyle is None:
        ls.linestyle = bpy.data.linestyles.new("ink")
    ls.linestyle.color = (0.1, 0.05, 0.06); ls.linestyle.thickness = thickness

def set_expr(tex, who, expr):
    tex.image = bpy.data.images.load(os.path.join(ASSET, "face_%s_%s.png" % (who, expr)), check_existing=True)
