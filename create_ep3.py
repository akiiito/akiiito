"""
create_ep3.py  ―  異世界デスゲーム 第三話「ルール違反」（一人称・720x1280・24fps・696f + タイトル静止）

  0s   「仲間を殺せ」制限時間つき → 少女「私を斬って」→「断る！」
  4.5s ポータルに巨大な"眼"が開く（ゲームマスター）→ 威嚇レーザー
  8.5s 雷刃で空のルール文字そのものを破壊
  12s  少女のスキル『足場』で空への階段 → レーザーの雨の中を駆け上がる（足場破壊→ジャンプ）
  20s  眼へ跳躍して一閃 → 白
  22.5s GAME CLEAR …と思った？ → 最終回戦「観客全員」→ 少女も剣を取る

  python create_ep3.py --anim --samples 24
"""
import os, sys, math, random
os.environ["BATTLE_AS_LIBRARY"] = "1"
os.environ["ISEKAI_AS_LIBRARY"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import create_battle as B
import create_isekai_short as S
import create_ep2 as E2

scene, M = B.scene, B.M
Track, EASE, lerp, clamp = B.Track, B.EASE, B.lerp, B.clamp
STANCE, ANK = B.STANCE, B.ANK
N = 696
FRAME_DIR = B.arg("--frame-dir", os.path.join(HERE, "frames_E3"))
random.seed(77)

EYE_OPEN, WARN = 112, 160
RULEBREAK = 240
STAIR0, RUN0, STAIR_A, STAIR_B = 296, 304, 336, 468
GAP = 424
JUMP, HIT, WHITE, CUT = 476, 502, 520, 532
CLEAR, FAKE, FINAL, GSWORD, FADE0 = 550, 598, 612, 644, 672
EYEPT = Vector((0, 45.2, 17.0))
TEXTPT = Vector((0, 44, 13.4))

def stair_top(y):
    return 0.0 if y < 13.0 else 0.5 + clamp((y - 13.0) / 26.0) * 14.5

def cam_path(f):
    if f >= CUT:
        return Vector((0, 7.0, 1.62))
    if f <= 150:
        return Vector((0, 6.8, 1.60))
    if f <= RUN0:
        k = EASE["out"](clamp((f - WARN) / 6)) * (1 - EASE["smooth"](clamp((f - 172) / 20)))
        return Vector((0.1 * k, 6.8 - 0.5 * k, 1.62 - 0.14 * k))
    if f <= STAIR_A:
        t = EASE["in"]((f - RUN0) / (STAIR_A - RUN0))
        return Vector((0.35 * t, lerp(6.8, 13.2, t), 1.62 - 0.03 * abs(math.sin(f * 0.6))))
    if f <= STAIR_B:
        t = (f - STAIR_A) / (STAIR_B - STAIR_A)
        y = lerp(13.2, 40.0, t)
        z = stair_top(y) + 1.62 - 0.04 * abs(math.sin(f * 0.6))
        if GAP <= f <= GAP + 16:
            z += 1.1 * math.sin(math.pi * (f - GAP) / 16)
        return Vector((0.35, y, z))
    if f <= JUMP:
        return Vector((0.35, 40.0, stair_top(40.0) + 1.62 - 0.12 * EASE["smooth"]((f - STAIR_B) / (JUMP - STAIR_B))))
    hs = min(f, HIT)
    t = (hs - JUMP) / (HIT - JUMP)
    p = Vector((0.35, 40.0, stair_top(40.0) + 1.5)).lerp(Vector((0.1, 43.7, 17.6)), EASE["out"](t))
    p.z += 1.3 * math.sin(math.pi * t)
    return p

class Girl:
    def __init__(self):
        mats = dict(e_blue=B.principled("g_cloth", (0.10, 0.25, 0.55)), e_dark=B.principled("g_dark", (0.05, 0.06, 0.16)),
                    e_light=M["cuff"], e_eye=B.emissive("g_eye", (1.0, 1.0, 1.0), 3.0))
        skin = B.principled("g_skin", (0.86, 0.66, 0.50))
        hair = B.principled("g_hair", (0.07, 0.05, 0.10))
        before = set(bpy.data.objects)
        saved = {k: M[k] for k in mats}
        M.update(mats)
        self.J = B.build_enemy()
        M.update(saved)
        for ob in set(bpy.data.objects) - before:
            n = ob.name
            if n.startswith(("E_horn", "E_crest", "E_visor", "E_plate", "E_core", "E_pad", "E_knee", "E_bracer")):
                bpy.data.objects.remove(ob)
            elif n.startswith(("E_head", "E_hand")):
                ob.data.materials[0] = skin
        nk = self.J["neck"]
        B.box("G_hair", (0.52, 0.50, 0.16), (0, 0.02, 0.44), hair, nk, bevel=0.03)
        B.box("G_hairb", (0.52, 0.16, 0.62), (0, 0.20, 0.14), hair, nk, bevel=0.03)
        for sx in (-1, 1):
            B.box("G_hairs", (0.08, 0.3, 0.36), (sx * 0.25, 0.08, 0.20), hair, nk, bevel=0.02)
        self.J["root"].scale = (0.86,) * 3
        self.blade = B.box("G_blade", (0.05, 0.03, 1.0), (0, 0, -1.0), B.principled("g_blade", (0.8, 0.9, 1.0), emit=(0.5, 0.9, 1.0), strength=3.0),
                           self.J["elR"], bevel=0.005)
        B.box("G_guard", (0.2, 0.06, 0.05), (0, 0, -0.5), M["guard"], self.blade, bevel=0.005)
        for f, s in ((1, 0.001), (GSWORD, 0.001), (GSWORD + 6, 1.15), (GSWORD + 9, 1.0)):
            S.key_scale(self.blade, f, s)

    def state(self, f):
        """(x, y, z, yaw, run weight, distance)"""
        if f >= CUT:
            yaw = lerp(math.pi, 0.75, EASE["smooth"](clamp((f - (GSWORD - 14)) / 12)))
            return -1.05, 8.6, 0.0, yaw, 0.0, 0.0
        if f < RUN0:
            return 0.0, 9.0, 0.0, 0.0 if f < STAIR0 - 8 else lerp(0.0, math.pi, EASE["smooth"](clamp((f - (STAIR0 - 8)) / 8))), 0.0, 0.0
        if f <= STAIR_A:
            t = EASE["in"]((f - RUN0) / (STAIR_A - RUN0))
            return lerp(0, -0.85, t), lerp(9.0, 15.2, t), stair_top(lerp(9.0, 15.2, t)), math.pi, min(1, (f - RUN0) / 3), 6.2 * t
        if f <= STAIR_B:
            t = (f - STAIR_A) / (STAIR_B - STAIR_A)
            y = lerp(15.2, 40.7, t)
            z = stair_top(y)
            if GAP - 8 <= f <= GAP + 8:
                z += 1.0 * math.sin(math.pi * (f - GAP + 8) / 16)
            return -0.85, y, z, math.pi, min(1.0, (STAIR_B - f) / 3), 6.2 + 26 * t
        return -0.85, 40.7, stair_top(40.7), math.pi, 0.0, 0.0

def build():
    flames, floats = B.build_arena()
    P = B.build_player()
    S.env_life(flames, floats, N)
    cam = P["cam"]
    pe = M["portal"].node_tree.nodes["Emission"]
    pe.inputs["Color"].default_value = (1.0, 0.10, 0.12, 1)
    for f, v in ((1, 2.2), (WHITE, 2.2), (CUT, 0.25), (FAKE, 0.25), (FINAL, 4.0)):
        pe.inputs["Strength"].default_value = v
        pe.inputs["Strength"].keyframe_insert("default_value", frame=f)

    # ---------------- sky text
    rmat = B.emissive("txt_rule", (1.0, 0.10, 0.18), 9.0)
    gmat = B.emissive("txt_clear", (0.35, 1.0, 0.55), 8.0)
    def sky(name, body, size, mat, z, keys):
        o = S.text_obj(name, body, size, mat, (0, 44, z), extrude=0.3)
        o.rotation_euler = (math.pi / 2, 0, 0)
        for f, s in keys:
            S.key_scale(o, f, s)
        return o
    sky("T_r3", "第三回戦", 4.2, rmat, 18.4, ((1, 1.0), (EYE_OPEN - 4, 1.0), (EYE_OPEN, 0.001)))
    sky("T_kill", "仲間を殺せ", 3.6, rmat, 13.4, ((1, 1.0), (RULEBREAK - 1, 1.0), (RULEBREAK, 0.001)))
    sky("T_clear", "GAME CLEAR", 3.6, gmat, 16.0, ((1, 0.001), (CLEAR, 0.001), (CLEAR + 5, 1.2), (CLEAR + 9, 1.0), (FAKE - 1, 1.0), (FAKE, 0.001)))
    sky("T_fake", "…と思った？", 3.6, rmat, 16.0, ((1, 0.001), (FAKE - 1, 0.001), (FAKE, 1.2), (FAKE + 4, 1.0), (FINAL - 1, 1.0), (FINAL, 0.001)))
    sky("T_final", "最終回戦", 4.4, rmat, 18.2, ((1, 0.001), (FINAL - 1, 0.001), (FINAL, 1.25), (FINAL + 5, 1.0)))
    sky("T_all", "観客 全員", 4.0, rmat, 13.2, ((1, 0.001), (FINAL + 3, 0.001), (FINAL + 4, 1.25), (FINAL + 9, 1.0)))
    E2.frag_burst("RuleFrag", RULEBREAK, TEXTPT, 90, 16.0, 1.1, 5, [rmat], life=44)

    # ---------------- the eye (game master) in the portal
    eye = B.empty("Eye", None, tuple(EYEPT))
    B.box("EyeWhite", (10.5, 0.4, 5.4), (0, 0, 0), B.emissive("eye_w", (0.95, 0.9, 0.95), 1.6), eye, bevel=0)
    iris_m = B.emissive("eye_iris", (1.0, 0.08, 0.10), 6.0)
    iris = B.box("EyeIris", (3.4, 0.5, 3.4), (0, -0.2, 0), iris_m, eye, bevel=0)
    B.box("EyePupil", (1.3, 0.6, 1.5), (0, -0.4, 0), B.principled("eye_p", (0, 0, 0)), eye, bevel=0)
    for f, sz in ((1, 0.001), (EYE_OPEN, 0.001), (EYE_OPEN + 8, 1.15), (EYE_OPEN + 12, 1.0), (RULEBREAK, 1.0), (RULEBREAK + 5, 1.35),
                  (HIT, 1.35), (WHITE, 1.6), (WHITE + 1, 0.001)):
        S.key_scale(eye, f, (1, 1, sz) if f <= EYE_OPEN + 12 else (1 if sz < 1.3 else 1.1, 1, sz))
    ist = iris_m.node_tree.nodes["Emission"].inputs["Strength"]
    for f, v in ((1, 6), (WARN - 12, 6), (WARN - 1, 30), (WARN + 8, 6), (RULEBREAK, 6), (RULEBREAK + 5, 22), (HIT, 22), (HIT + 2, 60)):
        ist.default_value = v
        ist.keyframe_insert("default_value", frame=f)
    ck = B.emissive("crack3", (1.0, 1.0, 0.8), 30.0)
    bm = bmesh.new()
    rnd = random.Random(3)
    for i in range(16):
        B.bm_box(bm, (rnd.uniform(1.5, 5), 0.1, 0.14), (rnd.uniform(-2.5, 2.5), -0.5, rnd.uniform(-1.5, 1.5)), Matrix.Rotation(rnd.uniform(0, 3.14), 3, 'Y'))
    cr = B.mesh_obj("EyeCrack", bm, ck, eye, bevel=0)
    for f, s in ((1, 0.001), (HIT, 0.001), (HIT + 1, 0.4), (WHITE, 1.2)):
        S.key_scale(cr, f, s)
    E2.frag_burst("EyeFrag", WHITE, EYEPT, 80, 18.0, 1.0, 9, [iris_m, B.M["float"]], life=30)

    # ---------------- lasers from the eye
    def laser(i, f0, target, big=False):
        tgt = Vector(target)
        ring = bmesh.new()
        for a in range(8):
            ang = a * math.pi / 4
            B.bm_box(ring, (0.5, 0.12, 0.02), tgt + Vector((math.cos(ang) * 0.8, math.sin(ang) * 0.8, 0.03)), Matrix.Rotation(ang + math.pi / 2, 3, 'Z'))
        ro = B.mesh_obj("Warn_%d" % i, ring, M["rbolt_glow"], bevel=0)
        B.vis_only(ro, list(range(f0 - 8, f0)))
        for f in range(f0, f0 + 5):
            k = 1 - (f - f0) / 5
            bc, bg = bmesh.new(), bmesh.new()
            w = (0.34 if big else 0.22) * (0.4 + 0.6 * k)
            B.bm_beam(bc, EYEPT + Vector((0, -0.6, 0)), tgt, w)
            B.bm_beam(bg, EYEPT + Vector((0, -0.6, 0)), tgt, w * 2.6)
            for bm_, m in ((bc, "rbolt_core"), (bg, "rbolt_glow")):
                ob = B.mesh_obj("Laser_%d_%d" % (i, f), bm_, M[m])
                ob.visible_shadow = False
                B.vis_only(ob, [f])
        S.dust_ring("LzDust%d" % i, f0, tgt, 9, 1.8, 300 + i, size=0.35)
        S.dust_ring("LzSpark%d" % i, f0, tgt, 8, 1.5, 400 + i, size=0.12, mat=M["spark"])
        L = B.light("LzL%d" % i, "POINT", 0, (1.0, 0.2, 0.15), tuple(tgt + Vector((0, 0, 0.8))), 0.4)
        for f, v in ((f0 - 1, 0), (f0, 2500), (f0 + 6, 0)):
            L.data.energy = v
            L.data.keyframe_insert("energy", frame=f)
    strikes = [(WARN, (1.7, 8.3, 0), True)]
    rnd = random.Random(21)
    for k in range(13):                                       # the rain: just ahead of the runners, left/right
        f0 = 310 + k * 12
        y = cam_path(f0 + 4).y + rnd.uniform(3.5, 6.5)
        x = rnd.choice((-1, 1)) * rnd.uniform(2.3, 3.6)
        strikes.append((f0, (x, y, stair_top(y) * (0 if abs(x) > 1.9 else 1)), False))
    for i, (f0, tg, big) in enumerate(strikes):
        laser(i, f0, tg, big)

    # ---------------- stairway of slabs (the girl's skill)
    slab_m = B.principled("slab", (0.30, 0.45, 0.95), emit=(0.2, 0.5, 1.0), strength=0.6)
    BROKEN = 6
    for k in range(14):
        y = 14 + 2 * k
        ob = B.box("Slab_%d" % k, (3.3, 1.9, 0.4), (0, 0, 0), slab_m, None, (-0.2, y, stair_top(y) - 0.2), bevel=0.04)
        f0 = STAIR0 + 4 + k * 2
        keys = [(1, 0.001), (f0, 0.001), (f0 + 3, 1.2), (f0 + 5, 1.0)]
        if k == BROKEN:
            keys += [(GAP - 22, 1.0), (GAP - 21, 0.001)]
            laser(50, GAP - 21, (-0.2, y, stair_top(y)), True)
            E2.frag_burst("SlabFrag", GAP - 21, (-0.2, y, stair_top(y)), 24, 7.0, 0.35, 8, [slab_m])
        else:
            keys += [(CUT - 1, 1.0), (CUT, 0.001)]
        for f, s in keys:
            S.key_scale(ob, f, s)

    # ---------------- the girl
    G = Girl()
    KNEEL = dict(E2.CROUCH, hz=-0.52, tp=0.35, np=-0.1, shRx=-0.2, shRy=0.1, elR=-0.3, shLx=-0.2, shLy=-0.1, elL=-0.3)
    STAND = dict(B.E_DEF, shRx=0.05, shLx=0.05, elR=-0.25, elL=-0.25)
    tl = B.PoseTimeline(B.E_DEF, [
        (1, KNEEL, "smooth"), (10, dict(KNEEL, shRx=-1.2, shLx=-1.2, elR=-1.5, elL=-1.5), "smooth"), (40, dict(), "smooth"),
        (58, STAND, "smoother"), (68, dict(STAND, shLx=-0.9, shLy=0.3, elL=-1.9, np=0.15), "smooth"), (88, dict(), "smooth"),
        (100, STAND, "smooth"), (EYE_OPEN + 6, dict(STAND, np=-0.4, tp=-0.1), "smooth"), (WARN - 2, dict(), "smooth"),
        (WARN + 4, dict(E2.SCARED), "out"), (184, dict(E2.SCARED, hz=-0.1), "smooth"), (200, dict(STAND, np=-0.3), "smooth"),
        (RULEBREAK + 8, dict(STAND, np=-0.35), "smooth"), (STAIR0 - 8, STAND, "smooth"),
        (STAIR0 + 2, dict(STAND, shRx=-1.9, shRy=0.1, elR=-0.05, tp=-0.1), "out"), (RUN0 - 1, dict(), "smooth"), (RUN0 + 2, STAND, "smooth"),
        (STAIR_B, STAND, "smooth"), (STAIR_B + 8, dict(STAND, shRx=-2.9, shRy=0.2, elR=-0.1, np=-0.4, tp=-0.15), "out"),
        (CUT - 1, dict(), "lin"), (CUT, dict(STAND, np=-0.3), "lin"), (FAKE, dict(STAND, np=-0.3), "smooth"),
        (FINAL + 6, dict(E2.SCARED, hz=-0.1), "out"), (GSWORD - 8, dict(STAND), "smooth"),
        (GSWORD + 6, dict(STANCE, shRx=-1.3, shRy=0.3, elR=-0.5, np=-0.1), "smooth"), (N, dict(), "smooth")])
    for f in range(1, N + 1):
        x, y, z, yaw, w, d = G.state(f)
        pose = tl(f)
        for k, v in E2.RUNP.items():
            pose[k] = lerp(pose[k], v, w)
        pose["run"] = w
        pose["hz"] += 0.006 * math.sin(f * 0.2)
        S.key_enemy(G.J, f, pose, (x, y, z), 0.0, yaw, run_phase=d / 2.0)

    # ---------------- camera + hands
    yawT = Track([(1, 0), (92, 0), (97, -9, "smooth"), (102, 9, "smooth"), (107, 0, "smooth"), (WARN + 3, 14, "out"), (186, 0, "smooth"),
                  (CUT - 1, 0), (CUT, 0), (GSWORD - 16, 0), (GSWORD - 2, -38, "smooth"), (N, -36)])
    pitT = Track([(1, -9), (44, -9), (60, -3, "smooth"), (WARN, -3), (WARN + 4, -16, "out"), (190, -3, "smooth"), (RUN0, -2),
                  (STAIR_A, 8, "smooth"), (STAIR_B, 14), (CUT - 1, 0), (CUT, 2), (CLEAR, 16, "smooth"), (FINAL + 20, 17),
                  (GSWORD - 4, -3, "smooth"), (N, -3)])
    wEye = Track([(1, 0), (104, 0), (EYE_OPEN + 4, 1, "smooth"), (148, 1), (WARN - 1, 0.25, "smooth"), (WARN + 4, 0, "out"),
                  (206, 0), (220, 1, "smooth"), (262, 1), (284, 0, "smooth"), (446, 0), (JUMP, 1, "smooth"), (WHITE + 8, 1), (CUT, 0), (N, 0)])
    def tgt(f):
        return TEXTPT if 200 < f < 290 else EYEPT
    rollT = Track([(1, 0), (WARN, 0), (WARN + 3, 0.12, "out"), (184, 0, "smooth"), (GAP, 0), (GAP + 8, 0.07), (GAP + 18, 0),
                   (JUMP, 0), (HIT, -0.08), (CUT, 0), (N, 0)])
    RH1, LH1 = B.RH(1), B.LH(1)
    LOW = (0.19, -0.44, -0.50, 0.25, 0.3, -0.92)
    UP = (0.10, -0.12, -0.52, 0.0, 1.0, -0.12)
    rh = Track([(1, LOW), (20, RH1, "smooth"), (88, RH1), (100, LOW, "smooth"), (WARN, LOW), (WARN + 4, (0.22, -0.26, -0.38, -0.5, 0.6, -0.4), "out"),
                (190, LOW, "smooth"), (204, LOW), (222, UP, "smooth"), (RULEBREAK - 6, (0.20, -0.20, -0.36, 0.3, 0.6, 0.5), "smooth"),
                (RULEBREAK - 1, (0.08, -0.10, -0.62, 0.0, 0.25, -1.0), "in"), (RULEBREAK + 12, (0.08, -0.12, -0.60, 0.0, 0.2, -1.0)),
                (276, RH1, "smooth"), (JUMP, RH1), (JUMP + 14, (0.17, 0.02, -0.44, -0.1, 1.0, 0.2), "smooth"), (HIT - 4, (0.17, 0.03, -0.44, -0.1, 1.0, 0.25)),
                (HIT, (0.06, -0.20, -0.60, 0.0, -0.25, -1.0), "in"), (CUT - 1, (0.06, -0.22, -0.60, 0.0, -0.3, -1.0)), (CUT, LOW),
                (FINAL + 10, LOW), (FINAL + 22, RH1, "smooth"), (N, RH1)])
    LHL = (-0.17, -0.42, -0.42)
    lh = Track([(1, LHL), (20, LH1, "smooth"), (88, LH1), (100, LHL, "smooth"), (WARN, LHL), (WARN + 4, (-0.10, -0.13, -0.44), "out"),
                (190, LHL, "smooth"), (STAIR0 + 4, LHL), (RUN0, (-0.16, -0.16, -0.56), "smooth"), (RUN0 + 10, LH1, "smooth"),
                (CUT - 1, LH1), (CUT, LHL), (FINAL + 22, LH1, "smooth"), (N, LH1)])
    shakes = [(WARN, 0.10, 5), (RULEBREAK, 0.06, 6), (GAP - 21, 0.06, 4), (HIT, 0.10, 5), (FAKE, 0.03, 4), (FINAL, 0.07, 8), (FINAL + 4, 0.05, 8)]
    shakes += [(f0, 0.03, 3) for f0, _, _ in strikes[1:]]
    prevq = {}
    for f in range(1, N + 1):
        sv, sr = Vector((0, 0, 0)), 0.0
        for f0, amp, dc in shakes:
            a, r = S.shake(f, f0, amp, dc)
            sv += a
            sr += r
        hs = f if not (HIT <= f <= HIT + 4) else HIT
        cp = cam_path(f) + sv + Vector((0, 0, 0.006 * math.sin(f * 0.25)))
        ya, pi_ = math.radians(yawT(f)), math.radians(pitT(f))
        d = Vector((math.sin(ya) * math.cos(pi_), math.cos(ya) * math.cos(pi_), math.sin(pi_)))
        w = wEye(f)
        if w > 0:
            d = d.lerp((tgt(f) - cp).normalized(), w).normalized()
        r_ = list(rh(hs))
        if RUN0 < f < JUMP:                                      # running arm swing
            r_[1] += 0.03 * math.sin(f * 0.6)
            r_[2] += 0.03 * math.cos(f * 0.6)
        S.key_player(P, f, cp, cp + d * 10, rollT(f) + sr, tuple(r_), lh(hs), prevq)

    # ---------------- sword glow, rule-breaking bolt, trails, flashes
    bl = M["blade"].node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"]
    for f, v in ((1, 1.0), (204, 1.0), (RULEBREAK - 4, 14), (RULEBREAK + 12, 3), (JUMP, 3), (HIT - 2, 16), (WHITE, 16), (CUT, 1.0)):
        bl.default_value = v
        bl.keyframe_insert("default_value", frame=f)
    tip_local = Vector((0, 1.13, 0))
    for f in range(208, RULEBREAK + 12):
        scene.frame_set(f)
        mw = P["blade"].matrix_world
        tip = mw @ tip_local
        rnd = random.Random(f)
        pairs = []
        if f < RULEBREAK - 1:
            for _ in range(4):
                a = mw @ Vector((0, rnd.uniform(0.2, 1.1), 0))
                pairs.append((a, a + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * 0.16))
            E2.bolts("Crk3", f, pairs, ("bolt_core", "bolt_glow"), amp=0.03, w=0.006, branches=0)
        else:
            k = clamp((f - RULEBREAK + 2) / 2)
            E2.bolts("RuleBolt", f, [(tip, tip.lerp(TEXTPT, k))] * 2, ("bolt_core", "bolt_glow"), amp=0.9, w=0.16, branches=5)
    for a, b_ in ((RULEBREAK - 5, RULEBREAK + 1), (HIT - 5, HIT + 1)):
        E2.slash_trail(P, a, b_)
    for name, col, loc, keys in (
            ("RuleL", (0.4, 0.7, 1.0), (0, 9.0, 3.0), ((1, 0), (RULEBREAK - 2, 0), (RULEBREAK, 5000), (RULEBREAK + 12, 0))),
            ("SkillL", (0.3, 0.5, 1.0), (0, 11.0, 2.0), ((1, 0), (STAIR0, 0), (STAIR0 + 6, 1500), (STAIR0 + 30, 0))),
            ("FinalL", (1.0, 0.1, 0.1), (0, 7.0, 6.0), ((1, 0), (FINAL - 1, 0), (FINAL, 4000), (FINAL + 30, 1200), (N, 1200)))):
        L = B.light(name, "POINT", 0, col, loc, 0.5)
        for f, v in keys:
            L.data.energy = v
            L.data.keyframe_insert("energy", frame=f)
    er = M["eye_red"].node_tree.nodes["Emission"].inputs["Strength"]      # the crowd's eyes flare up
    for f, v in ((1, 6), (FINAL - 1, 6), (FINAL + 4, 40), (N, 30)):
        er.default_value = v
        er.keyframe_insert("default_value", frame=f)
    wm = S.fade_material("FlashWhite", (5, 5, 5))
    S.cam_overlay(cam, "FlashPlane", wm, -0.06)
    for f, v in ((1, 0), (RULEBREAK - 1, 0), (RULEBREAK, 0.5), (RULEBREAK + 5, 0), (HIT - 1, 0), (HIT, 0.5), (HIT + 4, 0.1),
                 (WHITE, 1.0), (CUT + 2, 1.0), (CUT + 16, 0.0)):
        S.key_fade(wm, f, v)
    bk = S.fade_material("FadeBlack", (0, 0, 0))
    S.cam_overlay(cam, "FadePlane", bk, -0.05)
    for f, v in ((1, 0), (FADE0, 0), (FADE0 + 10, 1.0)):
        S.key_fade(bk, f, v)
    for body, size, col, y, d in (("異世界デスゲーム", 0.0034, (1.0, 0.5, 0.9), 0.004, 0),
                                  ("― 第三話「ルール違反」 ―", 0.0019, (0.9, 0.85, 1.0), -0.0025, 3),
                                  ("To Be Continued…", 0.0015, (1.0, 0.75, 0.3), -0.0065, 6)):
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
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "isekai_ep3.blend"))
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
