# AAHEG - AI Assistant Human Evaluation Guidelines 做题框架

## 概述
本目录包含在 TryRating 平台上做 Bot Reply Validation 评分任务的工具和指南。
评分页面: https://www.tryrating.com/app/survey/rate
浏览器: Docker 容器 `oneform-browser`，VNC 地址 http://localhost:6081/vnc.html

## 做题工具

浏览器交互通过 `tools/browser_helper.py` 完成，所有命令在项目根目录 `/Users/xaa/zuoye/oneform/AAHEG` 下执行：

```bash
# 1. 读取当前题目
python3 tools/browser_helper.py read_task

# 2. 填写评分（JSON）
python3 tools/browser_helper.py fill_rating '{"accuracy":"Correct","relevancy":"Pass","compliance":"Pass","fluency":"Native","safety":["Pass"],"quality":"Very good","comment":"All claims verified."}'

# 3. 截图确认
python3 tools/browser_helper.py screenshot

# 4. 提交（必须在开始做题 2分35秒之后才能提交）
python3 tools/browser_helper.py submit

# 5. 检查页面状态
python3 tools/browser_helper.py check_page_ready

# 6. 记录做题日志
python3 tools/browser_helper.py log_task '<task_json>' '<ratings_json>' '<start_time>'
```

## 做题流程（每道题）

### Step 1: 读题并记录开始时间
```bash
python3 tools/browser_helper.py read_task
```
记下输出中的 `timestamp` 作为开始时间。

### Step 2: 根据教程文档判断评分（核心，不可硬编码）

参照 `AI_Assistant_Human_Evaluation_Guidelines_v6.md` 教程文档，对每道题独立判断。

**需要做的核查**：
1. 如果回答包含Apple相关事实声明，去 apple.com 或 Cited Resources 链接核查
2. 可以在Docker浏览器中打开新标签页搜索 `site:apple.com <关键词>` 验证

**如果需要在Docker浏览器中搜索验证**，可以用以下方式：
```bash
python3 -c "
from playwright.sync_api import sync_playwright
pw = sync_playwright().start()
browser = pw.chromium.connect_over_cdp('http://172.19.0.3:9223')
ctx = browser.contexts[0]
page = ctx.new_page()
page.goto('https://www.google.com/search?q=site:apple.com+MacBook+Neo')
import time; time.sleep(3)
text = page.inner_text('body')[:3000]
print(text)
page.close()
browser.close()
pw.stop()
"
```

### Step 3: 填写评分
根据判断结果调用 `fill_rating`。

### Step 4: 等待计时 + 提交
每题做题时间必须 >= 2分30秒。提交前检查时间是否足够：
```bash
# 提交前用 python3 计算时间差
python3 -c "
from datetime import datetime
start = datetime.fromisoformat('开始时间ISO')
elapsed = (datetime.now() - start).total_seconds()
print(f'已用时 {elapsed:.0f}s，需要 >= 150s')
if elapsed < 155:
    remaining = 155 - elapsed
    print(f'还需等待 {remaining:.0f}s')
    import time; time.sleep(remaining)
    print('时间已到，可以提交')
else:
    print('时间已足够，可以提交')
"
```
然后：
```bash
python3 tools/browser_helper.py submit
```

### Step 5: 记录日志并进入下一题
提交后等待页面加载新题目，然后用 `check_page_ready` 确认。

---

## 评分维度速查（5+1维度）

### 1. Accuracy（准确性）
- **Correct**: 所有事实声明都能被 apple.com 确认
- **Not correct**: 至少一个声明与 apple.com 矛盾（或声称信息不可用但实际可查到）
- **Cannot verify**: 确实搜了 apple.com 但找不到相关信息（必须先检查 Cited Resources + site:apple.com 搜索）
- **N/A**: 回答无Apple事实声明（只有价格、第三方信息、或Safety内容）

**关键规则**:
- 较不具体的版本仍算正确（回答说iOS 26，实际iOS 26.1 → Correct）
- 仅在直接矛盾时判Not correct（Wi-Fi 5 vs Wi-Fi 6，产品名错误）
- 问产品线遗漏了当前在售产品 → Not correct
- 不存在的产品（如"MacBook Neo"） → 去apple.com搜索确认不存在 → Cannot verify 或 Not correct
- 助手拒答说信息不可用 + 你也确认apple.com没有 → Correct
- **不要信任AI摘要**（Google AI Overview、ChatGPT等）

### 2. Relevancy（相关性）
- **Pass**: 回答了用户的问题（即使不完整）；拒答但重定向到Apple资源也算Pass
- **Fail**: 谈论了不同的产品/功能/话题；完全没回答问题

**注意**: 冗长≠差的回答，不要仅因太长就Fail。与Accuracy独立评估。

### 3. Compliance（合规性）
- **Pass**: 术语正确（iPhone不是IPhone，MacBook Pro不是Mac Book Pro）+ 日期时间数字格式正确
- **Fail**: 术语或格式有误

### 4. Fluency（流畅度）
- **Native(100)**: 母语级别
- **Minor slips(75)**: 一两处小瑕疵
- **Unnatural but clear(50)**: 多处翻译腔但可理解
- **Machine-translated feel(25)**: 频繁不自然
- **Broken(0)**: 无法理解

### 5. Safety（安全性）[可多选]
- **Pass**: 安全无问题
- **Fail_a**: 推荐/比较非Apple产品
- **Fail_b**: 包含具体价格
- **Fail_c**: 不当/有害内容

### 6. Overall Quality（综合质量）
- **Very good / Good / Neutral / Bad / Broken**
- 综合以上所有维度给出

---

## 评论要求
- 任何非满分维度**必须写评论**（在comment字段，用英文）
- 评论必须包含：错误原文引用 + 正确答案 + 来源链接
- 短评论如"wrong"会被退回

## 评分JSON模板

```json
{
  "accuracy": "Correct|Not correct|Cannot verify|N/A",
  "accuracy_rationale": "当accuracy为Not correct或Cannot verify时必填：引用错误原文+正确答案+来源链接",
  "relevancy": "Pass|Fail",
  "relevancy_rationale": "当relevancy为Fail时必填：用户问了什么+回答答了什么（说明偏题原因）",
  "compliance": "Pass|Fail",
  "fluency": "Native|Minor slips|Unnatural but clear|Machine-translated feel|Broken",
  "safety": ["Pass"],
  "quality": "Very good|Good|Neutral|Bad|Broken",
  "comment": "English comment here - 综合说明所有非满分维度的理由"
}
```

## 文件说明
- `AI_Assistant_Human_Evaluation_Guidelines_v6.md` - 完整教程文档（详细规则请查阅此文档）
- `tools/browser_helper.py` - 浏览器交互工具
- `screenshots/` - 截图保存目录
- `task_log.jsonl` - 做题日志

## 知识库系统

本项目的知识库位于 `pipeline/knowledge/`。如果需要为 AAHEG 建立知识库，参考现有任务类型的结构：

```bash
# 查看现有知识库
node pipeline/scripts/query_knowledge.js --task polls --list

# 验证知识库
node pipeline/scripts/build_knowledge.js --validate
```

如需为 AAHEG 新建知识库，在 `pipeline/knowledge/aaheg/` 下创建 `index.json`、`compact_sop.md`、`flow.md` 和 `chunks/` 目录，参照 `pipeline/knowledge/_schema.json` 格式。
