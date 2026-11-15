"""
create_isekai_short.py
短編アニメ「もしもあなたが異世界に転生してデスゲームに参加すると…」の追加ショットを生成する。
create_battle.py（バトル本編 5秒）の部品（闘技場・敵リグ・一人称リグ・モーションヘルパー）を再利用。

ショット構成（24fps / 720x1280）
  A1  32f  転生前夜  : 夜の横断歩道、右からトラックのライトが迫り白飛び
  A2  64f  転生      : 白から紫へ変わる異空間をキューブと共に落下、魔法陣と「異世界転生」の文字
  B   96f  開幕      : 闘技場で目覚める→自分の手→剣が出現→空に「デスゲーム開始」→敵が空から着地（リール版は84fまで使用）
  C  264f  迷い      : 後ずさり→左右を見回す→振り返ると出口が封鎖→威嚇の雷で怯む→空に「戦わなければ死ぬ」
                       →震える手を見つめ、両手で握り直す→前へ踏み出し構える→敵が走り出す（バトル1f目に接続）
  (battle 120f)      : create_battle.py の映像
  D  120f  決着      : 敵が砕け散る→勝利→空に「第二回戦」と赤い敵の大群→暗転→タイトル

  python create_isekai_short.py --shot B --anim
  python create_isekai_short.py --shot D --frames 1,40,90 --res 40 --samples 10
"""
import os, sys, math, random
os.environ["BATTLE_AS_LIBRARY"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion
import create_battle as B

arg = B.arg
SHOT = arg("--shot", "B")
OUT_DIR = arg("--out", HERE)
FRAME_DIR = arg("--frame-dir", os.path.join(OUT_DIR, "frames_" + SHOT))
scene = B.scene
COL = B.COL
M = B.M
Track, EASE, lerp, clamp = B.Track, B.EASE, B.lerp, B.clamp
FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"

LENGTH = {"A1": 32, "A2": 64, "B": 96, "C": 264, "D": 120}[SHOT]
scene.frame_end = LENGTH
random.seed(23)

# ------------------------------------------------------------------ helpers
def text_obj(name, body, size, mat, loc=(0, 0, 0), parent=None, extrude=0.06):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    try:
        cu.font = bpy.data.fonts.load(FONT_PATH, check_existing=True)
    except Exception as ex:
        print("font load failed", ex)
    cu.size = size
    cu.extrude = extrude
    cu.bevel_depth = 0.0
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    ob = bpy.data.objects.new(name, cu)
    ob.data.materials.append(mat)
    COL.objects.link(ob)
    ob.parent = parent
    ob.location = loc
    return ob

def key_scale(ob, f, s):
    ob.scale = (s, s, s) if not isinstance(s, (tuple, list)) else s
    ob.keyframe_insert("scale", frame=f)

def fade_material(name, color=(0, 0, 0)):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = 1.0
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.name = "FADE"
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m

def key_fade(m, f, v):
    inp = m.node_tree.nodes["FADE"].inputs[0]
    inp.default_value = v
    inp.keyframe_insert("default_value", frame=f)

def cam_overlay(cam, name, mat, z=-0.05, size=(0.2, 0.2)):
    """plane glued in front of the lens (fades / flashes / eyelids)"""
    bm = bmesh.new()
    B.bm_box(bm, (size[0], size[1], 0.0005), (0, 0, 0))
    ob = B.mesh_obj(name, bm, mat, cam, (0, 0, z))
    ob.visible_shadow = False
    return ob

def key_enemy(J, f, pose, root_loc, rp, yaw, run_phase=None):
    """same rig logic as create_battle.animate (IK legs, run overlay)."""
    w = pose.get("run", 0.0)
    H = B.H
    key = B.key_loc
    root = J["root"]
    key(root, f, root_loc)
    B.key_rot(root, f, (rp, 0, yaw))
    ph = run_phase if run_phase is not None else 0.0
    yL, zL = B.foot_cycle(ph)
    yR, zR = B.foot_cycle(ph + 0.5)
    nL = yL / 0.456
    hz = pose["hz"] + w * (0.05 * math.cos(4 * math.pi * (ph - 0.05)))
    fRy, fRz = lerp(pose["fRy"], yR, w), lerp(pose["fRz"], zR, w)
    fLy, fLz = lerp(pose["fLy"], yL, w), lerp(pose["fLz"], zL, w)
    shRx = pose["shRx"] + w * (nL * 0.95)
    shLx = pose["shLx"] + w * (-nL * 0.95)
    tt = pose["tt"] + w * (0.16 * nL)
    key(J["hips"], f, (0, 0, H + hz))
    B.key_rot(J["torso"], f, (pose["tp"], pose["tl"], tt))
    B.key_rot(J["neck"], f, (pose["np"], 0, pose["nt"] - tt * 0.4))
    B.key_rot(J["shR"], f, (shRx, pose["shRy"], 0))
    B.key_rot(J["shL"], f, (shLx, pose["shLy"], 0))
    B.key_rot(J["elR"], f, (pose["elR"], 0, 0))
    B.key_rot(J["elL"], f, (pose["elL"], 0, 0))
    hipz = H + hz - 0.06
    for side, fy, fz in (("R", fRy, fRz), ("L", fLy, fLz)):
        hr, kr = B.leg_ik(fy, fz - hipz)
        B.key_rot(J["hip" + side], f, (hr, 0, 0))
        B.key_rot(J["kn" + side], f, (kr, 0, 0))
        B.key_rot(J["an" + side], f, (-(hr + kr) - rp * 0.7, 0, 0))

def key_player(P, f, cp, tgt, roll, rh, lh, prevq):
    cam = P["cam"]
    B.key_loc(cam, f, cp)
    B.key_quat(cam, f, B.look_quat(cp, tgt, roll), prevq)
    hloc = Vector(rh[:3])
    bdir = Vector(rh[3:]).normalized()
    B.key_loc(P["rh"], f, hloc)
    B.key_quat(P["rh"], f, bdir.to_track_quat('Y', 'Z'), prevq)
    B.key_loc(P["ra"], f, hloc)
    B.key_quat(P["ra"], f, (hloc - B.SHOULDER_R).normalized().to_track_quat('Y', 'Z'), prevq)
    l = Vector(lh)
    for k in ("lh", "la"):
        B.key_loc(P[k], f, l)
        B.key_quat(P[k], f, (l - B.SHOULDER_L).normalized().to_track_quat('Y', 'Z'), prevq)

def env_life(flames, floats, n):
    for ob, p, spd, ph in list(floats):
        if abs(p.x) < 13 and p.y > 24:
            ob.hide_render = True
            floats.remove((ob, p, spd, ph))
    for f in range(1, n + 1):
        for i, fl in enumerate(flames):
            rnd = random.Random(f * 31 + i)
            fl.scale = (1 + rnd.uniform(-0.12, 0.12), 1 + rnd.uniform(-0.12, 0.12), 1 + rnd.uniform(-0.25, 0.3))
            fl.keyframe_insert("scale", frame=f)
    for ob, p, spd, ph in floats:
        for f in (1, n):
            ob.location = p + Vector((0, 0, 0.4 * math.sin(ph + f * 0.03)))
            ob.keyframe_insert("location", frame=f)
            ob.rotation_euler.z += spd * (1 if f == n else 0) * n / 120
            ob.keyframe_insert("rotation_euler", frame=f)

def shake(f, start, amp, decay):
    if f < start:
        return Vector((0, 0, 0)), 0.0
    t = f - start
    a = amp * math.exp(-t / decay)
    return Vector((math.sin(t * 2.7) * a, 0, math.cos(t * 3.3) * a * 0.8)), math.sin(t * 2.1 + 1) * a * 0.6

def make_camera_only():
    for n in ("Sun", "RimLight", "FillLight"):
        bpy.data.objects.remove(bpy.data.objects[n])
    cd = bpy.data.cameras.new("FP_Cam")
    cd.lens, cd.sensor_fit, cd.sensor_height, cd.clip_start = 19, 'VERTICAL', 24, 0.02
    cam = bpy.data.objects.new("FP_Cam", cd)
    COL.objects.link(cam)
    scene.camera = cam
    cam.rotation_mode = 'QUATERNION'
    return cam

def dust_ring(prefix, f0, center, count, radius, seed, size=0.35, mat=None, init=True):
    r = random.Random(seed)
    for i in range(count):
        a = 2 * math.pi * i / count + r.uniform(-0.1, 0.1)
        d = Vector((math.cos(a), math.sin(a), 0))
        s0 = r.uniform(0.7, 1.0) * size
        ob = B.box("%s_%d" % (prefix, i), (1, 1, 1), (0, 0, 0), mat or M["dust"], bevel=0.08)
        ob.visible_shadow = False
        ob.rotation_euler = (r.random(), r.random(), r.random())
        if init:
            key_scale(ob, 1, 0.001)
        for f in range(f0 - 1, f0 + 18):
            t = clamp((f - f0) / 16)
            sc = 0.001 if f < f0 else s0 * (0.5 + 1.3 * EASE["out"](t)) * (1 - t ** 2) + 0.001
            ob.location = center + d * (0.3 + radius * EASE["out3"](t)) + Vector((0, 0, 0.1 + 0.4 * t * r.uniform(0.4, 1)))
            ob.keyframe_insert("location", frame=f)
            key_scale(ob, f, sc)

# ================================================================== SHOT A1 : street + truck
def shot_A1():
    cam = make_camera_only()
    road = B.principled("road", (0.05, 0.045, 0.07))
    walk = B.principled("walk", (0.13, 0.12, 0.16))
    bld = B.principled("bld", (0.08, 0.07, 0.12))
    stripe = B.principled("stripe", (0.75, 0.75, 0.8))
    win = B.emissive("win", (1.0, 0.8, 0.5), 3.0)
    lamp = B.emissive("lamp", (1.0, 0.85, 0.6), 8.0)
    truck_c = B.principled("truck", (0.85, 0.85, 0.9))
    truck_d = B.principled("truck_d", (0.15, 0.2, 0.35))
    head = B.emissive("headlight", (1.0, 0.97, 0.9), 60.0)
    B.box("Road", (60, 60, 0.2), (0, 0, -0.1), road, bevel=0)
    for x in (-5.5, 5.5):
        B.box("Walk", (3, 60, 0.3), (x * 1.0 + (1.5 if x > 0 else -1.5), 0, 0.0), walk, bevel=0.02)
    # crosswalk stripes (the player stands at the crossing)
    for i in range(-6, 7):
        B.box("Stripe", (0.5, 3.0, 0.02), (i * 1.0, 2.0, 0.01), stripe, bevel=0)
    # buildings
    rnd = random.Random(3)
    for side in (-1, 1):
        for j in range(-4, 10):
            h = rnd.uniform(6, 16)
            w = rnd.uniform(3, 5)
            cx = side * (9.5 + w / 2 * 0)
            cy = j * 5.0
            if -1 < cy < 6:
                continue
            ob = B.box("Bld", (6, 4.6, h), (cx, cy, h / 2), bld, bevel=0.05)
            bm = bmesh.new()
            for k in range(int(h / 1.6)):
                for m in range(3):
                    if rnd.random() < 0.45:
                        B.bm_box(bm, (0.05, 0.7, 0.8), (cx - side * 3.02, cy - 1.5 + m * 1.5, 1.2 + k * 1.6))
            B.mesh_obj("Win", bm, win, bevel=0)
    for y in (-6, 8, 18):
        for x in (-4.2, 4.2):
            B.box("LampPole", (0.15, 0.15, 5), (x, y, 2.5), bld, bevel=0)
            B.box("Lamp", (0.6, 0.35, 0.15), (x * 0.9, y, 5.0), lamp, bevel=0)
            B.light("LampL", "POINT", 250, (1, 0.8, 0.55), (x * 0.9, y, 4.7), 0.3)
    # truck from the right
    tr = B.empty("Truck")
    B.box("Cab", (2.2, 2.4, 2.6), (-2.2, 0, 1.6), truck_c, tr, bevel=0.08)
    B.box("Cargo", (5.0, 2.5, 3.2), (1.6, 0, 2.0), truck_c, tr, bevel=0.06)
    B.box("Glass", (0.05, 2.0, 0.9), (-3.31, 0, 2.3), truck_d, tr, bevel=0)
    B.box("Bumper", (0.3, 2.5, 0.4), (-3.35, 0, 0.6), truck_d, tr, bevel=0.03)
    for wy in (-0.8, 0.8):
        B.box("Head", (0.08, 0.45, 0.3), (-3.34, wy, 1.0), head, tr, bevel=0)
        for wx in (-2.2, 1.0, 2.8):
            B.box("Wheel", (0.9, 0.35, 0.9), (wx, wy * 1.45, 0.45), truck_d, tr, bevel=0.06)
    hl = B.light("TruckBeam", "SPOT", 0, (1, 0.97, 0.9), (-3.6, 0, 1.0), 0.4, tr)
    hl.rotation_euler = (0, -math.pi / 2 - 0.05, 0)
    hl.data.spot_size = math.radians(70)
    trk = Track([(1, (22, 2.0, 0)), (14, (14, 2.0, 0), "lin"), (31, (1.6, 2.0, 0), "in")])
    for f in range(1, 33):
        B.key_loc(tr, f, trk(f))
        hl.data.energy = 20000 + 60000 * clamp((f - 10) / 20) ** 2
        hl.data.keyframe_insert("energy", frame=f)
    # camera: walking across, glancing at phone-height, then turning to the light
    prevq = {}
    cpos = Track([(1, (-1.2, 1.2, 1.6)), (16, (-0.4, 1.7, 1.6), "lin"), (24, (-0.25, 1.8, 1.55), "out"),
                  (32, (-0.3, 1.75, 1.5))])
    tgt = Track([(1, (-0.9, 12, 1.2)), (12, (-0.2, 12, 1.0)), (22, (12, 2.2, 1.2), "smoother"),
                 (32, (10, 2.0, 1.3))])
    for f in range(1, 33):
        cp = Vector(cpos(f)) + Vector((0, 0, 0.03 * abs(math.sin(f * 0.45)) if f < 18 else 0))
        s, sr = shake(f, 26, 0.03, 4)
        B.key_loc(cam, f, cp + s)
        B.key_quat(cam, f, B.look_quat(cp, Vector(tgt(f)), sr + (0.0 if f < 20 else 0.05 * (f - 20) / 12)), prevq)
    # whiteout plane
    wm = fade_material("WhiteOut", (1, 1, 1))
    wm.node_tree.nodes["Emission"].inputs["Strength"].default_value = 3.0
    cam_overlay(cam, "WhiteOutPlane", wm)
    for f, v in ((1, 0), (27, 0), (30, 0.6), (32, 1.0)):
        key_fade(wm, f, v)
    w = bpy.data.worlds.new("Night")
    scene.world = w
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.01, 0.01, 0.03, 1)
    B.light("Moon", "SUN", 0.4, (0.6, 0.6, 1.0)).rotation_euler = (0.8, 0, 0.6)

