# Global Query 每日详细总结（2026-05-30）

数据来源：controlled-browser Docker 容器，通过 CDP 连接自动采集。
脚本：`global_query_daily_collect.js`

---

## 一、总体概览

- **可见工单**: 24 件
- **全部归属**: Isaac Lighthouse 项目（1 件元数据未提取 / 0044977）
- **已关闭**: 6 件（25%）
- **待处理**: 18 件（75%）
- **今日新建**: 8 件（0044970–0044978）

### 按分类统计

| 分类 | 数量 | 占比 |
|---|---|---|
| Other topics（其他话题） | 11 | 46% |
| TA/TC（文本标注/内容创作） | 4 | 17% |
| VCG（视觉内容生成） | 4 | 17% |
| Tag Tool Issues（标注工具问题） | 2 | 8% |
| LE（语言评估） | 1 | 4% |
| 未提取 | 1 | 4% |
| CYU | 0 | 0% |

### 按语言区统计

| 语言区 | 数量 |
|---|---|
| hi_IN / hi_Latn（印地语） | 4 |
| tr_TR（土耳其语） | 2 |
| pt_BR（巴西葡语） | 2 |
| pl_PL（波兰语） | 2 |
| ko_KR（韩语） | 2 |
| es_ES / es_MX（西班牙语） | 2 |
| vi_VN（越南语） | 1 |
| en_IN（印度英语） | 1 |
| id_ID（印尼语） | 1 |
| ms_MY（马来语） | 1 |
| it_IT（意大利语） | 1 |
| th_TH（泰语） | 1 |
| 其他/未明确 | 4 |

### 按状态统计

| 状态 | 数量 |
|---|---|
| pending（待处理） | 18 |
| closed（已关闭） | 6 |

---

## 二、按问题主题分类分析

### 🕐 今日最大热点：计时器/Timer 集体故障（5 件关联）

**今日新建工单中有 4 件直接涉及计时器异常，横跨多个语言区，表明平台存在系统性计时 Bug。**

| Issue | 标题 | 语言区 | 状态 | 上报时间 |
|---|---|---|---|---|
| 0044976 | VCG Task - Timer Showing "Unknown Error" | hi_IN | pending | 05-30 02:18 |
| 0044971 | Timer error on the platform pt_BR | pt_BR | pending | 05-29 18:17 |
| 0044974 | Technical Issue with Time Calculation Feature on Grading Interface | hi_Latn | pending | 05-29 22:54 |
| 0044977 | TPT warning consequences | id_ID | pending | 05-30 04:37 |
| 0044975 | High TpT report | es_ES | pending | 05-30 01:52 |

**0044976 详情（VCG 计时器显示 "Unknown Error"）**:
- 印度译员（hi_IN）报修：VCG 任务计时器间歇性显示 "Error: Unknown error"，关闭标注工具重开后恢复正常，但过一会儿又复现
- 05:08 法国译员跟帖确认：自己看到的是"无限旋转的沙漏"而非错误信息，希望只是 UI 问题
- 已分配至 Nenad.Vranic，截至采集无 PM 回复

**0044971 详情（巴西葡语区计时器故障）**:
- 巴西葡语译员报修：5月30日工作时段，计时器开始异常
- 00:19 越南英语译员跟帖确认："我也遇到类似问题，计时器显示故障"
- 已分配至 ines.vela，无 PM 回复

**0044974 详情（计时功能完全停止）**:
- 印度译员报修：标注工具界面的时间计算/自动计时功能完全停止工作，不再捕获或更新任务时长
- 严重影响工作流

**0044977 详情（TPT 警告连锁后果）**:
- 印尼译员提问：收到 VCG 高 TPT 警告后，是否会被限制其他工作流的任务？过去两周仪表盘完全无 Lighthouse 任务
- 担心是 TPT 警告导致全局禁用，询问是否应该在审核期间参加 Intelligent Poll 认证

**0044975 详情（高 TPT 自我申报）**:
- 西班牙译员申报：今天遇到一个需大量研究历史事实的任务，TPT 严重超标，之后试图加速补偿但工具已更新

**分析**: 计时器问题在今日集中爆发，涉及 hi_IN、pt_BR、hi_Latn、id_ID、es_ES 五个语区，有相互印证的趋势。结合昨日工单的计时器问题，可能是平台端部署了新版本导致。**严重性：高 — 直接影响译员工时记录和 TPT 统计。**

---

### 📋 TPT（单任务时长）争议（3件关闭 + 2件进行中）

