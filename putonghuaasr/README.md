# putonghuaasr

普通话 ASR 标注工作区持久化目录。

这个仓库保存了当前项目的关键资料、脚本、规则文档、复核结果，以及本地识别模型，便于后续继续做题、排查问题和复盘历史结论。

## 目录说明

- `docs/`
  - 标注规则原件与抽取文本
  - `asr_rules.docx`
  - `asr_rules.txt`
  - `itn_rules.pdf`
  - `itn_rules.txt`
- `models/`
  - `vosk-model-small-cn-0.22/`
  - `Qwen3-ASR/`
- `_work_context/local_segment_dual_asr.py`
  - 本地 Qwen3-ASR + FireRedASR-AED 双模型分段复核脚本
- `fill_page.js`
  - 页面回填脚本，已加入保存等待与刷新校验
- `page50_items.json`
  - 昨日 50 条任务原始抓取数据
- `page50_results.json`
  - 昨日 50 条任务整理后的候选答案
- `current_page_items.json`
  - 最近一次页面抓取快照

## 已知关键结论

- 平台要求句尾必须补标点。
- 非人声/噪声不单独标注；只转写需要标注的主说话人内容。
- AI 合成音如果清晰可辨且属于主内容，按正常语音转写。
- 回填脚本不能只看页面上“填进去了”，必须等待保存并刷新复验，否则后台可能仍为空白。

## 使用建议

1. 启动独立受控浏览器窗口。
2. 登录标注平台并定位到目标子任务。
3. 用 `_work_context/local_segment_dual_asr.py` 对页面分段跑 Qwen3-ASR + FireRedASR-AED 双路复核。
4. 用安全回填脚本回填并校验页面。
5. 复验通过后，再人工检查，再决定是否提交。

## 备注

- 当前仓库保留了本地模型，体积较大。
- 如果未来需要推送到远程 Git 平台，建议不要直接提交大型模型文件，改用外部存储或 Git LFS。
