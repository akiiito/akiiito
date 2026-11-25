"""
create_gk1.py ― 学園デスゲーム『出席番号13番』第1話（主観・CG＋輪郭線・夕方の教室）
  python create_gk1.py [--samples 14] [--thr 0.06] [--res 0.75] [--start 0] [--end N] [--test 24,100,...]
"""
import os, sys, math, json, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import s2_world as W, s3_toon as T, blk_hair as H
from gk1_timing import *

HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
SAMPLES = int(arg("--samples", "14")); FPS = 24; N = int(END * FPS)
RS = float(arg("--res", "0.75"))
START = int(arg("--start", "0")); STOP = int(arg("--end", str(N)))
TEST = [int(x) for x in arg("--test", "").split(",") if x]
OUT = os.path.join(HERE, "frames_GK1" + ("_test" if TEST else "")); os.makedirs(OUT, exist_ok=True)
sc = W.reset(SAMPLES, res=(int(1080 * RS), int(1920 * RS)))
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = float(arg("--thr", "0.06"))
sc.cycles.max_bounces = 5; sc.render.use_persistent_data = True
try: sc.cycles.denoising_prefilter = "ACCURATE"; sc.cycles.denoising_quality = "HIGH"
except Exception: pass
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"; sc.view_settings.exposure = -0.3
LINES = json.load(open(os.path.join(HERE, "gk1_lines.json"), encoding="utf-8"))
def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def talking(who, t): return any(l[0] <= t <= l[1] - 0.05 for l in LINES if l[5] == who)
def mouth(who, t): return talking(who, t) and int(t * 12) % 3 != 2
def blink(t, ph): return (t * 10 + ph) % 41 < 1.2

# ---------------------------------------------------------------- 教室（夕方）
random.seed(5)
room = W.classroom(sun_elev=10.0, sun_az=-30.0, haze=0.003, sun_str=12.0, fill=8)
D = room["D"]
kl = bpy.data.lights.new("facefill", "AREA"); kl.size = 2.5; kl.energy = 90; kl.color = (1.0, 0.9, 0.8)
ko = bpy.data.objects.new("facefill", kl); bpy.context.collection.objects.link(ko); ko.location = (0.6, -3.2, 2.2); W.aim(ko, (0, 1.5, 1.3))
# 輪郭線
sc.render.use_freestyle = True
try: sc.render.line_thickness_mode = "ABSOLUTE"; sc.render.line_thickness = 1.3 * RS / 0.75
except Exception: pass
try:
    fs_ = bpy.context.view_layer.freestyle_settings; ls_ = fs_.linesets[0] if fs_.linesets else fs_.linesets.new("ls")
    ls_.select_by_visibility = True; ls_.select_silhouette = True; ls_.select_border = False; ls_.select_crease = False
    if ls_.linestyle is None: ls_.linestyle = bpy.data.linestyles.new("ls")
    ls_.linestyle.color = (0.05, 0.035, 0.03); ls_.linestyle.thickness = 1.5
except Exception as ex: print("freestyle", ex)