# ================================================================== SHOT A2 : reincarnation void
def shot_A2():
    cam = make_camera_only()
    white = B.principled("void_white", (0.9, 0.88, 0.95))
    lav = B.principled("void_lav", (0.6, 0.5, 0.85))
    rune = M["rune"]
    rnd = random.Random(8)
    cubes = []
    for i in range(140):
        p = Vector((rnd.uniform(-14, 14), rnd.uniform(-14, 14), rnd.uniform(-40, 6)))
        if Vector((p.x, p.y)).length < 2.2:
            p.x += 3 * (1 if p.x >= 0 else -1)
        s = rnd.uniform(0.3, 1.6)
        ob = B.box("VoidCube", (s, s, s), (0, 0, 0), white if i % 3 else lav, loc=p, bevel=0.05)
        ob.rotation_euler = (rnd.random() * 3, rnd.random() * 3, rnd.random() * 3)
        cubes.append((ob, rnd.uniform(-1.5, 1.5)))
    for ob, sp in cubes:
        for f in (1, 64):
            ob.rotation_euler.x += sp * (1 if f == 64 else 0)
            ob.keyframe_insert("rotation_euler", frame=f)
            ob.location.z += 3.0 * (1 if f == 64 else 0)   # cubes drift up => feels like falling faster
            ob.keyframe_insert("location", frame=f)
    # magic circle far below (nested rotating rings of blocks)
    circ = B.empty("MagicCircle", loc=(0, 0, -46))
    rings = []
    for k, (r, n, w) in enumerate(((7, 72, 0.35), (5.4, 48, 0.25), (3.6, 6, 0.3))):
        bm = bmesh.new()
        if n == 6:   # hexagram lines
            pts = [Vector((math.cos(a) * r, math.sin(a) * r, 0)) for a in [2 * math.pi * i / 6 for i in range(6)]]
            for i in range(6):
                B.bm_beam(bm, pts[i], pts[(i + 2) % 6], w, 0.05)
        else:
            for s in range(n):
                if k == 1 and s % 3 == 0:
                    continue
                a = 2 * math.pi * s / n
                B.bm_box(bm, (2 * math.pi * r / n * 0.85, w, 0.05), (math.cos(a) * r, math.sin(a) * r, 0),
                         Matrix.Rotation(a + math.pi / 2, 3, 'Z'))
        ring = B.mesh_obj("Ring%d" % k, bm, rune, circ, bevel=0)
        rings.append(ring)
    for i, ring in enumerate(rings):
        for f in (1, 64):
            ring.rotation_euler.z = (0.9 if i % 2 else -0.7) * (f / 64) * 2
            ring.keyframe_insert("rotation_euler", frame=f)
    B.light("CircleLight", "POINT", 30000, (1.0, 0.3, 0.9), (0, 0, -44), 4)
    # floating title text
    tx = text_obj("TxtTensei", "異世界転生", 1.7, B.emissive("txt_white", (1.0, 0.9, 1.0), 6.0), (0, 0, -22))
    tx.rotation_euler = (0, 0, 0)
    sub = text_obj("TxtSub", "― あなたは死んだ。そして… ―", 0.55, B.emissive("txt_pink", (1.0, 0.45, 0.85), 5.0), (0, 0, -23.6))
    for o in (tx, sub):
        key_scale(o, 1, 0.001)
        key_scale(o, 14, 0.001)
        key_scale(o, 22, 1.15)
        key_scale(o, 26, 1.0)
    # camera falls head-first, looking down, slowly spinning
    prevq = {}
    zt = Track([(1, 4.0), (64, -38.0, "in")])
    for f in range(1, 65):
        z = zt(f)
        cp = Vector((0.0, -3.5 + 2.0 * f / 64, z))
        tgt = Vector((0, 1.5, z - 10))
        roll = 0.6 * f / 64 + 0.2 * math.sin(f * 0.08)
        B.key_loc(cam, f, cp)
        B.key_quat(cam, f, B.look_quat(cp, tgt, roll), prevq)
    # text must face the camera (camera looks down -Z, slightly +Y)
    for o in (tx, sub):
        o.rotation_euler = (0, 0, 0)
        o.rotation_mode = 'XYZ'
    # world: white -> purple ; flash in / out
    w = bpy.data.worlds.new("Void")
    scene.world = w
    bg = w.node_tree.nodes["Background"]
    for f, c in ((1, (1.0, 1.0, 1.0)), (16, (0.85, 0.8, 1.0)), (44, (0.35, 0.15, 0.55)), (64, (0.12, 0.04, 0.2))):
        bg.inputs["Color"].default_value = (*c, 1)
        bg.inputs["Color"].keyframe_insert("default_value", frame=f)
    sun = B.light("VoidSun", "SUN", 3.0, (1, 0.95, 1))
    sun.rotation_euler = (0.4, 0.3, 0)
    wm = fade_material("Flash", (1, 1, 1))
    wm.node_tree.nodes["Emission"].inputs["Strength"].default_value = 3.0
    cam_overlay(cam, "FlashPlane", wm)
    for f, v in ((1, 1.0), (8, 0.0), (58, 0.0), (64, 1.0)):
        key_fade(wm, f, v)