| Issue | 标题 | 语言区 | 状态 |
|---|---|---|---|
| 0043843 | Rewrite with follow-ups — TPT 12分钟严重不足 | tr_TR | closed |
| 0044598 | URGENT: [Cherry Opal] Low TPT Warning [5/6–5/14] | hi_Latn | closed |
| 0044768 | TpT for Safety AFM Grading | id_ID | closed |
| 0044059 | Project's TPT information | en_IN | closed |
| 0044975 | High TpT report (自我申报) | es_ES | pending |

**0043843 详情（Rewrite 任务 TPT 不公）**:
- 土耳其译员报告 Rewrite with follow-ups 任务包含 29 道主问题和子问题，共 58 个回答 + 评论，12 分钟根本不够
- 其他译员（04-28）共鸣："同样问题，12 分钟太低"
- PM Nenad（04-29）回复：TPT 是平均值而非单任务硬限制，但 20 分钟+不会被客户接受
- 译员反击：理解简单任务快、复杂任务慢的逻辑，但建议按子任务类型差异化 TPT
- **05-29 由 ines.vela 关闭**

**0044598 详情（Low TPT 警告引发译员集体不满 — 高热度工单）**:
- 印度译员提问：TPT 如何计算？含不含非活跃时间？均值 12 分钟 vs 阈值 15 分钟就收警告？
- 韩语译员（05-19）跟帖：收到同样邮件，要求"提供导致 TPT 偏低的短任务链接"，但根本记不住已完成的任务
- 挪威译员（05-19）激烈回应（4 次编辑）：**"先因为复杂任务超时被警告，又因为简单任务太快被警告，我们根本赢不了！申诉是浪费无薪时间，完全是官僚噪音。我就按自己节奏干活，系统要封就封吧。"**
- PM Mohan_Raj（05-29）正式回复：提供了申诉表单链接 (forms.office.com)，教译员用"Report a Problem → Shareable link"获取 Task Viewer 链接
- **05-29 关闭** — 译员的不满情绪非常强烈，反映 TPT 系统设计缺陷

**0044768 详情（Safety AFM Grading TPT 确认）**:
- 印尼译员提问 TPT，社区多人猜测为 15 分钟
- 讨论中译员抱怨：简单任务要故意等够时间才能提交以避免 Low TPT，浪费时间
- PM Mohan_Raj（05-29）：确认 active + inactive TPT = 15 分钟
- **05-29 关闭**

**0044059 详情（项目 TPT 信息汇总）**:
- 印度英语译员收到大量邮件搞不清自己资格和 TPT
- PM ines（05-29）：Lighthouse TA 任务 12分钟/720秒
- PM Mohan（05-29）：PR 任务 TPT 15分钟
- **05-29 关闭**

---

### 🚫 任务不可用 / NTA（No Tasks Available）（3件）

| Issue | 标题 | 语言区 | 状态 |
|---|---|---|---|
| 0044972 | No tasks available | hi_IN | pending |
| 0044968 | No Tasks Despite Production Emails from last 6-7 days | hi_IN | pending |
| 0044970 | Time Allowed — Lighthouse 8h vs Cherry Opal 10h | es_MX | pending |

**0044972 详情**: 印度印地语译员简单申报"长时间无任务"，附 NTA 截图。无 PM 回复。

**0044968 详情（LE 分类）**:
- 印度印地语译员详细描述：连续 6-7 天收到"PR Production 就绪"邮件，但打开平台始终显示 NTA
- 已尝试多次刷新，附邮件和 NTA 截图
- 已分配至 Nenad.Vranic，无回复

**0044970 详情（工时困惑）**:
- 墨西哥西班牙语译员：每天收到两封生产邮件 — Lighthouse 说 8 小时/天，Cherry Opal 说 10 小时/天
- 询问如何区分和分配两个项目的工时？怎么操作才安全不超限？
- 无 PM 回复

---

### 🖥️ 平台 Bug / 任务显示异常（3件）

| Issue | 标题 | 语言区 | 状态 |
|---|---|---|---|
| 0044973 | Problem in Rewrite with follow up tasks — 只显示1个回答 | tr_TR | pending |
| 0044978 | One out of three response did not load | ms_MY | pending |
| 0044867 | PR tasks workflow issue Cherry Opal — 任务类型混杂 | en_IN | closed |

**0044973 详情**:
- 土耳其译员报修：Rewrite with follow-ups 任务只显示 1 个回答（应有 2 个），评论区不可用
- 第二个任务打开后完全相同，未完成，标记为技术故障后停止工作
- 04:18 法国译员跟帖："我觉得只有 1 个回答且无评论要求不算 Bug"
- 05:37 越南英语译员同感："评论区关闭可能是因为只有 1 个任务无需比较"
- 无 PM 回复 — 译员间意见不一致，需要官方确认

