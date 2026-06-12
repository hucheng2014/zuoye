# PutonghuaASR Agent Memory

> **本文件是项目的持久记忆入口。Kilo 启动时自动读取。不要改动文件名。**

---

## 项目背景

- 目标：在 Sonic JD 标注页面完成普通话 ASR 标注任务
- 平台：`https://sonic.jd.com/#/annotation/dataset/annotate`
- 主要本地 ASR：`Qwen3-ASR` + `FireRedASR-AED-L` 双路复核；Linux 路径分别为 `/Users/xaa/zuoye/putonghuaasr/models/Qwen3-ASR` 和 `/Users/xaa/zuoye/putonghuaasr/models/FireRedASR-AED-L`

---

## 强制规则（每次做题前必读）

### 禁用项（绝对禁止）

1. **禁止使用页面"自动标注"按钮** —— 该功能不可靠，使用后高概率错题。
2. **禁止使用页面 ASR/`paraformer`/其它在线模型** —— 只能用本地 Qwen3-ASR 与本地 FireRedASR-AED。
3. **禁止在用户看不到做题依据时后台提交** —— 每题必须先展示依据。
4. **禁止用提示词导致复读幻觉** —— 短音频必须结合无备注诱导的本地双 ASR 结果复核，不能把提示词/备注当识别结论。
5. **禁止跳过本地 ASR** —— 任何情况下都必须先跑本地 `Qwen3-ASR` 与 `FireRedASR-AED-L`，不能只看备注、页面文本或主观猜测直接标注。
6. **禁止仅凭备注硬判 `SC`** —— 只有备注与本地双 ASR 均指向同一文本，且音频确有清晰人声时，才允许标 `SC` 并填写文本；若本地 ASR 为空、明显幻觉、与备注冲突或无法确认文本，不能标 `SC`。`SA` 只用于极少数方言/口音人声，普通话听不懂且无法确认文本的情况；其余不清晰音频优先按 `BS` 或静音题处理。

### ASR 工具链

- 双模型脚本：`/Users/xaa/zuoye/putonghuaasr/_work_context/local_segment_dual_asr.py`
- 用法：`/Users/xaa/zuoye/putonghuaasr/.venv/bin/python /Users/xaa/zuoye/putonghuaasr/_work_context/local_segment_dual_asr.py --url "音频URL" --segments "segmentId,start,end" --gains "5,10"`
- 模型：`/Users/xaa/zuoye/putonghuaasr/models/Qwen3-ASR`（本地 Transformers）与 `/Users/xaa/zuoye/putonghuaasr/models/FireRedASR-AED-L`（CPU）
- Qwen3-ASR 单模型脚本可用于排障：`/Users/xaa/zuoye/putonghuaasr/_work_context/local_segment_asr.py`
- 能量分析：`/Users/xaa/zuoye/putonghuaasr/_work_context/analyze_audio_energy.py`

### 标注分类（仅 3 种）

| 标签 | 含义 | 文本 |
|------|------|------|
| SC | 清晰可转写 | 填写文本 |
| SA | 方言/口音人声，普通话听不懂且无法确认文本 | 留空 |
| BS | 背景噪音/背景人声 | 留空 |

### 音频 URL 来源

- **不要用** `performance.getEntriesByType('resource')` 取历史 wav（可能拿到上一题）。
- **正确做法**：优先从当前题 Vue 状态 `currentUtterance.url` 或当前 `/annotation/get_utterance/` 接口响应获取。
- 每次做题必须先读取能绑定当前页面文件名的音频 URL，不能用历史缓存 URL。

### 文本与页面状态

- **SC 文本强制使用标点符号**：按实际语气和断句填写必要中文标点，提交前必须确认标点存在且合理，禁止去掉标点。
- **提交前复查分段完整性**：标注页面可能自动删掉人工分段，提交前必须确认当前分段仍存在；如被删掉，先按原人工分段恢复后再提交。
- **禁止删段逃避标注**：不想标注、听不清、背景音或出现多段音频时，都不能删除任何人工分段；每段都必须按标准判断为 SC/SA/BS 并完成标注。`SA` 只留给少数方言/口音听不懂且无法确认文本的段落。
- **无人工分段/无效音频处理**：如果页面没有人工分段，不能用旧 `tableData` 或补假分段提交；必须在页面顶部“请选择音频分类”下拉框选择 **无效音频**，确认选择已生效后再提交。
- **静音音频处理**：确认整段静音或本地能量分析 `rms = 0` 后，不新建分段、不填写文本，按“无人工分段/无效音频处理”选择顶部 **无效音频** 后提交。
- **失败即停止，禁止带错提交**：任何回填、分类、文本、分段数、DOM/Vue 校验失败时，必须停止处理并报告；禁止在已知 `set_text`、`select_category`、回填脚本、逐段复核失败后继续点击提交。
- **只允许 SC 有文本**：`SC` 必须填写带合理标点的文本；`SA`/`BS` 必须留空。若非 `SC` 行存在文本，或 `SC` 行无文本/无标点，禁止提交。

