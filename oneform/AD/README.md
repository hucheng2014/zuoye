# AD Search Ads Relevance 项目

本目录只保留教程、流程文档和离线校验工具。旧的自动判题/自动提交脚本已删除，避免再出现快速循环误判、漏选、评论串题等问题。

## 重要文件

- `Search Ads.md`：官方 Search Ads Relevance 教程。
- `AD_RATING_SOP.md`：本项目做题标准流程，必须优先遵守。
- `GPT_MINI_AD_PROMPT.md`：给未来较小模型使用的稳定提示词。
- `records/ad_batch_template.json`：每批题记录模板。
- `tools/validate_ad_batch.py`：离线校验记录完整性；不连接浏览器、不判题、不提交。

## 推荐流程

1. 读取当前页面题目。
2. 按 `AD_RATING_SOP.md` 逐题研究和判断。
3. 将判断记录到 `records/YYYY-MM-DD_batch_N.json`。
4. 填写页面。
5. 运行校验并人工复核页面：

```bash
python3 tools/validate_ad_batch.py records/YYYY-MM-DD_batch_N.json --require-checked
```

6. 全部通过后，再按用户授权点击 `Submit Rating`。

## 禁止

- 禁止恢复 `auto_rating.py`、`smart_rating.py`、`runner.py`、`loop_rating.py` 等自动判题/自动提交逻辑。
- 禁止无复核循环提交。
- 不确定的题必须先研究或请求人工确认。

## Native Antigravity Skill

本项目已集成原生的 Antigravity 技能（Skill），当您在 AI 助手会话中启动任务时，助手可直接激活以下技能：
*   **Skill Name**: `oneform-ad-rating`
*   **SKILL.md 路径**: `/Users/xaa/.gemini/config/plugins/oneform-plugin/skills/oneform-ad-rating/SKILL.md`
*   **功能**: 支持智能任务提取、SOP 深度相关性判定、React DOM 动态提取与 CDP Websocket 精准填充与提交。

