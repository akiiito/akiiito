"""
create_ep2.py  ―  異世界デスゲーム 第二話「十対一」（一人称・720x1280・24fps・696f + タイトル静止）
create_battle.py / create_isekai_short.py の部品（闘技場・敵リグ・一人称リグ）を再利用。

  0.0s  空から赤い敵が10体降ってくる            10.5s 回転斬りの後、残り6体が赤い雷を一斉発射→剣が吸収
  1.9s  一斉突撃、1体目をパリィして撃破          9.7s  雷刃の一閃で5体まとめて撃破
  5.3s  3体同時→回転斬り                        12.5s 最後の1体が破片を吸って巨大化→拳の叩きつけ
  18s   拳を足場に跳躍→頭上から雷刃              22.5s 殻が砕け、中から「人間」… 第三回戦の文字

  python create_ep2.py --anim --samples 24            （全フレーム → frames_E2/）
  python create_ep2.py --frames 1,90,240 --res 35 --samples 8 --no-save
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

scene, M = B.scene, B.M
Track, EASE, lerp, clamp = B.Track, B.EASE, B.lerp, B.clamp
STANCE, ANK = B.STANCE, B.ANK
N = 696
FRAME_DIR = B.arg("--frame-dir", os.path.join(HERE, "frames_E2"))
random.seed(52)

# ---- beat sheet (frames)
PARRY, K1 = 84, 92
SPIN0, SPIN1 = 128, 143
BOLT, SWEEP = 190, 232
ABSORB, GROW0, GROW1 = 300, 312, 340
SLAM, JUMP, HIT, LANDP, BOOM = 378, 436, 478, 500, 540
HEAD, RULE, FADE0 = 605, 640, 672
BOSS_S = 3.3 / B.E_SCALE

RED = dict(e_blue=B.principled("r_main", (0.80, 0.06, 0.09)), e_dark=B.principled("r_dark", (0.26, 0.02, 0.05)),
           e_light=B.principled("r_light", (1.0, 0.42, 0.32)), e_eye=B.emissive("r_eye", (1.0, 0.85, 0.3), 9.0))
M["rbolt_core"] = B.emissive("rbolt_core", (1.0, 0.75, 0.65), 40.0)
M["rbolt_glow"] = B.emissive("rbolt_glow", (1.0, 0.10, 0.08), 5.0)
M["trail"] = B.emissive("trail", (0.75, 0.95, 1.0), 9.0)
RUNP = dict(hz=-0.10, tp=0.38, elR=-1.5, elL=-1.5, np=-0.25)
CROUCH = dict(hz=-0.50, tp=0.75, np=-0.35, shRx=-0.55, shRy=0.15, elR=-0.2, shLx=0.4, shLy=-0.7, elL=-0.3,
              fRy=-0.35, fRz=ANK, fLy=0.40, fLz=ANK)
WIND = dict(hz=-0.14, tp=-0.28, tt=-0.38, tl=0.08, np=-0.18, shRx=-2.75, shRy=0.15, elR=-0.55,
            shLx=-1.0, shLy=-0.25, elL=-0.25, fRy=-0.20, fRz=ANK, fLy=0.32, fLz=ANK)
THROW = dict(hz=-0.22, tp=0.30, tt=0.32, tl=-0.05, np=-0.05, shRx=-1.45, shRy=0.02, elR=-0.02,
             shLx=0.35, shLy=-0.45, elL=-0.9, fRy=-0.55, fRz=ANK, fLy=0.47, fLz=ANK)
STAGGER = dict(hz=-0.12, tp=-0.6, tt=0.3, np=-0.5, shRx=-1.9, shRy=0.75, elR=-0.25, shLx=-1.3, shLy=-0.9, elL=-0.35,
               fRy=-0.45, fRz=ANK, fLy=0.2, fLz=ANK)
SCARED = dict(hz=-0.2, tp=-0.2, np=-0.1, shRx=-1.5, shRy=0.5, elR=-1.6, shLx=-1.5, shLy=-0.5, elL=-1.6,
              fRy=-0.2, fRz=ANK, fLy=0.3, fLz=ANK)

def polar(c, deg, r):
    a = math.radians(deg)
    return (c[0] + math.sin(a) * r, c[1] + math.cos(a) * r)

class En:
    """one red enemy: path segments + pose keys; always faces the player"""
    def __init__(self, i, p0):
        saved = {k: M[k] for k in RED}
        M.update(RED)
        self.J = B.build_enemy()
        M.update(saved)
        self.i, self.p0 = i, p0
        self.moves, self.keys = [], []
        self.land, self.death = 1, None
        self.scale = None
    def move(self, f0, f1, to):
        self.moves.append((f0, f1, to))
    def pos_dist(self, f):
        p, d = Vector(self.p0), 0.0
        for f0, f1, to in self.moves:
            q = Vector(to)
            t = clamp((f - f0) / (f1 - f0))
            d += (q - p).length * t
            p = p.lerp(q, t)
        return p, d
    def runw(self, f):
        return max([min(clamp((f - f0) / 3), clamp((f1 - f) / 3)) for f0, f1, _ in self.moves] + [0.0])
    def root(self, f):
        p, _ = self.pos_dist(f)
        return Vector((p.x, p.y, 0))

def frag_burst(prefix, f0, center, count, speed, size, seed, mats, life=36):
    rnd = random.Random(seed)
    for i in range(count):
        s0 = rnd.uniform(0.5, 1.0) * size
        ob = B.box("%s_%d" % (prefix, i), (1, 1, 1), (0, 0, 0), mats[i % len(mats)], bevel=0)
        v = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.1, 1.3))).normalized() * rnd.uniform(0.4, 1.0) * speed
        c = Vector(center) + Vector((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), rnd.uniform(-0.6, 0.6))) * size * 4
        spin = Vector((rnd.uniform(-9, 9), rnd.uniform(-9, 9), rnd.uniform(-9, 9)))
        S.key_scale(ob, max(1, f0 - 1), 0.001)
        for f in range(f0, f0 + life + 1, 2):
            t = (f - f0) / 24.0
            z = c.z + v.z * t - 4.9 * t * t
            k = clamp((f - f0) / life)
            ob.location = (c.x + v.x * t, c.y + v.y * t, max(z, s0 / 2))
            ob.keyframe_insert("location", frame=f)
            ob.rotation_euler = tuple(spin * t)
            ob.keyframe_insert("rotation_euler", frame=f)
            S.key_scale(ob, f, s0 * (1 - k ** 3) + 0.001)

def build_human(loc):
    """the 'player-like' figure hidden inside the boss (kneeling)"""
    skin = B.principled("h_skin", (0.86, 0.66, 0.50))
    hair = B.principled("h_hair", (0.07, 0.05, 0.10))
    cloth = B.principled("h_cloth", (0.10, 0.25, 0.55))
    eye = B.emissive("h_eye", (1.0, 1.0, 1.0), 3.0)
    root = B.empty("H_root", None, loc)
    B.box("H_legs", (0.46, 0.62, 0.22), (0, 0.12, 0.11), M["grip"], root)
    B.box("H_torso", (0.50, 0.30, 0.62), (0, 0, 0.53), cloth, root)
    B.box("H_belt", (0.52, 0.32, 0.08), (0, 0, 0.26), M["cuff"], root)
    for sx in (-1, 1):
        B.box("H_arm", (0.15, 0.17, 0.56), (sx * 0.33, -0.05, 0.50), cloth, root)
        B.box("H_hand", (0.15, 0.17, 0.13), (sx * 0.33, -0.05, 0.16), skin, root)
    neck = B.empty("H_neck", root, (0, 0, 0.86))
    B.box("H_head", (0.42, 0.40, 0.40), (0, 0, 0.20), skin, neck, bevel=0.03)
    B.box("H_hair", (0.46, 0.44, 0.16), (0, 0.02, 0.38), hair, neck, bevel=0.03)
    B.box("H_hairb", (0.46, 0.14, 0.34), (0, 0.17, 0.22), hair, neck, bevel=0.03)
    for ex in (-0.1, 0.1):
        B.box("H_eye", (0.07, 0.02, 0.09), (ex, -0.205, 0.20), eye, neck, bevel=0)
    return root, neck

def slash_trail(P, a, b):
    """emissive ribbon swept by the blade (sampled at sub-frames)"""
    blade = P["blade"]
    for f in range(a, b + 1):
        pts = []
        for k in range(9):
            fr = f - 1.7 * (1 - k / 8)
            scene.frame_set(int(math.floor(fr)), subframe=fr - math.floor(fr))
            mw = blade.matrix_world.copy()
            tip, base = mw @ Vector((0, 1.13, 0)), mw @ Vector((0, 0.2, 0))
            pts.append((tip.lerp(base, 0.15 + 0.85 * (k / 8)), tip))
        bm = bmesh.new()
        vs = [(bm.verts.new(p), bm.verts.new(q)) for p, q in pts]
        for (a0, b0), (a1, b1) in zip(vs, vs[1:]):
            bm.faces.new((a0, b0, b1, a1))
        ob = B.mesh_obj("Trail_%03d" % f, bm, M["trail"])
        ob.visible_shadow = False
        B.vis_only(ob, [f])

def bolts(name, f, pairs, mats, amp=0.2, w=0.035, branches=2):
    rnd = random.Random(f * 13 + len(name))
    bc, bg = bmesh.new(), bmesh.new()
    for a, b in pairs:
        B.add_bolt(bc, bg, a, b, rnd, amp=amp, w=w * (1 + 0.3 * rnd.random()), branches=branches)
    for bm, m in ((bc, mats[0]), (bg, mats[1])):
        ob = B.mesh_obj("%s_%03d" % (name, f), bm, M[m])
        ob.visible_shadow = False
        B.vis_only(ob, [f])

def build():
    flames, floats = B.build_arena()
    P = B.build_player()
    S.env_life(flames, floats, N)
    cam = P["cam"]
    M["portal"].node_tree.nodes["Emission"].inputs["Color"].default_value = (1.0, 0.10, 0.12, 1)

    # ---------------- sky text
    rmat = B.emissive("txt_rule", (1.0, 0.10, 0.18), 9.0)
    gmat = B.emissive("txt_gold", (1.0, 0.75, 0.25), 7.0)
    sky = [S.text_obj("T_r2", "第二回戦", 4.2, rmat, (0, 44, 17.8), extrude=0.3),
           S.text_obj("T_110", "1 対 10", 3.0, gmat, (0, 44, 13.2), extrude=0.3),
           S.text_obj("T_r3", "第三回戦", 4.2, rmat, (0, 44, 18.4), extrude=0.3),
           S.text_obj("T_kill", "仲間を殺せ", 3.6, rmat, (0, 44, 13.4), extrude=0.3)]
    for o in sky:
        o.rotation_euler = (math.pi / 2, 0, 0)
    for o in sky[:2]:
        for f, s in ((1, 1.0), (RULE - 4, 1.0), (RULE - 2, 1.15), (RULE, 0.001)):
            S.key_scale(o, f, s)
    for o, d in ((sky[2], 0), (sky[3], 4)):
        for f, s in ((1, 0.001), (RULE + d, 0.001), (RULE + d + 4, 1.2), (RULE + d + 8, 1.0)):
            S.key_scale(o, f, s)

    # ---------------- player path (yaw<0 = left; degrees)
    P0 = (0.0, 3.0)
    PB = (0.0, 1.8)                                    # where the player fights the first wave
    cpos = Track([(1, (0, 3.0, 1.62)), (46, (0, 3.0, 1.62)), (58, (0.03, 2.4, 1.60), "smooth"), (70, (0, 1.8, 1.62), "smooth"),
                  (PARRY, (0, 1.72, 1.55), "in"), (88, (0, 1.75, 1.58)), (K1, (0.05, 2.05, 1.52), "in"), (100, (0, 1.8, 1.62), "smooth"),
                  (SPIN0 - 4, (0, 1.8, 1.55), "smooth"), (SPIN1, (0, 1.8, 1.50)), (152, (0, 1.8, 1.62), "smooth"),
                  (BOLT, (0, 1.8, 1.62)), (BOLT + 4, (0, 1.68, 1.57), "out"), (222, (0, 1.75, 1.62), "smooth"),
                  (SWEEP - 2, (-0.05, 1.7, 1.56)), (SWEEP + 8, (0.08, 2.1, 1.52), "out"), (254, (0, 1.9, 1.62), "smooth"),
                  (268, (0, 1.9, 1.62)), (298, (0, 3.5, 1.62), "smooth"), (366, (0, 3.5, 1.62)),
                  (SLAM, (1.7, 2.7, 1.40), "out"), (392, (1.7, 2.7, 1.58), "smooth"), (418, (1.7, 2.7, 1.62)),
                  (JUMP - 2, (0.9, 4.3, 1.48), "in"), (462, (0.3, 6.4, 8.3), "out"), (HIT, (0.2, 7.05, 7.45), "in"),
                  (HIT + 4, (0.2, 7.07, 7.42)), (LANDP, (0.1, 4.8, 1.62), "in"), (LANDP + 2, (0.1, 4.8, 1.28), "out"),
                  (LANDP + 12, (0.1, 4.8, 1.62), "smooth"), (556, (0.1, 4.8, 1.62)), (598, (0, 6.7, 1.60), "smooth"), (N, (0, 6.8, 1.60))])
    yawT = Track([(1, -30), (4, -34), (34, 44, "smooth"), (43, 0, "smooth"), (SPIN0 - 4, 0), (SPIN0, 12, "smooth"),
                  (SPIN1, -360, "smooth"), (N, -360)])
    pitT = Track([(1, 3), (43, 1), (70, 0), (PARRY - 2, 9, "smooth"), (K1, -6, "in"), (104, 0, "smooth"), (SPIN0, -3),
                  (SPIN1, -3), (160, 2, "smooth"), (BOLT + 6, 12, "smooth"), (220, 5), (SWEEP + 6, -2), (268, 0),
                  (GROW1, 20, "smooth"), (360, 26), (SLAM, -12, "in"), (398, -4, "smooth"), (420, 22, "smooth"),
                  (JUMP, 30), (LANDP, 0), (LANDP + 2, -14, "out"), (LANDP + 16, 28, "smooth"), (BOOM, 26),
                  (562, 8, "smooth"), (598, -9, "smooth"), (RULE - 4, -9), (RULE + 8, 20, "smooth"), (660, 20),
                  (670, -9, "smooth"), (N, -9)])
    rollT = Track([(1, 0), (PARRY, 0), (PARRY + 2, -0.07), (K1 + 2, 0.12, "out"), (104, 0, "smooth"), (SPIN0, 0),
                   (SPIN0 + 4, -0.16), (SPIN1 - 2, -0.16), (SPIN1 + 6, 0, "smooth"), (SWEEP, 0), (SWEEP + 6, 0.14, "out"),
                   (252, 0, "smooth"), (366, 0), (SLAM, -0.28, "out"), (396, 0, "smooth"), (JUMP, 0), (462, 0.1),
                   (HIT, -0.06), (LANDP + 14, 0), (N, 0)])
    look_w = Track([(1, 0), (JUMP - 2, 0), (JUMP + 8, 1, "smooth"), (HIT + 6, 1), (LANDP + 2, 0, "smooth"), (N, 0)])
    HEADPT = Vector((0, 8.5, 6.2))
    RH1, LH1 = B.RH(1), B.LH(1)
    rh = Track([(1, (0.19, -0.44, -0.50, 0.25, 0.3, -0.92)), (44, (0.19, -0.44, -0.50, 0.25, 0.3, -0.92)), (56, RH1, "smooth"), (76, RH1),
                (PARRY - 1, (0.20, 0.02, -0.46, -1.0, 0.12, -0.15), "out"), (PARRY + 1, (0.20, -0.02, -0.44, -1.0, 0.10, -0.12)),
                (88, (0.22, 0.04, -0.46, -0.35, 0.85, -0.20), "smooth"), (91, (0.04, -0.19, -0.62, -0.85, 0.02, -0.52), "in"),
                (95, (-0.14, -0.28, -0.50, -0.60, -0.65, -0.20), "out"), (108, RH1, "smooth"), (SPIN0 - 6, RH1),
                (SPIN0, (0.26, -0.14, -0.50, 0.45, 0.10, -0.90), "smooth"), (SPIN1, (0.24, -0.14, -0.52, -0.30, 0.05, -0.95)),
                (154, RH1, "smooth"), (176, RH1), (BOLT - 4, (0.10, -0.13, -0.52, 0.0, 1.0, -0.12), "smooth"),
                (216, (0.10, -0.12, -0.52, 0.0, 1.0, -0.12)), (SWEEP - 2, (-0.16, -0.10, -0.44, -1.0, 0.25, -0.25), "smooth"),
                (SWEEP + 3, (0.10, -0.12, -0.56, 0.10, 0.05, -1.0), "in"), (SWEEP + 8, (0.30, -0.14, -0.44, 1.0, 0.0, -0.35), "out"),
                (258, RH1, "smooth"), (366, RH1), (SLAM, (0.24, -0.34, -0.42, 0.5, 0.4, -0.7), "out"), (400, RH1, "smooth"),
                (JUMP, (0.20, -0.36, -0.46, 0.2, 0.2, -0.95), "smooth"), (462, (0.17, 0.0, -0.44, -0.1, 1.0, 0.10), "smooth"),
                (HIT - 4, (0.17, 0.02, -0.44, -0.1, 1.0, 0.20)), (HIT, (0.06, -0.20, -0.60, 0.0, -0.25, -1.0), "in"),
                (HIT + 4, (0.06, -0.22, -0.60, 0.0, -0.30, -1.0)), (LANDP + 12, RH1, "smooth"),
                (560, (0.19, -0.44, -0.50, 0.25, 0.3, -0.92), "smooth"), (N, (0.19, -0.44, -0.50, 0.25, 0.3, -0.92))])
    LHL = (-0.17, -0.42, -0.42)
    lh = Track([(1, LHL), (44, LHL), (56, LH1, "smooth"), (PARRY - 1, (-0.06, -0.02, -0.47), "out"), (88, (-0.08, -0.06, -0.46)),
                (96, (-0.20, -0.42, -0.30), "smooth"), (110, LH1, "smooth"), (SPIN0, (-0.26, -0.20, -0.40), "smooth"),
                (SPIN1, (-0.26, -0.20, -0.40)), (154, LH1, "smooth"), (BOLT - 4, (-0.13, -0.30, -0.44), "smooth"),
                (216, (-0.13, -0.30, -0.44)), (SWEEP + 6, (-0.22, -0.40, -0.30), "smooth"), (258, LH1, "smooth"), (366, LH1),
                (SLAM, (-0.08, -0.16, -0.40), "out"), (400, LH1, "smooth"), (JUMP, LH1), (462, (-0.14, -0.24, -0.42), "smooth"),
                (HIT - 4, (-0.14, -0.24, -0.42)), (HIT, (0.02, -0.27, -0.56), "in"), (HIT + 4, (0.02, -0.28, -0.56)),
                (LANDP + 12, LH1, "smooth"), (560, LHL, "smooth"), (N, LHL)])
    def cam_xy(f):
        c = cpos(f)
        return Vector((c[0], c[1]))

    # ---------------- enemies
    E = [En(i, polar(P0, -54 + 12 * i, 8.0)) for i in range(10)]
    A, SL, SR, SF = 4, 1, 8, 5
    SIX = {0: -50, 2: -30, 3: -12, 6: 0, 7: 12, 9: 32}
    BOSS = E[6]
    for i, e in enumerate(E):
        order = [4, 5, 3, 6, 2, 7, 1, 8, 0, 9].index(i)
        e.land = 3 + int(order * 2.8)
        e.keys = [(1, dict(CROUCH, hz=-0.05, tp=-0.2, shRx=-2.6, shLx=-2.6, shLy=-0.5, fRz=0.35, fLz=0.25), "smooth"),
                  (e.land - 1, dict(), "lin"), (e.land + 1, dict(CROUCH), "out3"), (e.land + 9, dict(CROUCH, hz=-0.45), "smooth"),
                  (e.land + 17, dict(STANCE, tp=0.25, np=-0.15), "smoother")]
    # first attacker
    e = E[A]
    e.move(46, 74, polar(PB, -4, 1.75))
    e.keys += [(74, dict(STANCE), "smooth"), (80, dict(WIND, shRx=-2.9), "smooth"), (PARRY, dict(THROW, shRx=-1.9, tp=0.45), "in"),
               (PARRY + 3, dict(STAGGER), "out"), (K1, dict(STAGGER, tp=-0.75), "lin")]
    e.death = K1
    # spin-slash trio
    for i, ang, d in ((SL, -72, SPIN0 + 4), (SR, 70, SPIN0 + 11), (SF, 2, SPIN1 - 1)):
        e = E[i]
        e.move(46, 76, polar(PB, ang * 0.7, 5.2))
        e.move(104, 124, polar(PB, ang, 1.9))
        e.keys += [(100, dict(STANCE), "smooth"), (124, dict(WIND, shRx=-2.6), "smooth"), (d - 1, dict(WIND, shRx=-2.9), "smooth")]
        e.death = d
    # lightning six (boss candidate stands further back and ducks under the wave)
    kills = {}
    for k, i in enumerate((0, 2, 3, 7, 9)):
        kills[i] = SWEEP + 3 + k * 2
    for i, ang in SIX.items():
        e = E[i]
        r = 7.6 if i == 6 else 6.0
        e.move(46, 76, polar(PB, ang * 1.1, r + 0.6))
        e.move(148, 160, polar(PB, ang, r))
        e.keys += [(162, dict(STANCE), "smooth"), (178, dict(WIND), "smooth"), (BOLT - 3, dict(WIND, shRx=-2.9), "lin"),
                   (BOLT, dict(THROW), "in"), (BOLT + 14, dict(THROW, tp=0.22), "smooth"), (216, dict(STANCE), "smooth"),
                   (SWEEP, dict(SCARED), "smooth")]
        if i in kills:
            e.death = kills[i]
    b = BOSS
    BP1, BP2 = (0.0, 12.0), (0.0, 9.0)
    b.keys += [(SWEEP + 3, dict(CROUCH, hz=-0.62, tp=0.9), "out"), (SWEEP + 12, dict(CROUCH, hz=-0.62, tp=0.9), "smooth"),
               (256, dict(SCARED), "smooth"), (ABSORB, dict(SCARED, tp=-0.3), "smooth"),
               (GROW0, dict(STANCE, tp=0.5, np=0.4, shRx=0.2, shLx=0.2), "smooth"),
               (GROW1, dict(STANCE, tp=-0.25, np=-0.3, shRx=-0.9, shRy=0.9, elR=-1.4, shLx=-0.9, shLy=-0.9, elL=-1.4), "out"),
               (346, dict(STANCE, tp=0.2, np=0.25), "smooth"), (362, dict(STANCE, tp=0.2, np=0.3), "smooth"),
               (372, dict(WIND, shRx=-2.95, np=0.3), "smooth"),
               (SLAM, dict(hz=-0.38, tp=1.05, tt=0.25, np=-0.2, shRx=-1.25, shRy=0.0, elR=-0.02, shLx=0.5, shLy=-0.5, elL=-0.8,
                           fRy=-0.6, fRz=ANK, fLy=0.5, fLz=ANK), "in"),
               (402, dict(hz=-0.36, tp=1.0, tt=0.25, np=-0.3, shRx=-1.25, shRy=0.0, elR=-0.02), "smooth"),
               (JUMP + 14, dict(STANCE, tp=-0.1, np=-0.55, shRx=-0.3, shLx=-0.3), "smooth"),
               (HIT - 1, dict(STANCE, tp=-0.15, np=-0.65, shRx=-1.6, shRy=0.4, elR=-1.5, shLx=-1.6, shLy=-0.4, elL=-1.5), "smooth"),
               (HIT + 3, dict(hz=-0.25, tp=0.3, np=0.6, shRx=-0.2, shRy=0.5, elR=-0.2, shLx=-0.2, shLy=-0.5, elL=-0.2,
                              fRy=-0.3, fRz=ANK, fLy=0.3, fLz=ANK), "out"),
               (BOOM, dict(hz=-0.30, tp=0.36, np=0.66), "smooth")]
    b.move(250, 292, BP1)
    b.move(346, 368, BP2)
    b.death = BOOM
    grow = Track([(1, 1.0), (GROW0, 1.0), (GROW0 + 8, 1.5, "out"), (GROW0 + 12, 1.35), (GROW0 + 20, 2.5, "out"),
                  (GROW0 + 23, 2.3), (GROW1, BOSS_S, "out"), (N, BOSS_S)])

    red_mats = [RED["e_blue"], RED["e_dark"], RED["e_light"]]
    for e in E:
        tl = B.PoseTimeline(B.E_DEF, e.keys)
        zT = Track([(1, 2.3 * (e.land - 1) + 3.0), (e.land, 0.0, "in")])
        root = e.J["root"]
        for f in range(1, N + 1):
            dead = e.death is not None and f >= e.death
            sc = 0.001 if dead else B.E_SCALE * (grow(f) if e is BOSS else 1.0)
            S.key_scale(root, f, sc)
            if dead and f > e.death + 1:
                continue
            pose = tl(f)
            w = e.runw(f)
            for k, v in RUNP.items():
                pose[k] = lerp(pose[k], v, w)
            pose["run"] = w
            pose["hz"] += 0.008 * math.sin(f * 0.21 + e.i)
            p, d = e.pos_dist(f)
            c = cam_xy(f)
            yaw = math.atan2(c.x - p.x, -(c.y - p.y)) if e is not BOSS or f < GROW1 else 0.0
            S.key_enemy(e.J, f, pose, (p.x, p.y, zT(f)), 0.0, yaw, run_phase=d / 2.4)
        S.dust_ring("Land%d" % e.i, e.land, e.root(e.land), 8, 1.6, 40 + e.i, size=0.3)
        if e.death and e is not BOSS:
            frag_burst("Frag%d" % e.i, e.death, e.root(e.death) + Vector((0, 0, 1.1)), 26, 5.5, 0.2, 70 + e.i, red_mats)
    frag_burst("BossFrag", BOOM, Vector((0, 9.0, 3.4)), 130, 11.0, 0.5, 99, red_mats, life=50)
    # shards streaming into the last one before it grows
    rnd = random.Random(5)
    for i in range(54):
        ob = B.box("Absorb_%d" % i, (0.2, 0.2, 0.2), (0, 0, 0), red_mats[i % 3], bevel=0)
        a, r = rnd.uniform(0, 6.28), rnd.uniform(3, 9)
        src = Vector((math.sin(a) * r, 6 + math.cos(a) * r, 0.1))
        f0 = ABSORB + rnd.randrange(0, 22)
        S.key_scale(ob, 1, 0.001)
        for f in range(f0 - 1, f0 + 15):
            t = clamp((f - f0) / 13)
            dst = Vector((BP1[0], BP1[1], 1.2 + 1.5 * t))
            ob.location = src.lerp(dst, EASE["in"](t)) + Vector((0, 0, 2.2 * math.sin(math.pi * t)))
            ob.keyframe_insert("location", frame=f)
            ob.rotation_euler = (t * 7, t * 5, t * 3)
            ob.keyframe_insert("rotation_euler", frame=f)
            S.key_scale(ob, f, 0.001 if f < f0 or t >= 1 else 1.0)

    # ---------------- the human inside
    hroot, hneck = build_human((0, 9.0, 0))
    hroot.rotation_euler = (0, 0, 0)
    for f, s in ((1, 0.001), (BOOM - 1, 0.001), (BOOM, 1.0)):
        S.key_scale(hroot, f, s)
    for f, a in ((1, 0.85), (HEAD, 0.85), (HEAD + 14, -0.12), (N, -0.08)):
        hneck.rotation_euler = (a, 0, 0)
        hneck.keyframe_insert("rotation_euler", frame=f)
    hl = B.light("HumanLight", "SPOT", 0, (1.0, 0.95, 0.9), (0, 7.5, 6.0), 0.5)
    hl.rotation_euler = (math.radians(-18), 0, 0)
    hl.data.spot_size = math.radians(40)
    for f, v in ((1, 0), (BOOM + 6, 0), (BOOM + 24, 2500)):
        hl.data.energy = v
        hl.data.keyframe_insert("energy", frame=f)

    # ---------------- cracks on the boss
    ck = B.emissive("crack", (1.0, 0.95, 0.6), 18.0)
    rnd = random.Random(11)
    for parent, zc, n_ in ((BOSS.J["torso"], 0.36, 9), (BOSS.J["neck"], 0.24, 6)):
        bm = bmesh.new()
        for i in range(n_):
            B.bm_box(bm, (rnd.uniform(0.15, 0.4), 0.02, 0.025), (rnd.uniform(-0.2, 0.2), -0.245, zc + rnd.uniform(-0.2, 0.2)),
                     Matrix.Rotation(rnd.uniform(0, 3.14), 3, 'Y'))
        ob = B.mesh_obj("Crack", bm, ck, parent, bevel=0)
        for f, s in ((1, 0.001), (HIT, 0.001), (HIT + 1, 0.5), (HIT + 30, 1.0), (BOOM - 2, 1.25)):
            S.key_scale(ob, f, s)

    # ---------------- camera + hands
    prevq = {}
    shakes = [(e.land, 0.012, 3) for e in E] + [(PARRY, 0.05, 3), (K1, 0.03, 3), (SPIN0 + 4, 0.025, 3), (SPIN0 + 11, 0.025, 3),
              (SPIN1 - 1, 0.03, 3), (BOLT, 0.03, 6), (SWEEP + 3, 0.05, 5), (352, 0.05, 4), (364, 0.06, 4), (SLAM, 0.14, 6),
              (HIT, 0.10, 5), (LANDP, 0.05, 4), (BOOM, 0.12, 7), (RULE, 0.03, 5)]
    for f in range(1, N + 1):
        sv, sr = Vector((0, 0, 0)), 0.0
        for f0, amp, dc in shakes:
            a, r = S.shake(f, f0, amp, dc)
            sv += a
            sr += r
        hs = f if not (HIT <= f <= HIT + 4) else HIT                 # hit-stop
        cp = Vector(cpos(hs)) + sv + Vector((0, 0, 0.006 * math.sin(f * 0.25)))
        ya, pi_ = math.radians(yawT(f)), math.radians(pitT(f))
        d = Vector((math.sin(ya) * math.cos(pi_), math.cos(ya) * math.cos(pi_), math.sin(pi_)))
        w = look_w(f)
        if w > 0:
            d = d.lerp((HEADPT - cp).normalized(), w).normalized()
        S.key_player(P, f, cp, cp + d * 10, rollT(f) + sr, rh(hs), lh(hs), prevq)

    # ---------------- sword glow
    bl = M["blade"].node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"]
    for f, v in ((1, 0), (BOLT, 0), (BOLT + 14, 9), (SWEEP, 11), (SWEEP + 14, 3), (JUMP, 3), (462, 13), (HIT, 16),
                 (LANDP, 3), (BOOM, 1.5), (N, 1.0)):
        bl.default_value = v
        bl.keyframe_insert("default_value", frame=f)
    sl = B.light("SwordLight", "POINT", 0, (0.4, 0.7, 1.0), (0, 0.6, 0), 0.1, P["sword"])
    for f, v in ((1, 0), (BOLT, 0), (BOLT + 12, 60), (SWEEP, 90), (SWEEP + 14, 15), (JUMP, 15), (462, 80), (HIT, 400),
                 (HIT + 6, 60), (LANDP, 10), (BOOM, 0)):
        sl.data.energy = v
        sl.data.keyframe_insert("energy", frame=f)

    # ---------------- per-frame effects (need evaluated transforms)
    hand_local, tip_local = Vector((0, 0, -0.40)), Vector((0, 1.13, 0))
    for f in range(176, BOLT + 15):                               # six red bolts sucked into the blade
        scene.frame_set(f)
        tip = P["blade"].matrix_world @ tip_local
        rnd = random.Random(f)
        pairs = []
        for i in SIX:
            hp = E[i].J["elR"].matrix_world @ hand_local
            if f < BOLT:
                for _ in range(2):
                    rv = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
                    pairs.append((hp, hp + rv * rnd.uniform(0.25, 0.6)))
            else:
                pairs.append((hp, hp.lerp(tip, clamp((f - BOLT + 1) / 3))))
        bolts("RBolt", f, pairs, ("rbolt_core", "rbolt_glow"), amp=0.07 if f < BOLT else 0.22,
              w=0.015 if f < BOLT else 0.03, branches=0 if f < BOLT else 2)
    for f in range(BOLT + 15, SWEEP):                             # charged blade crackles
        scene.frame_set(f)
        mw = P["blade"].matrix_world
        rnd = random.Random(f)
        pairs = []
        for _ in range(3):
            a = mw @ Vector((0, rnd.uniform(0.2, 1.1), 0))
            pairs.append((a, a + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * 0.14))
        bolts("Crk", f, pairs, ("bolt_core", "bolt_glow"), amp=0.03, w=0.006, branches=0)
    for f in range(SWEEP + 1, SWEEP + 14):                        # chain lightning out of the sweep
        scene.frame_set(f)
        tip = P["blade"].matrix_world @ tip_local
        pairs = [(tip, E[i].root(f) + Vector((0, 0, 1.2))) for i, kf in kills.items() if kf - 2 <= f <= kf + 1]
        if pairs:
            bolts("Chain", f, pairs, ("bolt_core", "bolt_glow"), amp=0.3, w=0.06, branches=4)
    for f in range(HIT, HIT + 24):                                # lightning crawling over the boss
        rnd = random.Random(f)
        k = 1 - (f - HIT) / 24
        pairs = []
        for _ in range(2 + int(5 * k)):
            a = Vector((rnd.uniform(-1.2, 1.2), 9.0 - 1.0, rnd.uniform(1.0, 6.8)))
            pairs.append((HEADPT + Vector((0, -0.5, 0.6)), a))
        bolts("BossZap", f, pairs, ("bolt_core", "bolt_glow"), amp=0.35, w=0.05 * (0.4 + k), branches=2)
    for a, b_ in ((89, 96), (SPIN0 - 1, SPIN1 + 1), (SWEEP - 1, SWEEP + 9), (HIT - 5, HIT + 1)):
        slash_trail(P, a, b_)
    spark_m = M["spark"]
    for f0, who in ((PARRY, A),):
        scene.frame_set(f0)
        c = P["blade"].matrix_world @ Vector((0, 0.6, 0))
        S.dust_ring("ParrySpark", f0, c, 12, 1.2, 3, size=0.07, mat=spark_m)
    for i, kf in list(kills.items()) + [(A, K1), (SL, E[SL].death), (SR, E[SR].death), (SF, E[SF].death)]:
        S.dust_ring("KillSpark%d" % i, kf, E[i].root(kf) + Vector((0, 0, 1.0)), 8, 1.5, 200 + i, size=0.10, mat=M["spark_b"])
    S.dust_ring("SlamDust", SLAM, Vector((0, 4.6, 0)), 22, 4.0, 31, size=0.6)
    S.dust_ring("SlamDust2", SLAM + 1, Vector((0, 4.6, 0)), 14, 2.2, 32, size=0.4)
    for k, f0 in enumerate((352, 364)):
        S.dust_ring("StepDust%d" % k, f0, Vector((0.5 - k, 11.0 - k * 1.8, 0)), 10, 1.8, 33 + k, size=0.4)
    S.dust_ring("LandDustP", LANDP, Vector((0.1, 5.4, 0)), 10, 1.5, 36, size=0.25)
    # flashes
    for name, col, loc, keys in (
            ("ParryL", (1.0, 0.9, 0.7), (0, 2.6, 1.9), ((1, 0), (PARRY - 1, 0), (PARRY, 220), (PARRY + 4, 0))),
            ("BoltL", (1.0, 0.2, 0.15), (0, 3.2, 2.6), ((1, 0), (BOLT - 1, 0), (BOLT + 2, 1500), (BOLT + 14, 300), (BOLT + 20, 0))),
            ("SweepL", (0.35, 0.65, 1.0), (0, 5.0, 1.5), ((1, 0), (SWEEP, 0), (SWEEP + 4, 3000), (SWEEP + 12, 800), (SWEEP + 18, 0))),
            ("GrowL", (1.0, 0.15, 0.1), (0, 10.5, 2.5), ((1, 0), (ABSORB, 0), (GROW0 + 20, 2500), (GROW1 + 10, 0))),
            ("HitL", (0.5, 0.75, 1.0), (0, 7.6, 7.2), ((1, 0), (HIT - 1, 0), (HIT, 6000), (HIT + 6, 1500), (HIT + 24, 0))),
            ("BoomL", (1.0, 0.8, 0.7), (0, 8.0, 3.5), ((1, 0), (BOOM - 1, 0), (BOOM, 9000), (BOOM + 10, 0)))):
        L = B.light(name, "POINT", 0, col, loc, 0.4)
        for f, v in keys:
            L.data.energy = v
            L.data.keyframe_insert("energy", frame=f)
    wm = S.fade_material("FlashWhite", (1, 1, 1))
    S.cam_overlay(cam, "FlashPlane", wm, -0.06)
    for f, v in ((1, 0), (HIT - 1, 0), (HIT, 0.55), (HIT + 4, 0.0), (BOOM - 1, 0), (BOOM, 0.85), (BOOM + 8, 0)):
        S.key_fade(wm, f, v)
    bk = S.fade_material("FadeBlack", (0, 0, 0))
    S.cam_overlay(cam, "FadePlane", bk, -0.05)
    for f, v in ((1, 0), (FADE0, 0), (FADE0 + 10, 1.0)):
        S.key_fade(bk, f, v)
    for body, size, col, y, d in (("異世界デスゲーム", 0.0034, (1.0, 0.5, 0.9), 0.004, 0),
                                  ("― 第二話「十対一」 ―", 0.0019, (0.9, 0.85, 1.0), -0.0025, 3),
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
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "isekai_ep2.blend"))
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