### 上下文控制（防止超限）

- **每做 3-5 题主动压缩上下文**：优先执行 `/compact` 或 `/summarize`，不要等上下文超限报错后再处理。
- **每个新会话只做小批次题目**：重开新对话是正常工作流，不要追求单会话刷完整包。
- **AGENTS.md 保持精简**：只保留强制规则、常见坑和流程，不要追加完整做题流水。
- **详细流水写入外部文件**：做题记录写到 `_work_context/run_records.md`，需要追溯时再手动读取。
- **浏览器操作保持精简**：优先从当前题 Vue 状态读取文件名、音频 URL、备注和分段，不反复 dump 全页面、网络请求或历史 resource。
- **ASR 输出保持精简**：只保留每段最终候选、置信风险和判断依据，避免粘贴完整冗长日志。

### 提交前展示清单（必须展示给用户）

每题提交前在对话中列出：
1. 文件名
2. 人工分段时间
3. 本地 Qwen3-ASR 与 FireRedASR-AED 结果
4. 备注 USER
5. 最终标签
6. 最终文本（SC 必须带合理标点）
7. 回填校验结果：页面当前分段数、每行标签和文本必须与最终方案完全一致；不一致禁止提交

---

## 已验证的常见场景

### 短音频（如 < 1s）

本地 Qwen3-ASR/大模型 ASR 对 1~2s 音频可能出现：
- 空文本
- 复读幻觉（如 `好好好好`）
- 被提示词或常见语料带偏的幻觉文本

**判断原则**：
- ASR 空 + 备注上下文能确认短句 → 按确认文本填 SC
- ASR 空 + 增益后仍空 + 备注无法确认 → 优先 `BS`；只有确认是方言/口音人声但普通话听不懂时才用 `SA`，留空
- 复读/幻觉 → 不能按 ASR，参考备注

### 全零静音音频

本地能量分析 `rms = 0` 的整段静音音频，波形无起伏，按无效题处理（不新建分段、不填写文本，直接点击提交）。

### 幻觉文本

常见幻觉：`字幕志愿者`、`媽咪呀`、`蜂蜜`、`圣诞快乐`、`好好好好`、`蜜蜂`
—— 这些不是真实语音，不能按 ASR 填。

### 音频 URL 过期

页面 URL 有签名有效期（约 1 小时）。过期后下载会 403。
**解决**：从当前 Vue 状态重新取 URL，不要缓存历史 URL。

### 签名 URL 手抄错误

长签名 URL 容易在手抄时漏字符或拼错，导致 403。
**解决**：优先把当前 `/annotation/get_utterance/` 响应保存成文件后读取 `utterance.url`，或直接从工具返回结果原文复制完整 URL；不要凭片段手动重组签名链接。

### 下拉框串行/选错行

Element UI 下拉框在多行表格里可能把 `SC/SA/BS` 选到上一行或下一行。
**解决**：提交前必须复核每行 DOM 值；若下拉交互异常，可从当前表格 Vue 组件 `table.store.states.data` 直接修正 `row.sound_category` 与 `row.text`，执行 `$forceUpdate()` 后再次读取 DOM 确认，再提交。

---

## 做题流程

1. **读取页面**：文件名 + 音频 URL + 备注 USER + 人工分段
2. **下载 & ASR**：用 `local_segment_dual_asr.py` 对每段跑 Qwen3-ASR 与 FireRedASR-AED
3. **增益复核**：短音频/低音量加 `--gains "5,10"` 参数
4. **三方校验**：双模型 ASR + 备注 + 上下文，综合一致才按备注
5. **展示依据**：在对话中列出本题判断信息；必须展示本地 Qwen3-ASR 与 FireRedASR-AED 结果，且说明它们是否与备注一致
6. **提交前复查**：确认页面分段完整且未被自动删掉或人为删除，SC 文本已按实际语义添加必要标点
7. **回填 & 提交**：SC 填带合理标点文本，SA/BS 留空；`SA` 只在少数方言/口音听不懂且无法确认文本时使用。多段音频每段都必须保留并标注，静音音频直接提交
8. **硬性提交门禁**：提交前必须用安全回填脚本或等价 CDP 校验确认：最终方案行数 = 当前人工分段数；每行标签完全一致；每行文本完全一致；非 SC 行文本为空；SC 文本有标点。任一条件失败，禁止提交。
9. **无分段题门禁**：当前人工分段数为 0 时，禁止提交任何行级 JSON；只能使用顶部音频分类 **无效音频** 流程。若页面仍有旧 `tableData` 残留，必须视为脏状态，不能按旧行提交。

---

## 运行记录位置

