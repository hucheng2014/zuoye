# PR Certification 可靠做题流程（指纹防护 + 自动判分）

## 原则
- **页面 TPT** 是唯一计时标准，目标每题 **≈ 720s（12 分钟）**
- **禁止刷新页面**：刷新/重新 Start 后 TPT **归零**，720s 从 0 重计；`form_filled.flag` 作废，须重新填表
- **禁止**在脚本中 `page.reload()` — 会毁掉已累计的 TPT
- **新题检测** → extract → **Agent 手动判分** → `current_ratings.json`（含 `fingerprint`）
- **三重 stale guard**：文件指纹一致 + bridge 提交前校验 + submit 时 live 页面指纹校验
- **到点提交**：仅当 `validate_ratings.js` 通过 + 页面表单复检通过才允许 `submit_from_ratings.js`
- **单 CDP 拥有者**：`task_bridge.js`；判分不占用 CDP
- **LLM 判分 API 已停用**：不再调用 `grade_task.js`

## 两阶段：720s 前填表，720s 只提交

**判分完成后立即**（TPT 远小于 720s）：

1. `fill_from_ratings.js` — 填表 + 表单复检（不要求 TPT≥720）
2. 通过则写 `runs/form_filled.flag` + `runs/submittable.flag`

**到 720s**：

3. `submit_from_ratings.js --submit-only` — 复检表单 + TPT≥720 → 点 Submit（<15s）
4. 若表单被清空，紧急重填一次再提交
5. **提交后复检** `verifyAfterSubmitWithRetry()`

填表检查项（`verifyFormSubmittableOn`）：

- `RESPONSES N/N Complete`
- `Compare N/N Complete`
- Rationale ≥ 50 字符
- Submit 按钮为 **Submit**（非 Invalid answers）

手动复检命令：

```bash
node verify_task.js --form-only   # 仅检查页面表单是否填完（不验 TPT）
node verify_task.js               # 全量提交前检查
node verify_task.js --after       # 提交后检查
node validate_ratings.js          # 文件级 ratings 指纹门禁
```

## 启动
```bash
cd "PR CERTIFICATION"
chmod +x start_pipeline.sh
./start_pipeline.sh
```

进程：
| 进程 | 作用 |
|------|------|
| `task_bridge.js` | Start → extract → 保活 720s → 校验 → 提交 → 下一题 |
| `auto_grade_daemon.js` | ratings_watchdog：监控判分是否就绪（**不调用 LLM**） |

## Agent 手动判分流程（每题必做）

extract 完成后**立即**：

1. 读 `current_task.json`（含 fingerprint、responses、userRequest）
2. 按 PR V5 规则**独立判分**（读教程文档，禁止硬编码）
3. 写 `current_ratings.json`（**fingerprint 必须与 task 一致**）
4. 运行 `node validate_ratings.js` 确认通过
5. `task_bridge` 判分后立刻 `fill_from_ratings.js`，保活至 720s 后 `--submit-only` 提交

`runs/needs_grading.flag` 存在 = 该 fingerprint 尚待判分。

## 文件
| 文件 | 作用 |
|------|------|
| `current_task.json` | 当前题 + `fingerprint` + `extractedAt` |
| `current_ratings.json` | 判分 + **必须相同 `fingerprint`** + `gradedAt` |
| `task_utils.js` | 指纹计算、invalidate、校验 |
| `grade_task.js` | ~~LLM 判分~~ **已停用**，保留文件仅供参考 |
| `validate_ratings.js` | 提交前 CLI 门禁 |
| `runs/stale_guard.log` | 旧 ratings 作废记录 |

## 收尾停止（避免非活跃挂机）
```bash
# 含当前题再做 N 题后自动 shutdown（关 bridge + 关 Annotation Tool 标签页）
nohup bash auto_finish_after_n.sh 4 >> runs/auto_finish.log 2>&1 &
# 或立即手动收尾：
bash shutdown_all.sh
```
`shutdown_all.sh` 会：停 `task_bridge` / `auto_grade_daemon` → **关闭 starshot 标签页**。

## 2 响应 / 3 响应变体
- 页面可能是 **2 响应 + 1 对比**（`RESPONSES 0/2`、`Compare 0/1`）或 **3 响应 + 3 对比**
- `task_utils.js` 从 task-editor 的 tab 自动检测 `responseKeys` / `comparisonKeys`
- 修改 `task_utils.js` / `grade_task.js` 等后需 **重启** `start_pipeline.sh`，否则旧进程仍按 3 响应提取

## 铁律（封号级）
1. **绝不允许** fingerprint 不一致时提交
2. 新题开始时 `invalidateRatings()` 立即作废上一题 `current_ratings.json`
3. `ratingsReady=true` 仅当 `validateRatingsForTask()` 通过
4. Concision=Acceptable 必须带 `description` 字段
5. 禁止 `submit_task_*.js` 硬编码判分

## 手动
```bash
node run_pipeline.js      # 仅提取（会 invalidate 新 fingerprint）
# node grade_task.js      # 已停用 — 改由 Agent 写 current_ratings.json
node validate_ratings.js  # 检查判分是否可提交
node submit_now.js        # 紧急提交（同样走 stale guard）
```

## 环境变量
- `PR_SUBMIT_AT_SEC` — 默认 720
