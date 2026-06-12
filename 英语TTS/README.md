# 英语TTS 项目持久化副本

本目录是 2026-04-03 从 `C:\Users\BERN7P` 持久化出来的项目副本，用于长期保存当前音频标注、文本复核、判噪和本地模型工作流。

## 已保存内容

- `codex-audio/`
  - 任务产物目录 `41393/`、`41398/`
  - 离线复核脚本 `scripts/`
  - 经验文档 `labeling_lessons.md`
- `codex-browser/`
  - 受控浏览器脚本和状态文件
  - 页面抓取结果、噪音分析图、实验音频
  - 本地模型 `models/faster-whisper-large-v3/`
  - 本地模型 `models/faster-whisper-medium/`
- `reference/标准.jpg`
  - 当前标注标准图
- `environment/`
  - `python-version.txt`
  - `node-version.txt`
  - `requirements-audio.txt`
- `manifests/`
  - `project_inventory.json`
  - `persistence_manifest.json`

## 有意未复制的内容

以下目录或运行态内容没有复制到这里：

- `codex-browser/edge-profile/`
- `codex-browser/edge-profile-41393/`
- `codex-browser/node_modules/`
- `codex-audio/.venv-audio/`

原因：

- 浏览器 profile 含登录态和本地会话信息，不适合直接做长期归档。
- `node_modules/` 和虚拟环境属于可再生依赖，保留版本与依赖清单更稳。

## 恢复建议

1. 使用 `environment/python-version.txt` 和 `environment/requirements-audio.txt` 重新准备 Python 环境。
2. 使用 `codex-browser/package.json` 重新安装 Node 依赖。
3. 直接复用 `codex-browser/models/` 下已保存的 Whisper 模型。
4. 优先从 `codex-audio/scripts/` 和 `codex-audio/labeling_lessons.md` 恢复工作流与判定经验。

## Git 说明

本目录根部会初始化 Git 仓库。

- 仓库用于管理脚本、说明文档、规则、清单和关键结果。
- 大模型、音频缓存、浏览器运行态不会纳入版本控制，但会保留在磁盘里。
