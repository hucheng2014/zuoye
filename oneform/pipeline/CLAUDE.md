# Oneform Agent Pipeline — Claw Code 自动化流水线

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    orchestrate.js                            │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ monitor  │  │  lane:work-a │  │  lane:work-b │          │
│  │ (oneform)│  │ (Polls/Mail) │  │ (Proofread)  │          │
│  └────┬─────┘  └──────┬───────┘  └──────┬───────┘          │
│       │               │                 │                    │
│       ▼               ▼                 ▼                    │
│  ┌─────────┐   ┌────────────┐    ┌────────────┐            │
│  │CDP 9225 │   │ CDP 9233   │    │ CDP 9235   │            │
│  │VNC 6081 │   │ VNC 6082   │    │ VNC 6083   │            │
│  │oneform  │   │ work-a     │    │ work-b     │            │
│  │browser  │   │ browser    │    │ browser    │            │
│  └─────────┘   └────────────┘    └────────────┘            │
│                       │                 │                    │
│                       ▼                 ▼                    │
│                ┌─────────────────────────────┐              │
│                │     claw prompt (per task)  │              │
│                │  extract → SOP分析 → fill   │              │
│                │      → bridge → submit      │              │
│                └─────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

## 浏览器注册表

| ID       | 端口         | 角色     | 用途                          |
|----------|-------------|----------|-------------------------------|
| oneform  | CDP 9225, VNC 6081 | monitor  | tryrating.com 新题轮询        |
| work-a   | CDP 9233, VNC 6082 | worker   | TA Polls, MAIL, TAMESSAGE     |
| work-b   | CDP 9235, VNC 6083 | worker   | PROOFREAD, SharePoint docs    |
| asr      | CDP 9221, VNC 6080 | auxiliary| ASR/speech tasks              |

## 快速命令

```bash
cd /Users/xaa/zuoye/oneform/pipeline

# 查看全部浏览器和任务状态
npm run status

# 探测浏览器连通性
npm run probe

# 检测当前页面任务类型
npm run detect

# 启动单车道 (dry-run 不实际做题)
npm run lane:a:dry
npm run lane:b:dry

# 启动单车道 (实际做题)
npm run lane:a              # work-a 自动检测任务类型
npm run lane:b              # work-b 自动检测任务类型
npm run lane:a:proofread    # work-b 强制 PROOFREAD
npm run lane:a:polls        # work-a 强制 TA Polls
npm run lane:a:mail         # work-a 强制 MAIL

# 启动监控 (每5分钟检测新题, 有题桌面通知)
npm run monitor

# 启动监控 + 有题自动开 lane
npm run monitor:auto

# 启动全部 (monitor + 两个 lane)
npm run orchestrate

# 带参数启动
node orchestrate.js --lanes work-a,work-b --max-tasks 20 --max-hours 7
node orchestrate.js --lanes work-a --max-tasks 5 --dry-run
```

## 流水线工作流程

1. **monitor.js** 每 5 分钟轮询 oneform 浏览器 (CDP 9225) 的 tryrating 页面
2. 点击 "Check Now"，检测页面文本判断是否有新题
3. 有题 → 桌面通知 + 写 events.jsonl + (可选)自动启动 lane
4. **lane.js** 连接 worker 浏览器，检测当前任务类型
5. 根据任务类型加载对应 SOP 和脚本目录
6. 构建 claw prompt，调用 `claw prompt` 非交互式执行：
   - 运行 extract 脚本抓取题目
   - AI 根据 SOP 分析各评分维度
   - 运行 fill 脚本填写表单
   - 运行 submit 脚本提交
7. 每题结束后 cooldown，进入下一题循环
8. 到达每日上限或无更多任务时退出

## 任务类型

| 类型       | SOP                          | 浏览器 | 每题时间 | 每日上限 |
|-----------|------------------------------|--------|---------|---------|
| PROOFREAD | renzheng/PROOFREAD/SOP.md    | work-b | ≥12min  | 28题/7.5h |
| TA_POLLS  | renzheng/TA Intelligent Polls/SOP.md | work-a | ~5min | 70题/7h |
| MAIL      | renzheng/MAIL/grading.md     | work-a | ≥8min   | 40题/7h |
| TAMESSAGE | renzheng/TAMESSAGE/SOP.md    | work-a | ≥8min   | 40题/7h |

## 铁律

