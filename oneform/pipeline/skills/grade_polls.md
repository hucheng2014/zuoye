---
name: grade_polls
description: |
  抓取当前 Intelligent Polls 任务数据，根据 SOP 分析判分，生成答案 JSON，填写并提交。
  在 controlled-browser-browser (CDP 9233, VNC 6082) 上操作。
---

# Skill: grade_polls

## 步骤

1. **抓取题目**
   ```bash
   cd "/Users/xaa/zuoye/oneform/renzheng/TA Intelligent Polls/scripts" && node extract_task.js
   ```

2. **保活启动**
   ```bash
   cd "/Users/xaa/zuoye/oneform/renzheng/TA Intelligent Polls/scripts" && node keepalive_lite.js &
   ```

3. **分析判分**
   - 参考 SOP: `/Users/xaa/zuoye/oneform/renzheng/TA Intelligent Polls/SOP.md`
   - 评分维度: Relevance, Accuracy, Helpfulness, Harmfulness, Coherence
   - 每个维度独立评估
   - 生成答案 JSON 含 judgement 字段

4. **填写答案**
   ```bash
   cd "/Users/xaa/zuoye/oneform/renzheng/TA Intelligent Polls/scripts" && node fill_task.js --answer '<json>'
   ```

5. **停止保活，启动 bridge**
   ```bash
   pkill -f keepalive_lite.js
   cd "/Users/xaa/zuoye/oneform/renzheng/TA Intelligent Polls/scripts" && node bridge.js &
   ```

6. **提交**
   ```bash
   cd "/Users/xaa/zuoye/oneform/renzheng/TA Intelligent Polls/scripts" && node full_submit.js
   ```

7. **等待下一题**
   ```bash
   sleep 5
   cd "/Users/xaa/zuoye/oneform/renzheng/TA Intelligent Polls/scripts" && node click_next.js
   ```

## 约束
- 每题 ~5 分钟 (TpT 260s-320s 随机)
- 每日最多 70 题, 7 小时
- Inactive ≤ 10%
- 遇到登录/验证码 → 通知用户打开 VNC http://127.0.0.1:6082/vnc.html
