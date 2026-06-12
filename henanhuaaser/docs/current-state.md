# Current State

日期：2026-04-03

## 已保存的关键事实

- 飞书教程中的正字表已从预览页提取为本地 JSON
- 正字表缓存共 412 行
- Appen 相关辅助脚本已集中保存
- `appen_semi_auto.py` 当前为回退后的干净基线版本
- `appen_audio_asr.py` 已修通以下问题：
  - `FunASRNano` 本地注册
  - `transformers` / `tokenizers` / `openai-whisper` / `tiktoken` 依赖
  - 当前 Windows 环境中 `torchaudio` + `ffmpeg` 链路不可用时的 `.wav` 直接读取

## 已验证的 ASR 结果

- 预热成功
- 对一条 Appen `.wav` 验证成功
- 验证样例返回：
  - `周二你咋嫩多事儿还让俺难过`

## 后续可继续的方向

- 将 ASR 审查结果接入独立的“只读复核工具”
- 增加儿化音、正字表、`的/得/地` 审查规则
- 如需重新启用 Appen 页面辅助，建议单独新建分支再改