# ================================================================== SHOT B : arena awakening
def shot_B():
    flames, floats = B.build_arena()
    J = B.build_enemy()
    P = B.build_player()
    env_life(flames, floats, LENGTH)
    cam = P["cam"]
    # eyelids
    lid_m = B.principled("lid", (0.0, 0.0, 0.0))
    up = cam_overlay(cam, "LidUp", lid_m, -0.03, (0.2, 0.12))
    dn = cam_overlay(cam, "LidDn", lid_m, -0.03, (0.2, 0.12))
    lid = Track([(1, 0.0), (5, 0.0), (10, 0.45, "out"), (13, 0.3), (15, 0.02, "in"), (17, 0.0),
                 (21, 1.0, "out3")])    # 0=closed 1=open
    for f in range(1, LENGTH + 1):
        o = lid(f)
        B.key_loc(up, f, (0, 0.06 + o * 0.12, -0.03))
        B.key_loc(dn, f, (0, -0.06 - o * 0.12, -0.03))
    # sky text
    tmat = B.emissive("txt_sky", (1.0, 0.35, 0.8), 7.0)
    t1 = text_obj("TxtDG", "デスゲーム開始", 3.6, tmat, (0, 44, 17.5), extrude=0.3)
    t1.rotation_euler = (math.pi / 2, 0, 0)
    t2 = text_obj("TxtR1", "ROUND 1", 1.8, B.emissive("txt_gold", (1.0, 0.75, 0.25), 6.0), (0, 44, 13.3), extrude=0.2)
    t2.rotation_euler = (math.pi / 2, 0, 0)
    for o, d in ((t1, 0), (t2, 4)):
        key_scale(o, 1, 0.001)
        key_scale(o, 44 + d, 0.001)
        key_scale(o, 51 + d, 1.12)
        key_scale(o, 55 + d, 1.0)
    # sword materialises in the hand
    sw = P["sword"]
    for f, s in ((1, 0.001), (30, 0.001), (36, 1.15), (39, 1.0)):
        key_scale(sw, f, s)
    sp_m = B.emissive("sparkle", (0.6, 0.9, 1.0), 12.0)
    rnd = random.Random(4)
    for i in range(14):
        ob = B.box("Sparkle_%d" % i, (0.012, 0.012, 0.012), (0, 0, 0), sp_m, P["rh"], bevel=0)
        ob.visible_shadow = False
        a0, r0, h0 = rnd.uniform(0, 6.28), rnd.uniform(0.15, 0.3), rnd.uniform(-0.1, 0.6)
        for f in range(24, 44):
            t = clamp((f - 24) / 14)
            a = a0 + t * 5
            r = r0 * (1 - t)
            ob.location = (math.cos(a) * r, h0 * (1 - t) + 0.3 * t, math.sin(a) * r)
            ob.keyframe_insert("location", frame=f)
            key_scale(ob, f, 0.001 if f < 25 or f > 39 else 1.0 + math.sin(f + i))
        key_scale(ob, 1, 0.001)
    # enemy falls from the sky, lands, rises, starts to run toward the player
    E_DEF = B.E_DEF
    tl = B.PoseTimeline(E_DEF, [
        (1, dict(hz=-0.05, tp=-0.2, np=-0.3, shRx=-2.6, shRy=0.5, elR=-0.3, shLx=-2.6, shLy=-0.5, elL=-0.3,
                 fRy=-0.25, fRz=0.35, fLy=0.15, fLz=0.25), "smooth"),
        (66, dict(), "smooth"),
        (73, dict(hz=-0.1, tp=0.2, np=0.1, shRx=-1.6, shRy=0.6, elR=-0.6, shLx=-1.0, shLy=-0.6, elL=-0.6,
                  fRy=-0.35, fRz=0.20, fLy=0.30, fLz=0.15), "smooth"),
        (75, dict(hz=-0.50, tp=0.75, np=-0.35, shRx=-0.55, shRy=0.15, elR=-0.2, shLx=0.4, shLy=-0.7, elL=-0.3,
                  fRy=-0.35, fRz=B.ANK, fLy=0.40, fLz=B.ANK), "out3"),    # superhero landing
        (82, dict(hz=-0.46, tp=0.70, np=-0.40), "smooth"),
        (88, dict(B.STANCE, tp=0.25, np=-0.15), "smoother"),               # rises, glares
        (92, dict(run=0.6, hz=-0.10, tp=0.38, elR=-1.5, elL=-1.5, np=-0.25), "in"),
        (96, dict(run=1.0), "lin"),
    ])
    ry = Track([(1, 12.6), (86, 12.6), (96, 11.2, "in")])
    rz = Track([(1, 60.0), (50, 42.0, "lin"), (74, 0.0, "in")])
    rp = Track([(1, -0.5), (60, 0.3), (74, 0.0)])
    for f in range(1, LENGTH + 1):
        pose = tl(f)
        y = ry(f)
        key_enemy(J, f, pose, (0, y, rz(f)), rp(f), 0.0, run_phase=(11.2 - y) / 2.4)
    # eye flash when it rises
    eb = M["e_eye"].node_tree.nodes["Emission"].inputs["Strength"]
    for f, v in ((1, 8), (84, 8), (87, 40), (92, 8)):
        eb.default_value = v
        eb.keyframe_insert("default_value", frame=f)
    land = Vector((0, 12.6, 0))
    dust_ring("Shock", 75, land, 20, 3.0, 9)
    lf = B.light("LandFlash", "POINT", 0, (0.4, 0.6, 1.0), (0, 12.0, 1.0), 1.0)
    for f, v in ((1, 0), (74, 0), (75, 2500), (84, 0)):
        lf.data.energy = v
        lf.data.keyframe_insert("energy", frame=f)
    # rune flash on landing
    rb = M["rune"].node_tree.nodes["Emission"].inputs["Strength"]
    for f, v in ((1, 4), (74, 4), (76, 25), (90, 4)):
        rb.default_value = v
        rb.keyframe_insert("default_value", frame=f)
    # camera + hands
    prevq = {}
    look = Track([
        (1, (0.0, 1.0, 0.25)), (22, (0.0, 1.0, 0.3)),           # looking at own hands
        (30, (0.05, 1.0, 0.35), "smooth"),
        (40, (0.0, 1.0, 0.45), "smooth"),
        (54, (0.0, 44.0, 17.0), "smoother"),                    # sky text
        (64, (0.0, 44.0, 16.0)),
        (70, (0.0, 12.6, 6.0), "smooth"),                       # follow the falling enemy
        (75, (0.0, 12.6, 1.0), "in"),
        (84, (0.0, 12.6, 1.1)),
        (96, (0.0, 11.2, 1.45), "smooth"),
    ])
    cpos = Track([(1, (0, -0.05, 1.50)), (20, (0, -0.05, 1.50)), (30, (0, 0, 1.60), "smooth"), (96, (0, 0, 1.62))])
    RH1, LH1 = B.RH(1), B.LH(1)
    rh = Track([(1, (0.09, -0.20, -0.42, 0.0, 0.3, -1.0)), (20, (0.10, -0.18, -0.42, 0.1, 0.3, -1.0)),
                (28, (0.08, -0.14, -0.44, 0.0, 1.0, -0.2), "smooth"),   # raise and turn the hand
                (40, (0.10, -0.12, -0.46, -0.1, 1.0, -0.4), "smooth"),  # sword appears: look at it
                (52, (0.19, -0.44, -0.50, 0.25, 0.3, -0.92), "smooth"),
                (84, (0.19, -0.44, -0.50, 0.25, 0.3, -0.92)),
                (94, RH1, "smooth"), (96, RH1)])
    lh = Track([(1, (-0.09, -0.20, -0.42)), (20, (-0.10, -0.18, -0.42)), (30, (-0.12, -0.24, -0.44), "smooth"),
                (50, (-0.17, -0.42, -0.42), "smooth"), (90, LH1, "smooth"), (96, LH1)])
    for f in range(1, LENGTH + 1):
        s, sr = shake(f, 75, 0.06, 4)
        cp = Vector(cpos(f)) + s + Vector((0, 0, 0.006 * math.sin(f * 0.25)))
        tg = Vector(look(f))
        if 60 <= f <= 75:
            # track the falling enemy exactly while it drops
            e = Vector((0, 12.6, rz(f) + 1.4))
            tg = tg.lerp(e, clamp((f - 60) / 6) * (1 - clamp((f - 73) / 3)))
        key_player(P, f, cp, tg, sr, rh(f), lh(f), prevq)

