# 环境 \& prompt \& traj 标注标准

🔥 **高薪招募高级代码数据标注合作**

基于真实仓库，在 Trae 平台为 7 个 prompt（1 个阅读理解 \+ 6 个代码任务）跑 5 轮模型（GPT\-5\.4/Gemini/DeepSeek/豆包/轮换），完成评分记录与 git diff 上传。

要求：有大模型编码能力，会用 Docker \+ Trae，有测试环境。

流程：问卷报名 → 代码库审核 → 正式标注（量力投入）→ 流式交付

报名：[如何开始](https://ocnblxngb8jr.feishu.cn/wiki/W7yEw5qSciwY6CkxF7BccLeJnCd?from=from_parent_docx) 标准：[环境 \& prompt \& traj 标注标准](https://ocnblxngb8jr.feishu.cn/wiki/O9M2w4QUwiK4zokNEVbcmhZInvd) [标注补充要求](https://ocnblxngb8jr.feishu.cn/wiki/BFYgwdAoJi83Q9kny2zcIB0Cnne) 

踩坑记录（**必看**） [标注作业流程\_实操闭坑版](https://ocnblxngb8jr.feishu.cn/wiki/ODa1whwgdib4KfkKssbcBN4Enxe)

~~1、需要试标，试标大概花费1小时，试标主要考察是否具备大模型编码能力~~

2、项目维度，看自己意愿投入

3、项目类型 评测类项目

4、有自己的测试环境，需要搭建Docker镜像，环境会提供大模型token，不需要自费
~~5、如果有意愿参与试标，请在0523前填写问卷 ~~~~https://ocnblxngb8jr\.feishu\.cn/share/base/form/shrcnaYLryvP9riTk4mKJSbK2Gh~~

~~6、试标记录表格 ~~[需求2示例作业表BBS](https://ocnblxngb8jr.feishu.cn/base/GXdMbVqSxaSZENshBDUcqEdZnkb?table=tblyceoSMS2AUcJJ&view=vewxWP7trZ)

7、相关视频 [需求二试标培训](https://ocnblxngb8jr.feishu.cn/wiki/OfDwwGeE7i5Kt4kjXq5ckcWmn9b)

8、标注要求 [标注要求](https://ocnblxngb8jr.feishu.cn/wiki/VcNqwqPTciqUDNkbwiocTnMPndc)

9、如何正式开始标注 [如何开始](https://ocnblxngb8jr.feishu.cn/wiki/W7yEw5qSciwY6CkxF7BccLeJnCd)

10、如何通过大模型提效 [如何提效](https://ocnblxngb8jr.feishu.cn/wiki/LJIDw7xMGiHhXqkJ2OgcTvN3ngh)

11、补充要求，正式标注前查看，**过程中发现的问题动态更新，强烈建议关注文档更新** [补充要求](https://ocnblxngb8jr.feishu.cn/wiki/BFYgwdAoJi83Q9kny2zcIB0Cnne)

12、代码库要具备真实开发价值，可自己准备，自己准备开始前需要确认，也可联系@刀砍东风获取

20260528 **最新要求**：[补充要求](https://ocnblxngb8jr.feishu.cn/wiki/BFYgwdAoJi83Q9kny2zcIB0Cnne)

1、每个题目要求7轮prompt，包含一轮 **代码阅读理解与分析** prompt（没有git diff 那种）和另外6轮其他类型

2、在跑模型时**优先跑seed**，**只有Doubao\-Seed\-2\.0\-Code为0分的prompt****，才能去跑其他模型，**如果**seed未达到0分**，就需要**修改或废弃**这条prompt。（**除了“代码阅读理解与分析”类型**）

## 任务描述与目标

### 任务目标

本任务要求围绕真实代码仓库构建可复现环境，并基于同一环境采集多条真实用户 prompt。每条 prompt 需要在 **Trae 平台中打开对应容器** 后进行 5 次独立运行，并记录每次运行的 session 信息、模型信息、评分结果、评分理由以及 `git diff` 产物。

本任务的核心目标包括：

1. 收集可在 Trae 中打开并运行的**真实**代码仓库环境。

2. 基于同一套环境采集 5～20 条真实用户 prompt。

3. 对每条 prompt 在 Trae 中进行5次独立 rollout。

4. 每次 rollout 结束后记录 `session_id`、`model_name`、`score`、`score_reason`，并上传 `git diff` 产物文件。

### 数据组织方式

本任务在飞书多维表中采用三级结构：

1. **仓库级父记录**：记录仓库、Dockerfile、repo 初始文件等环境信息。

2. **Prompt 级一级子记录**：记录基于该仓库环境设计的用户 prompt 及任务元数据。

3. **Rollout 级二级子记录**：记录每条 prompt 的单次 Trae 运行结果。

关系如下：

- 一个仓库级记录对应 5～20 条 prompt。

- 一条 prompt 对应多条 rollout 记录。

- 一条 rollout 记录对应一次在 Trae 中打开容器后的独立单 session 运行。

### 标注职责

1. 准备并上传 Dockerfile。

2. 上传 repo 初始文件压缩包。

3. 填写仓库级环境信息。

4. 基于该仓库环境编写真实用户 prompt。

5. 标注 prompt 的难度、类别、技术栈和功能模块。

6. 在 Trae 中打开容器，并基于该容器执行 rollout。

7. 记录每次 rollout 的 `session_id`、`model_name`、`score`、`score_reason`。

8. 每次 rollout 结束后执行 `git diff`，将结果转存为 patch 文件并上传到飞书表附件字段。

### Trae 容器运行要求

所有 rollout 必须在 **Trae 中打开对应容器后执行**，不得使用本地环境、普通终端环境或其他未指定环境替代。

标注人员需要确保：

1. 使用的是当前仓库记录对应的 Docker 环境。

2. Trae 中打开的容器代码现场与任务初始现场一致。

3. **每次 rollout 均从同一初始现场开始。**

4. **每次 rollout 均为独立单 session。**

Trae 中打开容器的具体操作方法见[附录 D](https://ocnblxngb8jr.feishu.cn/wiki/O9M2w4QUwiK4zokNEVbcmhZInvd#share-VyYmdmp0Ooh3Amx3aEZc5BdVnXc)。

### 模型使用要求

5 次 rollout 需要在 Trae 中进入 PPE ，并使用以下模型进行 rollout：

- GPT5\.4，Gemini 3\.1 pro，DeepSeek\-v4，Doubao\-Seed\-2\.0\-Code，MinMax\-M2\.7/GLM\-5\.1/Qwen3\.6\-Plus

要求：

- 前四次 rollout 需要按照 GPT5\.4，Gemini 3\.1 pro，DeepSeek\-v4，Doubao\-Seed\-2\.0\-Code 四个模型的顺序一次进行。

- 每一个 prompt 的第五次 rollout 按照 MinMax\-M2\.7/GLM\-5\.1/Qwen3\.6\-Plus 这个顺序轮流选择进行。

Trae 中进入PPE的操作方法见[附录E](https://ocnblxngb8jr.feishu.cn/wiki/O9M2w4QUwiK4zokNEVbcmhZInvd#share-Fab6dH7ODoRiDCxixKtcZ1Sunid)。

### Prompt 设计与分数覆盖要求

本任务采集的 Prompt 不仅需要基于真实仓库上下文，还需要具备一定的任务层次和模型区分度。在设计 prompt 时，应尽量覆盖不同难度、不同模块、不同任务类型，避免所有 prompt 都集中在简单局部修改、纯文档补充或高度重复的问题上。

每条 prompt 完成 5 次独立 rollout 后，根据该 prompt 下 5 个 rollout 的真实 `score` 结果，判断该 prompt 的分数覆盖类型。不允许为了满足分布要求修改真实评分。

##### prompt 基本要求

每条 prompt 应满足以下要求：

1. 必须基于当前仓库的真实代码上下文设计。

2. 问题应具体、可执行，避免“优化一下项目”“看看哪里有问题”这类目标过泛的表达。

3. prompt 中应尽量包含明确的任务目标、涉及模块、期望行为或验证方式。

4. 可以是代码修改类任务，也可以是仓库相关的理解、分析、解释或问答类任务。

5. 问答类任务必须与当前仓库的代码实现、模块设计、运行现象、工程配置或使用方式直接相关，不得设计为脱离仓库上下文的泛知识问题。

6. 同一仓库下的 prompt 不得高度重复，应覆盖不同功能模块、不同任务类型或不同复杂度。

7. prompt 必须能够在当前 Docker / Trae 容器环境中执行，不得依赖当前环境不支持的能力。

8. 不得设计恶意、不可完成、故意模糊或与仓库无关的问题。

#### prompt 分数覆盖类型

每条 prompt 需要使用 5 个模型各独立 rollout 一次。我们会根据 5 次 rollout 的真实 `score` 集合，将 prompt 分为以下三类：

示例：

```Plain Text
A 类：0, 1, 2, 2, 1
B 类：1, 1, 2, 2, 2
B 类：0, 0, 1, 1, 1
```

注意：

1. 上述比例按标注人员或批次累计结果统计，不要求单个仓库严格满足。

2. 单个仓库的 prompt 数量为 5～20 条，只需尽量保证 prompt 类型多样。

3. 最终 prompt 类型以 5 个 rollout 的真实 `score` 结果为准。

4. **不得为了让 prompt 落入某一类型而修改 score。**

5. 如果实际结果与预期不一致，以真实结果为准，后续通过补充 prompt 调整整体分布。

#### 禁止事项

标注人员需特别注意：

1. 不得为了满足分数覆盖比例修改真实 score。

2. 不得在看到模型结果后反向调整 prompt，并将原 rollout 结果挂到调整后的 prompt 下。

3. 如果 prompt 内容发生实质修改，需要重新执行该 prompt 下的 5 次 rollout。

4. 不得故意设计无法完成、目标不清、脱离仓库上下文的问题。

5. 不得通过重复相似 prompt 批量填充数量。

6. Score 必须根据 prompt 目标、模型执行过程、最终代码状态、git diff 和评分标准如实填写。

最终要求是：**prompt 设计应真实、具体、可执行，并尽量具备区分度；分数结果必须真实记录，不得人为调整。**

---

## 字段描述

### 仓库级字段

仓库级字段对应多维表中的父记录，一条记录代表一套共享环境。

### Prompt 级字段

Prompt 级字段对应仓库级记录下的一级子记录，一条记录代表一条用户 prompt。

### Rollout 级字段

Rollout 级字段对应 prompt 下的二级子记录，一条记录代表一次在 Trae 中打开容器后的独立运行。

---

## 标注流程

### 创建仓库级记录

标注人员首先在多维表中创建仓库级父记录，并填写以下字段：

- `repo_url`

- `repo_type`

- `language`

- `dockerfile`

- `repo`

- `environment_notes`

- `task_count`

仓库环境应满足：

- **必须是日常开发使用的**

- 具备真实开发上下文

- 代码结构足以支撑至少 5 条任务

- 可以在 docker 中构建和复现

- 不建议选择过于空泛、纯 demo、过小或无法运行的仓库

### 准备 Dockerfile 与 repo 压缩包

标注人员需准备并上传：

1. Dockerfile 附件。

2. repo 初始文件压缩包。

环境准备要求如下：

1. Dockerfile 中必须设置 `WORKDIR /app`

2. **容器内仓库目录统一为 ****`/app`**

3. 必须确保容器内仓库状态为 Agent 处理任务前的初始现场

4. 若当前仓库快照不是目标现场，应在 Dockerfile 中直接 checkout 到正确现场 

5. 所有项目都必须完成 Git 初始化

6. Dockerfile 需完成最小可用初始化，包括安装必要依赖、创建工作目录、预留 app 目录，并提供默认 shell 或默认命令（可选）

### 验证环境可用性

环境准备完成后，需进行自检。

自检要求如下：

1. Docker 镜像可成功构建。

2. 容器可正常启动。

3. 当前工作目录为 `/app`。

4. `/app` 中已包含任务相关代码内容。

5. `/app` 已完成 Git 初始化，并且是一个可用的 Git 仓库。

6. 容器内代码即为任务起始现场，无需额外 checkout 或手工准备。

7. 进入容器后无需额外手工初始化即可开始工作。

8. 环境可在 Trae 中正常打开。

> 特别要求：
> **后续 rollout 必须基于 Trae 中打开的该容器执行。环境仅能本地构建成功不代表满足 rollout 要求，必须确认可在 Trae 中打开和使用。**
> 
> 

### 采集 Prompt

围绕该仓库设计 5～20 条任务（基于原始仓库设计难度），并创建对应子记录。

任务设计要求：

- Prompt 必须要确保在给定的 docker 环境中是可运行的问题。（我们现在不支持DinD）

- 尽量模拟真实用户在 Agent 中的表达方式

- 应建立在当前仓库真实代码上下文之上，题目中最好涉及到/引用到原始代码片段，保证分布足够真实。

    - 示例：

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NWVmMDFhYTc5ZTE0NGRhMzFlYTlkNGUzN2MyOGQ5ODdfNDA3NzMwMTYxODJkYzE4MjI5MWUyMzQ2NDBjNWI3MzFfSUQ6NzY0MjcxODQ0NDcyMjQ5MDU4MV8xNzgwOTM3ODgzOjE3ODEwMjQyODNfVjM)

- 可包含需要修改代码的任务，也可包含不需要修改代码的理解、分析、解释或问答类任务 

- 问答类任务必须与当前仓库、代码实现、模块设计、运行现象或工程配置直接相关，不应设计为脱离仓库上下文的泛知识问答

- 同一仓库下的任务不得高度重复 

- 应覆盖不同难度、不同类型或不同模块，体现一定多样性

- 每条 prompt 必须填写 `difficulty`、`category`、`tech_stack`、`module_tags`。

### 标注 Prompt 元数据

每条 prompt 需补充任务元数据：

1. `difficulty`：按[附录 A](https://ocnblxngb8jr.feishu.cn/wiki/O9M2w4QUwiK4zokNEVbcmhZInvd#share-Xv0SdfLN6okh8yxDQNEcmNn1nL0) 的难度规则标注。

2. `category`：按[附录 B](https://ocnblxngb8jr.feishu.cn/wiki/O9M2w4QUwiK4zokNEVbcmhZInvd#share-YhO8dHqSvoqUpQxW0vAckLFCnzh) 的任务类别定义选择。

3. `tech_stack`：填写涉及的技术栈，多个值可用逗号分隔。

4. `module_tags`：填写涉及的功能模块，多个值可用逗号分隔。

填写要求：

1. 难度应根据任务本身的需求清晰度、修改或分析范围、环境复杂度、验证复杂度综合判断。

2. 类别按任务主要目标选择单一类型。

3. 技术栈和功能模块只用于描述任务涉及的技术或模块，不填写难度、类别、评分等信息。

4. 多个标签可使用中英文逗号分隔，后续由项目侧统一清洗处理。

### 在 Trae 中打开容器并执行 Rollout

每条 prompt 完成后，需在 Trae 中打开当前仓库对应容器，并基于该容器执行 rollout。

执行要求如下：

1. 每次 rollout 必须在 Trae 中打开目标容器后执行。

2. 每次 rollout 均从相同初始代码现场开始。

3. 不得在本地环境或其他未指定环境中替代执行。

4. 每次rollout从【】五个模型中选择，每个模型各一次。注意：一个prompt需要使用不同模型跑五次，需要单开五个任务，不能在一个会话里换模型跑五次

5. 每次运行结束后，记录本次运行的 `session_id`。

6. 每次运行结束后，记录本次运行使用的 `model_name`。

7. 每次运行结束后，保留运行后的代码现场，用于提取 `git diff`。

8. 如 Trae 打开容器失败、session 异常中断或无法继续运行，应在 rollout 记录的 `notes` 中说明。

Trae 中打开容器的具体操作见[附录 D](https://ocnblxngb8jr.feishu.cn/wiki/O9M2w4QUwiK4zokNEVbcmhZInvd#share-NOutd4cSEovoKsxnQ5YcnIjinbb)。 

### 提取 git diff 并上传

每次 rollout 结束后，需在运行后的代码现场执行 `git diff`。

操作要求如下：

1. 使用运行后的代码现场生成 diff。

2. 将 `git diff` 结果转存为 patch 文件。

3. 将 patch 文件上传到 rollout 级记录的 `git_diff` 附件字段。

4. 确保上传的 patch 文件与当前 rollout 记录一一对应。

5. 若本次运行未产生代码修改，也需要上传空 patch 或说明文件，并在 `notes` 中说明原因。

建议文件命名：

```Plain Text
{rollout_id}.patch
```

### 评分与填写理由

每次 rollout 结束后，标注人员需要对运行结果进行评分。

评分取值如下：

填写要求：

1. 评分理由应说明本次运行为什么得到该分数。

2. 评分应结合 prompt 目标、运行过程、最终结果和 `git_diff` 内容判断。

3. 如果由于资源或是工程问题导致的输出中断，需要进行重试，只提交运行成功的结果。

---

### 提交前自检

提交前需确认：

1. 仓库级字段均已填写完整。

2. Dockerfile 附件已上传。

3. repo 初始文件压缩包已上传。

4. 当前仓库下 prompt 数量为 5～20 条。

5. 每条 prompt 均已填写 `prompt_index` 和 `prompt`。

6. 每条 prompt 均已填写 `difficulty`、`category`、`tech_stack`、`module_tags`。

7. 每条 prompt 已完成规定次数的 rollout。

8. 每条 rollout 均已在 Trae 中打开容器后执行。

9. 每条 rollout 均已填写 `session_id`、`model_name`、`score` 和 `score_reason`。

10. 每条 rollout 均已上传 `git_diff` 附件，或在 `notes` 中说明无 diff 原因。

---

## 其他要求

1. 在作业过程中docker部分额外强调一下：

    1. 统一版本Docker version 29\.4\.2, build 055a478。

    2. 不允许使用 DinD、docker compose，遇到需要使用的应该更换仓库。

    3. 不允许用清华源。

    4. 构建的仓库需要统一为repo文件夹就是项目文件夹，下面不要有子的项目文件夹（目前的逻辑是repo下面是单独的文件夹就会把对应文件夹的内容抽取出来放到repo里面），像这种。dockerfile的路径也需要这么去写，不然可能我们复现起来会有报错

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NjBiODlhMWM5YzZiZDVlZDI4ZmEwNjhhODFjZjQwZDdfZTdlZDI4M2UyM2M0NDQ0YzQzMDBjYzAxOWEwNDFiMmVfSUQ6NzY0NTg1MTM4NDA0NjIxMDI1M18xNzgwOTM3ODgzOjE3ODEwMjQyODNfVjM)

2. 有一条规则需要再明确一下：

每一条prompt，需要跑五个模型，每个模型都需要单开一个会话；7条prompt应该有35个会话窗口，目前发现有好多同学只开五个会话窗口，session ID调出轨迹后发现多轮对话，不符合规则，抽检发现后将全部打回重新作业，情况严重的会剔除作业名单。请大家认真负责的作业，不要生产无效数据，无效数据不予结算。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NDM2NzRlZGQ4NjRiYjY4ZjcyZWRlNjA2N2VhNzM1MjFfYTkzMjQyOTc5MTliMWY1YTJiNWE5ODBjN2E1NTUwOWFfSUQ6NzY0NTg1MTc5Nzg4MzE3Nzk1MF8xNzgwOTM3ODgzOjE3ODEwMjQyODNfVjM)

## 附录

### 附录 A：难度定义

#### A\.1 评分维度表

#### A\.2 难度映射表

### 附录 B：任务类别定义

### 附录 C：Trae 中打开容器操作说明

本任务所有 rollout 均需在 Trae 中打开对应容器后执行。

具体打开方法请参考单独文档：[如何将日常使用的仓库环境构建成dockerfile，并用Trae启动容器？](https://ocnblxngb8jr.feishu.cn/wiki/LibcwnlCHi7jbpkDA9dcjl2vn5r)

### 附录D：Dockerfile 示例

#### D\. 1 Linux dockerfile

```Dockerfile
# 基础镜像（自定义，可选择一个最合适当前项目的base image）
FROM ubuntu:22.04

# 设置工作目录
WORKDIR /app

# 把宿主机当前目录下 xxx 仓库文件夹内的“所有内容”复制到容器的 /app 目录下
COPY xxx/ ./

# (可选) 安装必要环境 等操作
RUN apt-get update && apt-get install -y --no-install-recommends \
    tmux \
    git \
    curl \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/* # 使用 pip3 安装 Python 依赖
RUN pip3 install --no-cache-dir pandas scipy numpy scikit-learn
```

#### D\. 2 Windows dockerfile

```Dockerfile
# 1. 基础镜像（自定义，可选择一个最合适当前项目的base image）
FROM python:3.10-windowsservercore-ltsc2022

# 2. (可选) 安装必要环境
RUN pip install --no-cache-dir pandas scipy numpy scikit-learn

# 3. 设置工作目录
WORKDIR C:\app

# 4. 把宿主机当前目录下 xxx 仓库文件夹内的“所有内容”复制到容器的 C:\app 目录下
COPY xxx/ ./

# 5. （可选）默认启动命令 (进入 Windows 命令行)
CMD ["cmd.exe"]
```

### 附录E：Trea 中进入 PPE 方式

#### 打开用户json设置 

F1键或点击搜索，输出\>json，点击选择下图所示内容：

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OWYyNTE2ZDA4ZjkxMGM2NWNjZTA1NjRhNDA5ODRhYWRfYTUzOGQyMmZkYmRmODNkMTU2MzE5OTM2ZTQzZDU0ZDZfSUQ6NzY0MjcxODQ0NDIzMTkwNDQ1Nl8xNzgwOTM3ODgzOjE3ODEwMjQyODNfVjM)

#### 添加ppe配置:

在打开的 `settings.json`中，添加以下两行并保存：

```Python
{
  "ai_assistant.request.env": "ppe",                                 
"ai_assistant.request.ppe": "ppe_data_label_trae",    
}
```

#### reload window

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MDEzYTE5NzE0MzFhNGZkMDMzYWNmNWJiZTJiMTc2YzFfYjU4MjlhMDQxYzI2YmMxMGE5ZjVkNWI5ZDk1ZWFkNzVfSUQ6NzY0MjcxODQ0MzQ3NjkyOTUwMF8xNzgwOTM3ODgzOjE3ODEwMjQyODNfVjM)

#### 选择内置模型 （会变化）

再次进入模型选择界面即可看见我们的待测模型：

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YzVlN2NiYjA1NTllNGY1ZGMwMzFjNGJhNjIxOWI3ODBfYmExNzYyM2MxMzRiOTVhZGFhMTE0NWNmOTZlYTAxMThfSUQ6NzY0MjcxODQ0NzE2MzUyNjMzOV8xNzgwOTM3ODgzOjE3ODEwMjQyODNfVjM)



