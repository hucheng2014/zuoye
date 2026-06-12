# agent行为标签质检规则总结

来源：飞书规则页 `agent行为标签质检`

更新时间：2026-06-11 整理

## 一、试标任务要求

群内试标要求是：每人标注一条 case，合格即通过。试标题目是 `agent行为人机一致率`，规则文档是 `agent行为标签质检`。

标注目标是人工复核 agent 轨迹的行为标签和质量分，判断机标结果是否合理；如果人工判断与机标不同，需要在对应 remark 字段写清楚原因。

## 二、交付字段

| 字段 | 填写内容 | 规则 |
| --- | --- | --- |
| `positive_lable_check` | 人工选择的正向/中性/结构性主标签 | 从正向、中性、结构性标签中选一个最核心标签 |
| `positive_lable_remark` | 正向主标签备注 | 仅当人工结果与机标不一致时说明原因 |
| `negative_label_check` | 人工选择的负向标签 | 从负向标签中选择；若无明确负向缺陷选 `Negative Placeholder`；若有真实缺陷但不在已有负向标签中选 `Other` |
| `negative_label_remark` | 负向标签备注 | 仅当人工结果与机标不一致时说明原因 |
| `score_check` | 人工选择的质量分 | 0-5 分，越高表示轨迹质量越高、越适合作为高质量评测样本 |
| `secondary_positive_check` | 人工选择的二级正向/中性/结构性标签 | 不能与 `positive_lable_check` 重复；用于补充轨迹的第二个明显行为模式 |
| `secondary_positive_remark` | 二级标签备注 | 仅当人工结果与机标不一致时说明原因 |
| `是否完成` | 完成状态 | 以上字段均完成后填写 `完成` |

## 三、标注流程

1. 先看完整 agent trace，不要只看最终回答。
2. 判断是否存在明确负向缺陷，优先确定 `negative_label_check`。
3. 判断轨迹中最主要的正向/中性/结构性行为，填写 `positive_lable_check`。
4. 再选择一个不重复的二级正向/中性/结构性标签，填写 `secondary_positive_check`。
5. 按负向标签约束确定 `score_check` 的分数区间，再结合正向与结构性标签细化分数。
6. 与机标不同的字段，在对应 remark 中简明说明依据。
7. 最后填写 `是否完成 = 完成`。

## 四、打分规则

打分要综合考虑样本的所有标签，包括正向主标签、负向主标签、二级正向标签。

质量分范围是 0-5 分，分数越高表示轨迹质量越高、越适合作为高质量评测样本。

| 负向标签情况 | 分数范围 | 含义 |
| --- | --- | --- |
| `Negative Placeholder` | 3-5 分 | 轨迹未命中明确负向缺陷 |
| `Other` | 0-5 分 | 轨迹有真实缺陷，但缺陷不在当前已有负向标签中，需要结合缺陷严重度和正向/二级标签综合判断 |
| 其他负向标签 | 0-2 分 | 轨迹真实命中了已有负向标签，只能落在低分区间 |

## 五、正向标签

| 标签 | 中文名 | 典型特征 | 检测方法 |
| --- | --- | --- | --- |
| `Fail-then-Success` | 失败后恢复 | 工具调用失败后，Agent 读取 error、诊断根因、调整策略、重新调用直至成功 | 遍历 tool 消息：检测 `stderr`、`exit_code != 0` 或 content 含 `error/failed/exception`；记录失败 call 的 `name` 和 `args_hash`；判断后续是否存在同名但参数不同的 call，且结果成功 |
| `Explore-then-Act` | 先探索后行动 | 进入未知 codebase 时，先用 `ls/Glob/Grep` 建立认知，再做修改操作 | 将工具按读/写分类；统计 trace 前 1/3 阶段读类占比 >= 70%，且后 2/3 阶段出现至少一次写类调用 |
| `Plan-Execute-Verify` | 计划-执行-验证 | response 中明确拆分计划，顺序执行工具调用，最后用测试或检查命令验证结果 | assistant 文本含计划关键词，如“先...再...最后”、`step 1/2/3`、`plan:`；trace 末尾 3 步内含验证类调用，如 `pytest/jest/build/lint/curl/echo $?`；还要校验 plan 与 execute 步骤一致 |
| `Parallel Independent Calls` | 并行独立调用 | 识别出多个互不依赖的工具调用，并在同一轮 assistant 消息中并行发起 | 检查每条 assistant 消息的 `tool_calls` 数组，`len(tool_calls) >= 2` 即可能命中；还要判断各 call 的 arguments 是否互不依赖 |
| `Tool Switching` | 工具切换 | 某工具不适合任务时，主动切换到更合适的工具 | 滑动窗口检测连续两次相似任务，`function.name` 发生变化；再判断切换后效果是否改善 |
| `Context Gathering before Decision` | 决策前充分上下文 | Edit 之前先 Read 完整文件，避免破坏已有结构 | 对每次 Edit/Write，向前回溯是否存在同 `file_path` 的 Read；覆盖率 = Edit 前有 Read 的次数 / 总 Edit 次数，覆盖率 >= 0.8 标记为命中 |
| `Test-Driven Trajectory` | 测试驱动 | 写测试 -> 运行失败 -> 实现功能 -> 运行通过 -> 重构的完整闭环 | 检测四步时序：先修改测试文件，再运行测试失败，再修改非测试文件，再次运行同样测试并通过 |