- `AGENTS.md` 只保留强制规则、常见坑和流程，避免每次新会话自动注入过多历史流水。
- 详细做题流水写入 `/Users/xaa/zuoye/putonghuaasr/_work_context/run_records.md`，需要追溯时再手动读取。

---

## CDP 控制方式

- 不依赖 MCP Playwright（避免与其它项目冲突），通过 Chrome DevTools Protocol 直连浏览器控制做题页面。
- CDP 端口统一用 **9225**，独立 profile `/Users/xaa/zuoye/putonghuaasr/.browser_profile`。
- 工具脚本：`_work_context/cdp_helper.py`（基于 Python websocket-client 直连 CDP WebSocket）。
- 获取题目数据：遍历 Vue 组件树找 `currentUtterance`（`app.__vue__` → 递归 `$children`/$parent）。
- **Chrome 启动命令**：`google-chrome --remote-debugging-port=9225 --remote-allow-origins=* --user-data-dir=/Users/xaa/zuoye/putonghuaasr/.browser_profile --no-first-run --disable-sync --disable-default-apps --no-default-browser-check`
- **严禁关闭或跳转用户已打开的做题页面**：任何情况下不得 kill Chrome 进程、关闭标签页、或导航到其他页面；页面状态是用户准备好的做题上下文。

## 题包完成判断

- 提交最后一题后页面不再显示新题（无音频波形、无表格行），即题包完成。
- 等待用户开启新题包后再继续，不要自动切题包。

---

## Docker 容器做题模式

当浏览器运行在 Docker 容器内时（通过 noVNC 可视化），使用以下命令：

### 快速命令

```bash
# 1. 一键读取当前题目（文件名、URL、备注、分段）
docker exec asr-worker-1-agent python3 /app/_work_context/container_read_question.py

# 2. 跑双模型 ASR（Qwen3-ASR + FireRed，耗时取决于本地模型/设备，不要中断）
docker exec asr-worker-1-agent python3 /app/_work_context/local_segment_dual_asr.py \
  --url "音频URL" \
  --segments "seg0,开始秒,结束秒;seg1,开始秒,结束秒" \
  --gains "5,10" \
  --output /app/_work_audio/asr_out.json

# 3. 安全填写并校验（不提交）
docker exec asr-worker-1-agent python3 /app/_work_context/container_safe_fill_submit.py \
  '{"0":"BS","1":{"category":"SC","text":"大家。"}}'

# 4. 校验通过后再提交（推荐把 --expect-filename 填成当前题 filename，防止误提上一题/下一题）
docker exec asr-worker-1-agent python3 /app/_work_context/container_safe_fill_submit.py \
  '{"0":"BS","1":{"category":"SC","text":"大家。"}}' \
  --expect-filename "当前题文件名.wav" \
  --submit

# 无人工分段题：选择顶部音频分类“无效音频”并提交
docker exec asr-worker-1-agent python3 /app/_work_context/container_safe_fill_submit.py \
  '{}' \
  --expect-filename "当前题文件名.wav" \
  --invalid-audio \
  --submit
```

### 容器 CDP 注意事项

- CDP 地址：`http://browser:9223`（容器内部）
- HTTP 请求必须加 `Host: localhost:9222` header
- WebSocket URL 中 `ws://localhost:9222` 需替换为 `ws://browser:9223`
- `cdp_helper.py` 已适配容器环境（读取 `PUTONGHUAASR_CDP_ENDPOINT` 环境变量）
- **禁止用旧脚本直接提交**：`container_fill_annotation.py`、`container_fill_and_submit.py`、`cdp_helper.py select_category/set_text/submit` 只能排障，不得作为正常提交链路；这些脚本可能写错旧 `tableData` 或文本输入失败后仍继续。正常提交必须使用 `container_safe_fill_submit.py --submit` 并检查返回 `ok: true`。
- **禁止 shell 链式盲提**：不得使用 `cmd1 && cmd2 && submit` 这种无法逐段验证结果的链式提交。任何命令输出 `ERROR`、`no text input found`、`no store found`、`ok:false`、空结果或行数不符，都必须停止。
- **多段题特别要求**：最终 JSON 必须覆盖 `0..N-1` 所有分段索引，不能少填、不能多填；安全脚本会强制校验索引完整性。
- **无分段题特别要求**：`container_read_question.py` 返回 `segments: []` 时，必须走 `container_safe_fill_submit.py '{}' --invalid-audio --submit`；禁止用 `{"0":"BS"}` 或任何行级标注处理无分段题。

### 判断规则补充说明

- **FireRed 输出与备注发音接近时视为一致**：如 FireRed="他家" + 备注="大家"，声母韵母高度相似，应判为 SC 并按备注填写
- **Qwen3-ASR 输出繁体或不规范文字但与 FireRed/备注发音一致**：可整理为简体自然文本；若文本不可确认，不能仅凭模型幻觉判 SC
- **短音频双模型仅产生单字语气词或互相冲突，且备注无法确认**：优先 BS
