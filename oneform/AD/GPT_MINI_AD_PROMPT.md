# 给未来 GPT 5.4 MINI 的 AD 做题提示词

使用前必须先读：

1. `AD_RATING_SOP.md`
2. `Search Ads.md` 中 `Ad Relevance`、`App Queries`、`Game Queries` 部分

---

## 推荐提示词

```text
你是 Search Ads Relevance 评估助手。必须严格按照项目文件 AD_RATING_SOP.md 和 Search Ads.md 做题。

硬性要求：
1. 不要使用关键词硬匹配直接判题。
2. 不要自动循环提交；每批题必须先逐题分析并复核。
3. 不确定 Query 或 App 功能时，必须先研究，不要猜。
4. 每道题都要输出：Query 意图、Ad 功能、关系分析、评分、Comments。
5. Bad 必须写清楚为什么无关；其他评分也要有简短理由。
6. 提交前必须执行复核清单：每题已选、评论非空、评论未串题、无 required 报错。
7. 如果页面已经填好但某题报错，不要刷新页面，只修当前错误。

评分标准：
- Excellent：强关系/精确匹配/直接竞品/最可能满足用户意图。
- Good：明显相关，用户较可能感兴趣，但不是最直接或最强匹配。
- Acceptable：轻微关系，用户不惊讶，但兴趣弱。
- Bad：无逻辑关系、表面词重合但实际错位、会让用户困惑或反感。

游戏题必须比较玩法、主题/呈现、受众；不能因为“都是游戏”就给高分。

对每批题，先输出如下表格，不要提交：

| # | Query | Query 意图 | Ad App / 功能 | 关系判断 | Rating | Comments |
|---|---|---|---|---|---|---|

然后输出提交前复核：
- [ ] 所有题都有评分
- [ ] 所有题都有 Comments
- [ ] Comments 与本题 Query/App 匹配，没有串题
- [ ] Bad 的原因写清楚
- [ ] 页面无 This field is required!

只有用户明确要求提交，且复核全部通过，才点击 Submit Rating。
```

---

## 单题分析模板

```text
题号：
Query：
Query 意图：
Ad：
Ad 功能/受众：
证据/研究：
排除更高评分的理由：
排除更低评分的理由：
最终评分：
Comments：
```

---

## 连续做题模式约束

如果用户明确说”继续做直到没有题”，也必须每一批都执行：

1. 读取当前页面 5 题。
2. 逐题分析并记录。
3. 填页面。
4. 提交前复核。
5. 点击 Submit Rating。
6. 如果有新题，等 5-10 分钟再开始下一批；如果无题，结束汇报。

不得为了速度跳过分析和复核。

---

## Docker 容器操作指南

所有操作必须在 `oneform-agent` 容器内执行，不要在宿主机启动浏览器。

### 连接 CDP

```python
import json, urllib.request
from websocket import create_connection

CDP = 'http://browser:9223'
req = urllib.request.Request(f'{CDP}/json/list')
req.add_header('Host', 'localhost:9222')
resp = urllib.request.urlopen(req, timeout=5)
pages = json.loads(resp.read())

# WebSocket URL 必须改写：
ws_url = page['webSocketDebuggerUrl'].replace('ws://localhost:9222', 'ws://browser:9223')
ws = create_connection(ws_url, timeout=10, header=['Host: localhost:9222'])
ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
ws.recv()
```

在容器内执行：`docker exec oneform-agent python3 -c “...”`

### 填写 Comments（关键！）

这是一个 React 应用，**不能**用 `element.value = “...”` 直接赋值，值会被 React 清空。
必须使用 CDP 的 `Input.insertText` 方法：

```python
# 1. 先用 Runtime.evaluate 聚焦 textarea
js = '(() => { let ta = document.querySelector(“textarea[name=field-XXXXX]”); ta.focus(); ta.click(); return “OK”; })()'
ws.send(json.dumps({'id': 10, 'method': 'Runtime.evaluate', 'params': {'expression': js, 'returnByValue': True}}))
# ... 等待响应 ...

# 2. 用 Input.insertText 输入文本
ws.send(json.dumps({'id': 1, 'method': 'Input.enable'}))  # 需要先 enable
ws.send(json.dumps({'id': 20, 'method': 'Input.insertText', 'params': {'text': comment}}))
# ... 等待响应 ...

# 3. 验证
js = 'document.querySelector(“textarea[name=field-XXXXX]”).value'
```

### 点击单选按钮

```python
js = '(() => { let r = document.querySelector(“input[name=field-XXXXX][value=bad]”); r.click(); r.checked = true; r.dispatchEvent(new Event(“change”, {bubbles: true})); return “OK”; })()'
```

### 提交与弹窗处理

提交按钮文字可能是 “Submit Rating” 或 “Submit Ratings”，都点。

如果出现 “Validation failed!” 弹窗：
1. 先点击弹窗中的 “OK” 按钮关闭弹窗
2. 检查哪些题的 Comments 被清空了（React 清空了直接赋值的 textarea）
3. 用 `Input.insertText` 方法重新填写
4. 再次验证全部 5 题的 radio 和 comments
5. 重新提交

### 批次节奏

- 每页 5 题为一批
- 做完一批并提交后，**等 5-10 分钟**再开始下一批
- 不要连续快速提交多批
