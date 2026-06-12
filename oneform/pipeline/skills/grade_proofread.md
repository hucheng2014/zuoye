---
name: grade_proofread
description: |
  抓取当前 PROOFREAD 任务数据，根据 SOP 分析判分，生成答案 JSON，填写并提交。
  在 controlled-browser-local-browser (CDP 9235, VNC 6083) 上操作。
---

# Skill: grade_proofread

## 步骤

1. **抓取题目**
   ```bash
   cd /Users/xaa/zuoye/oneform/renzheng/PROOFREAD/scripts && node extract_task.js
   ```

2. **保活启动**（AI 分析期间必须运行）
   ```bash
   cd /Users/xaa/zuoye/oneform/renzheng/PROOFREAD/scripts && node keepalive_lite.js &
   ```

3. **分析判分**
   - 参考 SOP: `/Users/xaa/zuoye/oneform/renzheng/PROOFREAD/SOP.md`
   - V2 核心判分体系：Correctness (Y/N), Completeness (Y/N), Formality
   - 中文本地化：zh-CN / zh-TW / zh-HK 各有不同标点规范
   - Harmfulness 安全评估：23 个子类
   - 每个维度独立评估，禁止互相污染

4. **填写答案**
   ```bash
   cd /Users/xaa/zuoye/oneform/renzheng/PROOFREAD/scripts && node fill_task.js --answer '<json>'
   ```

5. **停止保活，启动 bridge**
   ```bash
   pkill -f keepalive_lite.js
   cd /Users/xaa/zuoye/oneform/renzheng/PROOFREAD/scripts && node bridge.js &
   ```

6. **提交**
   ```bash
   cd /Users/xaa/zuoye/oneform/renzheng/PROOFREAD/scripts && node full_submit.js
   ```

7. **等待下一题**（至少 4 秒）
   ```bash
   sleep 5
   cd /Users/xaa/zuoye/oneform/renzheng/PROOFREAD/scripts && node click_next_task.js
   ```

## 约束
- 每题 ≥ 12 分钟
- 每日最多 28 题, 7.5 小时
- Inactive ≤ 30%
- 遇到登录/验证码 → 通知用户打开 VNC http://127.0.0.1:6083/vnc.html
