# CJK Locale Case Studies

## Purpose
Official case studies from the May 22 feedback report for Chinese locale tasks. These are the exact calibration examples used by the official auditors.

---

## zh_CN (Simplified Chinese): Hidden Additional Personal Info

### Scenario
- **Previous Mail**: Li Mingyuan writes to Liu Yang, asking if Liu Yang is available for the next round of interviews.
- **User Prompt**: `这是我的空档` ("Here are my available times")
- **Additional Personal Info field** contains: `2026年1月5日（周一）下午 2:00-4:00` and `2026年1月6日（周二）上午 9:30-11:00`

### Model Response
`很高兴收到您的邮件...我目前在 2026 年 1 月 5 日（周一）下午 2:00 至 4:00，以及 2026 年 1 月 6 日（周二）上午 9:30 至 11:00 这两个时间段比较方便...`

### Original (Wrong) Rating
Rater scored this as **Not Grounded**, believing the specific dates and times were hallucinated since the User Prompt only says "here are my available times" without listing any times.

### Official Calibration Verdict
**Grounded.** The specific dates and times appear verbatim in the Additional Personal Info field. The rater failed to check this field before scoring.

### Lesson
The Additional Personal Info field often contains the actual data that the User Prompt references in shorthand. ALWAYS check this field before ruling on Groundedness. This is the single most common source of false "Not Grounded" ratings in zh_CN tasks.

---

## zh_HK (Hong Kong Cantonese): Minor Styling Leniency

### Scenario
- **Previous Mail**: Lam Ka Yan writes to Yu Han, reminding about domain renewal and asking about interest in AI customer service partnership with "智聯科技."
- **User Prompt**: `暫時沒有興趣` ("Not interested for now")

### Model Response (Cantonese)
`你好嘉欣, 多謝你嘅電郵同埋更新。關於你提到嘅域名續期，我會盡快安排處理。至於你介紹嘅「智聯科技」合作機會，我哋暫時未有興趣進一步了解，不過都多謝你嘅推薦。祝好, 宇瀚`

### Formatting Issues Present
- Greeting `你好嘉欣,` has no space after comma before next sentence
- Sign-off `祝好,` and name `宇瀚` are on the same line with no paragraph break
- Lacks clear paragraph structure/segmentation

### Official Calibration Verdict
**Followed and Fit** for Instruction Adherence. **No Localization Issue.** In Hong Kong Cantonese business email context, these are defined as "minor stylistic issues" that do not constitute serious contextual violations. The draft uses natural Cantonese vocabulary (`多謝你嘅`, `我哋`, `同埋`), appropriate tone, and correctly follows the instruction to decline.

### Lesson
Do not over-penalize zh_HK drafts for minor formatting/spacing issues when the content, vocabulary, and instruction compliance are all correct. Hong Kong business email formatting is more flexible than Taiwan or mainland standards.

---

## zh_TW (Taiwan Traditional Chinese): Punctuation Format Errors

### Scenario
- **User Prompt**: `謝謝你的關心` ("Thanks for your concern")

### Response A (Contains Localization Error)
`奕安啊：看到你的信我也很開心啦，謝謝你的關心喔！我最近都還不錯，一切都好。你也要好好照顧自己喔！ 志明`

### Response B (Fully Compliant)
`奕安啊：看到你的信我也很開心啦！謝謝你的關心，我最近一切都很好喔，請不用擔心。...`

### Analysis
- Both responses correctly use full-width colon `：` after the greeting (`奕安啊：`) -- this part is correct
- Response A has punctuation format issues: inconsistent comma and period combinations that deviate from Taiwan-standard email formatting, potential half-width/full-width mixing
- Response B follows Taiwan punctuation conventions consistently throughout

### Official Calibration Verdict
- Response A: **Localization Issue** flagged for punctuation format non-compliance in zh_TW context
- Response B: **No Localization Issue**, fully compliant with Taiwan formatting standards

### Lesson
For zh_TW tasks, check not just the greeting colon (which is often correct) but ALL punctuation throughout the body text for full-width consistency and Taiwan-standard formatting. Inconsistent punctuation within the body is a localization error even if the greeting format is correct.
