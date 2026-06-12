#!/bin/bash
# 兼容入口 — 请使用 start_pipeline.sh（含自动判分 + stale guard）
exec "$(dirname "$0")/start_pipeline.sh"
