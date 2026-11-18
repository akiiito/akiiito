#!/bin/bash
cd "$(dirname "$0")"
for s in HW HG HM HC; do /tmp/bvenv/bin/python create_s3e2.py --shot $s --samples 16 >> /tmp/render_s3e2.log 2>&1; done
echo S3E2 DONE >> /tmp/render_s3e2.log