# ================================================================== SHOT C : hesitation
BCUT = 84          # shot B is cut after this frame; shot C continues from the same state

def _b_state():
    """state of shot B at frame BCUT (same key data as shot_B) so that C starts seamlessly"""
    tl = B.PoseTimeline(B.E_DEF, [
        (75, dict(hz=-0.50, tp=0.75, np=-0.35, shRx=-0.55, shRy=0.15, elR=-0.2, shLx=0.4, shLy=-0.7, elL=-0.3,
                  fRy=-0.35, fRz=B.ANK, fLy=0.40, fLz=B.ANK), "out3"),
        (82, dict(hz=-0.46, tp=0.70, np=-0.40), "smooth"),
        (88, dict(B.STANCE, tp=0.25, np=-0.15), "smoother"),
    ])
    cpos = Track([(30, (0, 0, 1.60)), (96, (0, 0, 1.62), "smooth")])
    lh = Track([(50, (-0.17, -0.42, -0.42)), (90, B.LH(1), "smooth")])
    return dict(tl(BCUT)), Vector(cpos(BCUT)), tuple(lh(BCUT))

def shot_C():
    flames, floats = B.build_arena()
    J = B.build_enemy()
    P = B.build_player()
    env_life(flames, floats, LENGTH)
    pose0, c0, lh0 = _b_state()
    STANCE, ANK = B.STANCE, B.ANK
    G = Vector((0.9, 1.9, 0.0))                 # where the warning bolt hits the floor
    ZAP = 141

    # ---- leftovers of the landing (shot B) so the cut is continuous
    dust_ring("Shock", 75 - (BCUT - 1), Vector((0, 12.6, 0)), 20, 3.0, 9, init=False)
    rb = M["rune"].node_tree.nodes["Emission"].inputs["Strength"]
    for f, v in ((1, 13), (7, 4), (ZAP + 1, 4), (ZAP + 3, 22), (ZAP + 16, 4)):
        rb.default_value = v
        rb.keyframe_insert("default_value", frame=f)
    eb = M["e_eye"].node_tree.nodes["Emission"].inputs["Strength"]
    for f, v in ((1, 8), (12, 8), (17, 45), (26, 8), (128, 8), (138, 40), (150, 8), (252, 8), (256, 40), (262, 8)):
        eb.default_value = v
        eb.keyframe_insert("default_value", frame=f)

    # ---- sky text: "death game start" is replaced by the rule
    tmat = B.emissive("txt_sky", (1.0, 0.35, 0.8), 7.0)
    t1 = text_obj("TxtDG", "デスゲーム開始", 3.6, tmat, (0, 44, 17.5), extrude=0.3)
    t2 = text_obj("TxtR1", "ROUND 1", 1.8, B.emissive("txt_gold", (1.0, 0.75, 0.25), 6.0), (0, 44, 13.3), extrude=0.2)
    rmat = B.emissive("txt_rule", (1.0, 0.10, 0.18), 9.0)
    t3 = text_obj("TxtRule1", "戦わなければ", 3.3, rmat, (0, 44, 18.6), extrude=0.3)
    t4 = text_obj("TxtRule2", "死ぬ", 5.6, rmat, (0, 44, 13.6), extrude=0.4)
    for o in (t1, t2, t3, t4):
        o.rotation_euler = (math.pi / 2, 0, 0)
    for o in (t1, t2):
        for f, s in ((1, 1.0), (163, 1.0), (165, 1.15), (167, 0.001)):
            key_scale(o, f, s)
    for o, d in ((t3, 0), (t4, 3)):
        for f, s in ((1, 0.001), (167 + d, 0.001), (171 + d, 1.18), (175 + d, 1.0), (244, 1.0), (246, 1.1), (249, 0.001)):
            key_scale(o, f, s)

    # ---- exit gate behind the player: open (green) -> bars slam down (red)
    SLAM = 100
    gy = -9.25
    gm = B.principled("gate_frame", (0.20, 0.11, 0.34))
    barm = B.principled("gate_bar", (0.04, 0.02, 0.07))
    door = B.emissive("gate_door", (0.55, 1.0, 0.75), 6.0)
    bm = bmesh.new()
    for x in (-1.75, 1.75):
        B.bm_box(bm, (0.6, 0.7, 3.9), (x, gy, 1.95))
    B.bm_box(bm, (4.5, 0.8, 0.6), (0, gy, 4.0))
    B.mesh_obj("GateFrame", bm, gm, bevel=0.05)
    B.box("GateDoor", (2.9, 0.05, 3.7), (0, gy - 0.2, 1.85), door, bevel=0)
    ds = door.node_tree.nodes["Emission"].inputs["Strength"]
    for f, v in ((1, 6.0), (SLAM - 1, 6.0), (SLAM + 1, 1.2)):
        ds.default_value = v
        ds.keyframe_insert("default_value", frame=f)
    s_open = text_obj("GateOpen", "出口", 0.95, B.emissive("gate_g", (0.4, 1.0, 0.6), 9.0), (0, gy + 0.45, 4.0), extrude=0.05)
    s_shut = text_obj("GateShut", "封鎖", 0.95, B.emissive("gate_r", (1.0, 0.12, 0.15), 10.0), (0, gy + 0.45, 4.0), extrude=0.05)
    for o in (s_open, s_shut):
        o.rotation_euler = (math.pi / 2, 0, math.pi)
    for f, s in ((1, 1.0), (SLAM - 1, 1.0), (SLAM, 0.001)):
        key_scale(s_open, f, s)
    for f, s in ((1, 0.001), (SLAM - 1, 0.001), (SLAM, 1.25), (SLAM + 4, 1.0)):
        key_scale(s_shut, f, s)
    bars = B.empty("GateBars", None, (0, gy + 0.1, 0))
    bm = bmesh.new()
    for i in range(6):
        B.bm_box(bm, (0.2, 0.2, 3.7), (-1.2 + i * 0.48, 0, 1.85))
    for z in (0.9, 2.8):
        B.bm_box(bm, (3.0, 0.24, 0.2), (0, 0, z))
    B.mesh_obj("GateBarMesh", bm, barm, bars, bevel=0.03)
    for f, z, sz in ((1, 3.7, 0.01), (SLAM - 4, 3.7, 0.01), (SLAM, 0.0, 1.0), (SLAM + 2, 0.12, 1.0), (SLAM + 4, 0.0, 1.0)):
        bars.location = (0, gy + 0.1, z)
        bars.keyframe_insert("location", frame=f)
        key_scale(bars, f, (1, 1, sz))
    gl = B.light("GateGreen", "POINT", 700, (0.4, 1.0, 0.6), (0, gy + 2.0, 2.0), 1.0)
    gr = B.light("GateRed", "POINT", 0, (1.0, 0.1, 0.15), (0, gy + 2.0, 2.4), 1.0)
    for f, a, b in ((1, 700, 0), (SLAM - 1, 700, 0), (SLAM, 60, 1500), (SLAM + 8, 0, 500)):
        gl.data.energy, gr.data.energy = a, b
        gl.data.keyframe_insert("energy", frame=f)
        gr.data.keyframe_insert("energy", frame=f)
    dust_ring("GateDust", SLAM, Vector((0, gy + 0.5, 0)), 12, 1.6, 12, size=0.3)

    # ---- enemy: rises, points at you, fires a warning shot, taunts, then charges
    WIND = dict(hz=-0.14, tp=-0.28, tt=-0.38, tl=0.08, np=-0.18, shRx=-2.75, shRy=0.15, elR=-0.55,
                shLx=-1.0, shLy=-0.25, elL=-0.25, fRy=-0.20, fRz=ANK, fLy=0.32, fLz=ANK)
    THROW = dict(hz=-0.22, tp=0.30, tt=0.32, tl=-0.05, np=-0.05, shRx=-1.30, shRy=0.02, elR=-0.02,
                 shLx=0.35, shLy=-0.45, elL=-0.9, fRy=-0.55, fRz=ANK, fLy=0.47, fLz=ANK)
    GLARE = dict(STANCE, tp=0.25, np=-0.15)
    POINT = dict(STANCE, tp=0.10, tt=0.18, np=-0.12, shRx=-1.50, shRy=0.02, elR=-0.05)
    BECK_A = dict(STANCE, tp=0.08, shLx=-1.35, shLy=-0.1, elL=-0.55)
    BECK_B = dict(STANCE, tp=0.08, shLx=-1.45, shLy=-0.1, elL=-1.9)
    tl = B.PoseTimeline(B.E_DEF, [
        (1, pose0, "smooth"),
        (22, GLARE, "smoother"),
        (34, GLARE, "smooth"),
        (44, POINT, "smooth"),
        (62, dict(POINT, tp=0.14), "smooth"),
        (80, dict(STANCE), "smooth"),
        (118, dict(STANCE, tp=0.05), "smooth"),
        (131, WIND, "smooth"),
        (137, dict(WIND, tp=-0.32, tt=-0.42, shRx=-2.9), "lin"),
        (ZAP, THROW, "in"),
        (ZAP + 4, dict(THROW, hz=-0.18, tp=0.12, tt=0.22, shRx=-1.60, elR=-0.15), "out"),
        (ZAP + 14, dict(THROW, hz=-0.17, tp=0.18, tt=0.25, shRx=-1.30, elR=-0.05), "smooth"),
        (172, dict(STANCE, tp=0.16), "smooth"),
        (196, dict(STANCE, tp=0.12), "smooth"),
        (204, BECK_A, "smooth"), (210, BECK_B, "smooth"), (216, BECK_A, "smooth"), (222, BECK_B, "smooth"),
        (232, dict(STANCE), "smooth"),
        (244, GLARE, "smooth"),
        (256, GLARE, "smooth"),
        (260, dict(run=0.6, hz=-0.10, tp=0.38, elR=-1.5, elL=-1.5, np=-0.25), "in"),
        (264, dict(run=1.0), "lin"),
    ])
    ry = Track([(1, 12.6), (254, 12.6), (264, 11.2, "in")])
    for f in range(1, LENGTH + 1):
        pose = tl(f)
        pose["hz"] += 0.008 * math.sin(f * 0.21)          # breathing
        y = ry(f)
        key_enemy(J, f, pose, (0, y, 0), 0.0, 0.0, run_phase=(11.2 - y) / 2.4)

    # ---- warning bolt
    elR = J["elR"]
    hand_local = Vector((0, 0, -0.40))
    orb = B.box("FX_orb", (0.22, 0.22, 0.22), (0, 0, 0), M["bolt_core"], elR, (0, 0, -0.42), bevel=0)
    B.box("FX_orb_glow", (0.4, 0.4, 0.4), (0, 0, 0), M["bolt_glow"], orb, bevel=0)
    for f in range(1, LENGTH + 1):
        if 124 <= f <= ZAP:
            s = 0.25 + 0.95 * ((f - 124) / (ZAP - 124)) ** 1.3 + 0.1 * math.sin(f * 2.3)
        elif ZAP < f <= ZAP + 5:
            s = 1.1 * (1 - (f - ZAP) / 5) + 0.001
        else:
            s = 0.001
        key_scale(orb, f, s)
        orb.rotation_euler = (f * 0.5, f * 0.37, f * 0.21)
        orb.keyframe_insert("rotation_euler", frame=f)
    hl = B.light("FX_handLight", "POINT", 0, (0.3, 0.6, 1.0), (0, 0, -0.42), 0.15, elR)
    for f, v in ((1, 0), (124, 0), (ZAP - 1, 150), (ZAP, 350), (ZAP + 6, 60), (ZAP + 14, 0)):
        hl.data.energy = v
        hl.data.keyframe_insert("energy", frame=f)
    for f in range(126, ZAP + 11):
        scene.frame_set(f)
        hp = elR.matrix_world @ hand_local
        rnd = random.Random(3000 + f)
        bc, bg = bmesh.new(), bmesh.new()
        if f < ZAP:
            k = (f - 126) / (ZAP - 126)
            for _ in range(3 + int(k * 4)):
                rv = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
                B.add_bolt(bc, bg, hp, hp + rv * rnd.uniform(0.25, 0.55 + k * 0.4), rnd, amp=0.06, w=0.015, branches=0)
        else:
            t = clamp((f - ZAP) / 2.0)
            fade = 1.0 if f < ZAP + 6 else max(0.0, 1 - (f - ZAP - 6) / 5)
            tip = hp.lerp(G + Vector((0, 0, 0.05)), max(t, 0.15))
            w = 0.05 * (0.4 + 0.6 * fade) * (1.0 + 0.3 * rnd.random())
            B.add_bolt(bc, bg, hp, tip, rnd, amp=0.30, w=w, branches=5 if fade > 0.5 else 2)
            if f % 2 == 0 and fade > 0.3:
                B.add_bolt(bc, bg, hp, tip, random.Random(f * 7), amp=0.4, w=w * 0.6, branches=1)
            if t >= 1.0 and fade > 0.2:                     # crackle crawling over the floor
                for _ in range(5):
                    a = rnd.uniform(0, 6.28)
                    e = G + Vector((math.cos(a), math.sin(a), 0)) * rnd.uniform(0.5, 1.5) + Vector((0, 0, 0.04))
                    B.add_bolt(bc, bg, G + Vector((0, 0, 0.05)), e, rnd, amp=0.08, w=0.02, branches=0)
        oc = B.mesh_obj("FX_boltCore_%03d" % f, bc, M["bolt_core"])
        og = B.mesh_obj("FX_boltGlow_%03d" % f, bg, M["bolt_glow"])
        for o in (oc, og):
            o.visible_shadow = False
            B.vis_only(o, [f])
    zl = B.light("FX_zapLight", "POINT", 0, (0.35, 0.65, 1.0), tuple(G + Vector((0, 0, 0.5))), 0.3)
    for f, v in ((1, 0), (ZAP + 1, 0), (ZAP + 2, 2600), (ZAP + 6, 1100), (ZAP + 12, 0)):
        zl.data.energy = v
        zl.data.keyframe_insert("energy", frame=f)
    sc_m = B.emissive("scorch", (0.3, 0.7, 1.0), 14.0)
    scorch = bmesh.new()
    r_ = random.Random(8)
    for i in range(9):
        a = i * 0.7
        B.bm_box(scorch, (r_.uniform(0.25, 0.7), 0.07, 0.012), G + Vector((0, 0, 0.012)),
                 Matrix.Rotation(a, 3, 'Z'))
    so = B.mesh_obj("Scorch", scorch, sc_m, bevel=0)
    so.visible_shadow = False
    for f, s in ((1, 0.001), (ZAP + 1, 0.001), (ZAP + 2, 1.0), (226, 1.0), (236, 0.001)):
        key_scale(so, f, s)
    ss = sc_m.node_tree.nodes["Emission"].inputs["Strength"]
    for f, v in ((1, 14.0), (ZAP + 2, 30.0), (ZAP + 20, 6.0), (228, 0.0)):
        ss.default_value = v
        ss.keyframe_insert("default_value", frame=f)
    dust_ring("ZapSpark", ZAP + 2, G, 12, 1.6, 5, size=0.10, mat=M["spark_b"])
    dust_ring("ZapDust", ZAP + 2, G, 9, 1.1, 6, size=0.26)

    # ---- camera (yaw / pitch in degrees; yaw<0 = left, -180 = looking back at the gate)
    p0 = math.degrees(math.atan2(1.1 - c0.z, 12.6))
    p1 = math.degrees(math.atan2(1.45 - 1.62, 11.2))
    yawT = Track([(1, 0), (28, 0), (36, -52, "smooth"), (42, -50), (52, 56, "smooth"), (57, 54),
                  (65, 0, "smooth"), (70, 0), (88, -180, "smoother"), (118, -180),
                  (130, 0, "smoother"), (ZAP, 0), (ZAP + 3, -24, "out"), (ZAP + 11, -18),
                  (164, 0, "smooth"), (264, 0)])
    pitT = Track([(1, p0), (22, -0.5, "smooth"), (36, 4), (52, 5), (65, -1), (88, -3), (118, -4),
                  (130, -2), (ZAP, -3), (ZAP + 3, -17, "out"), (ZAP + 11, -13), (162, -2, "smooth"),
                  (173, 19, "smooth"), (186, 19), (198, -40, "smoother"), (224, -38),
                  (238, -2, "smooth"), (264, p1, "smooth")])
    rollT = Track([(1, 0), (ZAP, 0), (ZAP + 3, 0.13, "out"), (ZAP + 12, 0.07), (166, 0, "smooth"), (264, 0)])
    cpos = Track([(1, tuple(c0)), (26, (0, 0, 1.62)),
                  (36, (0.04, -0.45, 1.585), "smooth"), (46, (-0.04, -0.95, 1.60), "smooth"),
                  (56, (0.03, -1.35, 1.585), "smooth"), (66, (0, -1.6, 1.61), "smooth"),
                  (86, (0, -1.6, 1.61)), (96, (0, -2.05, 1.60), "smooth"), (118, (0, -2.05, 1.60)),
                  (130, (0, -1.6, 1.61), "smooth"), (ZAP, (0, -1.6, 1.61)),
                  (ZAP + 4, (-0.12, -1.98, 1.42), "out"), (ZAP + 14, (-0.10, -1.98, 1.47)),
                  (170, (0, -1.9, 1.58), "smooth"), (198, (0, -1.9, 1.56), "smooth"), (226, (0, -1.9, 1.58)),
                  (236, (0.04, -1.2, 1.585), "smooth"), (244, (-0.03, -0.55, 1.60), "smooth"),
                  (252, (0, 0, 1.62), "smooth"), (264, (0, 0, 1.62))])
    LOW = (0.19, -0.44, -0.50, 0.25, 0.3, -0.92)
    GUARD = (0.16, -0.30, -0.52, 0.05, 0.30, -0.95)
    FLINCH = (0.22, -0.24, -0.36, -0.55, 0.6, -0.4)
    HOLD = (0.085, -0.15, -0.46, -0.10, 0.75, -0.65)
    RH1, LH1 = B.RH(1), B.LH(1)
    rh = Track([(1, LOW), (24, LOW), (34, GUARD, "smooth"), (66, GUARD), (78, LOW, "smooth"), (128, LOW),
                (136, (0.17, -0.31, -0.54, 0.0, 0.4, -0.9), "smooth"), (ZAP, (0.17, -0.31, -0.54, 0.0, 0.4, -0.9)),
                (ZAP + 4, FLINCH, "out"), (ZAP + 13, FLINCH), (166, LOW, "smooth"), (190, LOW),
                (201, HOLD, "smooth"), (226, HOLD), (240, RH1, "smooth"), (264, RH1)])
    LHLOW = (-0.17, -0.42, -0.42)
    lh = Track([(1, lh0), (24, LHLOW), (34, (-0.15, -0.30, -0.46), "smooth"), (66, (-0.15, -0.30, -0.46)),
                (78, LHLOW, "smooth"), (90, LHLOW), (97, (-0.08, -0.10, -0.56), "smooth"),
                (101, (-0.08, -0.10, -0.56)), (110, LHLOW, "smooth"), (ZAP, LHLOW),
                (ZAP + 4, (-0.10, -0.13, -0.44), "out"), (ZAP + 13, (-0.11, -0.15, -0.44)), (166, LHLOW, "smooth"),
                (190, LHLOW), (202, (-0.07, -0.17, -0.44), "smooth"), (212, (-0.07, -0.17, -0.44)),
                (220, (0.045, -0.215, -0.455), "smooth"), (230, (0.045, -0.215, -0.455)),
                (242, LH1, "smooth"), (264, LH1)])
    trem = Track([(1, 0), (20, 0), (30, 1.0), (66, 1.0), (80, 0.5), (128, 0.5), (ZAP + 4, 1.3),
                  (198, 1.6), (208, 1.6), (221, 0.0, "smooth"), (264, 0)])
    prevq = {}
    for f in range(1, LENGTH + 1):
        s0, r0 = shake(f + BCUT - 1, 75, 0.06, 4)                    # tail of the landing shake
        s1, r1 = shake(f, SLAM, 0.035, 4)
        s2, r2 = shake(f, ZAP + 2, 0.07, 5)
        cp = Vector(cpos(f)) + s0 + s1 + s2 + Vector((0, 0, 0.006 * math.sin((f + BCUT - 1) * 0.25)))
        ya, pi_ = math.radians(yawT(f)), math.radians(pitT(f))
        d = Vector((math.sin(ya) * math.cos(pi_), math.cos(ya) * math.cos(pi_), math.sin(pi_)))
        k = trem(f)
        tv = Vector((math.sin(f * 2.9) + 0.6 * math.sin(f * 4.7 + 1), math.sin(f * 3.7 + 2) + 0.6 * math.sin(f * 5.3),
                     0.5 * math.sin(f * 4.1 + 4)))
        r = list(rh(f))
        for i in range(3):
            r[i] += tv[i] * 0.004 * k
        r[3] += tv[1] * 0.035 * k
        r[4] += tv[0] * 0.02 * k
        l = Vector(lh(f)) + Vector((tv[1], tv[2], tv[0])) * 0.004 * k
        key_player(P, f, cp, cp + d * 10, rollT(f) + r0 + r1 + r2, tuple(r), tuple(l), prevq)