- **禁止跳题** — 必须做当前页面显示的题目
- **各维度独立评估** — 禁止连带处罚
- **保活必运行** — AI 分析期间 keepalive_lite.js 必须运行
- **同一时刻只有一个 CDP 脚本** — 多进程会卡死
- **遇到登录/验证码** → 立即停止，通知用户打开 VNC 手动处理

## 文件结构

```
pipeline/
├── package.json              # npm scripts 入口
├── orchestrate.js            # 多 lane 并行编排器
├── status.js                 # 状态仪表盘
├── scripts/
│   ├── browsers.json         # 浏览器注册表 (CDP/VNC/container)
│   ├── task_types.json       # 任务类型注册表 (SOP/脚本/限制)
│   ├── cdp_probe.js          # 浏览器健康探测
│   ├── detect_task.js        # 页面任务类型识别
│   ├── monitor.js            # 新题轮询 + 通知
│   └── lane.js               # 单车道编排 (claw 集成)
├── skills/
│   ├── grade_proofread.md    # claw skill: PROOFREAD
│   ├── grade_polls.md        # claw skill: TA Polls
│   └── grade_mail.md         # claw skill: MAIL/TAMESSAGE
├── runs/                     # 运行日志和输出
│   ├── events.jsonl          # 事件流
│   └── work-a-YYYY-MM-DD/   # 每日每 lane 运行记录
└── CLAUDE.md                 # 本文件
```

## 知识库系统（RAG 按需检索）

做题时**不再需要**把完整 SOP 塞入上下文。改用分层知识库：

### 架构

```
pipeline/knowledge/
├── _schema.json              # 知识库 schema 定义
├── polls/                    # TA Intelligent Polls
│   ├── index.json            # chunk 注册表（含关键词、优先级）
│   ├── compact_sop.md        # 精简评分规则 (~3KB)
│   ├── flow.md               # 纯操作流程（无评分规则）
│   └── chunks/               # 按维度拆分的详细规则
├── mail/                     # MAIL Smart Reply
├── proofread/                # PROOFREAD 中文校对
├── ad/                       # Search Ads
└── rqoae/                    # Audio Quality
```

### 做题时的上下文加载策略

1. **固定前缀**（prompt cache 友好）：
   - `compact_sop.md`（2-4KB）— 每个维度一句话定义 + 关键判断标准
   - `flow.md`（2-4KB）— 纯脚本命令序列 + 时间约束
   - 合计 ~6KB，替代原来 15-50KB 的完整 CLAUDE.md + SOP

2. **变化部分**：
   - 当前题目 JSON（extract_task.js 输出）

3. **按需查询**（只在不确定时拉取）：
   ```bash
   node pipeline/scripts/query_knowledge.js --task polls --query "relevance off-topic"
   node pipeline/scripts/query_knowledge.js --task mail --chunk groundedness
   ```

### 查询工具用法

```bash
# 关键词搜索（返回最相关的 chunks）
node pipeline/scripts/query_knowledge.js --task <task_id> --query "<问题>"

# 直接读取某个 chunk
node pipeline/scripts/query_knowledge.js --task <task_id> --chunk <chunk_id>

# 查看精简 SOP
node pipeline/scripts/query_knowledge.js --task <task_id> --sop

# 查看操作流程
node pipeline/scripts/query_knowledge.js --task <task_id> --flow

# 列出所有 chunks
node pipeline/scripts/query_knowledge.js --task <task_id> --list

# JSON 格式输出（供程序解析）
node pipeline/scripts/query_knowledge.js --task <task_id> --query "..." --json
```

有效的 task_id: `polls`, `mail`, `proofread`, `ad`, `rqoae`

### lane.js 集成

lane.js 构建 claw prompt 时应：
1. 读取 `knowledge/<task>/compact_sop.md` 作为 system prompt 前缀
2. 读取 `knowledge/<task>/flow.md` 作为操作指令
3. 在 prompt 中告知 AI 可用 `query_knowledge.js` 按需查询
4. 题目数据作为 user message（变化部分）

这样相同前缀在连续做题时触发 prompt caching，token 费用降低 70-90%。

### 维护

```bash
# 验证知识库完整性
node pipeline/scripts/build_knowledge.js --validate

# 查看统计
node pipeline/scripts/build_knowledge.js --stats

# 教程更新后重新构建（手动编辑 chunks 后运行）
node pipeline/scripts/build_knowledge.js
```
