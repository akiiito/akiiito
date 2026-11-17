#!/bin/bash
# 『君は写真に写らない』の3Dカットを順番に描く。途中で止まっても、もう一度実行すれば続きから。
cd "$(dirname "$0")"
PY=/tmp/bvenv/bin/python
LOG=/tmp/render_s2_queue.log
$PY create_s2e2.py --shot A --samples 48 >> $LOG 2>&1
$PY create_s2e3.py --shot S --samples 48 >> $LOG 2>&1
$PY create_s2e3.py --shot E --samples 48 >> $LOG 2>&1
$PY create_s2e4.py --shot P --samples 64 >> $LOG 2>&1
$PY create_s2e4.py --shot N --samples 48 >> $LOG 2>&1
for s in U1 U2 V; do $PY create_s2e5.py --shot $s --samples 64 >> $LOG 2>&1; done
for s in R1 R2; do $PY create_s2e6.py --shot $s --samples 64 >> $LOG 2>&1; done
echo QUEUE DONE >> $LOG
