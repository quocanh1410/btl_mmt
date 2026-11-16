#!/usr/bin/env bash
# Tạo file nộp: ET4230_HK[ky]_N[so-nhom]_D09.zip
# Dùng: bash scripts/make_submission.sh <ky> <so-nhom>     ví dụ: bash scripts/make_submission.sh 20261 03
set -euo pipefail
KY=${1:?"thiếu mã học kỳ"}; NHOM=${2:?"thiếu số nhóm"}
OUT="ET4230_HK${KY}_N${NHOM}_D09.zip"
git archive --format=zip -o "$OUT" HEAD
echo "Đã tạo $OUT (chỉ gồm file đã commit). Kiểm tra: unzip -l $OUT"
