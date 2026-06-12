---
name: grade_mail
description: |
  抓取当前 Mail Smart Reply / TA Message Reply 任务数据，根据 SOP 分析判分，生成答案，填写并提交。
  在 controlled-browser-browser (CDP 9233, VNC 6082) 上操作。
---

# Skill: grade_mail

## 步骤

1. **抓取题目**
   ```bash
   cd /Users/xaa/zuoye/oneform/renzheng/MAIL/scripts && node extract_task.js
   ```

2. **分析判分**
   - 参考 SOP: `/Users/xaa/zuoye/oneform/renzheng/MAIL/grading.md`
   - 高风险维度: Personalization, Groundedness
   - 中英文标点与本地化 (zh_TW / zh_CN / zh_HK / da_DK / nb_NO)
   - 指令遵循与语境契合 (Contextual Fit)
   - Subject Line 与成对比较 (Pairwise)
   - 核查 Additional Personal Info 完整数据，禁止盲打幻觉标签

3. **填写答案**
   ```bash
   cd /Users/xaa/zuoye/oneform/renzheng/MAIL/scripts && node fill_task.js --answer '<json>'
   ```

4. **提交**
   ```bash
   cd /Users/xaa/zuoye/oneform/renzheng/MAIL/scripts && node next_task.js
   ```

## 约束
- 每题 ≥ 8 分钟
- 各维度独立评估，禁止连带处罚
- Additional Info 100% 核查后再判 Groundedness
- 遇到登录/验证码 → 通知用户打开 VNC http://127.0.0.1:6082/vnc.html