def img_mat(name, path, emit=0.0, alpha=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(path)
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.6
    if emit: nt.links.new(tx.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = emit
    if alpha: nt.links.new(tx.outputs["Alpha"], b.inputs["Alpha"])
    return m
def plane(name, loc, sx, sy, m, rot=(math.pi / 2, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc); p = bpy.context.object; p.name = name
    p.scale = (sx, sy, 1); p.rotation_euler = rot; p.data.materials.append(m); return p
A = os.path.join(HERE, "s3_assets")
# 16:44 で止まった時計（F1）と黒板の文字（F7）
CLOCK = Vector((0.2, D / 2 - 0.05, 2.55))
W.cyl("clock_rim", (CLOCK.x, CLOCK.y + 0.02, CLOCK.z), 0.2, 0.05, W.mat("clockrim", (0.08, 0.08, 0.09), 0.4), rot=(math.pi / 2, 0, 0), verts=40)
cf = plane("clock_face", (CLOCK.x, CLOCK.y - 0.006, CLOCK.z), -0.36, 0.36, img_mat("clockface", os.path.join(A, "gk_clock.png"), 0.6, alpha=True), rot=(math.pi / 2, 0, math.pi))
BOARDT = Vector((0.2, D / 2 - 0.045, 1.6))
plane("chalk", BOARDT, -4.3, 1.075, img_mat("chalk", os.path.join(A, "gk_board.png"), 0.25, alpha=True), rot=(math.pi / 2, 0, math.pi))
SPK = Vector((2.35, D / 2 - 0.12, 2.72))
W.box("speaker", SPK, (0.42, 0.16, 0.3), W.mat("spk", (0.75, 0.74, 0.7), 0.6), bevel=0.02)
W.box("grille", SPK + Vector((0, -0.085, 0)), (0.34, 0.01, 0.22), W.mat("grille", (0.15, 0.15, 0.16), 0.7))
# 後ろの席の白い菊（F6）
VASE = Vector((1.15, -2.2, 0.735))
W.vase(tuple(VASE), seed=5)

# ---------------------------------------------------------------- 生徒
def pbr(root, cmap):
    for o in [root] + list(root.children_recursive):
        if o.type != "MESH": continue
        for i, m in enumerate(o.data.materials):
            if not (m and m.node_tree) or "facemat" in m.name: continue
            rp = [n for n in m.node_tree.nodes if n.type == "VALTORGB"]
            if not rp: continue
            key = m.name.split("_")[-1]
            c = cmap.get(key) or tuple(x ** 0.4545 for x in rp[0].color_ramp.elements[1].color[:3])
            lin = tuple(x ** 2.2 for x in c); sk = "skin" in m.name; hr = "hair" in m.name
            nm = W.mat(m.name + "_pbr", lin, 0.5 if sk else (0.36 if hr else 0.8), sss=0.25 if sk else 0.0)
            b = nm.node_tree.nodes["Principled BSDF"]
            if hr: b.inputs["Coat Weight"].default_value = 0.25; b.inputs["Sheen Weight"].default_value = 0.4
            o.data.materials[i] = nm
def face_to(o, p, tgt):
    o.location = (p[0], p[1], 0); d = Vector((tgt[0] - p[0], tgt[1] - p[1], 0)).normalized()
    o.rotation_euler = (0, 0, math.atan2(-d.x, d.y))
P0 = Vector((-0.1, -1.55, 1.18))                      # 自分（席に座っている）
FRONT = Vector((0.2, 9.0, 0))
POINT = {"R": ((-0.2, 0.3, 1.3), (-0.12, 0.62, 1.33))}           # 指さし
CLING = {"L": ((0.2, 0.2, 1.08), (0.12, 0.42, 1.02)), "R": ((-0.2, 0.2, 1.08), (-0.1, 0.4, 1.02))}
BOOK = {"L": ((0.2, 0.15, 1.05), (0.08, 0.3, 1.15)), "R": ((-0.2, 0.15, 1.05), (-0.08, 0.3, 1.15))}
C = {}
def add_girl(nm, face, pos, hair, ponytail, arms=None, seed=3):
    r_, tx_ = T.girl(nm, (0, 0, 0), hair=hair, face=face, ponytail=ponytail, arms=arms)
    pbr(r_, {}); H.upgrade(r_, nm, [m for o in r_.children if o.name.startswith(nm + "_hair") for m in o.data.materials][0], seed=seed)
    return r_, tx_
def add_boy(nm, face, pos, hair, arms=None):
    r_, tx_ = T.boy(nm, (0, 0, 0), hair=hair, face=face, arms=arms); pbr(r_, {}); return r_, tx_
def objs(r_): return [r_] + list(r_.children_recursive)
def show(r_, on):
    for o in objs(r_):
        if o.type == "MESH": o.hide_render = not on
# ユイ（隣の席の女の子）：ふつう／すがりつく
YUI_P = Vector((-0.95, -0.55, 0))
C["yui"] = add_girl("yui", "hana", YUI_P, (0.12, 0.08, 0.07), False, seed=11)
C["yuic"] = add_girl("yuic", "hana", YUI_P, (0.12, 0.08, 0.07), False, arms=CLING, seed=11)
# カイト：ふつう／指さす
KAI_P = Vector((-0.72, 0.55, 0))
C["kai"] = add_boy("kai", "yota", KAI_P, (0.07, 0.06, 0.06))
C["kaip"] = add_boy("kaip", "yota", KAI_P, (0.07, 0.06, 0.06), arms=POINT)
# 委員長サエ：出席簿を持つ
SAE_P = Vector((1.0, 3.45, 0))
C["sae"] = add_girl("sae", "sae", SAE_P, (0.05, 0.05, 0.07), True, arms=BOOK, seed=21)
W.box("rollbook", (0, 0.32, 1.17), (0.24, 0.03, 0.32), W.mat("rollbook", (0.15, 0.2, 0.35), 0.6), rot=(0.5, 0, 0), parent=C["sae"][0])
# ほかの生徒
EXTRA = {"mio": ("girl", "mio", Vector((-1.97, 1.75, 0)), (0.3, 0.18, 0.1)), "mei": ("girl", "mei", Vector((1.77, 1.9, 0)), (0.08, 0.06, 0.08)),
         "boss": ("boy", "boss", Vector((1.77, -0.05, 0)), (0.12, 0.1, 0.09))}
for k, (kind, face, p, hc) in EXTRA.items():
    C[k] = add_girl(k, face, p, hc, k == "mio", seed=len(k) * 7) if kind == "girl" else add_boy(k, face, p, hc)

# ---------------------------------------------------------------- カメラ
cam = W.camera(tuple(P0), (0.2, 4.0, 2.4), lens=40, fstop=2.8)
cam.data.dof.use_dof = True
def vy(p, z): return Vector((p.x, p.y, z))
LOOKS = dict(
    clock=CLOCK + Vector((0, 0, -0.05)), duty=Vector((1.75, D / 2, 2.0)), spk=SPK, mio=vy(EXTRA["mio"][2], 1.42), boss=vy(EXTRA["boss"][2], 1.45),
    kai=vy(KAI_P, 1.5), sae=vy(SAE_P, 1.42), mei=vy(EXTRA["mei"][2], 1.35), yui=vy(YUI_P, 1.42), vase=VASE + Vector((0, 0, 0.12)), yuic=vy(YUI_P, 1.38))
# (時刻, 見る先, レンズ, そこへ動く時間) ― 止めている間はわずかに寄る。見せたい物は1.4秒以上止める
KEYS = [(0.0, "clock", 95, 0.0), (1.7, "clock", 100, 0.0), (2.45, "duty", 70, 0.65), (3.0, "duty", 72, 0.0),
        (3.5, "spk", 40, 0.55), (4.6, "spk", 42, 0.0),
        (5.2, "mio", 30, 0.55), (7.0, "boss", 30, 1.8),
        (7.6, "kai", 38, 0.55), (10.9, "kai", 42, 0.0),
        (11.5, "sae", 46, 0.55), (14.0, "sae", 48, 0.0),
        (14.5, "mei", 32, 0.5), (15.3, "mei", 33, 0.0),
        (15.65, "yui", 34, 0.35), (17.4, "yui", 36, 0.0),
        (18.2, "vase", 42, 0.75), (20.3, "vase", 50, 0.0),
        (20.65, "kai", 36, 0.35), (24.8, "kai", 40, 0.0),
        (25.2, "yuic", 36, 0.4), (28.2, "yuic", 40, 0.0),
        (28.9, "clock", 70, 0.6), (END, "clock", 80, 0.0)]
def shot(t):
    i = max([j for j, k in enumerate(KEYS) if k[0] <= t] or [0]); k1 = KEYS[i]
    if i + 1 < len(KEYS):
        k2 = KEYS[i + 1]; ts_ = k2[0] - k2[3]
        if k2[3] > 0 and t >= ts_:
            u = ease((t - ts_) / k2[3]); return LOOKS[k1[1]].lerp(LOOKS[k2[1]], u), k1[2] + (k2[2] - k1[2]) * u
        u = (t - k1[0]) / max(0.01, ts_ - k1[0])
        if k2[3] == 0: return LOOKS[k1[1]].lerp(LOOKS[k2[1]], u), k1[2] + (k2[2] - k1[2]) * u
        return LOOKS[k1[1]], k1[2] + 1.2 * min(1, u)
    return LOOKS[k1[1]], k1[2]

# ---------------------------------------------------------------- 表情・向き
def expr(who, t):
    tk = mouth(who, t); bl = blink(t, len(who) * 7)
    if who == "yui":
        if t < 15.4: return "sadblink" if bl else "sad"
        if t < 20.5: return "sadtalk" if tk else ("sadblink" if bl else "sad")
        if t < 24.9: return "shock" if t < 22.6 else "shockc"
        return "tearsadtalk" if tk else "tearsad"
    if who == "kai":
        if t < 11.0: return "shock"
        return "coldtalk" if tk else ("blink" if bl else "cold")
    if who == "sae":
        if 11.0 <= t < 14.0: return "talk" if tk else "base"
        return "blink" if bl else "cold"
    return "shockc" if t < 11.0 else ("blink" if bl else "base")
def place(t):
    # ユイ：すがりつく形は 25秒から
    cling = t >= 25.0
    show(C["yui"][0], not cling); show(C["yuic"][0], cling)
    for k in ("yui", "yuic"):
        p = YUI_P + (Vector((0.1, -0.05, 0)) * ease((t - 25.0) / 0.5) if k == "yuic" else Vector())
        face_to(C[k][0], p, P0); T.set_expr(C[k][1], "hana", expr("yui", t))
    # カイト：20.6秒から指さす
    pt = t >= 20.6
    show(C["kai"][0], not pt); show(C["kaip"][0], pt)
    for k in ("kai", "kaip"): face_to(C[k][0], KAI_P, P0 if t < 11.0 or t >= 20.0 else FRONT * 0 + SAE_P); T.set_expr(C[k][1], "yota", expr("kai", t))
    face_to(C["sae"][0], SAE_P, P0 + Vector((0.6, 0, 0))); T.set_expr(C["sae"][1], "sae", expr("sae", t))
    # ほかの生徒：最初はざわついて互いを見る → 出席確認からは前（委員長）を向く。誰も「あなた」に振り向かない
    for k, (kind, face, p, hc) in EXTRA.items():
        tgt = (P0 + Vector((1.2 if k == "mio" else -1.5, 1.0, 0))) if t < 11.0 else SAE_P
        face_to(C[k][0], p, tgt); T.set_expr(C[k][1], face, expr(k, t))
    look, lens = shot(t)
    sway = Vector((0.006 * math.sin(t * 1.3), 0.004 * math.sin(t * 0.9), 0.005 * math.sin(t * 1.7)))
    cam.location = P0 + sway; W.aim(cam, look); cam.data.lens = lens
    cam.data.dof.focus_distance = max(0.5, (look - P0).length)
    return dict(t=t, impact=0.0, kind="", edit=0.0, pov=True, dash=0.0,
                wake=1.0 - ease((t - 0.0) / 1.2), red=ease((t - 20.5) / 0.4) * (1 - ease((t - 25.0) / 0.6)) * 0.5 + ease((t - 28.2) / 0.6) * 0.6)

frames = TEST or range(START, STOP)
t0 = time.time()
for f in frames:
    p = os.path.join(OUT, "%04d.png" % (f + 1))
    if os.path.exists(p) and not TEST: continue
    t = f / FPS; meta = place(t); bpy.context.view_layer.update()
    json.dump(meta, open(p[:-4] + ".json", "w"))
    tmp = p[:-4] + "_tmp.png"; sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True); os.replace(tmp, p)
    print("frame %s t=%.2f %.1fs" % (p, t, time.time() - t0), flush=True); t0 = time.time()
