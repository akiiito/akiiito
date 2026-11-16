"""
create_ep4.py  ―  異世界デスゲーム 第四話「一万対二」（一人称・720x1280・24fps・696f + タイトル静止）

  0s   観客一万が客席から飛び降りてくる → 少女と二人で迎え撃つ（斬っても斬ってもキリがない）
  7s   完全包囲 → 少女のスキル『足場』で柱がせり上がる → 観客が積み重なって登ってくる
  12s  「私の足場、全部あげる」→ 足場が剣に連結して巨大な刃に（合体スキル【天断】）→ 落雷
  17s  回転斬り一周で闘技場ごと薙ぎ払う（撃破 9999 / 10000）
  21s  最後の一人が降り立つ … 仮面の下は「未来のお前」

  python create_ep4.py --anim --samples 24
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
FRAME_DIR = B.arg("--frame-dir", os.path.join(HERE, "frames_E4"))
random.seed(404)

K1, K2, GK1, K3, GK2, K4 = 72, 96, 106, 118, 140, 158
SPIN0, SPIN1 = 166, 206
LIFT0, LIFT1 = 216, 250
GIVE, SLAB0, ZAP = 296, 302, 372
SW0, SW1 = 400, 448
BREAK, DOWN0, DOWN1 = 460, 472, 502
LAND, MASK, REVEAL, FADE0 = 508, 600, 612, 672
CAM0 = Vector((0, 7.0, 1.62))
PC = Vector((-0.7, 6.65, 0))                 # pillar centre
PH = 7.0
NSLAB = 12
CH_A, CH_B = Vector((0.8, 22.0, 0)), Vector((0.8, 12.5, 0))
BLADE_OFF = 23.0                           # the giant blade points this far left of the view axis

hT = Track([(1, 0.0), (LIFT0, 0.0), (LIFT1, PH, "smooth"), (DOWN0, PH), (DOWN1, 0.0, "smooth"), (N, 0.0)])
def sweep(f):
    return 360.0 * EASE["smooth"](clamp((f - SW0) / (SW1 - SW0)))
def sweep_death(deg):
    deg = (deg + BLADE_OFF) % 360.0
    for f in range(SW0, SW1 + 1):
        if sweep(f) >= deg:
            return f + 1
    return SW1 + 1
def ang_of(p):
    return math.degrees(math.atan2(p[0] - CAM0.x, p[1] - CAM0.y)) % 360.0

MOB = dict(e_blue=B.principled("m_main", (0.20, 0.08, 0.30)), e_dark=B.principled("m_dark", (0.07, 0.03, 0.12)),
           e_light=B.principled("m_light", (0.45, 0.20, 0.60)), e_eye=B.emissive("m_eye", (1.0, 0.12, 0.25), 14.0))
MOBB = B.principled("mob_body", (0.12, 0.055, 0.19))
MENACE = dict(STANCE, shRx=-2.3, shLx=-2.3, shRy=0.3, shLy=-0.3, elR=-0.7, elL=-0.7, tp=0.2)

class Human:
    """enemy rig re-skinned as a person (girl / the champion)"""
    def __init__(self, tag, cloth, dark, hair_col, scale, blade_mat):
        mats = dict(e_blue=cloth, e_dark=dark, e_light=M["cuff"], e_eye=B.emissive(tag + "_eye", (1.0, 1.0, 1.0), 3.0))
        skin = B.principled(tag + "_skin", (0.86, 0.66, 0.50))
        hair = B.principled(tag + "_hair", hair_col)
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
        self.neck = nk
        B.box(tag + "_hair", (0.52, 0.50, 0.16), (0, 0.02, 0.44), hair, nk, bevel=0.03)
        B.box(tag + "_hairb", (0.52, 0.16, 0.62 if tag == "G" else 0.34), (0, 0.20, 0.14 if tag == "G" else 0.28), hair, nk, bevel=0.03)
        if tag == "G":
            for sx in (-1, 1):
                B.box("G_hairs", (0.08, 0.3, 0.36), (sx * 0.25, 0.08, 0.20), hair, nk, bevel=0.02)
        self.scale = scale
        self.J["root"].scale = (scale,) * 3
        self.blade = B.box(tag + "_blade", (0.05, 0.03, 1.0), (0, 0, -1.0), blade_mat, self.J["elR"], bevel=0.005)
        B.box(tag + "_guard", (0.2, 0.06, 0.05), (0, 0, -0.5), M["guard"], self.blade, bevel=0.005)

def crowd_fig(bm, x, y, z, rz, s=1.0):
    """one low-poly spectator (faces local -y), eyes get material slot 1"""
    R = Matrix.Rotation(rz, 3, 'Z')
    def put(size, off, mi=0):
        n0 = len(bm.faces)
        B.bm_box(bm, tuple(v * s for v in size), Vector((x, y, z)) + R @ (Vector(off) * s), R)
        if mi:
            bm.faces.ensure_lookup_table()
            for fc in bm.faces[n0:]:
                fc.material_index = mi
    put((0.44, 0.30, 0.55), (0, 0, 0.275))
    put((0.60, 0.38, 0.70), (0, 0, 0.90))
    put((0.46, 0.44, 0.44), (0, 0, 1.48))
    for sx in (-1, 1):
        put((0.14, 0.55, 0.14), (sx * 0.37, -0.30, 1.12))
        put((0.09, 0.03, 0.06), (sx * 0.10, -0.225, 1.52), 1)

def build():
    flames, floats = B.build_arena()
    P = B.build_player()
    S.env_life(flames, floats, N)
    cam = P["cam"]
    pe = M["portal"].node_tree.nodes["Emission"]
    pe.inputs["Color"].default_value = (1.0, 0.10, 0.12, 1)
    pe.inputs["Strength"].default_value = 4.0
    M["eye_red"].node_tree.nodes["Emission"].inputs["Strength"].default_value = 22.0
    for n in ("Crowd", "CrowdEyes"):                       # the stands empty out
        for f, s in ((1, 1.0), (56, 1.0), (57, 0.001)):
            S.key_scale(bpy.data.objects[n], f, s)

    # ---------------- sky text
    rmat = B.emissive("txt_rule", (1.0, 0.10, 0.18), 9.0)
    def sky(name, body, size, z, keys):
        o = S.text_obj(name, body, size, rmat, (0 if z > 15 else 2.2, 44, z), extrude=0.3)
        o.rotation_euler = (math.pi / 2, 0, 0)
        for f, s in keys:
            S.key_scale(o, f, s)
    sky("T_final", "最終回戦", 4.4, 18.2, ((1, 1.0),))
    sky("T_all", "観客 全員", 3.6, 13.2, ((1, 1.0), (SW1 + 7, 1.0), (SW1 + 8, 0.001)))
    sky("T_one", "残り 1", 3.8, 13.2, ((1, 0.001), (SW1 + 7, 0.001), (SW1 + 8, 1.25), (SW1 + 13, 1.0), (REVEAL - 1, 1.0), (REVEAL, 0.001)))
    sky("T_you", "未来のお前", 3.2, 13.2, ((1, 0.001), (REVEAL - 1, 0.001), (REVEAL, 1.25), (REVEAL + 5, 1.0)))

    # ---------------- the crowd: clumps of simple figures that drop from the wall and close in
    mob_mats = [MOBB, M["eye_red"]]
    frag_mats = [MOB["e_blue"], MOB["e_dark"], MOB["e_light"]]
    rnd = random.Random(11)
    nclump = 0
    for j in range(6):
        r_stop = 5.2 + 1.45 * j
        n = int(round(2 * math.pi * r_stop / 3.1))
        for c in range(n):
            a = 2 * math.pi * (c + 0.5 * (j % 2)) / n + rnd.uniform(-0.04, 0.04)
            d = Vector((math.sin(a), math.cos(a), 0))
            f_d = rnd.randint(2, 36)
            f_a = 150 + 8 * j + rnd.randint(0, 16)
            stop = Vector((CAM0.x, CAM0.y, 0)) + d * (r_stop + rnd.uniform(-0.3, 0.3))
            death = sweep_death(math.degrees(a))
            for sub in range(2):
                bm = bmesh.new()
                for k in range(4):
                    crowd_fig(bm, -1.3 + 0.86 * k + rnd.uniform(-0.15, 0.15) + 0.3 * sub, rnd.uniform(-0.45, 0.45) + 0.5 * sub, 0,
                              rnd.uniform(-0.3, 0.3), rnd.uniform(0.9, 1.08))
                ob = B.mesh_obj("Clump_%d_%d_%d" % (j, c, sub), bm, mob_mats)
                ob.rotation_euler = (0, 0, -a)
                ph, om = rnd.uniform(0, 6.28), rnd.uniform(0.55, 0.8)
                S.key_scale(ob, 1, 0.001)
                S.key_scale(ob, f_d - 1, 0.001)
                S.key_scale(ob, f_d, 1.0)
                S.key_scale(ob, death - 1, 1.0)
                S.key_scale(ob, death, 0.001)
                top = Vector((CAM0.x, CAM0.y, 0)) + d * 17.4
                land = Vector((CAM0.x, CAM0.y, 0)) + d * 15.4
                for f in range(f_d, death + 1, 2):
                    if f < f_d + 10:
                        t = (f - f_d) / 10.0
                        p = top.lerp(land, t)
                        p.z = 3.0 * (1 - t) + 2.0 * math.sin(math.pi * t)
                    elif f < f_a:
                        t = (f - f_d - 10) / max(1, f_a - f_d - 10)
                        p = land.lerp(stop, t)
                        p.z = 0.14 * abs(math.sin(f * om + ph))
                    else:
                        p = stop + d * (0.12 * math.sin(f * 0.13 + ph))
                        p.z = 0.07 * abs(math.sin(f * om * 0.6 + ph))
                    ob.location = p
                    ob.keyframe_insert("location", frame=f)
            if nclump % 3 == 0:
                E2.frag_burst("CF%d" % nclump, death, stop + Vector((0, 0, 1.0)), 8, 9.0, 0.34, 500 + nclump, frag_mats, life=26)
            nclump += 1

    # the pile that climbs the pillar: 6 sectors x 5 layers
    for s in range(6):
        for k in range(5):
            bm = bmesh.new()
            for _ in range(6 - k // 2):
                a = math.radians(60 * s + rnd.uniform(-28, 28))
                r = rnd.uniform(2.3, 4.0 - 0.25 * k)
                crowd_fig(bm, PC.x + math.sin(a) * r, PC.y + math.cos(a) * r, 1.25 * k + rnd.uniform(-0.2, 0.2), -a + rnd.uniform(-0.4, 0.4))
            ob = B.mesh_obj("Pile_%d_%d" % (s, k), bm, mob_mats)
            f0 = 256 + 11 * k + rnd.randint(0, 8)
            death = sweep_death(60 * s)
            for f, v in ((1, 0.001), (f0, 0.001), (f0 + 4, 1.0), (death - 1, 1.0), (death, 0.001)):
                S.key_scale(ob, f, (1, 1, v))
        E2.frag_burst("PF%d" % s, sweep_death(60 * s), PC + Vector((math.sin(math.radians(60 * s)) * 3.6, math.cos(math.radians(60 * s)) * 3.0, 3.5)),
                      10, 8.0, 0.34, 700 + s, frag_mats, life=26)

    # ---------------- full-rig spectators for the close fighting
    old = E2.RED
    E2.RED = MOB
    specs = [  # start, stop, f0, f1, death, target ("cam"/"girl"), idle
        ((0.5, 21.0), (0.1, 9.0), 30, K1 - 2, K1, "cam"),
        ((5.5, 20.0), (0.3, 9.0), 52, K2 - 2, K2, "cam"),
        ((10.0, 15.0), (1.34, 8.5), 70, K3 - 2, K3, "cam"),
        ((-7.0, 19.0), (-2.0, 9.9), 60, GK1 - 2, GK1, "girl"),
        ((-12.0, 11.0), (-2.5, 8.7), 92, GK2 - 2, GK2, "girl"),
        ((-3.0, 21.0), (-0.55, 9.1), 108, K4 - 2, K4, "cam"),
        ((3.5, 21.0), (0.6, 9.2), 112, K4 - 3, K4, "cam"),
        ((-6.0, 20.0), (-1.6, 10.2), 132, 182, None, "cam"),
        ((1.0, 22.0), (0.2, 10.6), 138, 188, None, "cam"),
        ((7.0, 19.0), (1.9, 10.0), 136, 178, None, "cam")]
    mobs = []
    for i, (p0, p1, f0, f1, death, tg) in enumerate(specs):
        e = E2.En(i, p0)
        e.move(f0, f1, p1)
        e.f0, e.tg = f0, tg
        e.death = death if death else sweep_death(ang_of(p1))
        if death:
            e.keys = [(1, B.E_DEF, "smooth"), (f1 - 7, dict(), "smooth"), (f1, E2.WIND, "out")]
        else:
            e.keys = [(1, B.E_DEF, "smooth"), (f1, dict(), "smooth"), (f1 + 10, MENACE, "smooth")]
        mobs.append(e)
    E2.RED = old
    GPOS = Vector((-1.05, 8.6, 0))
    for e in mobs:
        tl = B.PoseTimeline(B.E_DEF, e.keys)
        root = e.J["root"]
        for f in range(1, N + 1):
            alive = e.f0 - 8 <= f < e.death
            S.key_scale(root, f, B.E_SCALE if alive else 0.001)
            if not alive and f > e.death + 1 or f < e.f0 - 9:
                continue
            pose = tl(f)
            w = e.runw(f)
            for k, v in E2.RUNP.items():
                pose[k] = lerp(pose[k], v, w)
            pose["run"] = w
            pose["hz"] += 0.01 * math.sin(f * 0.21 + e.i)
            pose["tp"] += 0.05 * math.sin(f * 0.17 + e.i * 2)
            p, d = e.pos_dist(f)
            c = GPOS if e.tg == "girl" else CAM0
            yaw = math.atan2(c.x - p.x, -(c.y - p.y))
            z = 3.0 * (1 - EASE["in"](clamp((f - (e.f0 - 8)) / 8)))
            S.key_enemy(e.J, f, pose, (p.x, p.y, z), 0.0, yaw, run_phase=d / 2.4)
        if e.death < SW0:
            E2.frag_burst("MFrag%d" % e.i, e.death, e.root(e.death) + Vector((0, 0, 1.1)), 22, 5.5, 0.2, 70 + e.i, frag_mats)

    # ---------------- pillar (the girl's skill) + the giant blade made of slabs
    slab_m = B.principled("slab", (0.30, 0.45, 0.95), emit=(0.2, 0.5, 1.0), strength=0.6)
    pil = B.box("Pillar", (3.0, 2.5, PH + 0.5), (0, 0, -(PH + 0.5) / 2 - 0.03), slab_m, None, (PC.x, PC.y, 0), bevel=0.05)
    for k in range(4):
        B.box("PillarBand", (3.12, 2.62, 0.14), (0, 0, -0.6 - 1.7 * k), M["bolt_glow"], pil, bevel=0)
    PL = B.light("PillarL", "POINT", 0, (0.4, 0.6, 1.0), (0.7, 0.3, 3.0), 0.6, parent=pil)
    for f, v in ((1, 0), (LIFT0, 0), (LIFT0 + 6, 900), (DOWN1, 900), (DOWN1 + 10, 0)):
        PL.data.energy = v
        PL.data.keyframe_insert("energy", frame=f)
    for f in range(1, N + 1):
        B.key_loc(pil, f, (PC.x, PC.y, hT(f)))
    S.dust_ring("LiftDust", LIFT0, PC, 14, 3.4, 31, size=0.45)
    gs_m = B.principled("gslab", (0.35, 0.55, 1.0), emit=(0.25, 0.6, 1.0), strength=1.5)
    gse = gs_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    for f, v in ((1, 1.5), (ZAP - 1, 1.5), (ZAP + 2, 26), (ZAP + 12, 9), (SW0, 14), (SW1, 14), (BREAK, 3)):
        gse.default_value = v
        gse.keyframe_insert("default_value", frame=f)
    GL = 1.3 + 1.5 * NSLAB
    for k in range(NSLAB):
        ob = B.box("GSlab_%d" % k, (0.17 - 0.008 * k, 1.44, 0.035), (0, 0, 0), gs_m, P["blade"], (0, 1.3 + 1.5 * k + 0.7, 0), bevel=0.02)
        f0 = SLAB0 + 3 * k
        for f, s in ((1, 0.001), (f0, 0.001), (f0 + 3, 1.25), (f0 + 5, 1.0), (BREAK - 1, 1.0), (BREAK, 0.001)):
            S.key_scale(ob, f, s)

    # ---------------- the girl
    G = Human("G", B.principled("g_cloth", (0.10, 0.25, 0.55)), B.principled("g_dark", (0.05, 0.06, 0.16)), (0.07, 0.05, 0.10), 0.86,
              B.principled("g_blade", (0.8, 0.9, 1.0), emit=(0.5, 0.9, 1.0), strength=3.0))
    STAND = dict(B.E_DEF, shRx=0.05, shLx=0.05, elR=-0.25, elL=-0.25)
    GRD = dict(STANCE, shRx=-1.3, shRy=0.3, elR=-0.5, np=-0.1)
    GW = dict(STANCE, shRx=-2.6, shRy=0.2, elR=-0.6, tt=-0.4)
    GS = dict(STANCE, shRx=-0.8, shRy=-0.3, elR=-0.1, tt=0.45, tp=0.3)
    UPH = dict(STAND, shRx=-2.9, shRy=0.2, elR=-0.1, shLx=-2.9, shLy=-0.2, elL=-0.1, np=-0.4, tp=-0.1)
    GIV = dict(STAND, shLx=-1.5, shLy=0.1, elL=-0.1, shRx=-0.3, np=-0.15, tp=0.1)
    gtl = B.PoseTimeline(B.E_DEF, [
        (1, GRD, "smooth"), (GK1 - 8, GRD, "smooth"), (GK1 - 3, GW, "smooth"), (GK1, GS, "in"), (GK1 + 8, dict(), "smooth"), (GK1 + 16, GRD, "smooth"),
        (GK2 - 8, GRD, "smooth"), (GK2 - 3, GW, "smooth"), (GK2, GS, "in"), (GK2 + 8, dict(), "smooth"), (GK2 + 18, GRD, "smooth"),
        (LIFT0 - 12, GRD, "smooth"), (LIFT0 - 2, UPH, "out"), (LIFT1, dict(), "smooth"), (LIFT1 + 14, dict(E2.SCARED, hz=-0.1), "smooth"),
        (GIVE - 8, dict(), "smooth"), (GIVE + 2, GIV, "out"), (SLAB0 + 36, dict(), "smooth"), (ZAP - 10, dict(STAND, np=-0.45), "smooth"),
        (ZAP + 4, dict(E2.SCARED, hz=-0.25), "out"), (SW0 - 4, dict(), "smooth"), (SW0 + 4, dict(E2.CROUCH), "out"), (SW1 + 6, dict(), "smooth"),
        (SW1 + 24, dict(STAND, np=-0.2), "smooth"), (LAND - 2, dict(), "smooth"), (LAND + 6, GRD, "out"), (MASK, dict(), "smooth"),
        (REVEAL + 8, dict(E2.SCARED, hz=-0.1), "out"), (N, dict(), "smooth")])
    gyaw = Track([(1, 0.75), (40, 0.75), (GK1 - 14, -2.45, "smooth"), (GK1 + 10, -2.45), (GK2 - 10, -1.5, "smooth"), (GK2 + 12, -1.5),
                  (190, -2.6, "smooth"), (LIFT1, -2.6), (GIVE - 6, -5.0, "smooth"), (SLAB0 + 36, -5.0), (ZAP - 10, -4.2, "smooth"),
                  (DOWN0, -4.2), (DOWN1, -math.pi, "smooth"), (N, -math.pi)])
    gxy = Track([(1, (-1.05, 8.6)), (176, (-1.05, 8.6)), (196, (-1.4, 7.5), "smooth"), (N, (-1.4, 7.5))])
    for f in range(1, N + 1):
        pose = gtl(f)
        pose["hz"] += 0.006 * math.sin(f * 0.2)
        x, y = gxy(f)
        S.key_enemy(G.J, f, pose, (x, y, hT(f)), 0.0, gyaw(f), run_phase=0.0)

    # ---------------- the last one: the champion (future self)
    C = Human("C", M["sleeve"], B.principled("c_dark", (0.10, 0.03, 0.05)), (0.55, 0.55, 0.60), 1.0,
              B.principled("c_blade", (0.78, 0.80, 0.92), emit=(0.4, 0.8, 1.0), strength=4.0))
    B.box("C_scar", (0.05, 0.02, 0.30), (0.12, -0.235, 0.25), B.principled("c_scar", (0.45, 0.08, 0.10)), C.neck, bevel=0,
          rot=Matrix.Rotation(0.3, 3, 'Y'))
    mask_m = B.principled("c_mask", (0.9, 0.9, 0.95))
    mask = B.box("C_mask", (0.52, 0.05, 0.48), (0, -0.265, 0.24), mask_m, C.neck, bevel=0.01)
    B.box("C_maskeye", (0.34, 0.02, 0.05), (0, -0.30, 0.28), M["eye_red"], mask, bevel=0)
    for f, s in ((1, 1.0), (MASK - 1, 1.0), (MASK, 0.001)):
        S.key_scale(mask, f, s)
    E2.frag_burst("MaskFrag", MASK, CH_B + Vector((0, -0.3, 1.78)), 14, 3.0, 0.09, 61, [mask_m], life=30)
    CWALK = dict(STAND, shRx=0.1, elR=-0.15)
    ctl = B.PoseTimeline(B.E_DEF, [
        (1, CWALK, "smooth"), (LAND, dict(E2.CROUCH), "smooth"), (LAND + 12, CWALK, "smooth"), (MASK - 16, CWALK, "smooth"),
        (MASK - 4, dict(CWALK, shLx=-1.7, shLy=0.5, elL=-2.1), "smooth"), (MASK + 2, dict(CWALK, shLx=-1.2, shLy=-0.7, elL=-0.4), "out"),
        (MASK + 22, CWALK, "smooth"), (630, dict(), "smooth"), (642, dict(CWALK, shRx=-1.45, shRy=0.05, elR=-0.05, tp=0.1), "smooth"), (N, dict(), "smooth")])
    W0, W1 = LAND + 14, MASK - 12
    for f in range(1, N + 1):
        S.key_scale(C.J["root"], f, 1.0 if f >= LAND - 6 else 0.001)
        if f < LAND - 7:
            continue
        t = clamp((f - W0) / (W1 - W0))
        w = 0.55 * min(clamp((f - W0) / 4), clamp((W1 - f) / 4))
        p = CH_A.lerp(CH_B, t)
        pose = ctl(f)
        pose["run"] = w
        z = 14.0 * (1 - EASE["in"](clamp((f - (LAND - 6)) / 6)))
        S.key_enemy(C.J, f, pose, (p.x, p.y, z), 0.0, 0.0, run_phase=(CH_A - CH_B).length * t / 1.5)
    S.dust_ring("ChampDust", LAND, CH_A, 12, 3.2, 77, size=0.5)

    # ---------------- camera + hands
    yawT = Track([(1, 0), (6, 0), (18, -55, "smooth"), (40, 55, "smooth"), (56, 0, "smooth"), (88, 0), (94, 8, "smooth"), (98, 8),
                  (105, -36, "smooth"), (108, -36), (115, 42, "smooth"), (124, 42), (134, 0, "smooth"), (136, 0), (141, -46, "smooth"),
                  (144, -46), (151, 0, "smooth"), (SPIN0, 0), (SPIN1, -360, "smooth"), (SPIN1 + 1, 0), (250, 0), (270, 20, "smooth"),
                  (284, 0, "smooth"), (GIVE, -66, "smooth"), (326, -66), (340, 0, "smooth"), (N, 0)])
    pitT = Track([(1, 3), (56, -2, "smooth"), (SPIN1, -3), (LIFT0, -6), (240, -40, "smooth"), (282, -54, "smooth"), (GIVE, -6, "smooth"),
                  (326, -6), (342, 50, "smooth"), (384, 50), (398, -10, "smooth"), (SW0, -22, "smooth"), (SW1, -22), (462, -30, "smooth"),
                  (500, -8, "smooth"), (516, 1, "smooth"), (MASK + 4, 1), (REVEAL + 6, 12, "smooth"), (640, 4, "smooth"), (N, 3)])
    rollT = Track([(1, 0), (SW0 - 2, 0), (SW0 + 8, -0.10, "smooth"), (SW1 - 6, -0.10), (SW1 + 6, 0, "smooth"), (N, 0)])
    RH1, LH1 = B.RH(1), B.LH(1)
    LOW = (0.19, -0.44, -0.50, 0.25, 0.3, -0.92)
    WU = (0.20, -0.20, -0.36, 0.3, 0.6, 0.5)
    SL = (0.08, -0.10, -0.62, 0.0, 0.25, -1.0)
    WUL = (-0.02, -0.20, -0.42, -0.9, 0.35, -0.1)
    SLR = (0.26, -0.24, -0.50, 0.9, 0.05, -0.45)
    UP = (0.10, -0.12, -0.52, 0.0, 1.0, -0.12)
    UPF = (0.17, -0.17, -0.50, -0.20, 0.60, -0.78)
    SWP = (0.20, -0.18, -0.52, -0.42, -0.06, -1.0)
    rh = Track([(1, RH1), (K1 - 12, RH1), (K1 - 4, WU, "smooth"), (K1, SL, "in"), (K1 + 8, SL), (K2 - 8, WUL, "smooth"), (K2, SLR, "in"),
                (K2 + 6, SLR), (K3 - 8, WU, "smooth"), (K3 - 3, WU), (K3, SL, "in"), (K3 + 8, SL), (K3 + 22, RH1, "smooth"),
                (K4 - 8, WUL, "smooth"), (K4, SLR, "in"), (K4 + 8, SLR), (K4 + 22, RH1, "smooth"), (GIVE - 6, RH1), (GIVE + 4, UP, "smooth"),
                (330, UP), (342, UPF, "smooth"), (384, UPF), (398, (0.22, -0.14, -0.40, 0.5, 0.6, 0.5), "smooth"), (SW0, SWP, "in"),
                (SW1 + 10, SWP), (BREAK + 14, RH1, "smooth"), (LAND - 10, RH1), (LAND + 14, LOW, "smooth"), (MASK, LOW),
                (REVEAL + 6, RH1, "out"), (N, RH1)])
    LHL = (-0.17, -0.42, -0.42)
    lh = Track([(1, LH1), (K4 + 22, LH1), (LIFT0, LHL, "smooth"), (LIFT0 + 6, (-0.14, -0.20, -0.50), "out"), (LIFT1 + 10, LHL, "smooth"),
                (SW0 - 6, LHL), (SW0, (-0.16, -0.16, -0.56), "out"), (SW1 + 10, (-0.16, -0.16, -0.56)), (BREAK + 14, LH1, "smooth"),
                (LAND + 14, LHL, "smooth"), (MASK, LHL), (REVEAL + 6, LH1, "out"), (N, LH1)])
    shakes = [(K1, 0.035, 4), (K2, 0.035, 4), (K3, 0.035, 4), (K4, 0.045, 5), (LIFT0, 0.05, 18), (ZAP, 0.09, 6), (SW0, 0.06, 5),
              (SW1, 0.05, 8), (BREAK, 0.03, 5), (LAND, 0.08, 6), (MASK, 0.03, 4), (REVEAL, 0.06, 8)]
    camx = Track([(1, 0.0), (DOWN0, 0.0), (DOWN1, 0.9, "smooth"), (N, 0.9)])
    prevq = {}
    for f in range(1, N + 1):
        sv, sr = Vector((0, 0, 0)), 0.0
        for f0, amp, dc in shakes:
            a, r = S.shake(f, f0, amp, dc)
            sv += a
            sr += r
        if LIFT0 < f < LIFT1:                                   # rumble while the pillar rises
            sv += Vector((0.012 * math.sin(f * 2.3), 0, 0.012 * math.sin(f * 3.1)))
        cp = CAM0 + Vector((camx(f), 0, hT(f))) + sv + Vector((0, 0, 0.006 * math.sin(f * 0.25)))
        ya, pi_ = math.radians(yawT(f) + sweep(f)), math.radians(pitT(f))
        d = Vector((math.sin(ya) * math.cos(pi_), math.cos(ya) * math.cos(pi_), math.sin(pi_)))
        S.key_player(P, f, cp, cp + d * 10, rollT(f) + sr, rh(f), lh(f), prevq)

    # ---------------- sword glow, bolts, trails, flashes
    bl = M["blade"].node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"]
    for f, v in ((1, 3.0), (ZAP - 1, 3.0), (ZAP + 2, 18), (BREAK, 10), (BREAK + 20, 3.0)):
        bl.default_value = v
        bl.keyframe_insert("default_value", frame=f)
    for a, b_ in ((K1 - 5, K1 + 1), (K2 - 5, K2 + 1), (K3 - 5, K3 + 1), (K4 - 5, K4 + 1)):
        E2.slash_trail(P, a, b_)
    for f in range(GIVE + 2, SLAB0 + 3 * NSLAB + 4):            # the girl's power streams into the blade
        scene.frame_set(f)
        a = G.J["elL"].matrix_world @ Vector((0, 0, -0.45))
        b_ = P["blade"].matrix_world @ Vector((0, 0.6 + min(GL, 1.5 * (f - SLAB0) / 3.0), 0))
        E2.bolts("Give", f, [(a, b_)] * 2, ("bolt_core", "bolt_glow"), amp=0.25, w=0.03, branches=1)
    for f in range(ZAP, SW1 + 8):
        scene.frame_set(f)
        mw = P["blade"].matrix_world
        pts = [mw @ Vector((0, 0.3 + GL * k / 6.0, 0)) for k in range(7)]
        if f < ZAP + 6:
            top = pts[-1] + Vector((random.Random(f).uniform(-3, 3), 4.0, 45.0))
            E2.bolts("SkyBolt", f, [(top, pts[-1])] * 3, ("bolt_core", "bolt_glow"), amp=1.6, w=0.22, branches=6)
        E2.bolts("BladeBolt", f, list(zip(pts, pts[1:])), ("bolt_core", "bolt_glow"), amp=0.10, w=0.012, branches=1)
    E2.frag_burst("SlabBreak", BREAK, CAM0 + Vector((-2, 6, PH - 1.0)), 30, 7.0, 0.3, 88, [gs_m, slab_m], life=30)
    E2.bolts("ChampBolt", LAND, [(CH_A + Vector((0, 6, 40)), CH_A)] * 3, ("rbolt_core", "rbolt_glow"), amp=1.2, w=0.2, branches=4)
    E2.bolts("ChampBolt", LAND + 1, [(CH_A + Vector((0, 6, 40)), CH_A)] * 2, ("rbolt_core", "rbolt_glow"), amp=1.2, w=0.12, branches=3)
    for name, col, loc, keys in (
            ("SkillL", (0.3, 0.5, 1.0), (0, 9.0, PH + 3.0), ((1, 0), (GIVE, 0), (GIVE + 8, 1500), (ZAP - 1, 1500), (ZAP, 9000), (ZAP + 14, 2500), (BREAK, 2500), (BREAK + 12, 0))),
            ("SweepL", (0.5, 0.75, 1.0), (0, 7.0, 4.0), ((1, 0), (SW0 - 1, 0), (SW0, 6000), (SW1, 6000), (SW1 + 14, 0))),
            ("ChampL", (1.0, 0.15, 0.12), (0, 20.0, 3.0), ((1, 0), (LAND - 1, 0), (LAND, 6000), (LAND + 10, 500), (N, 500))),
            ("ChampKey", (1.0, 0.8, 0.75), (1.2, 10.6, 2.6), ((1, 0), (MASK - 30, 0), (MASK, 500), (N, 500)))):
        L = B.light(name, "POINT", 0, col, loc, 0.5)
        for f, v in keys:
            L.data.energy = v
            L.data.keyframe_insert("energy", frame=f)
    wm = S.fade_material("FlashWhite", (5, 5, 5))
    S.cam_overlay(cam, "FlashPlane", wm, -0.06)
    for f, v in ((1, 0), (ZAP - 1, 0), (ZAP, 0.55), (ZAP + 6, 0), (SW0 - 1, 0), (SW0, 0.3), (SW0 + 4, 0), (SW1 - 2, 0), (SW1 + 2, 0.6), (SW1 + 12, 0),
                 (LAND - 1, 0), (LAND, 0.35), (LAND + 5, 0), (REVEAL - 1, 0), (REVEAL, 0.25), (REVEAL + 5, 0)):
        S.key_fade(wm, f, v)
    bk = S.fade_material("FadeBlack", (0, 0, 0))
    S.cam_overlay(cam, "FadePlane", bk, -0.05)
    for f, v in ((1, 0), (FADE0, 0), (FADE0 + 10, 1.0)):
        S.key_fade(bk, f, v)
    for body, size, col, y, d in (("異世界デスゲーム", 0.0034, (1.0, 0.5, 0.9), 0.004, 0),
                                  ("― 第四話「一万対二」 ―", 0.0019, (0.9, 0.85, 1.0), -0.0025, 3),
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
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "isekai_ep4.blend"))
    os.makedirs(FRAME_DIR, exist_ok=True)
    frames = []
    if B.FRAMES_ARG and B.FRAMES_ARG is not True:
        frames = [int(x) for x in B.FRAMES_ARG.split(",")]
    elif B.DO_ANIM:
        frames = [f for f in range(1, 672 + 1) if not os.path.exists(os.path.join(FRAME_DIR, "%04d.png" % f))]
    import time
    for f in frames:
        t0 = time.time()
        scene.frame_set(f)
        scene.render.filepath = os.path.join(FRAME_DIR, "%04d.png" % f)
        bpy.ops.render.render(write_still=True)
        print("frame %d  %.1fs" % (f, time.time() - t0), flush=True)

if __name__ == "__main__":
    main()
