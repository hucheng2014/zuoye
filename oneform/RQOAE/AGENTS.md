# RQOAE - Rating Quality of Audio Edits

## 任务概述

在 TryRating 上评估**音乐音频编辑质量**，1–5 分（Awful → Excellent）。

- 平台：tryrating.com
- 容器：`oneform-agent` / `oneform-browser`
- noVNC：**http://127.0.0.1:6081/vnc.html**
- 自动化入口：`solve_tasks.py`（见 `start_solve.sh`）

## 评分标准

| 分数 | 标签 | 含义 |
|------|------|------|
| 1 | Awful | 大段静音、极度突兀、严重失真 |
| 2 | Poor | 节奏拖拽、轻微突兀、不自然过渡 |
| 3 | Average | 小瑕疵可接受 |
| 4 | Good | 平滑自然，几乎无瑕疵 |
| 5 | Excellent | 无缝衔接，听不出编辑痕迹 |

## 编辑类型（从文件名 / 页面说明判断）

- **intro_**：开头是否平滑引入
- **outro_**：结尾是否自然收束
- **bridge_**：两段过渡是否流畅
- **pre_**：Pre-Extension 延伸是否自然
- **post_**：Post-Extension 延伸是否自然

文件名含 `7.5-to-13.7` 表示编辑区 7.5s–13.7s；无时间戳时脚本按类型取头/尾/中段窗口。

## 页面结构（动态，勿硬编码 index）

任务数据来自 Redux：`window.store.getState().survey.workableSurvey`

| templateTaskType | 形态 |
|---|---|
| **SFX-MUSHRA-Style** | 1 task × A–E 五样本，5 个 slider，约 2 分钟/批 |
| **Transition quality** | 多 task，每题 `audio_src` + `overlap`，各 1 slider |

旧文档中的「audio index 32–34」仅适用于特定教程数据集，正式题以 Redux 为准。

## Slider 操作要点

- 分值 1–5 对应 rail 位置 0% / 25% / 50% / 75% / 100%
- **验证用 `aria-valuenow`**（1–5），不要用 `activeDots` 计数
- 点击方式：CDP `Input.dispatchMouseEvent` 点 rail（dot.click 在 MUSHRA 页不可靠）

## 双模型分析

### PANNs
- 路径：`/root/panns_data/Cnn14_mAP=0.431.pth`
- 声学：RMS、静音比、能量跳变

### CLAP
- 路径：`/app/RQOAE/models/music_audioset_epoch_15_esc_90.14.pt`

### Whisper（仅 Transition quality）
- 路径：`/app/RQOAE/models/faster-whisper-large-v3`
- 检测过渡区人声截断

## 音频下载

必须通过浏览器 fetch + cookie：

```bash
docker exec oneform-agent python3 /app/RQOAE/fetch_audio.py "URL" /tmp/audio.wav
```

`solve_tasks.py` 会自动将 `api.tryrating.com` URL 转为 `www.tryrating.com/api/catalog/datasets/...` 并带 `credentials: include`。

## 自动化流程

```bash
/Users/xaa/zuoye/oneform/RQOAE/start_solve.sh   # 启动
tail -f /Users/xaa/zuoye/oneform/RQOAE/solve.log
/Users/xaa/zuoye/oneform/RQOAE/stop_solve.sh    # 停止
```

每批：读 Redux → 下载分析 → 设 slider → 提交前复检 → 提交 → 等 90s → 下一批。无题自动退出。

## CDP

- 容器内：`http://browser:9223`
- HTTP Header：`Host: localhost:9222`
- WebSocket：`ws://localhost:9222` → `ws://browser:9223`

## 网络

- 容器可访问 tryrating.com；Google/HF 等可能 DNS 失败
- 模型已预置在 `/app/RQOAE/models/` 和 `/root/panns_data/`

## 知识库

```bash
cat pipeline/knowledge/rqoae/compact_sop.md
cat pipeline/knowledge/rqoae/flow.md
node pipeline/scripts/query_knowledge.js --task rqoae --query "..."
```
