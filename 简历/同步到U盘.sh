#!/usr/bin/env bash
# 在本机（已挂载 U 盘）执行：把仓库里的脱敏简历拷到 U 盘
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="/Volumes/u盘/zuoye/简历"
mkdir -p "$DEST"
cp -f "$SRC/专家访谈_脱敏简历.pdf" "$DEST/"
cp -f "$SRC/专家访谈_脱敏简历.md" "$DEST/"
cp -f "$SRC/专家访谈_脱敏简历.html" "$DEST/"
echo "已复制到 $DEST"
ls -la "$DEST"