## 六、中性标签

| 标签 | 中文名 | 典型特征 | 检测方法 |
| --- | --- | --- | --- |
| `Single-Shot Success` | 一次成功 | 一次工具调用即完成任务，无错误无迭代 | `n_tool_calls == 1`，唯一 tool_result 无 error，且 final response 非空 |
| `Information Query Only` | 纯信息查询 | 整个 trace 只有读操作，无任何修改 | 所有 tool_calls 都属于只读集合；Bash 命令中不能包含 `rm/mv/cp/touch/mkdir/sed -i/echo >` 等 mutation 动作 |
| `Clarification-Driven` | 澄清驱动 | Agent 先向用户提问澄清，再开始执行 | 首轮 assistant 消息没有 tool_calls，且内容包含问号或疑问关键词，如“请问”“能否”“是否”“could you”“would you like” |
| `Progressive Refinement` | 渐进式优化 | 多次小修改逐步逼近目标 | 检测 `Edit/Write -> Bash run/test` 的交替对，连续出现次数 >= 3；且每次 Edit 的目标文件高度重叠 |

## 七、结构性标签

| 标签 | 中文名 | 典型特征 | 检测方法 |
| --- | --- | --- | --- |
| `Linear Trajectory` | 线性轨迹 | 直线推进，无回退，常见于简单任务 | 整个 trace 无 error，且无重复 fingerprint；工具调用按依赖单调推进，没有回退到已访问的早期状态 |
| `Branching Trajectory` | 分支轨迹 | 中途因发现新信息而改变方向 | trace 中段出现 read/write/run 类别切换，后续 5 步策略明显不同；需判断切换原因是发现新信息，而非陷入混乱 |
| `Loop-and-Converge` | 循环收敛 | 通过多次迭代逐步收敛到正确答案，如调参、调试 | 同一 `function.name` 连续调用 >= 3 次，但 arguments 逐次变化；最后一次无 error，前几次有 error |
| `Multi-File Coordination` | 多文件协作 | 单 trace 涉及 5 个以上文件的协同修改 | 从 Edit/Write/MultiEdit 的 arguments 中抽取 `file_path`，去重后 `unique_file_count >= 5` |
| `Long-Horizon Trajectory` | 长程轨迹 | 轮次 > 10，工具调用 > 20，依赖链路深 | `n_turns > 10` 或 `n_tool_calls > 20` 即可标记；可加严看最大依赖链深度是否 > 5 |
| `Recursive Decomposition` | 递归分解 | 将大任务拆分为子任务，逐个完成 | assistant response 中有明确子任务列表，并且后续 tool_calls 按子任务分组推进，每组完成后再进入下一组 |

## 八、负向标签