**0044978 详情**:
- 马来语译员报修：Fine-Tuning Grading 任务中 3 个回答有 1 个完全空白，刷新多次无效
- 跳过该任务，附前后截图
- 询问今后遇到此类问题应如何处理
- 无 PM 回复

**0044867（已关闭）**:
- 印度英语译员报修：AFM 和 PR 任务链接上出现了 Intelligent Polls 任务
- 05-27 译员自行回帖"已解决，请关单"
- PM Mohan（05-29）正式关闭

---

### 🔑 账号 / 登录问题（2件）

| Issue | 标题 | 语言区 | 状态 |
|---|---|---|---|
| 0044967 | Can't log in on TAG tool, no SMS | th_TH | pending |
| 0044964 | AppleConnect Account Locked Due to Email Verification | pl_PL | pending |

**0044967 详情**:
- 泰国译员报修：工作时被登出（错误 440），重新登录收不到短信验证码，多次重发无效
- 12:04 译员自行回帖：**"问题已自行解决，抱歉造成不便"** — 但无法自行关闭工单
- 本质上已解决，等待 PM 关闭

**0044964 详情**:
- 波兰译员报修：AppleConnect 要求验证一个 `@scilliance Apple` 邮箱地址，但从未收到过该邮箱的登录凭据
- 2026年2月已成功设置 2SV 并获准生产访问
- 多次点击"发送验证链接"但无邮件到达收件箱/垃圾箱
- 10:05 追加信息：找到其他同类工单 — 解释说验证邮件应自动转发到个人邮箱，但自己的没收到，请求检查转发配置
- 已分配至 Behsookfong_Chew，无回复

---

### 💰 支付问题（1件）

| Issue | 标题 | 语言区 | 状态 |
|---|---|---|---|
| 0044914 | URGENT! VCG certificates payment missing — 缺 3 小时奖励金 | pl_PL | pending |

**0044914 详情**:
- 波兰译员申诉：3月完成 VCG Edit Model + Base Creation 双认证，应得 7 小时（基础 2×1.5h + 双认证奖金 2+2h），实际只付了 4 小时
- 05-28 越南译员跟帖："PSR 认证我也遇到了 — 没发奖金只付了基础工资"
- 05-29 法国译员质疑：VCG 认证常规只付 1h/个，7h 的预期很奇怪；奖金有严格截止日期
- 05-29 波兰译员逐条反驳：**引用原始邮件原文**，清晰列出 3h（基础）+ 4h（奖金）= 7h 的算法，均在 3月22日截止前完成
- 已从 Nenad 转至 ines.vela，无 PM 回复

---

### 📝 认证问题（3件）

| Issue | 标题 | 语言区 | 状态 |
|---|---|---|---|
| 0043132 | TA Proofread 2.0 Certification Status After 2nd Attempt | ko_KR | closed |
| 0044950 | Failed PR cert but having PR task | vi_VN | closed |
| 0044957 | certification Lighthouse Knowledge Check - Handwriting Synthesis | ko_KR | pending |

**0043132 详情（已关闭）**:
- 韩语译员：第1次母语版失败，按推荐邮件用英语版重考，TA 0 to 1 Composition 显示 Pass，但 TA Proofread 2.0 仍显示 "Failed First Attempt"
- PM ines（05-29）最终回复：**"两次尝试均失败"** — 关闭工单

**0044950 详情（已关闭）**:
- 越南译员反复申诉：自认 PR 认证未通过，但仍收到 PR 任务，请求从 PR 团队移除
- PM Mohan（05-29）：**"根据记录，你于2月8日成功通过 PR 认证，因此可以访问 PR 任务"**
- 译员追问：通过认证但从未收到 PR 认证付款，能否补付 5 月？
- PM 确认：PR TPT 为 15 分钟，付款问题可联系 [email masked]
- **05-29 关闭**

**0044957 详情**:
- 韩语译员：收到 "Lighthouse Knowledge Check - Handwriting Synthesis and Refinement" 考试邮件，但收件人名字是 Maudie Kautzer（非本人），已收到 3 封
- 05-30 译员自行回帖：**"已完成考试，请关闭此报告"**
- 等待 PM 关闭

---

### 🔄 项目路由 / Cherry Opal 任务分配问题（2件）

| Issue | 标题 | 语言区 | 状态 |
|---|---|---|---|
| 0044707 | Kuokka Add Tasks — 错误项目任务阻塞 Lighthouse | it_IT | pending |
| 0044860 | RP Cherry — 请求重考机会 | pt_BR | pending |

