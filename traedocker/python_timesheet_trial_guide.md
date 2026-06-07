# python-timesheet 试标全通关指南

本文档是针对你获取的真实试标库 [python-timesheet](file:///home/jianglei/zuoye/traedocker/python-timesheet.zip) 量身定制的标注全通关指南。我们已在本地完成了该仓库的 Docker 镜像构建验证与单元测试执行，72项测试已全部通过，完全符合项目的技术标准。

---

## 🛠️ 第一部分：环境配置与项目打包

为了通过系统的“项目自动构建质检”，我们需要对代码层级和 Dockerfile 进行规范化调整：

### 1. 本地目录结构（已验证）
确保你的上传包解压后**只有且仅有一个 `repo` 文件夹**，所有代码都在里面。结构如下：
```text
. (构建根目录)
├── Dockerfile
└── repo/
    ├── requirements.txt
    ├── pytest.ini
    ├── README.md
    ├── src/
    └── tests/
```

### 2. 标准 Dockerfile 内容
我们编写并验证过的 Dockerfile 如下，它包含 Git 初始化，完全满足 `/app` 作为初始化工作目录的要求：
```dockerfile
FROM python:3.11-slim
WORKDIR /app

# 安装 git（自动构建与版本校验必备）
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖并安装
COPY repo/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY repo/ ./

# 在容器内进行 Git 初始化，以确保 /app 为有效 Git 仓库且状态干净
RUN git init && \
    git config --global user.email "annotator@example.com" && \
    git config --global user.name "annotator" && \
    git add . && \
    git commit -m "initial commit"

EXPOSE 8000
CMD ["uvicorn", "src.timesheet.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

> [!NOTE]
> 已经为你创建并整理好了上述构建环境。打包时，直接将 Dockerfile 和 repo 文件夹一同压缩为 `repo.zip` 即可。

---

## 📝 第二部分：试标 7 个 Prompt 设计方案

根据规则，第 1 个 Prompt 必须是**代码解释**类型（不要求豆包为0），剩下的 6 个必须是**代码修改**类型，且**必须先运行豆包模型，验证其得分为 0** 才能继续。

以下为你设计了 7 个完美适配 `python-timesheet` 业务的 Prompt：

### 1. Prompt 1（代码解释类 - 第一轮首发，豆包可不为 0）
* **Prompt 内容**：
  > 请详细解释一下 `src/timesheet/services/entry_service.py` 中 `_calc_duration` 方法的实现逻辑，它是如何计算工时并处理跨天情况的？另外，为什么旧的 `old_duration_calc` 方法被废弃了，它存在什么精度和边界计算问题？
* **设计意图**：第一轮硬性要求的解释题，用于暖场并测试容器基础连通性。

### 2. Prompt 2（代码修改类 - 计时器状态数据库持久化 ⚠️ 豆包易错）
* **Prompt 内容**：
  > 目前 `src/timesheet/services/entry_service.py` 中计时器功能使用了一个模块级别的内存字典 `self._timers` 模拟，导致应用重启时计时器状态会全部丢失。
  > 请将其升级为数据库持久化存储：
  > 1. 在 `TimeEntry` 模型中新增字段 `start_time_iso` (String) 和 `is_active_timer` (Boolean)。
  > 2. 修改 `start_timer`，让它在启动计时器时，如果当前用户已经有运行的计时器，应抛出 `ValueError("已有正在运行的计时器")`，否则将计时器持久化到数据库。
  > 3. 修改 `stop_timer` 逻辑，从数据库查找当前用户激活的计时器并计算时长，保存为正式工时记录，并将计时器标记为失效。
  > 4. 相应重构数据访问层、Service 层逻辑和 `tests/test_entries.py` 中对应的单元测试。
* **让豆包得0分点**：需要更改数据库模型、新增字段、重写存取逻辑，并且要在测试中重写内存字典相关的断言。豆包极易在更新数据库定义或重写测试断言时漏写代码，导致测试跑不通。

### 3. Prompt 3（代码修改类 - 累计工时上限校验 ⚠️ 豆包易错）
* **Prompt 内容**：
  > 目前在 `src/timesheet/services/entry_service.py` 中，用户创建工时时，系统只校验了单次工时是否超过上限（`settings.max_hours_per_day`）。
  > 我们需要将其升级为“今日累计总工时上限校验”：
  > 当用户通过 `create_entry` 创建记录时，系统应该先去数据库统计该用户在该日期已录入的全部工时之和（duration 累加），如果“已录入的累计工时”加上“当前准备创建的工时”超过了 `settings.max_hours_per_day`，则必须抛出 `ValueError("今日累计工时超过每日上限")` 异常。请完成逻辑修改并在 `tests/test_entries.py` 中补充测试。
* **让豆包得0分点**：需要与数据库交互做累计数值计算。豆包在处理这种需要根据主外键进行聚合求和的校验逻辑时，经常在测试中没有正确伪造已有的记录，或者在累加 float/Decimal 精度上报错。

### 4. Prompt 4（代码修改类 - Excel 报表增加加粗公式汇总行 ⚠️ 豆包必错）
* **Prompt 内容**：
  > 目前 `src/timesheet/utils/export.py` 中导出的 Excel 只有原始明细。我们需要在所有数据行写入完成后，添加一个美化后的汇总行：
  > 1. 在表格最下方留空一行，然后写入一行汇总行，首列单元格内容为“Total”。
  > 2. 在工时时长（`duration`）对应的列（假设为 D 列），写入 Excel 计算公式 `=SUM(D2:Dn)`，其中 n 为数据结束行号。
  > 3. 使用 `openpyxl` 的样式功能对“Total”这一行进行加粗处理，并设置单元格背景填充为淡灰色。
  > 4. 请在 `tests/test_reports.py` 中添加测试用例，验证生成的 Excel 是否包含正确的公式和样式定义。
* **让豆包得0分点**：涉及 `openpyxl` 库的样式定义（如 Font, PatternFill 导入）、公式格式定义和动态数据范围行计算。豆包对这类特定库的多 API 调用经常写错导入路径，导致运行时 `NameError` 或测试失败。

### 5. Prompt 5（代码修改类 - 增加项目经理审批流校验 ⚠️ 豆包必错）
* **Prompt 内容**：
  > 我们需要为工时审批流引入权限控制。请进行如下重构：
  > 1. 在 `Project` 模型中新增字段 `manager_id` (Integer) 指代负责人。
  > 2. 更新 Pydantic 校验 Schema `src/timesheet/schemas/project_schema.py` 允许设置该字段。
  > 3. 修改 `src/timesheet/services/timesheet_service.py` 中的 `approve_timesheet` 和 `reject_timesheet` 方法：在操作时必须传入 `operator_id`，并校验操作人是否等于当前工时表关联项目的 `manager_id`，若无权操作则抛出 `PermissionError("无权审批该工时表")`。请同步修改相关的测试。
* **让豆包得0分点**：典型多文件级联重构（Model -> Schema -> Service -> Tests）。需要对实体关联以及业务校验权限链做全面调整，豆包通常只能完成部分代码，导致级联报错。

### 6. Prompt 6（代码修改类 - 项目生命周期管理 ⚠️ 豆包必错）
* **Prompt 内容**：
  > 我们需要对项目的生命周期状态做更细致的管控：
  > 1. 将 `Project` 模型中的布尔字段 `is_active` 改为枚举状态 `status`（包含值：`DRAFT`、`ONGOING`、`COMPLETED`、`SUSPENDED`）。
  > 2. 修改项目创建和任务创建规则：只允许状态为 `ONGOING` 的项目创建任务或记录工时。
  > 3. 如果项目处于 `COMPLETED` 或 `SUSPENDED` 状态，创建工时记录应抛出 `ValueError("当前项目不可录入工时")` 异常。
  > 请重构所有受影响的 Schema、服务逻辑和数据访问层，并修正现有的测试。
* **让豆包得0分点**：属于破化性数据库字段重构（从 Boolean 转换为 Enum/String 状态），对于这种重构历史代码兼容性的高级开发任务，豆包没有能力独立完成全部代码整合，一定会得 0 分。

### 7. Prompt 7（代码修改类 - 加班统计权重计算 ⚠️ 豆包易错）
* **Prompt 内容**：
  > 我们需要在报表生成中支持弹性加班时长折算统计：
  > 1. 修改 `src/timesheet/schemas/report_schema.py` 中的报表返回 Schema，新增 `overtime_hours` 和 `weighted_billable_hours` 两个可选的统计输出字段。
  > 2. 修改 `src/timesheet/services/report_service.py` 中的 `generate_report` 逻辑：如果某用户在一天内记录的 `is_billable` 工时超过了 8 小时，则超过的部分计入 `overtime_hours`，且超过的部分在 `weighted_billable_hours` 中按 1.5 倍加权计算（例如某天工作了 10 小时，正常 8 小时 + 加班 2 * 1.5 = 11 小时）。
  > 请修改计算逻辑并为其添加测试用例。
* **让豆包得0分点**：基于日期的聚合、超额溢出切分计算，并在原有的统计返回结构里添加新字段。计算公式极易出现逻辑 Bug，导致测试不通过。

---

## 🚀 第三部分：试标实操步骤与打分避坑

在 Trae 中打开配置好的 Docker 环境后，请严格按以下步骤操作：

1. **配置 PPE 环境**：
   在 Trae 软件的设置 `settings.json` 中添加：
   ```json
   {
     "ai_assistant.request.env": "ppe",
     "ai_assistant.request.ppe": "ppe_data_label_trae"
   }
   ```
   配置完成后，**重新加载窗口**。
2. **测试豆包（Seed-first）**：
   * 在 Trae 侧边栏的 AI Assistant 窗口中，将模型切换为 `Doubao-Seed-2.0-Code`。
   * 发送 Prompt 2。
   * **打分标准**：观察它的修改是否完整、测试是否能通过。如果它没有修改完整，或者测试跑不通，或者代码报错，在作业表给它打 **0分**。
   * 确认豆包得分为 0 后，该 Prompt 即通过“前置筛选”，可以去跑其他模型了。
3. **依次跑其他模型**：
   针对该 Prompt，依次切换模型，每个模型新建一个独立的对话 session（**切忌在同一个会话里切换模型**）：
   * **Rollout 1**: `GPT-5.4` (查看输出并打分，提取 diff)
   * **Rollout 2**: `Gemini 3.1 pro` (查看输出并打分，提取 diff)
   * **Rollout 3**: `DeepSeek-v4` (查看输出并打分，提取 diff)
   * **Rollout 4**: `Doubao-Seed-2.0-Code` (已经跑过，直接记录 0 分和 reason)
   * **Rollout 5**: `GLM-5.1` 或 `Qwen3.6-Plus` (轮流切换选择，打分并提取 diff)
4. **表格提交**：
   在 需求二正式作业表 中依次录入 prompt、分值、reason、git_diff 附件，等待自动质检。

> [!IMPORTANT]
> **绝对不能手动开启 Trae 隐私模式**！开启会导致当前仓库产生的所有标注数据被判定为无效，并且可能会被封号。