| 标签 | 中文名 | 典型缺陷 | 检测方法 |
| --- | --- | --- | --- |
| `Infinite Loop` | 死循环 | 同一组 tool_calls 以相同参数反复执行 >= 3 次，每次都失败 | 计算 `fingerprint = hash(name + canonical_json(arguments))`；滑动窗口检测连续 >= 3 个相同 fingerprint，且结果都含 error 或 `exit_code != 0` |
| `Hallucinated Tool Call` | 幻觉工具调用 | 调用 `tool_list` 中不存在的工具名 | 从 trace meta 获取合法工具集合，检查 `function.name not in tool_list`，并验证 type 字段是否为 function |
| `Hallucinated Success` | 虚假成功宣称 | 工具明确返回错误或任务未完成，但 Agent 在 response 中声称已完成 | 检查 trace 末尾 3 个 tool_result 的 error 状态与 final response 是否一致；若 final 声称“完成/成功/通过/done/passed”但实际失败，则命中 |
| `Premature Termination` | 过早终止 | 任务明显未完成就给出最终 response | 从用户请求抽取 sub_goals，扫描 trace 实际完成的 sub_goals；若 `completed/total < 0.7`，标记为过早终止 |
| `Tool Misuse` | 工具误用 | 用 Bash cat 而不用 Read，用 Bash echo 写文件而不用 Write 等 | 命中黑名单：Bash command 含 `cat`、`grep -r`、`echo ... >` 等且存在更优专用工具；也可由人工判断是否有更合适工具可替代 |
| `Parameter Hallucination` | 参数幻觉 | `function.arguments` 包含 schema 未声明字段，或缺少 required 字段 | 逐个 tool_call 解析 arguments JSON，与对应 function schema 比对 required、额外字段和字段类型 |
| `Context Loss` | 上下文丢失 | 后续轮次忘记前面已获取的信息，重复读取相同文件或重新探索已知路径 | 对每个 Read 文件建立时间戳序列；同一路径 Read >= 2 次且中间没有对应 Edit/Write 修改，则命中 |
| `Over-Engineering` | 过度设计 | 简单任务被拆成大量调用，例如改一个变量名却 Read 20 个文件 | 估算任务复杂度；low 复杂度但 `n_tool_calls > 8` 或 `n_unique_files > 5` 标记为过度设计 |
| `Sycophantic Acknowledgment` | 谄媚式确认 | response 中包含大量 LLM artifact，如 “Great question!”、“As an AI...” 等 | 维护谄媚短语库并 regex 匹配；任一 assistant content 命中 >= 1 次即可标记 |
| `Unfinished / No Closure` | 未闭环 | 任务轨迹没有最终总结、明确结论或结束信号，用户无法判断是否完成 | 检查会话尾部是否缺少“已完成/结论/最终结果/下一步建议/需你补充”等收束语义；若最近 assistant turn 以报错、阻塞、等待条件等结束且没有补救动作，则命中 |
| `Broken Edit Corruption` | 编辑破坏 | 编辑导致代码、文档或配置结构、缩进、格式或语义损坏，且后续未修复 | 检查 edit/write 前后 diff，若出现括号/标签/引号不闭合、缩进异常、字段缺失、重复覆盖、截断写入等，且无修复或验证通过信号，则命中 |
| `Out-of-Scope Overreach` | 严重越界 | 修改范围明显超出任务需求，如无关重构、删除测试、违反用户硬性限制 | 比对用户请求边界与实际行为；若出现新增大批无关文件修改、触达未授权模块、删除/绕过测试、擅自重定义需求等，则命中 |
| `Environment-Only Failure` | 环境型失败 | 主要执行内容停留在环境、权限、网络、依赖、沙箱、令牌等外部失败上，未形成有效业务推理或替代方案 | 统计 tool_results 中环境类错误占比，如 `permission denied`、`network error`、`module not found`、`token expired`、`sandbox restriction`、`dependency missing`；若核心轨迹主要由此类失败组成且缺乏有效降级方案，则命中 |
| `Truncated Critical Trajectory` | 关键截断 | 关键修改、验证结果或最终结论处中断，导致无法判断任务是否真正完成 | 检查关键阶段是否缺失，例如已有修改但无验证结果，已有执行命令但无输出结论，或在“正在修复/正在运行/即将给出结果”后对话结束 |

## 九、占位和兜底负向标签

| 标签 | 使用场景 | 分数影响 |
| --- | --- | --- |
| `Negative Placeholder` | 没有明确负向缺陷时使用 | 分数必须在 3-5 分 |
| `Other` | 有真实缺陷，但不属于已有负向标签 | 分数可在 0-5 分，需要按缺陷严重度判断 |

## 十、实操判定注意点

1. 负向标签优先影响分数上限：只要命中已有负向标签，分数不能超过 2 分。
2. `Negative Placeholder` 不是负向缺陷，而是“未命中明确负向”的占位。
3. `Other` 不是“没有问题”，而是“有问题但不在现有负向标签内”。
4. `positive_lable_check` 和 `secondary_positive_check` 不能重复。
5. 二级标签只能从正向、中性、结构性标签里选，不能填负向标签。
6. 如果机标与人工一致，remark 可以不写；如果不一致，remark 要写具体依据，不要只写“机标错了”。
7. 打分时不要只看最终是否成功，还要看过程质量：是否探索充分、是否验证、是否误用工具、是否过度设计、是否出现未闭环。
8. 对低质量失败轨迹，优先检查是否属于 `Infinite Loop`、`Hallucinated Success`、`Premature Termination`、`Unfinished / No Closure`、`Truncated Critical Trajectory`。
9. 对高质量成功轨迹，优先检查是否命中 `Fail-then-Success`、`Plan-Execute-Verify`、`Context Gathering before Decision`、`Test-Driven Trajectory`。
10. 对复杂长任务，结构性标签能帮助描述轨迹形态，但不直接抵消负向缺陷；若同时命中负向标签，仍按负向分数区间约束。

## 十一、推荐填写模板

```text
positive_lable_check: <正向/中性/结构性主标签>
positive_lable_remark: <与机标不一致时写原因；一致可空>
negative_label_check: <Negative Placeholder / Other / 具体负向标签>
negative_label_remark: <与机标不一致时写原因；一致可空>
score_check: <0-5>
secondary_positive_check: <不同于主标签的二级正向/中性/结构性标签>
secondary_positive_remark: <与机标不一致时写原因；一致可空>
是否完成: 完成
```

## 十二、快速质检口诀

先定负向，再定正向；先看过程，再看结论。  
有负向现有标签，分数 0-2；无明确负向，分数 3-5；真实缺陷但无对应标签，用 Other 后综合打分。  
主标签和二级标签不能重复，remark 只在人工与机标不一致时写清楚理由。