**0044707 详情（高热度长工单）**:
- 意大利译员（05-21）首报：仪表盘出现 Kuokka Add 项目任务，而非 Lighthouse 任务
- PM ines（05-21）：已告知客户，请勿做这些任务
- 05-25 译员跟帖：问题依旧
- 05-26 葡萄牙译员加入：同样被 Kuokka 任务阻塞，要求 Lighthouse 优先
- PM 教译员用 "Report a Problem" 获取 TV 链接和日志
- 05-28 意大利译员：Kuokka 任务消失
- 05-28 挪威译员：我的还在
- 05-29 土耳其译员加入：同样受影响
- PM（05-29）：已报客户，希望尽快解决
- **跨 9 天仍未根本解决，影响多语区**

**0044860 详情**:
- 巴西葡语译员：请求 RP Cherry 重考机会
- 05-27 上传大量截图（含 PDF、多张支付界面截图）
- 05-29 再次上传截图 — 试图证明自己已通过认证
- 已转至 aleksandra.randjelovic，无 PM 回复

---

### ⏱️ 工时记录差异（1件）

| Issue | 标题 | 语言区 | 状态 |
|---|---|---|---|
| 0044848 | Working hours mismatch issue on dashboard | en_IN | pending |

**0044848 详情**:
- 印度英语译员：仪表盘显示工时约 6 小时，但本地计时器显示 7.5-8 小时，长期存在显著差异
- 05-29 另一印地语译员跟帖解释："TAG 工具计时器只记录活跃时间，不含非活跃时间，笔记本总时间自然会更高"
- 已从 Nenad 转至 ines.vela，无 PM 回应

---

## 三、PM 响应分析

| PM | 处理工单数 | 响应情况 |
|---|---|---|
| ines.vela | ~10 | 有回复，多数转派后无后续 |
| Mohan_Raj_Angaragonda | ~6 | 回复较完整，含具体解决方案 |
| Nenad.Vranic | ~6 | 多为初始分配，少量回复 |
| Behsookfong_Chew | 2 | 仅分配，无回复 |
| aleksandra.randjelovic | 1 | 未回复 |

**今日 PM 表现总结**:
- Mohan 表现最佳：0044950、0044598、0044768 等工单均给出了完整解答并关闭
- ines 处理量最大但多为批量关闭旧工单（04-28 至 05-29 的老单集中处理）
- **今日新建的 8 个工单（0044970–0044978）几乎全部无 PM 回复**，仅译员间互助讨论
- 计时器故障（0044976、0044971、0044974）作为今日最大热点，至今没有任何 PM 确认或回应

---

## 四、趋势观察

1. **计时器故障为本周新问题**：与昨天（05-29）的 `0044974 Technical Issue with Time Calculation Feature` 形成连续，今天又新增 0044976（Unknown Error）和 0044971（pt_BR），表明可能是 05-29/30 的部署引发

2. **TPT 争议持续发酵**：0044598 中挪威译员的激烈回应代表了一线译员对 TPT 系统的普遍不满，虽然 PM 提供了申诉表单，但译员认为"申诉是浪费无薪时间"

3. **老工单集中关闭**：ines.vela 在 05-29 批量关闭了多个 4-5 月的长期工单（0043843、0043132、0044059、0044867），部分工单等待超过一个月才得到处理

4. **Cherry Opal vs Lighthouse 路由混乱未解**：0044707 自 05-21 开启至今未根本解决，Kuokka/其他项目任务错误出现的问题仍在影响译员

5. **支付问题响应慢**：0044914 自 05-28 开启，译员引用原始邮件逐条反驳后仍无 PM 回复

6. **译员互助文化明显**：多个工单中译员相互确认问题（如 0044973、0044976）、分享经验（如 0044848）、提供解决方案，减轻了 PM 响应不及时的负面影响

---

## 五、建议关注

| 优先级 | 问题 | 建议 |
|---|---|
| 🔴 紧急 | 计时器/Timer 集体故障（3件活跃） | 需尽快确认是否为服务端问题并统一回复 |
| 🔴 紧急 | AppleConnect 邮箱验证导致无法工作 (0044964) | 需立即检查 Scilliance 邮箱转发配置 |
| 🟡 重要 | VCG 证书奖金未足额支付 (0044914) | 需核对 3 月双认证奖励政策并补付 |
| 🟡 重要 | Kuokka 任务阻塞 Lighthouse (0044707) | 需推动客户侧根本性修复 |
| 🟢 一般 | 大量 NTA 申报 (0044972, 0044968) | 需确认任务分配机制是否正常 |
| 🟢 一般 | TPT 争议 (0044598 已关但不满仍在) | 考虑优化申诉流程降低译员负担 |

---

*生成时间: 2026-05-30 自动采集*
*详细原始数据: `Global_Query_Detailed_Summary_2026-05-30.md`*
*JSON 数据: `.global_query_issue_details_2026-05-30.json`*