# ================================================================== SHOT D : aftermath
def shot_D():
    flames, floats = B.build_arena()
    J = B.build_enemy()
    P = B.build_player()
    env_life(flames, floats, LENGTH)
    cam = P["cam"]
    F0 = 120  # continuity: the battle's last frame
    prevq = {}
    pose0 = B.E_TL(F0)
    root0 = Vector((0, B.E_RY(F0), 0))
    yaw0 = B.enemy_yaw(F0)
    SH = 20   # shatter frame
    for f in range(1, SH + 2):
        pose = dict(pose0)
        k = f / SH
        pose["tt"] = pose0["tt"] + 0.06 * k * math.sin(f * 3.1)
        pose["tp"] = pose0["tp"] + 0.035 * math.sin(f * 0.45 + 120 * 0.45) - 0.25 * k ** 3
        pose["np"] = pose0["np"] - 0.5 * k ** 2
        pose["shRx"] = pose0["shRx"] - 0.4 * k ** 2
        pose["shLx"] = pose0["shLx"] - 0.4 * k ** 2
        key_enemy(J, f, pose, root0 + Vector((0.02 * k * math.sin(f * 5), 0, 0)), 0.0, yaw0)
    # eyes flicker then the body flashes
    eb = M["e_eye"].node_tree.nodes["Emission"].inputs["Strength"]
    for f in range(1, SH + 1):
        eb.default_value = 8 if (f < 8 or f % 3) else 0.5
        eb.keyframe_insert("default_value", frame=f)
    for mk in ("e_blue", "e_dark", "e_light"):
        b = M[mk].node_tree.nodes.get("Principled BSDF")
        b.inputs["Emission Color"].default_value = (0.5, 0.8, 1.0, 1)
        for f, v in ((1, 0), (12, 0.0), (SH, 2.5)):
            b.inputs["Emission Strength"].default_value = v
            b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
    # shatter into cubes
    scene.frame_set(SH)
    parts = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("E_")]
    center = J["torso"].matrix_world.translation.copy()
    frag_mats = {"e_blue": M["e_blue"], "e_dark": M["e_dark"], "e_light": M["e_light"]}
    rnd = random.Random(12)
    frags = []
    for o in parts:
        mw = o.matrix_world
        cs = [mw @ Vector(c) for c in o.bound_box]
        lo = Vector((min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs)))
        hi = Vector((max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs)))
        vol = max(0.001, (hi - lo).x * (hi - lo).y * (hi - lo).z)
        n = max(1, min(10, int(vol / 0.006)))
        mat = o.data.materials[0]
        for i in range(n):
            p = Vector((rnd.uniform(lo.x, hi.x), rnd.uniform(lo.y, hi.y), rnd.uniform(lo.z, hi.z)))
            frags.append((p, mat))
    for o in parts:
        o.hide_render = False
        o.keyframe_insert("hide_render", frame=SH)
        o.hide_render = True
        o.keyframe_insert("hide_render", frame=SH + 1)
    print("fragments", len(frags))
    for i, (p, mat) in enumerate(frags):
        s0 = rnd.uniform(0.07, 0.14)
        ob = B.box("Frag_%d" % i, (1, 1, 1), (0, 0, 0), mat, bevel=0.05)
        d = (p - center)
        d.z = abs(d.z) * 0.5
        v = d.normalized() * rnd.uniform(2.5, 6.0) + Vector((0, 0, rnd.uniform(1.5, 4.5)))
        v.y += 1.5  # pushed away from the player
        spin = Vector((rnd.uniform(-12, 12), rnd.uniform(-12, 12), rnd.uniform(-12, 12)))
        life = rnd.uniform(22, 40)
        key_scale(ob, 1, 0.001)
        key_scale(ob, SH, 0.001)
        for f in range(SH + 1, LENGTH + 1):
            t = (f - SH) / 24.0
            pos = p + v * t + Vector((0, 0, -4.9 * t * t))
            if pos.z < s0 / 2:
                pos.z = s0 / 2
            ob.location = pos
            ob.keyframe_insert("location", frame=f)
            ob.rotation_euler = spin * t
            ob.keyframe_insert("rotation_euler", frame=f)
            sc = s0 * (1 - clamp((f - SH) / life) ** 2) + 0.001
            key_scale(ob, f, sc)
            if sc < 0.002:
                break
    fl = B.light("ShatterFlash", "POINT", 0, (0.4, 0.7, 1.0), center + Vector((0, -0.5, 0.3)), 0.6)
    for f, v in ((1, 0), (SH - 1, 300), (SH + 1, 9000), (SH + 10, 300), (SH + 18, 0)):
        fl.data.energy = v
        fl.data.keyframe_insert("energy", frame=f)
    burst = B.box("Burst", (1, 1, 1), (0, 0, 0), M["bolt_core"], loc=center, bevel=0)
    burst.visible_shadow = False
    for f, s in ((1, 0.001), (SH, 0.001), (SH + 1, 0.7), (SH + 4, 0.25), (SH + 7, 0.001)):
        key_scale(burst, f, s)
    # victory text over where the enemy was
    win = text_obj("TxtWin", "勝利", 1.6, B.emissive("txt_win", (1.0, 0.78, 0.3), 8.0),
                   root0 + Vector((0, 0.5, 2.6)), extrude=0.15)
    win.rotation_euler = (math.pi / 2, 0, yaw0)
    for f, s in ((1, 0.001), (34, 0.001), (40, 1.2), (44, 1.0), (60, 1.0), (66, 0.001)):
        key_scale(win, f, s)
    # crowd goes wild
    crowd = [bpy.data.objects[n] for n in ("Crowd", "CrowdEyes")]
    for f in range(1, LENGTH + 1):
        a = 0.0 if f < SH else 0.22 * abs(math.sin((f - SH) * 0.55))
        for o in crowd:
            o.location = (0, 0, a)
            o.keyframe_insert("location", frame=f)
    eyes = M["eye_red"].node_tree.nodes["Emission"].inputs["Strength"]
    for f, v in ((1, 6), (SH, 6), (SH + 4, 14), (60, 10)):
        eyes.default_value = v
        eyes.keyframe_insert("default_value", frame=f)
    # ROUND 2 in the sky: portal turns red, red army appears
    pe = M["portal"].node_tree.nodes["Emission"].inputs
    for f, c, s in ((1, (0.9, 0.25, 0.85), 2.2), (62, (0.9, 0.25, 0.85), 2.2), (74, (1.0, 0.05, 0.08), 6.0)):
        pe["Color"].default_value = (*c, 1)
        pe["Color"].keyframe_insert("default_value", frame=f)
        pe["Strength"].default_value = s
        pe["Strength"].keyframe_insert("default_value", frame=f)
    r2 = text_obj("TxtR2", "第二回戦", 3.4, B.emissive("txt_red", (1.0, 0.15, 0.2), 9.0), (0, 44, 23.5), extrude=0.3)
    r2.rotation_euler = (math.pi / 2, 0, 0)
    for f, s in ((1, 0.001), (68, 0.001), (74, 1.15), (78, 1.0)):
        key_scale(r2, f, s)
    red = B.principled("red_army", (0.55, 0.04, 0.06))
    red_d = B.principled("red_army_d", (0.25, 0.02, 0.04))
    rnd = random.Random(31)
    k = 0
    for row, (z, n, y) in enumerate(((10.5, 9, 40), (14.5, 7, 42), (6.5, 7, 38))):
        for i in range(n):
            x = (i - (n - 1) / 2) * 3.0 + rnd.uniform(-0.4, 0.4)
            g = B.empty("RedFoe_%d" % k, loc=(x, y, z))
            k += 1
            B.box("RF_plat", (1.8, 1.8, 0.4), (0, 0, -0.2), M["float"], g, bevel=0.05)
            B.box("RF_legs", (0.7, 0.4, 0.9), (0, 0, 0.45), red_d, g)
            B.box("RF_body", (0.9, 0.5, 0.8), (0, 0, 1.3), red, g)
            B.box("RF_arms", (1.4, 0.35, 0.25), (0, 0, 1.55), red_d, g)
            B.box("RF_head", (0.55, 0.5, 0.5), (0, 0, 1.98), red, g)
            for ex in (-0.12, 0.12):
                B.box("RF_eye", (0.1, 0.03, 0.06), (ex, -0.26, 2.0), M["eye_red"], g, bevel=0)
            g.scale = (0.001,) * 3
            st = 66 + int(rnd.uniform(0, 14))
            for f, s in ((1, 0.001), (st, 0.001), (st + 5, 1.6), (st + 8, 1.4)):
                key_scale(g, f, s)
            for f in range(st, LENGTH + 1, 4):
                g.location = (x, y, z + 0.25 * math.sin(f * 0.2 + i))
                g.keyframe_insert("location", frame=f)
    rl = B.light("RedLight", "AREA", 0, (1.0, 0.1, 0.15), (0, 30, 18), 20)
    rl.rotation_euler = Vector((0, -1, -0.5)).to_track_quat('-Z', 'Y').to_euler()
    for f, v in ((1, 0), (66, 0), (76, 25000)):
        rl.data.energy = v
        rl.data.keyframe_insert("energy", frame=f)
    # camera + hands
    cp0 = B.cam_pos(F0)
    lag = B.LOOK_LAG(F0)
    tg0 = B.enemy_root_pos(F0 - lag)
    tg0.z = B.LOOK_Z(F0)
    tg0 += Vector(B.LOOK_OFF(F0))
    look = Track([(1, tuple(tg0)), (SH, tuple(tg0 + Vector((0, 0, 0.2))), "smooth"),
                  (SH + 6, tuple(tg0 + Vector((0, 0, 0.5))), "out"),
                  (40, tuple(root0 + Vector((0.4, 0.5, 2.3))), "smooth"),    # 勝利
                  (58, tuple(root0 + Vector((0.4, 0.5, 2.5)))),
                  (74, (0, 44, 17.0), "smoother"),                        # ROUND 2 / red army
                  (110, (0, 44, 16.0))])
    cpos = Track([(1, tuple(cp0)), (SH, tuple(cp0)), (SH + 5, tuple(cp0 + Vector((0, -0.25, -0.05)))),
                  (40, tuple(cp0 + Vector((0, -0.1, 0.05))), "smooth"), (110, tuple(cp0 + Vector((0, -0.6, 0.0))), "smooth")])
    roll = Track([(1, B.CAM_ROLL(F0)), (40, 0.0), (74, -0.05, "smooth"), (110, 0.0)])
    RHe, LHe = B.RH(F0), B.LH(F0)
    rh = Track([(1, RHe), (SH, RHe), (SH + 4, (0.22, -0.36, -0.50, 0.2, 0.3, -0.9), "out"),   # guard from blast
                (36, (0.21, 0.04, -0.46, 0.18, 1.0, 0.1), "smooth"),                      # raise sword (victory)
                (42, (0.20, 0.08, -0.46, 0.15, 1.0, 0.05), "out"),
                (60, (0.20, 0.07, -0.46, 0.15, 1.0, 0.05)),
                (72, (0.17, -0.38, -0.50, 0.05, 0.6, -0.8), "smooth"),                    # lower: something's coming
                (110, (0.18, -0.36, -0.52, 0.10, 0.65, -0.75))])
    lh = Track([(1, LHe), (SH, LHe), (SH + 4, (-0.10, -0.22, -0.40), "out"),
                (40, (-0.17, -0.40, -0.42), "smooth"), (110, (-0.17, -0.40, -0.42))])
    blade = M["blade"].node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"]
    for f, v in ((1, 0), (34, 0), (42, 5), (60, 1), (70, 0)):
        blade.default_value = v
        blade.keyframe_insert("default_value", frame=f)
    for f in range(1, LENGTH + 1):
        s, sr = shake(f, SH + 1, 0.05, 4)
        s2, sr2 = shake(f, 74, 0.03, 8)
        cp = Vector(cpos(f)) + s + s2 + Vector((0, 0, 0.008 * math.sin((f + F0) * 0.25)))
        key_player(P, f, cp, Vector(look(f)), roll(f) + sr + sr2, rh(f), lh(f), prevq)
    # fade to black + title card
    bm_ = fade_material("FadeBlack", (0, 0, 0))
    cam_overlay(cam, "FadePlane", bm_, -0.05)
    for f, v in ((1, 0), (88, 0), (100, 1.0)):
        key_fade(bm_, f, v)
    tmat = B.emissive("title_m", (1.0, 0.5, 0.9), 4.0)
    title = text_obj("Title", "異世界デスゲーム", 0.0034, tmat, (0, 0.004, -0.04), cam, extrude=0.0)
    sub = text_obj("TitleSub", "― 第一話「転生、そして開幕」 ―", 0.0017, B.emissive("title_s", (0.9, 0.85, 1.0), 3.0),
                   (0, -0.0025, -0.04), cam, extrude=0.0)
    nxt = text_obj("TitleNext", "To Be Continued…", 0.0015, B.emissive("title_n", (1.0, 0.75, 0.3), 3.0),
                   (0, -0.0065, -0.04), cam, extrude=0.0)
    for o, d in ((title, 0), (sub, 4), (nxt, 8)):
        o.visible_shadow = False
        for f, s in ((1, 0.001), (100 + d, 0.001), (105 + d, 1.08), (108 + d, 1.0)):
            key_scale(o, f, s)

# ------------------------------------------------------------------ main
B.setup_world_render()
scene.frame_end = LENGTH
{"A1": shot_A1, "A2": shot_A2, "B": shot_B, "C": shot_C, "D": shot_D}[SHOT]()
if SHOT in ("A1", "A2"):
    scene.render.use_motion_blur = True
scene.frame_set(1)
if not B.NO_SAVE:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, "isekai_shot_%s.blend" % SHOT))
os.makedirs(FRAME_DIR, exist_ok=True)
frames = []
if B.FRAMES_ARG and B.FRAMES_ARG is not True:
    frames = [int(x) for x in B.FRAMES_ARG.split(",")]
elif B.DO_ANIM:
    frames = list(range(1, LENGTH + 1))
import time
for f in frames:
    t0 = time.time()
    scene.frame_set(f)
    scene.render.filepath = os.path.join(FRAME_DIR, "%04d.png" % f)
    bpy.ops.render.render(write_still=True)
    print("frame %d  %.1fs" % (f, time.time() - t0), flush=True)
