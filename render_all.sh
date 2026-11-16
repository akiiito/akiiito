#!/bin/bash
# resumable: renders every missing frame of episodes 2-6 in order (skips finished episodes)
cd "$(dirname "$0")"
PY=${PY:-/tmp/bvenv/bin/python}
for n in 2 3 4 5 6; do
  [ "$(ls frames_E$n 2>/dev/null | wc -l)" -ge 696 ] && continue
  save=""; [ -f isekai_ep$n.blend ] && save="--no-save"
  $PY create_ep$n.py --anim --samples 24 $save >> /tmp/render_e$n.log 2>&1 || exit 1
done
echo ALLDONE
