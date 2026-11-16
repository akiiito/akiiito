"""
create_ep6.py  ―  異世界デスゲーム 最終話「二人なら」（一人称・720x1280・24fps・696f + タイトル静止）

  0s   眼のレーザーを二刀で弾く → 少女の『足場』で空への階段
  2s   歴代の敵が次々降ってくる中を二刀流で駆け上がる（COMBO）→ 巨大ボスを十字斬り
  8s   眼がまぶたを閉じる（硬い）→ カウントダウン → 少女が足場でこじ開ける
  12s  極太レーザーを二刀で割りながら前進 → 瞳に突き刺す
  16s  眼の奥：ゲームの核。「壊せばお前も消える」→「二人なら、いける」→ 二人で斬る
  21s  白 → 青空と草原。ゲームの外。生存者 2名 →「スキル引き継ぎ：全部」→ 完

  python create_ep6.py --anim --samples 24
"""
import os, sys, math, random
os.environ["BATTLE_AS_LIBRARY"] = "1"
os.environ["ISEKAI_AS_LIBRARY"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
import create_battle as B
import create_isekai_short as S
import create_ep2 as E2
import create_ep4 as E4

scene, M = B.scene, B.M
Track, EASE, lerp, clamp = B.Track, B.EASE, B.lerp, B.clamp
STANCE, ANK = B.STANCE, B.ANK
N = 696
FRAME_DIR = B.arg("--frame-dir", os.path.join(HERE, "frames_E6"))
random.seed(606)

LZ0 = 8
STAIR0, RUN0, RUN1 = 28, 44, 200
KILLS = [60, 70, 80, 90, 100, 108]
BOSS_IN, BOSS_X = 120, 152
LID, BOUNCE, WEDGE, MEGA, STAB = 198, 226, 262, 286, 372
VOID, TURN, VDASH, CORE_X = 380, 420, 452, 464
FIELD, SIT0, SIT1, SURV, SKILL, FADE0 = 508, 530, 566, 600, 620, 666
EYEPT = Vector((0, 45.2, 17.0))
V0 = Vector((-500, 0, 0))
F0 = Vector((500, 0, 0))
COREP = V0 + Vector((0, 5.0, 1.8))

def stair_top(y):
    return 0.0 if y < 13.0 else 0.5 + clamp((y - 13.0) / 26.0) * 14.5

def cam_path(f):
    if f < VOID:
        if f <= RUN0:
            return Vector((0.9, 11.0, 1.62))
        if f <= RUN1:
            t = (f - RUN0) / (RUN1 - RUN0)
            y = lerp(11.0, 34.0, t)
            return Vector((lerp(0.9, 0.35, clamp(t * 4)), y, stair_top(y) + 1.62 - 0.04 * abs(math.sin(f * 0.6))))
        t = EASE["smooth"](clamp((f - (MEGA + 14)) / (STAB - 10 - MEGA - 14)))
        u = EASE["in"](clamp((f - (STAB - 10)) / 10))
        y = lerp(34.0, 39.6, t)
        return Vector((lerp(0.35, 0.0, t), y + 4.4 * u, lerp(stair_top(y) + 1.62, 17.1, u) + 0.9 * math.sin(math.pi * u)))
    if f < FIELD:
        t = EASE["in"](clamp((f - VDASH) / (CORE_X - VDASH)))
        return V0 + Vector((0, 2.6 * t, 1.62))
    t = EASE["smooth"](clamp((f - SIT0) / (SIT1 - SIT0)))
    return F0 + Vector((0, 0.5 * t, lerp(0.45, 1.05, t)))

def girl_state(f):
    """(pos, yaw, run weight, distance)"""
    if f < VOID:
        if f <= RUN0:
            return Vector((-0.25, 11.3, 0)), math.pi, 0.0, 0.0
        if f <= RUN1:
            t = (f - RUN0) / (RUN1 - RUN0)
            y = lerp(11.3, 34.7, EASE["out"](t) * 0.25 + t * 0.75)
            return Vector((lerp(-0.25, -0.95, clamp(t * 5)), y, stair_top(y))), math.pi, min(1.0, (f - RUN0) / 3, (RUN1 - f) / 3), 30 * t
        return Vector((-1.25, 34.5, stair_top(34.5))), math.pi, 0.0, 0.0
    if f < FIELD:
        t = EASE["in"](clamp((f - VDASH) / (CORE_X - VDASH)))
        yaw = math.pi - 2.5 * EASE["smooth"](clamp((f - TURN) / 10)) * (1 - EASE["smooth"](clamp((f - (VDASH - 8)) / 8)))
        return V0 + Vector((-0.95, 1.6 + 2.2 * t, 0)), yaw, min(clamp((f - VDASH) / 3), clamp((CORE_X - f) / 3)), 2.2 * t
    return F0 + Vector((-0.6, 2.7, 0)), -0.2, 0.0, 0.0

def build():
    flames, floats = B.build_arena()
    P = B.build_player()
    S.env_life(flames, floats, N)
    cam = P["cam"]
    pe = M["portal"].node_tree.nodes["Emission"]
    pe.inputs["Color"].default_value = (1.0, 0.10, 0.12, 1)
    pe.inputs["Strength"].default_value = 0.3
    for n in ("Crowd", "CrowdEyes"):
        bpy.data.objects[n].hide_render = True

    # ---------------- world: arena violet -> void black -> open blue sky
    ramp = scene.world.node_tree.nodes["Color Ramp"].color_ramp if "Color Ramp" in scene.world.node_tree.nodes else \
        [n for n in scene.world.node_tree.nodes if n.type == 'VALTORGB'][0].color_ramp
    for f, c0, c1 in ((1, (0.22, 0.05, 0.25), (0.02, 0.01, 0.05)), (VOID - 1, (0.22, 0.05, 0.25), (0.02, 0.01, 0.05)),
                      (VOID, (0.03, 0.0, 0.02), (0.0, 0.0, 0.0)), (FIELD - 1, (0.03, 0.0, 0.02), (0.0, 0.0, 0.0)),
                      (FIELD, (0.75, 0.90, 1.0), (0.16, 0.42, 0.95))):
        for el, c in zip(ramp.elements, (c0, c1)):
            el.color = (*c, 1)
            el.keyframe_insert("color", frame=f)
    sun = bpy.data.objects["Sun"]
    for f, e, c in ((1, 2.2, (0.85, 0.78, 1.0)), (VOID - 1, 2.2, (0.85, 0.78, 1.0)), (VOID, 0.4, (1.0, 0.5, 0.5)), (FIELD - 1, 0.4, (1.0, 0.5, 0.5)),
                    (FIELD, 4.5, (1.0, 0.96, 0.86))):
        sun.data.energy, sun.data.color = e, c
        sun.data.keyframe_insert("energy", frame=f)
        sun.data.keyframe_insert("color", frame=f)

    # ---------------- sky text + the eye and its lids
    rmat = B.emissive("txt_rule", (1.0, 0.10, 0.18), 9.0)
    o = S.text_obj("T_true", "真・最終回戦", 3.4, rmat, (0, 44, 22.4), extrude=0.3)
    o.rotation_euler = (math.pi / 2, 0, 0)
    eye = B.empty("Eye", None, tuple(EYEPT))
    B.box("EyeWhite", (10.5, 0.4, 5.4), (0, 0, 0), B.emissive("eye_w", (0.95, 0.9, 0.95), 1.6), eye, bevel=0)
    iris_m = B.emissive("eye_iris", (1.0, 0.08, 0.10), 10.0)
    B.box("EyeIris", (3.4, 0.5, 3.4), (0, -0.2, 0), iris_m, eye, bevel=0)
    B.box("EyePupil", (1.3, 0.6, 1.5), (0, -0.4, 0), B.principled("eye_p", (0, 0, 0)), eye, bevel=0)
    ist = iris_m.node_tree.nodes["Emission"].inputs["Strength"]
    for f, v in ((1, 10), (LZ0 - 4, 40), (LZ0 + 12, 10), (BOUNCE + 6, 10), (MEGA - 2, 60), (STAB, 60)):
        ist.default_value = v
        ist.keyframe_insert("default_value", frame=f)
    lid_m = B.principled("lid", (0.09, 0.03, 0.12))
    lidT = Track([(1, 4.4), (LID, 4.4), (LID + 6, 1.42, "in"), (WEDGE, 1.42), (WEDGE + 6, 2.0, "out"), (WEDGE + 14, 2.5, "smooth"), (MEGA - 4, 4.4, "out"), (N, 4.4)])
    lids = [B.box("Lid%d" % s, (11.2, 0.7, 2.9), (0, 0, 0), lid_m, None, (0, 44.7, 17.0), bevel=0.05) for s in (0, 1)]
    for f in range(1, VOID):
        for s, ob in zip((1, -1), lids):
            B.key_loc(ob, f, (0, 44.7, 17.0 + s * lidT(f)))
    slab_m = B.principled("slab", (0.30, 0.45, 0.95), emit=(0.2, 0.5, 1.0), strength=0.6)
    for k, x in enumerate((-3.6, 3.6)):
        ob = B.box("Wedge%d" % k, (0.7, 0.7, 5.0), (0, 0, 0), slab_m, None, (x, 44.2, 17.0), bevel=0.04)
        for f, s in ((1, 0.001), (WEDGE, 0.001), (WEDGE + 4, 0.45), (WEDGE + 14, 1.0)):
            S.key_scale(ob, f, (1, 1, s))
    for o_ in [eye] + lids:
        pass
    # stairway + bridge
    for k in range(16):
        y = 14 + 2 * k
        top = stair_top(min(y, 39.0)) if k < 14 else 15.0
        ob = B.box("Slab_%d" % k, (3.3, 1.9, 0.4), (0, 0, 0), slab_m, None, (-0.2, y, top - 0.2), bevel=0.04)
        f0 = STAIR0 + 2 + k * 2 if k < 14 else WEDGE + 2 + (k - 14) * 4
        for f, s in ((1, 0.001), (f0, 0.001), (f0 + 3, 1.2), (f0 + 5, 1.0)):
            S.key_scale(ob, f, s)

    # ---------------- lasers
    def beam(name, a, b_, f0, f1, w):
        for f in range(f0, f1):
            k = 0.7 + 0.3 * random.Random(f).random()
            bc, bg = bmesh.new(), bmesh.new()
            B.bm_beam(bc, Vector(a), Vector(b_), w * k)
            B.bm_beam(bg, Vector(a), Vector(b_), w * 2.6 * k)
            for bm_, m in ((bc, "rbolt_core"), (bg, "rbolt_glow")):
                ob = B.mesh_obj("%s_%d" % (name, f), bm_, M[m])
                ob.visible_shadow = False
                B.vis_only(ob, [f])
    HITP = Vector((0.9, 11.75, 1.62))
    beam("Lz1", EYEPT + Vector((0, -0.6, 0)), HITP, LZ0, LZ0 + 12, 0.22)
    beam("Lz1b", HITP, Vector((-13, 16, 0.2)), LZ0, LZ0 + 12, 0.14)
    S.dust_ring("LzSpark", LZ0, HITP, 10, 1.4, 5, size=0.08, mat=M["spark"])
    rnd = random.Random(21)
    rain = []
    for k in range(11):
        f0 = 56 + k * 13
        y = cam_path(min(f0 + 4, RUN1)).y + rnd.uniform(4.0, 7.0)
        x = rnd.choice((-1, 1)) * rnd.uniform(2.6, 3.8)
        beam("Rain%d" % k, EYEPT + Vector((0, -0.6, 0)), Vector((x, y, 0)), f0, f0 + 5, 0.2)
        rain.append(f0)
    # the mega beam, glued to the camera: main shaft into the crossed blades, split left/right
    def cam_beam(name, size, loc, rot, mat):
        ob = B.box(name, size, (0, 0, 0), M[mat], cam, loc, bevel=0)
        ob.rotation_euler = rot
        ob.visible_shadow = False
        for f in range(MEGA - 1, STAB + 2):
            on = MEGA <= f < STAB
            k = 0.85 + 0.3 * random.Random(f * 3 + len(name)).random()
            S.key_scale(ob, f, (k, k, 1) if on else 0.001)
        S.key_scale(ob, 1, 0.001)
    cam_beam("MegaCore", (0.55, 0.55, 14.0), (0, 0.03, -0.95 - 7.0), (0, 0, 0), "rbolt_core")
    cam_beam("MegaGlow", (1.25, 1.25, 14.0), (0, 0.03, -1.05 - 7.0), (0, 0, 0), "rbolt_glow")
    for sx in (-1, 1):
        cam_beam("SplitCore%d" % sx, (0.34, 0.34, 9.0), (sx * 4.4, 0.03 + 0.5, -0.4), (0.11, sx * 1.42, 0), "rbolt_core")
        cam_beam("SplitGlow%d" % sx, (0.8, 0.8, 9.0), (sx * 4.5, 0.03 + 0.5, -0.4), (0.11, sx * 1.42, 0), "rbolt_glow")

    # ---------------- enemies on the stairs (all the old ones) + the boss
    BLUE = {k: M[k] for k in ("e_blue", "e_dark", "e_light", "e_eye")}
    kinds = [BLUE, E2.RED, E4.MOB, E2.RED, BLUE, E4.MOB]
    old = E2.RED
    fr_mats = []
    for i, kf in enumerate(KILLS):
        E2.RED = kinds[i]
        e = E2.En(i, (0, 0))
        E2.RED = old
        c = cam_path(kf)
        pos = Vector((c.x + (0.45 if i % 2 == 0 else -0.45), c.y + 1.75, 0))
        pos.z = stair_top(pos.y)
        tl = B.PoseTimeline(B.E_DEF, [(1, dict(E2.CROUCH), "smooth"), (kf - 8, dict(E2.CROUCH), "smooth"), (kf - 2, dict(E2.WIND), "out"), (N, dict(), "smooth")])
        for f in range(kf - 18, kf + 2):
            alive = f < kf
            S.key_scale(e.J["root"], f, B.E_SCALE if alive else 0.001)
            z = pos.z + 7.0 * (1 - EASE["in"](clamp((f - (kf - 17)) / 9)))
            S.key_enemy(e.J, f, tl(f), (pos.x, pos.y, z), 0.0, 0.0, run_phase=0.0)
        S.key_scale(e.J["root"], 1, 0.001)
        E2.frag_burst("KF%d" % i, kf, pos + Vector((0, 0, 1.1)), 18, 5.5, 0.2, 70 + i, [kinds[i]["e_blue"], kinds[i]["e_dark"], kinds[i]["e_light"]], life=24)
    boss = E2.En(9, (0, 0))
    BS = 2.3
    bc = cam_path(BOSS_X)
    bpos = Vector((0.0, bc.y + 3.4, stair_top(bc.y + 3.4)))
    btl = B.PoseTimeline(B.E_DEF, [(1, dict(E2.CROUCH), "smooth"), (BOSS_IN + 8, dict(E2.CROUCH), "smooth"), (BOSS_IN + 18, dict(E4.MENACE), "smooth"),
                                   (BOSS_X - 6, dict(E2.WIND), "smooth"), (N, dict(), "smooth")])
    for f in range(BOSS_IN - 2, BOSS_X + 2):
        S.key_scale(boss.J["root"], f, B.E_SCALE * BS if BOSS_IN <= f < BOSS_X else 0.001)
        z = bpos.z + 14.0 * (1 - EASE["in"](clamp((f - BOSS_IN) / 8)))
        S.key_enemy(boss.J, f, btl(f), (bpos.x, bpos.y, z), 0.0, 0.0, run_phase=0.0)
    S.key_scale(boss.J["root"], 1, 0.001)
    E2.frag_burst("BossFrag", BOSS_X, bpos + Vector((0, 0, 2.4)), 70, 9.0, 0.42, 99, [E2.RED["e_blue"], E2.RED["e_dark"], E2.RED["e_light"]], life=34)

    # ---------------- the girl
    G = E4.Human("G", B.principled("g_cloth", (0.10, 0.25, 0.55)), B.principled("g_dark", (0.05, 0.06, 0.16)), (0.07, 0.05, 0.10), 0.86,
                 B.principled("g_blade", (0.8, 0.9, 1.0), emit=(0.5, 0.9, 1.0), strength=3.0))
    for f, s in ((1, 1.0), (FIELD - 1, 1.0), (FIELD, 0.001)):
        S.key_scale(G.blade, f, s)
    STAND = dict(B.E_DEF, shRx=0.05, shLx=0.05, elR=-0.25, elL=-0.25)
    GRD = dict(STANCE, shRx=-1.3, shRy=0.3, elR=-0.5, np=-0.1)
    UPH = dict(STAND, shRx=-2.9, shRy=0.2, elR=-0.1, shLx=-2.9, shLy=-0.2, elL=-0.1, np=-0.3, tp=-0.1)
    GW = dict(STANCE, shRx=-2.6, shRy=0.2, elR=-0.6, tt=-0.4)
    GS = dict(STANCE, shRx=-0.8, shRy=-0.3, elR=-0.1, tt=0.45, tp=0.3)
    KNEEL = dict(E2.CROUCH, hz=-0.52, tp=0.2, np=-0.05, shRx=-0.2, shRy=0.1, elR=-0.3, shLx=-0.2, shLy=-0.1, elL=-0.3)
    gtl = B.PoseTimeline(B.E_DEF, [
        (1, GRD, "smooth"), (STAIR0 - 6, GRD, "smooth"), (STAIR0 + 2, UPH, "out"), (RUN0 - 2, dict(), "smooth"), (RUN0 + 2, GRD, "smooth"),
        (RUN1, GRD, "smooth"), (WEDGE - 8, GRD, "smooth"), (WEDGE, UPH, "out"), (MEGA, dict(), "smooth"), (VOID - 1, GRD, "smooth"),
        (VOID, GRD, "lin"), (TURN + 8, dict(STAND, np=0.0, shLx=-0.9, shLy=0.3, elL=-1.2), "smooth"), (VDASH - 6, dict(), "smooth"), (VDASH, GRD, "smooth"),
        (CORE_X - 5, GW, "smooth"), (CORE_X, GS, "in"), (FIELD - 1, dict(), "lin"), (FIELD, KNEEL, "lin"), (SIT1, KNEEL, "smooth"),
        (SIT1 + 14, dict(KNEEL, shLx=-1.3, shLy=0.2, elL=-0.3, np=-0.1), "smooth"), (SKILL, dict(), "smooth"),
        (SKILL + 14, dict(KNEEL, shLx=-1.5, shLy=0.4, elL=-2.2, shRx=-1.5, shRy=-0.4, elR=-2.2, np=-0.25), "smooth"), (N, dict(), "smooth")])
    for f in range(1, N + 1):
        p, yaw, w, d = girl_state(f)
        pose = gtl(f)
        for k, v in E2.RUNP.items():
            pose[k] = lerp(pose[k], v, w)
        pose["run"] = w
        pose["hz"] += 0.006 * math.sin(f * 0.2)
        if f > SKILL + 14:
            pose["tp"] += 0.06 * math.sin(f * 0.9)                # laughing
        S.key_enemy(G.J, f, pose, tuple(p), 0.0, yaw, run_phase=d / 2.0)

    # ---------------- the void and the core
    core_m = B.emissive("core", (1.0, 0.05, 0.08), 12.0)
    core = B.empty("Core", None, tuple(COREP))
    B.box("CoreIn", (1.3, 1.3, 1.3), (0, 0, 0), core_m, core, bevel=0)
    bm = bmesh.new()
    for ax in range(3):
        for s1 in (-1, 1):
            for s2 in (-1, 1):
                size, off = [0.16, 0.16, 0.16], [0.0, 0.0, 0.0]
                size[ax] = 1.9
                off[(ax + 1) % 3], off[(ax + 2) % 3] = s1 * 0.87, s2 * 0.87
                B.bm_box(bm, tuple(size), tuple(off))
    B.mesh_obj("CoreCage", bm, B.principled("core_cage", (0.02, 0.02, 0.03)), core, bevel=0.01)
    for f in range(VOID - 1, CORE_X + 2):
        core.rotation_euler = (0.03 * f, 0.021 * f, 0.045 * f)
        core.keyframe_insert("rotation_euler", frame=f)
        pulse = 1.0 + 0.06 * math.sin(f * 0.7)
        S.key_scale(core, f, pulse if VOID <= f < CORE_X else 0.001)
    S.key_scale(core, 1, 0.001)
    E2.frag_burst("CoreFrag", CORE_X, COREP, 70, 9.0, 0.3, 123, [core_m, M["spark"]], life=40)
    B.box("VoidFloor", (40, 40, 0.2), (0, 0, -0.1), B.principled("void_floor", (0.03, 0.02, 0.04)), None, tuple(V0), bevel=0)
    rnd = random.Random(8)
    bm = bmesh.new()
    for _ in range(90):
        s = rnd.uniform(0.12, 0.5)
        B.bm_box(bm, (s, s, s), (rnd.uniform(-9, 9), rnd.uniform(2, 22), rnd.uniform(0.3, 9)), Euler((rnd.random() * 3, rnd.random() * 3, 0)).to_matrix())
    B.mesh_obj("VoidBits", bm, B.emissive("void_bits", (1.0, 0.1, 0.15), 3.0), None, tuple(V0), bevel=0)
    CL_ = B.light("CoreL", "POINT", 0, (1.0, 0.15, 0.15), tuple(COREP + Vector((0, -1.6, 0.6))), 0.6)
    for f, v in ((1, 0), (VOID - 1, 0), (VOID, 2500), (CORE_X, 2500), (CORE_X + 2, 20000), (FIELD - 1, 20000), (FIELD, 0)):
        CL_.data.energy = v
        CL_.data.keyframe_insert("energy", frame=f)

    # ---------------- the field outside the game
    grass = [B.principled("grass%d" % i, c) for i, c in enumerate(((0.16, 0.50, 0.14), (0.20, 0.58, 0.16), (0.13, 0.44, 0.13)))]
    rnd = random.Random(31)
    bms = [bmesh.new() for _ in grass]
    for i in range(-14, 15):
        for j in range(-6, 30):
            B.bm_box(bms[rnd.randrange(3)], (1.96, 1.96, 0.5), (i * 2.0, j * 2.0, -0.25 + rnd.uniform(-0.04, 0.0)
                                                                + (0.0 if j < 8 else 0.25 * math.sin(i * 0.5) * (j - 8) / 6.0)))
    for bm, m in zip(bms, grass):
        B.mesh_obj("Grass_" + m.name, bm, m, None, tuple(F0), bevel=0.03)
    bm = bmesh.new()
    for _ in range(260):
        x, y = rnd.uniform(-9, 9), rnd.uniform(0.8, 22)
        h = rnd.uniform(0.12, 0.3)
        B.bm_box(bm, (0.07, 0.07, h), (x, y, h / 2), Matrix.Rotation(rnd.random() * 3, 3, 'Z'))
    B.mesh_obj("Tufts", bm, B.principled("tuft", (0.30, 0.70, 0.20)), None, tuple(F0), bevel=0)
    bm_t, bm_l, bm_f = bmesh.new(), bmesh.new(), bmesh.new()
    for x, y, s in ((-5.5, 12, 1.3), (5.0, 15, 1.6), (-8.5, 22, 1.8), (8.5, 26, 1.5), (2.8, 30, 2.0), (-3.5, 34, 1.7)):
        B.bm_box(bm_t, (0.5 * s, 0.5 * s, 2.2 * s), (x, y, 1.1 * s))
        B.bm_box(bm_l, (2.4 * s, 2.4 * s, 1.5 * s), (x, y, 2.7 * s))
        B.bm_box(bm_l, (1.5 * s, 1.5 * s, 1.0 * s), (x, y, 3.8 * s))
    for _ in range(40):
        x, y = rnd.uniform(-7, 7), rnd.uniform(1.5, 16)
        B.bm_box(bm_f, (0.12, 0.12, 0.12), (x, y, 0.3))
    B.mesh_obj("Trunks", bm_t, B.principled("trunk", (0.30, 0.18, 0.10)), None, tuple(F0), bevel=0.04)
    B.mesh_obj("Leaves", bm_l, B.principled("leaf", (0.12, 0.42, 0.14)), None, tuple(F0), bevel=0.06)
    B.mesh_obj("Flowers", bm_f, B.principled("flower", (1.0, 0.85, 0.3), emit=(1.0, 0.8, 0.3), strength=0.4), None, tuple(F0), bevel=0)
    bm = bmesh.new()
    for x, y, z, s in ((-9, 60, 24, 5), (10, 70, 30, 6), (-2, 85, 38, 7), (18, 55, 20, 4), (-20, 75, 28, 5), (4, 30, 34, 4), (-6, 22, 38, 3.5)):
        B.bm_box(bm, (2.6 * s, 1.4 * s, 0.7 * s), (x, y, z))
        B.bm_box(bm, (1.5 * s, 1.2 * s, 0.6 * s), (x + 0.5 * s, y, z + 0.5 * s))
    clouds = B.mesh_obj("Clouds", bm, B.principled("cloud", (1, 1, 1), emit=(1, 1, 1), strength=0.5), None, tuple(F0), bevel=0.3)
    clouds.visible_shadow = False
    for f, x in ((FIELD, F0.x), (N, F0.x + 2.5)):
        B.key_loc(clouds, f, (x, 0, 0))
    wmat = B.emissive("txt_surv", (1.0, 0.80, 0.15), 3.0)
    o = S.text_obj("T_surv", "生存者　2名", 3.3, wmat, tuple(F0 + Vector((0, 30, 9.6))), extrude=0.25)
    o.rotation_euler = (math.pi / 2, 0, 0)
    for f, s in ((1, 0.001), (SURV, 0.001), (SURV + 6, 1.12), (SURV + 10, 1.0)):
        S.key_scale(o, f, s)
    FL = B.light("FieldFill", "POINT", 0, (1.0, 0.95, 0.85), tuple(F0 + Vector((1.5, -0.5, 2.5))), 1.0)
    for f, v in ((1, 0), (FIELD - 1, 0), (FIELD, 250)):
        FL.data.energy = v
        FL.data.keyframe_insert("energy", frame=f)

    # ---------------- second sword (left hand), keyed in camera space
    relic_m = B.principled("relic", (0.78, 0.80, 0.92), emit=(1.0, 0.3, 0.2), strength=5.0)
    held = B.empty("Held", cam, (-0.20, -0.30, -0.52))
    B.box("Held_b", (0.07, 0.95, 0.02), (0, 0.6, 0), relic_m, held, bevel=0.006)
    B.box("Held_g", (0.24, 0.045, 0.06), (0, 0.10, 0), M["guard"], held, bevel=0.008)
    B.box("Held_h", (0.035, 0.20, 0.035), (0, -0.02, 0), M["grip"], held, bevel=0.005)
    REST = ((-0.20, -0.30, -0.52), (-0.45, 0.0, 0.18))
    XB = ((-0.20, -0.20, -0.50), (-0.25, 0.0, -0.72))            # crossed block (blade leaning right)
    LW = ((-0.26, -0.18, -0.42), (0.3, 0.0, 0.9))                # wind up (blade out to the left)
    LS = ((-0.06, -0.22, -0.60), (-1.25, 0.0, -0.55))            # strike (blade forward, swept right)
    hk = [(1, REST, "smooth"), (LZ0 - 3, XB, "out"), (LZ0 + 14, XB, "smooth"), (RUN0, REST, "smooth")]
    for i, kf in enumerate(KILLS):
        if i % 2 == 1:
            hk += [(kf - 5, LW, "smooth"), (kf, LS, "in"), (kf + 4, LS, "lin")]
    hk += [(KILLS[-1] + 12, REST, "smooth"), (BOSS_X - 8, LW, "smooth"), (BOSS_X, LS, "in"), (BOSS_X + 8, LS, "lin"), (BOSS_X + 20, REST, "smooth"),
           (BOUNCE + 20, REST, "smooth"), (MEGA - 4, XB, "out"), (STAB - 7, XB, "smooth"), (STAB, ((-0.10, -0.16, -0.66), (-1.5, 0.0, -0.12)), "in"),
           (VOID - 1, ((-0.10, -0.16, -0.66), (-1.5, 0.0, -0.12)), "lin"), (VOID, REST, "lin"), (CORE_X - 8, LW, "smooth"), (CORE_X, LS, "in"), (N, LS, "lin")]
    hT = Track([(f, v[0] + v[1], e) for f, v, e in hk])
    for f in range(1, FIELD + 1):
        v = hT(f)
        B.key_loc(held, f, v[:3])
        held.rotation_euler = v[3:]
        held.keyframe_insert("rotation_euler", frame=f)
        S.key_scale(held, f, 1.0 if f < FIELD else 0.001)
    sw = P["sword"]
    for f, s in ((1, 1.0), (FIELD - 1, 1.0), (FIELD, 0.001)):
        S.key_scale(sw, f, s)

    # ---------------- camera + right hand
    yawT = Track([(1, 0), (RUN0, 0), (BOSS_X, 0), (LID, 0), (VOID - 1, 0), (VOID, 0), (TURN, 0), (TURN + 8, -24, "smooth"), (VDASH - 8, -24),
                  (VDASH, 0, "smooth"), (FIELD - 1, 0), (FIELD, 0), (SIT1, -14, "smooth"), (SURV - 6, -14), (SURV + 4, 0, "smooth"), (SKILL - 4, 0),
                  (SKILL + 6, 6, "smooth"), (SKILL + 26, -12, "smooth"), (N, -12)])
    pitT = Track([(1, 8), (LZ0 + 12, 8), (STAIR0 + 6, 3, "smooth"), (RUN0, 6), (RUN0 + 30, 10, "smooth"), (BOSS_IN, 10), (BOSS_IN + 10, 20, "smooth"),
                  (BOSS_X, 16), (BOSS_X + 14, 12, "smooth"), (RUN1, 12), (LID + 6, 5, "smooth"), (MEGA, 5), (STAB, 2), (VOID - 1, 2), (VOID, 3),
                  (FIELD - 1, 3), (FIELD, 78), (SIT0, 78), (SIT1, 0, "smooth"), (SURV - 6, 0), (SURV + 4, 14, "smooth"), (SKILL - 6, 14),
                  (SKILL + 4, -22, "smooth"), (SKILL + 18, -22), (SKILL + 28, -2, "smooth"), (N, -2)])
    rollT = Track([(1, 0), (LZ0, 0), (LZ0 + 3, 0.06, "out"), (LZ0 + 14, 0, "smooth"), (BOSS_X, 0), (BOSS_X + 4, -0.08, "out"), (BOSS_X + 16, 0, "smooth"),
                   (FIELD - 1, 0), (FIELD, 0.25), (SIT1, 0, "smooth"), (N, 0)])
    RH1, LH1 = B.RH(1), B.LH(1)
    LOW = (0.19, -0.44, -0.50, 0.25, 0.3, -0.92)
    WU = (0.20, -0.20, -0.36, 0.3, 0.6, 0.5)
    SL = (0.08, -0.10, -0.62, 0.0, 0.25, -1.0)
    RXB = (0.18, -0.22, -0.50, -0.62, 0.78, -0.05)               # right blade leaning left: the other half of the X
    rk = [(1, RH1), (LZ0 - 3, RXB, "out"), (LZ0 + 14, RXB), (RUN0, RH1, "smooth")]
    for i, kf in enumerate(KILLS):
        if i % 2 == 0:
            rk += [(kf - 5, WU, "smooth"), (kf, SL, "in"), (kf + 4, SL)]
    rk += [(KILLS[-1] + 12, RH1, "smooth"), (BOSS_X - 8, WU, "smooth"), (BOSS_X, SL, "in"), (BOSS_X + 8, SL), (BOSS_X + 20, RH1, "smooth"),
           (BOUNCE - 8, WU, "smooth"), (BOUNCE, SL, "in"), (BOUNCE + 4, WU, "out"), (BOUNCE + 20, RH1, "smooth"), (MEGA - 4, RXB, "out"), (STAB - 7, RXB),
           (STAB, (0.10, -0.14, -0.66, 0.0, 0.1, -1.0), "in"), (VOID - 1, (0.10, -0.14, -0.66, 0.0, 0.1, -1.0)), (VOID, RH1), (CORE_X - 8, WU, "smooth"),
           (CORE_X, SL, "in"), (FIELD - 1, SL), (FIELD, (0.22, -0.50, -0.30, 0.3, 0.3, -0.9)), (SKILL - 8, (0.22, -0.50, -0.30, 0.3, 0.3, -0.9)),
           (SKILL + 4, (0.12, -0.20, -0.48, 0.0, 0.9, -0.4), "smooth"), (N, (0.12, -0.20, -0.48, 0.0, 0.9, -0.4))]
    rh = Track(rk)
    lh = Track([(1, (-0.20, -0.33, -0.52)), (FIELD - 1, (-0.20, -0.33, -0.52)), (FIELD, (-0.22, -0.50, -0.30)), (SKILL - 8, (-0.22, -0.50, -0.30)),
                (SKILL + 4, (-0.12, -0.22, -0.48), "smooth"), (N, (-0.12, -0.22, -0.48))])
    shakes = [(LZ0, 0.09, 6)] + [(kf, 0.035, 4) for kf in KILLS] + [(BOSS_IN + 8, 0.09, 6), (BOSS_X, 0.10, 6), (LID + 6, 0.05, 5), (BOUNCE, 0.07, 5),
              (WEDGE, 0.04, 6), (MEGA, 0.10, 8), (STAB, 0.12, 6), (CORE_X, 0.12, 8)] + [(f0, 0.025, 3) for f0 in rain]
    prevq = {}
    for f in range(1, N + 1):
        sv, sr = Vector((0, 0, 0)), 0.0
        for f0, amp, dc in shakes:
            a, r = S.shake(f, f0, amp, dc)
            sv += a
            sr += r
        if MEGA < f < STAB:
            sv += Vector((0.012 * math.sin(f * 2.9), 0, 0.012 * math.sin(f * 3.7)))
        cp = cam_path(f) + sv + Vector((0, 0, 0.006 * math.sin(f * 0.25)))
        ya, pi_ = math.radians(yawT(f)), math.radians(pitT(f))
        d = Vector((math.sin(ya) * math.cos(pi_), math.cos(ya) * math.cos(pi_), math.sin(pi_)))
        if LID <= f < VOID:
            w = EASE["smooth"](clamp((f - LID) / 8))
            d = d.lerp((EYEPT - cp).normalized(), w).normalized()
        r_ = list(rh(f))
        l_ = list(lh(f)) if f >= FIELD else [hT(f)[0], hT(f)[1] - 0.03, hT(f)[2]]
        if RUN0 < f < RUN1 and not any(kf - 6 <= f <= kf + 5 for kf in KILLS + [BOSS_X]):
            r_[1] += 0.03 * math.sin(f * 0.6)
            r_[2] += 0.03 * math.cos(f * 0.6)
        S.key_player(P, f, cp, cp + d * 10, rollT(f) + sr, tuple(r_), tuple(l_), prevq)

    # ---------------- glow, trails, sparks, lights, flashes
    bl = M["blade"].node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"]
    for f, v in ((1, 4.0), (MEGA - 4, 4.0), (MEGA, 14), (CORE_X, 16)):
        bl.default_value = v
        bl.keyframe_insert("default_value", frame=f)
    for i, kf in enumerate(KILLS):
        if i % 2 == 0:
            E2.slash_trail(P, kf - 5, kf + 1)
    for a, b_ in ((BOSS_X - 5, BOSS_X + 1), (BOUNCE - 5, BOUNCE + 1), (CORE_X - 5, CORE_X + 1)):
        E2.slash_trail(P, a, b_)
    for f in range(MEGA, STAB):                                  # sparks where the beam hits the crossed blades
        scene.frame_set(f)
        c = cam.matrix_world @ Vector((0, 0.03, -0.62))
        rnd = random.Random(f * 7)
        E2.bolts("Split", f, [(c, c + cam.matrix_world.to_3x3() @ Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.2, 0.2))) * 0.3) for _ in range(5)],
                 ("bolt_core", "bolt_glow"), amp=0.04, w=0.007, branches=0)
    for f in range(SKILL, SKILL + 34):                           # the lightning is still in his hand
        scene.frame_set(f)
        mw = P["rh"].matrix_world
        rnd = random.Random(f * 5)
        pairs = []
        for _ in range(4):
            a = mw @ Vector((rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05)))
            pairs.append((a, a + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.3, 1))) * 0.14))
        E2.bolts("Hand", f, pairs, ("bolt_core", "bolt_glow"), amp=0.03, w=0.005, branches=0)
    bstop = Vector((0.0, 44.2, 16.3))
    S.dust_ring("BounceSpark", BOUNCE, bstop, 14, 3.0, 17, size=0.3, mat=M["spark"])
    for f in range(BOUNCE, BOUNCE + 5):                          # thunder slash thrown at the closed lid: no effect
        scene.frame_set(f)
        tip = P["blade"].matrix_world @ Vector((0, 1.13, 0))
        E2.bolts("LidBolt", f, [(tip, bstop)] * 2, ("bolt_core", "bolt_glow"), amp=0.6, w=0.10, branches=3)
    VL = B.light("VoidFill", "POINT", 0, (0.9, 0.9, 1.0), tuple(V0 + Vector((0.3, 0.2, 2.3))), 0.8)
    for f, v in ((1, 0), (VOID - 1, 0), (VOID, 350), (FIELD - 1, 350), (FIELD, 0)):
        VL.data.energy = v
        VL.data.keyframe_insert("energy", frame=f)
    for name, col, loc, keys in (
            ("Lz1L", (1.0, 0.2, 0.15), tuple(HITP), ((1, 0), (LZ0 - 1, 0), (LZ0, 4000), (LZ0 + 12, 4000), (LZ0 + 14, 0))),
            ("StairL", (0.3, 0.5, 1.0), (0, 14.0, 3.0), ((1, 0), (STAIR0, 0), (STAIR0 + 6, 1500), (STAIR0 + 40, 300), (RUN1, 300))),
            ("TopL", (1.0, 0.5, 0.5), (0, 41.0, 18.5), ((1, 0), (RUN1 - 20, 0), (RUN1, 700), (MEGA, 700), (MEGA + 2, 6000), (STAB, 6000), (VOID, 0))),
            ("HandL", (0.4, 0.7, 1.0), tuple(F0 + Vector((0.2, 1.0, 1.0))), ((1, 0), (SKILL, 0), (SKILL + 6, 120), (SKILL + 34, 120), (SKILL + 40, 0)))):
        L = B.light(name, "POINT", 0, col, loc, 0.5)
        for f, v in keys:
            L.data.energy = v
            L.data.keyframe_insert("energy", frame=f)
    wm = S.fade_material("FlashWhite", (5, 5, 5))
    S.cam_overlay(cam, "FlashPlane", wm, -0.06)
    for f, v in ((1, 0), (LZ0 - 1, 0), (LZ0, 0.35), (LZ0 + 4, 0), (BOSS_X - 1, 0), (BOSS_X, 0.45), (BOSS_X + 5, 0), (MEGA - 1, 0), (MEGA, 0.4), (MEGA + 4, 0),
                 (STAB - 1, 0), (STAB + 2, 1.0), (VOID + 2, 1.0), (VOID + 12, 0), (CORE_X - 1, 0), (CORE_X + 2, 0.7), (CORE_X + 16, 1.0), (FIELD + 4, 1.0), (FIELD + 26, 0)):
        S.key_fade(wm, f, v)
    bk = S.fade_material("FadeBlack", (0, 0, 0))
    S.cam_overlay(cam, "FadePlane", bk, -0.05)
    for f, v in ((1, 0), (FADE0, 0), (FADE0 + 10, 1.0)):
        S.key_fade(bk, f, v)
    for body, size, col, y, d in (("異世界デスゲーム", 0.0034, (1.0, 0.5, 0.9), 0.0045, 0),
                                  ("― 完 ―", 0.0030, (1.0, 1.0, 1.0), -0.0030, 3),
                                  ("最後まで見てくれてありがとう！", 0.0013, (1.0, 0.75, 0.3), -0.0085, 6)):
        o = S.text_obj("Title%d" % d, body, size, B.emissive("title%d" % d, col, 4.0), (0, y, -0.04), cam, extrude=0.0)
        o.visible_shadow = False
        for f, s in ((1, 0.001), (FADE0 + 10 + d, 0.001), (FADE0 + 14 + d, 1.08), (FADE0 + 17 + d, 1.0)):
            S.key_scale(o, f, s)

def main():
    B.setup_world_render()
    scene.frame_end = N
    build()
    scene.frame_set(1)
    if not B.NO_SAVE:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "isekai_ep6.blend"))
    os.makedirs(FRAME_DIR, exist_ok=True)
    frames = []
    if B.FRAMES_ARG and B.FRAMES_ARG is not True:
        frames = [int(x) for x in B.FRAMES_ARG.split(",")]
    elif B.DO_ANIM:
        frames = [f for f in range(1, N + 1) if not os.path.exists(os.path.join(FRAME_DIR, "%04d.png" % f))]
    import time
    for f in frames:
        t0 = time.time()
        scene.frame_set(f)
        scene.render.filepath = os.path.join(FRAME_DIR, "%04d.png" % f)
        bpy.ops.render.render(write_still=True)
        print("frame %d  %.1fs" % (f, time.time() - t0), flush=True)

if __name__ == "__main__":
    main()
