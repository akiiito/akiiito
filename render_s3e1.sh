#!/bin/bash
cd "$(dirname "$0")"
for s in MC YC WD1 WD2 WD3 WD4; do /tmp/bvenv/bin/python create_s3e1.py --shot $s --samples 16 >> /tmp/render_s3e1.log 2>&1; done
echo S3E1 DONE >> /tmp/render_s3e1.log
