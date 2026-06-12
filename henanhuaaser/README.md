# henanhuaaser

河南话 Appen 标注辅助与方言 ASR 项目持久化目录。

## 当前内容

- `scripts/appen_audio_asr.py`
  - 方言 ASR 辅助脚本
  - 已处理 `Fun-ASR-Nano-2512` 的本地注册问题
  - 已绕开当前环境中的 `torchaudio/ffmpeg` 读取问题，直接读取 `.wav`
- `scripts/appen_henan_assets.py`
  - 从飞书正字表预览 HTML 中提取表格
- `scripts/appen_semi_auto.py`
  - Appen 半自动辅助脚本
  - 当前已回退到较干净基线，不包含最后两轮匆忙修改
- `data/orthography/henan_orthography_rows.json`
  - 本地正字表缓存
- `data/feishu/henan_preview_type8.bin`
  - 飞书附件预览导出 HTML
- `data/audio_cache/`
  - 已保存的示例音频缓存
- `logs/appen_batch_log.jsonl`
  - 之前半自动流程的日志
- `cache/modelscope/Fun-ASR-Nano-2512`
  - 已下载的方言 ASR 模型缓存
- `requirements/appen-punc312-freeze.txt`
  - 现有虚拟环境依赖快照

## 当前已验证状态

- 正字表缓存已成功生成并可离线使用
- `FunAudioLLM/Fun-ASR-Nano-2512` 模型缓存已完整落盘
- `appen_audio_asr.py --warmup` 已成功
- `appen_audio_asr.py --audio-url <Appen wav>` 已成功返回转写结果

## 建议使用环境

- 现有虚拟环境路径：
  - `C:\Users\BERN7P\.venvs\appen-punc312`

如果以后要重建环境，可优先参考：

- `requirements/appen-punc312-freeze.txt`

## 说明

- 该目录同时保存“项目资料”和“运行缓存”
- 为避免仓库过大，模型缓存、音频缓存、日志默认不纳入 Git 跟踪
