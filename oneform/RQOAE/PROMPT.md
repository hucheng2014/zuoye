# RQOAE 自动化工作规范

> 给 AI Agent 的操作说明。做题前读完本文件 + `AGENTS.md`。

---

## 环境（只用 oneform 容器）

| 项 | 值 |
|---|---|
| 浏览器容器 | `oneform-browser`，noVNC：**http://127.0.0.1:6081/vnc.html** |
| Agent 容器 | `oneform-agent` |
| 页面 | https://www.tryrating.com/app/survey/rate |
| CDP（容器内） | `http://browser:9223`，Header `Host: localhost:9222` |
| 宿主机调试 | `/Users/xaa/zuoye/tools/agent-browser.sh oneform snapshot -i` |

**不要用** work-a / asr 等其他浏览器。

---

## 一键启停（推荐）

```bash
# 启动（单实例，日志追加 solve.log）
/Users/xaa/zuoye/oneform/RQOAE/start_solve.sh

# 观察
tail -f /Users/xaa/zuoye/oneform/RQOAE/solve.log

# 停止
/Users/xaa/zuoye/oneform/RQOAE/stop_solve.sh
```

主脚本：**`solve_tasks.py`**（分析 → 设 slider → 提交前复检 → 提交 → 等 90s → 下一批）。无题后自动退出。

---

## 当前任务形态（2026-06 实测）

平台 `templateTaskType` 常见两类，脚本均已支持：

### 1. SFX-MUSHRA-Style（当前主流）

- 页面标题如：*Rating quality of Post-Extension Audio Edits*
- 每批 **1 个 Redux task**，含 **A–E 五个样本**（`audio_model_A` … `audio_model_E`）
- 页面上 **5 个 rc-slider**，每样本一个 1–5 分
- 页面预估做题时间约 **2 分钟**
- 分析：**PANNs + CLAP**（不跑 Whisper，节省时间）
- 音频 URL 来自 `api.tryrating.com`，下载时必须 `credentials: include`（脚本已处理）

### 2. Transition quality（历史批次）

- 每批多个 task，各有 `audio_src` + `overlap`
- 编辑窗口：`10 ± overlap/2` 秒附近
- 分析：**PANNs + CLAP + Whisper**（人声截断检测）

---

## 评分原则

- 每段音频**独立**分析，模型输出仅作参考，禁止单一阈值批量定分。
- 编辑类型（intro/outro/bridge/pre/post）评判重点不同，见 `AGENTS.md`。
- 双模型分歧 >1.5 时，以 PANNs 为准。

---

## 提交前必须复检（脚本已内置）

1. 所有 slider 的 `aria-valuenow` 与预期 1–5 一致（**不是** `activeDots` 数量）
2. 复检失败 → 重设一次 → 仍失败则**不提交**
3. 提交后检查 URL / 弹窗；无题时循环自动结束

---

## 时间安排

| 阶段 | 策略 |
|---|---|
| 单批做题 | 目标约 110s（MUSHRA）/ 90s（Transition）；仅在做题过快时最多补等 40s |
| 批间等待 | 提交成功后等 **90s** 再做下一批 |
| 无题 | 连续 5 次无任务或页面显示 *Looking for surveys* → 退出 |

---

## 遇错即停

| 情况 | 处理 |
|---|---|
| 音频下载失败 / <1KB | 停止，报告用户 |
| 模型分析异常 | 停止，不猜分 |
| 登录 / 验证码 | 通知用户用 noVNC 处理 |
| 同一错误 | 最多重试 2 次 |

---

## 辅助脚本（手动调试用）

| 脚本 | 用途 |
|---|---|
| `fetch_audio.py` | 单条音频下载 |
| `analyze_audio_quality.py` | 单条 PANNs+CLAP 分析 |
| `submit_now.py` / `do_all.py` | 手动设 slider 并提交 |

日常做题**只需** `solve_tasks.py`，不要从零重写。

---

## 知识库（按需）

```bash
cat pipeline/knowledge/rqoae/compact_sop.md
cat pipeline/knowledge/rqoae/flow.md
```

---

## 开工检查清单

```
[ ] oneform 浏览器已登录 tryrating，页面在 /app/survey/rate
[ ] 用 start_solve.sh 启动（确认无重复进程）
[ ] tail solve.log 确认 FOUND NEW BATCH → PRE-SUBMIT ✓ → Submit
[ ] 无题后脚本自行退出，或 stop_solve.sh 手动停止
```
