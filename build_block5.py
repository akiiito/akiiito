"""build_block5.py ― create_block5_src.py の {{...}} にパート4の共通部品（霧・地形・手・溶ける材質）を差し込んで create_block5.py を作る"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
src4 = open(os.path.join(HERE, "create_block4.py"), encoding="utf-8").read()
def seg(a, b):
    i = src4.index(a); j = src4.index(b, i); return src4[i:j]
parts = {
    "fog": seg("# ---------------------------------------------------------------- 霧", "# ---------------------------------------------------------------- ドット絵の質感"),
    "terrain": seg("# ---------------------------------------------------------------- 地形", "build_terrain()\n"),
    "hands": seg("hood = P(\"me_hood\"", "ARMS = {}"),
    "setarm": seg("def between(o, p0, p1):", "hl = bpy.data.lights.new"),
    "dissolve": seg("DCUT = []", "def kage_mat():"),
}
s = open(os.path.join(HERE, "create_block5_src.py"), encoding="utf-8").read()
parts["hands"] = parts["hands"].replace("(0.28, 0.29, 0.32)", "(0.08, 0.08, 0.09)")   # 袖は暗い色（近くで大きく映るので目立たせない）
parts["dissolve"] = parts["dissolve"].replace("(1.0, 0.75, 0.35, 1); em.inputs[\"Strength\"].default_value = 12.0", "(1.0, 0.6, 0.22, 1); em.inputs[\"Strength\"].default_value = 5.0")
for k, v in parts.items(): s = s.replace("{{%s}}" % k, v)
open(os.path.join(HERE, "create_block5.py"), "w", encoding="utf-8").write(s)
print("wrote create_block5.py")
