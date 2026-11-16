"""
create_ep5.py  ―  異世界デスゲーム 第五話「俺 対 俺」（一人称・720x1280・24fps・696f + タイトル静止）

  0s   未来の自分が斬りかかる → 四連撃を全部同じ動きで返される → 雷刃どうしの撃ち合いで吹き飛ぶ
  7s   少女の足場投げも斬られ、赤い『足場』の檻に閉じ込められる（相手も同じスキル）
  9s   真相：優勝者は次の「最後の一人」になる。未来の俺は少女を守れなかった
  12s  赤い【天断】が振り下ろされる → 受け止めるが膝をつく、剣が折れそう
  17s  少女が檻を破って刃を重ねる →「俺は一人じゃない」→ 赤い刃を砕いて二人で十字斬り
  22s  未来の俺「核はあの眼の奥だ」→ 消える → 遺された剣を左手に（二刀流）→ 真・最終回戦

  python create_ep5.py --anim --samples 24
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
import create_ep4 as E4

scene, M = B.scene, B.M
Track, EASE, lerp, clamp = B.Track, B.EASE, B.lerp, B.clamp
STANCE, ANK = B.STANCE, B.ANK
N = 696
FRAME_DIR = B.arg("--frame-dir", os.path.join(HERE, "frames_E5"))
random.seed(505)

CL = [44, 60, 74, 88]
CHG, BEAM = 116, 150
THROWS = [178, 184, 190]
CAGE, TRUTH, MEM0, MEMX = 204, 216, 236, 262
RED0, SWING, BLOCK = 286, 344, 356
CAGEX, JOIN, SHAT = 404, 436, 478
DASH1, XS, DISS, CATCH, SKY, FADE0 = 508, 512, 612, 636, 652, 672
NRED = 10
EYEPT = Vector((0, 45.2, 15.2))
GCAGE = Vector((-1.4, 7.5, 0))

camT = Track([(1, (0.9, 7.0, 1.62)), (BEAM, (0.9, 7.0, 1.62)), (BEAM + 16, (0.9, 5.6, 1.62), "out"), (BLOCK - 1, (0.9, 5.6, 1.62)),
              (BLOCK + 6, (0.9, 5.6, 1.30), "out"), (JOIN, (0.9, 5.6, 1.30)), (SHAT - 2, (0.9, 5.6, 1.46), "smooth"), (SHAT + 6, (0.9, 5.6, 1.62), "out"),
              (DASH1, (0.9, 11.0, 1.62), "in"), (N, (0.9, 11.0, 1.62))])
chT = Track([(1, (0.8, 12.5)), (34, (0.8, 12.5)), (CL[0], (0.9, 8.95), "in"), (96, (0.9, 8.95)), (110, (0.8, 13.0), "out"), (N, (0.8, 13.0))])
gT = Track([(1, (-1.4, 7.5)), (CAGEX + 6, (-1.4, 7.5)), (JOIN - 4, (0.3, 6.95), "smooth"), (SHAT + 6, (0.3, 6.95)), (DASH1, (-0.25, 11.3), "in"), (N, (-0.25, 11.3))])

def build():
    flames, floats = B.build_arena()
    P = B.build_player()
    S.env_life(flames, floats, N)
    cam = P["cam"]
    pe = M["portal"].node_tree.nodes["Emission"]
    pe.inputs["Color"].default_value = (1.0, 0.10, 0.12, 1)
    for f, v in ((1, 4.0), (SKY - 1, 4.0), (SKY, 0.3)):
        pe.inputs["Strength"].default_value = v
        pe.inputs["Strength"].keyframe_insert("default_value", frame=f)
    for n in ("Crowd", "CrowdEyes"):
        bpy.data.objects[n].hide_render = True

    # ---------------- sky text + the eye returning
    rmat = B.emissive("txt_rule", (1.0, 0.10, 0.18), 9.0)
    def sky(name, body, size, z, keys, x=0.0):
        o = S.text_obj(name, body, size, rmat, (x, 44, z), extrude=0.3)
        o.rotation_euler = (math.pi / 2, 0, 0)
        for f, s in keys:
            S.key_scale(o, f, s)
    sky("T_final", "最終回戦", 4.4, 18.2, ((1, 1.0), (SKY - 1, 1.0), (SKY, 0.001)))
    sky("T_you", "未来のお前", 3.2, 13.2, ((1, 1.0), (TRUTH + 7, 1.0), (TRUTH + 8, 0.001)), 2.2)
    sky("T_truth", "優勝者＝次の敵", 2.7, 13.2, ((1, 0.001), (TRUTH + 7, 0.001), (TRUTH + 8, 1.25), (TRUTH + 13, 1.0), (SKY - 1, 1.0), (SKY, 0.001)), 2.4)
    sky("T_true", "真・最終回戦", 3.4, 21.0, ((1, 0.001), (SKY + 7, 0.001), (SKY + 8, 1.25), (SKY + 13, 1.0)))
    eye = B.empty("Eye", None, tuple(EYEPT))
    B.box("EyeWhite", (10.5, 0.4, 5.4), (0, 0, 0), B.emissive("eye_w", (0.95, 0.9, 0.95), 1.6), eye, bevel=0)
    B.box("EyeIris", (3.4, 0.5, 3.4), (0, -0.2, 0), B.emissive("eye_iris", (1.0, 0.08, 0.10), 14.0), eye, bevel=0)
    B.box("EyePupil", (1.3, 0.6, 1.5), (0, -0.4, 0), B.principled("eye_p", (0, 0, 0)), eye, bevel=0)
    for f, sz in ((1, 0.001), (SKY, 0.001), (SKY + 7, 1.15), (SKY + 11, 1.0)):
        S.key_scale(eye, f, (1, 1, sz))

    # ---------------- champion (future self) and the girl
    red_m = B.principled("rslab", (0.95, 0.10, 0.12), emit=(1.0, 0.08, 0.08), strength=1.2)
    slab_m = B.principled("slab", (0.30, 0.45, 0.95), emit=(0.2, 0.5, 1.0), strength=0.6)
    c_dark = B.principled("c_dark", (0.10, 0.03, 0.05))
    C = E4.Human("C", M["sleeve"], c_dark, (0.55, 0.55, 0.60), 1.0,
                 B.principled("c_blade", (0.78, 0.80, 0.92), emit=(1.0, 0.25, 0.2), strength=4.0))
    B.box("C_scar", (0.05, 0.02, 0.30), (0.12, -0.235, 0.25), B.principled("c_scar", (0.45, 0.08, 0.10)), C.neck, bevel=0, rot=Matrix.Rotation(0.3, 3, 'Y'))
    G = E4.Human("G", B.principled("g_cloth", (0.10, 0.25, 0.55)), B.principled("g_dark", (0.05, 0.06, 0.16)), (0.07, 0.05, 0.10), 0.86,
                 B.principled("g_blade", (0.8, 0.9, 1.0), emit=(0.5, 0.9, 1.0), strength=3.0))
    STAND = dict(B.E_DEF, shRx=0.05, shLx=0.05, elR=-0.25, elL=-0.25)
    GRD = dict(STANCE, shRx=-1.3, shRy=0.3, elR=-0.5, np=-0.1)
    POINT = dict(STAND, shRx=-1.45, shRy=0.05, elR=-0.05, tp=0.1)
    UPR = dict(STAND, shRx=-3.0, shRy=0.05, elR=0.0, tp=-0.15, np=-0.2)
    DOWNR = dict(STANCE, shRx=-2.0, shRy=0.0, elR=0.0, tp=0.35, hz=-0.15, shLx=-0.3, elL=-0.6)
    KNEEL = dict(E2.CROUCH, hz=-0.52, tp=0.35, np=0.25, shRx=-0.2, shRy=0.1, elR=-0.3, shLx=-0.2, shLy=-0.1, elL=-0.3)
    ckeys = [(1, POINT, "smooth"), (30, GRD, "smooth")]
    for i, c in enumerate(CL):
        ckeys += [(c - 6, dict(E2.WIND, tt=-0.38 if i % 2 == 0 else 0.38), "smooth"), (c, dict(E2.THROW, tt=0.32 if i % 2 == 0 else -0.32), "in"), (c + 4, dict(), "lin")]
    ckeys += [(100, dict(E2.CROUCH), "smooth"), (110, GRD, "smooth"), (CHG + 8, UPR, "smooth"), (BEAM - 4, dict(), "smooth"), (BEAM, POINT, "in"),
              (BEAM + 18, dict(), "smooth"), (176, GRD, "smooth")]
    for k, f0 in enumerate(THROWS):
        ckeys += [(f0 + 5, dict(E2.WIND), "smooth"), (f0 + 8, dict(E2.THROW), "in")]
    ckeys += [(CAGE - 2, dict(STAND, shLx=-1.5, shLy=0.0, elL=-0.1, tp=0.1), "out"), (CAGE + 10, dict(), "smooth"), (TRUTH + 8, STAND, "smooth"),
              (MEM0 - 8, dict(), "smooth"), (MEM0, dict(STAND, shLx=-1.1, shLy=-0.9, elL=-0.7, np=0.15), "smooth"), (MEMX, dict(), "smooth"),
              (MEMX + 10, dict(STAND, np=0.4, tp=0.15), "smooth"), (RED0 - 4, dict(), "smooth"), (RED0 + 8, UPR, "smooth"), (SWING, dict(UPR, tp=-0.3), "smooth"),
              (BLOCK, DOWNR, "in"), (SHAT - 1, dict(DOWNR, tp=0.5, hz=-0.22, shRx=-2.13), "smooth"), (SHAT + 5, dict(E2.STAGGER), "out"), (XS - 1, dict(), "smooth"),
              (XS + 4, dict(E2.STAGGER, tp=-0.9), "out"), (XS + 18, KNEEL, "smooth"), (DISS - 30, dict(), "smooth"), (DISS - 10, dict(KNEEL, np=-0.25), "smooth"), (N, dict(), "smooth")]
    ctl = B.PoseTimeline(B.E_DEF, ckeys)
    for f in range(1, DISS + 2):
        x, y = chT(f)
        pose = ctl(f)
        w = min(clamp((f - 34) / 3), clamp((CL[0] - f) / 3)) if f < 60 else 0.0
        for k, v in E2.RUNP.items():
            pose[k] = lerp(pose[k], v, w)
        pose["run"] = w
        pose["hz"] += 0.006 * math.sin(f * 0.2)
        S.key_enemy(C.J, f, pose, (x, y, 0.0), 0.0, 0.0, run_phase=(12.5 - y) / 2.2)
        S.key_scale(C.J["root"], f, 1.0 if f < DISS else 0.001)
    cmats = [M["sleeve"], c_dark, M["spark"]]
    E2.frag_burst("ChampFrag", DISS, Vector((0.8, 13.0, 0.8)), 40, 3.5, 0.16, 12, cmats, life=40)

    UPH = dict(STAND, shRx=-2.9, shRy=0.2, elR=-0.1, shLx=-2.9, shLy=-0.2, elL=-0.1, np=-0.2, tp=-0.1)
    THR = dict(STAND, shRx=-1.5, shLx=-1.5, elR=-0.1, elL=-0.1, tp=0.3)
    POUND = dict(STAND, shRx=-1.6, shLx=-1.6, elR=-0.9, elL=-0.9, tp=0.2)
    BLK = dict(STANCE, shRx=-2.7, shRy=0.1, elR=-0.2, shLx=-2.5, shLy=-0.1, elL=-0.4, tp=-0.1)
    GW = dict(STANCE, shRx=-2.6, shRy=0.2, elR=-0.6, tt=-0.4)
    GS = dict(STANCE, shRx=-0.8, shRy=-0.3, elR=-0.1, tt=0.45, tp=0.3)
    gkeys = [(1, GRD, "smooth"), (168, GRD, "smooth")]
    for f0 in THROWS:
        gkeys += [(f0 - 4, UPH, "smooth"), (f0, THR, "in")]
    gkeys += [(198, GRD, "smooth"), (CAGE + 4, dict(E2.SCARED), "out"), (236, POUND, "smooth"), (CAGEX - 6, dict(), "smooth"), (CAGEX, UPH, "out"),
              (CAGEX + 8, GRD, "smooth"), (JOIN - 4, dict(), "smooth"), (JOIN, BLK, "out"), (SHAT, dict(), "smooth"), (SHAT + 6, GRD, "smooth"),
              (XS - 5, GW, "smooth"), (XS, GS, "in"), (XS + 12, GRD, "smooth"), (544, STAND, "smooth"), (N, dict(), "smooth")]
    gtl = B.PoseTimeline(B.E_DEF, gkeys)
    gdist = 0.0
    prev = Vector(gT(1))
    for f in range(1, N + 1):
        p = Vector(gT(f))
        gdist += (p - prev).length
        w = clamp((p - prev).length / 0.08)
        prev = p
        pose = gtl(f)
        for k, v in E2.RUNP.items():
            pose[k] = lerp(pose[k], v, w)
        pose["run"] = w
        pose["hz"] += 0.006 * math.sin(f * 0.2)
        if 236 <= f < CAGEX - 6:                                # pounding on the bars
            pose["elR"] += 0.5 * math.sin(f * 0.9)
            pose["elL"] += 0.5 * math.sin(f * 0.9 + 1.5)
        S.key_enemy(G.J, f, pose, (p.x, p.y, 0.0), 0.0, math.pi, run_phase=gdist / 2.0)

    # ---------------- thrown slabs, cage, memory figure, giant red blade
    for k, f0 in enumerate(THROWS):
        ob = B.box("Thrown_%d" % k, (1.1, 0.18, 0.7), (0, 0, 0), slab_m, bevel=0.03)
        a, b_ = Vector((-1.4 + 0.2 * k, 8.0, 1.9)), Vector((0.8 - 0.3 * (k - 1), 12.4, 1.3 + 0.2 * k))
        for f, s in ((1, 0.001), (f0 - 1, 0.001), (f0, 1.0), (f0 + 7, 1.0), (f0 + 8, 0.001)):
            S.key_scale(ob, f, s)
        for f in range(f0, f0 + 9):
            t = (f - f0) / 8.0
            B.key_loc(ob, f, tuple(a.lerp(b_, t) + Vector((0, 0, 0.5 * math.sin(math.pi * t)))))
            ob.rotation_euler = (0.9 * (f - f0), 0, 0.5 * k)
            ob.keyframe_insert("rotation_euler", frame=f)
        E2.frag_burst("ThrFrag%d" % k, f0 + 8, b_, 12, 5.0, 0.2, 30 + k, [slab_m])
    bm = bmesh.new()
    for sx, sy in ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)):
        B.bm_box(bm, (0.12, 0.12, 2.3), (sx * 0.75, sy * 0.75, 1.15))
    B.bm_box(bm, (1.75, 1.75, 0.14), (0, 0, 2.3))
    cage = B.mesh_obj("Cage", bm, red_m, None, tuple(GCAGE), bevel=0.02)
    for f, s in ((1, 0.001), (CAGE, 0.001), (CAGE + 4, 1.15), (CAGE + 7, 1.0), (CAGEX - 1, 1.0), (CAGEX, 0.001)):
        S.key_scale(cage, f, (1, 1, s))
    E2.frag_burst("CageFrag", CAGEX, GCAGE + Vector((0, 0, 1.3)), 30, 6.0, 0.2, 44, [red_m])
    mem_m = B.emissive("mem", (0.5, 0.8, 1.0), 2.5)
    MEMP = Vector((2.2, 12.4, 0))
    bm = bmesh.new()
    for size, off in (((0.34, 0.24, 0.6), (0, 0, 0.3)), ((0.44, 0.28, 0.55), (0, 0, 0.88)), ((0.36, 0.34, 0.34), (0, 0, 1.36)),
                      ((0.12, 0.14, 0.5), (-0.29, 0, 0.9)), ((0.12, 0.14, 0.5), (0.29, 0, 0.9)), ((0.40, 0.12, 0.5), (0, 0.2, 1.2))):
        B.bm_box(bm, size, off)
    mem = B.mesh_obj("Memory", bm, mem_m, None, tuple(MEMP), bevel=0.02)
    for f, s in ((1, 0.001), (MEM0, 0.001), (MEM0 + 6, 1.1), (MEM0 + 9, 1.0), (MEMX - 1, 1.0), (MEMX, 0.001)):
        S.key_scale(mem, f, s)
    E2.frag_burst("MemFrag", MEMX, MEMP + Vector((0, 0, 0.9)), 26, 2.5, 0.14, 55, [mem_m], life=44)
    RL = 1.6 + 1.5 * NRED
    for k in range(NRED):
        ob = B.box("RSlab_%d" % k, (0.20 - 0.01 * k, 0.045, 1.44), (0, 0, 0), red_m, C.blade, (0, 0, -(1.6 + 1.5 * k + 0.72)), bevel=0.02)
        f0 = RED0 + 6 + 3 * k
        for f, s in ((1, 0.001), (f0, 0.001), (f0 + 3, 1.25), (f0 + 5, 1.0), (SHAT - 1, 1.0), (SHAT, 0.001)):
            S.key_scale(ob, f, s)
    rse = red_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    for f, v in ((1, 1.2), (SWING - 10, 1.2), (SWING, 10), (SHAT, 10)):
        rse.default_value = v
        rse.keyframe_insert("default_value", frame=f)
    for k, y in enumerate((7.0, 9.0, 11.0)):
        E2.frag_burst("RedBreak%d" % k, SHAT, Vector((0.9, y, 2.1)), 16, 7.0, 0.26, 90 + k, [red_m], life=30)

    # relic sword: flies to the hero, then sits in the left hand
    relic_m = B.principled("relic", (0.78, 0.80, 0.92), emit=(1.0, 0.3, 0.2), strength=5.0)
    def sword_mesh(name, parent, loc):
        e = B.empty(name, parent, loc)
        B.box(name + "_b", (0.07, 0.95, 0.02), (0, 0.6, 0), relic_m, e, bevel=0.006)
        B.box(name + "_g", (0.24, 0.045, 0.06), (0, 0.10, 0), M["guard"], e, bevel=0.008)
        B.box(name + "_h", (0.035, 0.20, 0.035), (0, -0.02, 0), M["grip"], e, bevel=0.005)
        return e
    relic = sword_mesh("Relic", None, (0.8, 13.0, 1.0))
    held = sword_mesh("Held", cam, (-0.20, -0.30, -0.52))
    held.rotation_euler = (-0.45, 0, 0.18)
    for f, s in ((1, 0.001), (CATCH - 1, 0.001), (CATCH, 1.0)):
        S.key_scale(held, f, s)
    for f, s in ((1, 0.001), (DISS - 1, 0.001), (DISS, 1.0), (CATCH - 1, 1.0), (CATCH, 0.001)):
        S.key_scale(relic, f, s)
    for f in range(DISS, CATCH + 1):
        t = (f - DISS) / (CATCH - DISS)
        p = Vector((0.8, 13.0, 1.0)).lerp(Vector((0.72, 11.5, 1.32)), EASE["smooth"](t)) + Vector((0, 0, 0.9 * math.sin(math.pi * t)))
        B.key_loc(relic, f, tuple(p))
        relic.rotation_euler = (0.5 * (f - DISS), 0.2, 0)
        relic.keyframe_insert("rotation_euler", frame=f)

    # ---------------- camera + hands
    yawT = Track([(1, 0), (166, 0), (174, -38, "smooth"), (180, -38), (190, 0, "smooth"), (200, 0), (206, -48, "smooth"), (214, -48),
                  (224, 0, "smooth"), (236, 0), (244, 12, "smooth"), (264, 12), (276, 0, "smooth"), (CAGEX - 6, 0), (CAGEX, -46, "smooth"),
                  (CAGEX + 8, -46), (JOIN - 6, -10, "smooth"), (SHAT, -8), (SHAT + 8, 0, "smooth"), (N, 0)])
    pitT = Track([(1, 2), (BEAM, 3), (236, 2), (RED0, 2), (RED0 + 24, 32, "smooth"), (SWING - 4, 32), (BLOCK, 16, "in"), (CAGEX - 6, 16),
                  (CAGEX, 0, "smooth"), (CAGEX + 8, 0), (JOIN - 6, 16, "smooth"), (SHAT, 18), (SHAT + 8, 2, "smooth"), (XS, 0), (XS + 20, -15, "smooth"),
                  (DISS, -15), (DISS + 12, 2, "smooth"), (CATCH, -6, "smooth"), (SKY - 4, -4), (SKY + 8, 19, "smooth"), (N, 19)])
    rollT = Track([(1, 0), (BEAM, 0), (BEAM + 6, 0.08, "out"), (BEAM + 20, 0, "smooth"), (BLOCK, 0), (BLOCK + 4, -0.06, "out"), (SHAT, -0.03), (SHAT + 6, 0), (N, 0)])
    RH1, LH1 = B.RH(1), B.LH(1)
    LOW = (0.19, -0.44, -0.50, 0.25, 0.3, -0.92)
    WU = (0.20, -0.20, -0.36, 0.3, 0.6, 0.5)
    SL = (0.08, -0.10, -0.62, 0.0, 0.25, -1.0)
    UP = (0.10, -0.12, -0.52, 0.0, 1.0, -0.12)
    BLa = (0.14, -0.10, -0.48, -0.85, 0.5, -0.1)
    BLb = (0.00, -0.16, -0.48, 0.85, 0.5, -0.1)
    HB = (0.25, 0.07, -0.47, -1.0, 0.10, 0.0)
    rkeys = [(1, RH1), (CL[0] - 8, RH1)]
    for i, c in enumerate(CL):
        rkeys += [(c - 1, BLa if i % 2 == 0 else BLb, "out"), (c + 3, tuple(v + (0.03 if j == 1 else 0) for j, v in enumerate(BLa if i % 2 == 0 else BLb)), "out")]
    rkeys += [(104, RH1, "smooth"), (CHG + 2, RH1), (CHG + 12, UP, "smooth"), (BEAM - 5, UP), (BEAM, SL, "in"), (BEAM + 18, SL), (180, RH1, "smooth"),
              (SWING + 2, RH1), (BLOCK - 2, HB, "out"), (BLOCK + 4, (0.25, 0.03, -0.47, -1.0, 0.06, 0.0), "out"), (JOIN, (0.25, 0.02, -0.47, -1.0, 0.04, 0.0)),
              (SHAT - 2, (0.25, 0.10, -0.47, -1.0, 0.14, 0.0), "smooth"), (SHAT + 3, (0.25, 0.16, -0.45, -1.0, 0.3, 0.0), "out"), (XS - 6, WU, "smooth"),
              (XS, SL, "in"), (XS + 12, SL), (548, LOW, "smooth"), (CATCH + 2, LOW), (CATCH + 12, RH1, "smooth"), (N, RH1)]
    rh = Track(rkeys)
    LHL = (-0.17, -0.42, -0.42)
    SUP = (-0.12, 0.04, -0.48)
    lh = Track([(1, LH1), (SWING + 2, LH1), (BLOCK - 2, SUP, "out"), (BLOCK + 4, (-0.12, 0.0, -0.48), "out"), (JOIN, (-0.12, -0.01, -0.48)),
                (SHAT - 2, (-0.12, 0.07, -0.48), "smooth"), (SHAT + 6, LH1, "smooth"), (548, LHL, "smooth"), (DISS + 8, LHL),
                (CATCH - 3, (-0.16, -0.16, -0.60), "smooth"), (CATCH + 4, (-0.20, -0.33, -0.52), "smooth"), (N, (-0.20, -0.33, -0.52))])
    shakes = [(c, 0.05, 4) for c in CL] + [(BEAM, 0.08, 12), (BEAM + 14, 0.07, 6), (CAGE, 0.03, 5), (MEMX, 0.02, 5), (BLOCK, 0.12, 8), (CAGEX, 0.05, 5),
                                           (JOIN, 0.05, 5), (SHAT, 0.10, 7), (XS, 0.10, 6), (CATCH, 0.03, 4), (SKY + 7, 0.07, 8)]
    prevq = {}
    for f in range(1, N + 1):
        sv, sr = Vector((0, 0, 0)), 0.0
        for f0, amp, dc in shakes:
            a, r = S.shake(f, f0, amp, dc)
            sv += a
            sr += r
        if BLOCK + 8 < f < SHAT:                                 # straining under the red blade
            sv += Vector((0.006 * math.sin(f * 2.9), 0, 0.008 * math.sin(f * 3.7)))
        cp = Vector(camT(f)) + sv + Vector((0, 0, 0.006 * math.sin(f * 0.25)))
        ya, pi_ = math.radians(yawT(f)), math.radians(pitT(f))
        d = Vector((math.sin(ya) * math.cos(pi_), math.cos(ya) * math.cos(pi_), math.sin(pi_)))
        S.key_player(P, f, cp, cp + d * 10, rollT(f) + sr, rh(f), lh(f), prevq)

    # ---------------- sparks, bolts, trails, lights, flashes
    for i, c in enumerate(CL):
        ctr = Vector((0.9 + (0.15 if i % 2 else -0.15), 7.75, 1.72))
        S.dust_ring("Clash%d" % i, c, ctr, 10, 1.2, 60 + i, size=0.07, mat=M["spark"])
        L = B.light("ClashL%d" % i, "POINT", 0, (1.0, 0.85, 0.6), tuple(ctr), 0.2)
        for f, v in ((c - 1, 0), (c, 900), (c + 4, 0)):
            L.data.energy = v
            L.data.keyframe_insert("energy", frame=f)
    bl = M["blade"].node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"]
    for f, v in ((1, 3.0), (CHG, 3.0), (BEAM - 2, 16), (BEAM + 16, 3.0), (BLOCK, 3.0)):
        bl.default_value = v
        bl.keyframe_insert("default_value", frame=f)
    for f in range(BLOCK + 1, SHAT + 1):                         # the blade flickers as it starts to give
        k = clamp((f - BLOCK) / (JOIN - BLOCK))
        bl.default_value = 3.0 + (random.Random(f).uniform(-2.5, 4.0) * k if f < JOIN else 10.0)
        bl.keyframe_insert("default_value", frame=f)
    for f, v in ((SHAT + 6, 16), (XS + 8, 16), (XS + 30, 3.0)):
        bl.default_value = v
        bl.keyframe_insert("default_value", frame=f)
    MID = Vector((0.85, 9.6, 1.7))
    for f in range(CHG + 6, BEAM + 16):
        scene.frame_set(f)
        tip = P["blade"].matrix_world @ Vector((0, 1.13, 0))
        ctip = C.blade.matrix_world @ Vector((0, 0, -1.5))
        rnd = random.Random(f)
        if f < BEAM:
            for src, mats in ((tip, ("bolt_core", "bolt_glow")), (ctip, ("rbolt_core", "rbolt_glow"))):
                pairs = [(src, src + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.2, 1.5))) * 0.5) for _ in range(3)]
                E2.bolts("Chg" + mats[0][:2], f, pairs, mats, amp=0.06, w=0.012 if src is tip else 0.03, branches=0)
        else:
            E2.bolts("BeamB", f, [(tip, MID)] * 2, ("bolt_core", "bolt_glow"), amp=0.25, w=0.06, branches=2)
            E2.bolts("BeamR", f, [(ctip, MID)] * 2, ("rbolt_core", "rbolt_glow"), amp=0.35, w=0.09, branches=2)
    ball = B.box("BeamBall", (1, 1, 1), (0, 0, 0), M["bolt_core"], None, tuple(MID), bevel=0)
    for f, s in ((1, 0.001), (BEAM - 1, 0.001), (BEAM + 2, 0.3), (BEAM + 14, 0.9), (BEAM + 16, 0.001)):
        S.key_scale(ball, f, s)
    for f in range(SWING, SHAT):
        scene.frame_set(f)
        mw = C.blade.matrix_world
        pts = [mw @ Vector((0, 0, -(0.6 + RL * k / 6.0))) for k in range(7)]
        E2.bolts("RedBolt", f, list(zip(pts, pts[1:])), ("rbolt_core", "rbolt_glow"), amp=0.12, w=0.02, branches=1)
        if f >= BLOCK:                                           # sparks where the blades grind
            c = P["blade"].matrix_world @ Vector((0, 0.55, 0))
            rnd = random.Random(f * 7)
            E2.bolts("Grind", f, [(c, c + Vector((rnd.uniform(-1, 1), rnd.uniform(-0.6, 0.2), rnd.uniform(-1, 0.3))) * 0.35) for _ in range(4)],
                     ("bolt_core", "rbolt_glow"), amp=0.04, w=0.008, branches=0)
    for a, b_ in ((BEAM - 5, BEAM + 1), (XS - 5, XS + 1)):
        E2.slash_trail(P, a, b_)
    S.dust_ring("XSpark", XS, Vector((0.8, 12.6, 1.3)), 14, 2.0, 91, size=0.1, mat=M["spark"])
    S.dust_ring("DissSpark", DISS, Vector((0.8, 13.0, 0.2)), 14, 2.2, 92, size=0.08, mat=M["spark"])
    for name, col, loc, keys in (
            ("BeamL", (0.8, 0.6, 1.0), tuple(MID), ((1, 0), (BEAM - 1, 0), (BEAM, 3000), (BEAM + 14, 9000), (BEAM + 18, 0))),
            ("CageL", (1.0, 0.15, 0.1), (-1.4, 7.0, 2.6), ((1, 0), (CAGE - 1, 0), (CAGE, 1500), (CAGE + 10, 300), (CAGEX - 1, 300), (CAGEX, 2500), (CAGEX + 8, 0))),
            ("MemL", (0.5, 0.8, 1.0), (2.0, 11.6, 1.6), ((1, 0), (MEM0, 0), (MEM0 + 6, 500), (MEMX, 500), (MEMX + 6, 0))),
            ("RedL", (1.0, 0.12, 0.1), (0.9, 8.0, 3.2), ((1, 0), (RED0, 0), (SWING, 1500), (BLOCK, 4000), (SHAT, 4000), (SHAT + 4, 0))),
            ("JoinL", (0.4, 0.7, 1.0), (0.7, 6.4, 2.2), ((1, 0), (JOIN - 1, 0), (JOIN, 2500), (SHAT, 3500), (SHAT + 2, 9000), (SHAT + 10, 0))),
            ("EndL", (1.0, 0.85, 0.7), (1.6, 11.6, 2.6), ((1, 0), (XS, 0), (XS + 10, 500), (N, 500))),
            ("TrueL", (1.0, 0.1, 0.1), (0, 16.0, 6.0), ((1, 0), (SKY, 0), (SKY + 7, 5000), (N, 1500)))):
        L = B.light(name, "POINT", 0, col, loc, 0.5)
        for f, v in keys:
            L.data.energy = v
            L.data.keyframe_insert("energy", frame=f)
    wm = S.fade_material("FlashWhite", (5, 5, 5))
    S.cam_overlay(cam, "FlashPlane", wm, -0.06)
    fl = [(1, 0)]
    for c in CL:
        fl += [(c - 1, 0), (c, 0.12), (c + 3, 0)]
    fl += [(BEAM + 12, 0), (BEAM + 15, 0.8), (BEAM + 24, 0), (BLOCK - 1, 0), (BLOCK, 0.35), (BLOCK + 4, 0), (SHAT - 1, 0), (SHAT, 0.6), (SHAT + 6, 0),
           (XS - 1, 0), (XS, 0.9), (XS + 10, 0), (SKY + 6, 0), (SKY + 7, 0.3), (SKY + 12, 0)]
    for f, v in fl:
        S.key_fade(wm, f, v)
    bk = S.fade_material("FadeBlack", (0, 0, 0))
    S.cam_overlay(cam, "FadePlane", bk, -0.05)
    for f, v in ((1, 0), (FADE0, 0), (FADE0 + 10, 1.0)):
        S.key_fade(bk, f, v)
    for body, size, col, y, d in (("異世界デスゲーム", 0.0034, (1.0, 0.5, 0.9), 0.004, 0),
                                  ("― 第五話「俺 対 俺」 ―", 0.0019, (0.9, 0.85, 1.0), -0.0025, 3),
                                  ("次回　最終話", 0.0016, (1.0, 0.75, 0.3), -0.0065, 6)):
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
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "isekai_ep5.blend"))
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
