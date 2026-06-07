# Feishu/Lark Bitable OpenAPI Sync Template

这个目录是一套脱敏的多维表格同步骨架，用于下次优先走 OpenAPI、SDK、MCP 或 CLI，而不是依赖 canvas 坐标点击。

这里不包含真实表格 ID、字段 ID、token、cookie、日志、截图或业务数据。提交前仍应做一次 secret scan。

## 文件

- `config.example.json`: 配置模板，只包含占位符和环境变量名。
- `records.example.json`: 数据模板，只包含脱敏样例行。
- `sync_bitable.py`: Python 标准库版同步脚本骨架，默认不写入。

## 推荐流程

1. 复制配置模板到本地文件，例如 `config.local.json`。
2. 把 `APP_TOKEN_PLACEHOLDER`、`TABLE_ID_PLACEHOLDER` 和字段显示名替换成目标表信息。
3. 通过环境变量提供凭证，不要把 token 写入配置文件：

```bash
export FEISHU_TENANT_ACCESS_TOKEN='...'
```

或使用应用凭证让脚本换取 tenant token：

```bash
export FEISHU_APP_ID='...'
export FEISHU_APP_SECRET='...'
```

4. 先离线校验数据结构：

```bash
python3 sync_bitable.py --config config.local.json --data records.example.json --offline-plan
```

5. 再做只读 dry-run。脚本会读取字段 schema 和远端记录，但不会写入：

```bash
python3 sync_bitable.py --config config.local.json --data records.local.json
```

6. 确认计划无误后显式写入：

```bash
python3 sync_bitable.py --config config.local.json --data records.local.json --apply
```

## 设计约定

- 数据文件使用逻辑字段名，例如 `external_id`、`title`。
- 配置文件把逻辑字段名映射到飞书字段显示名或字段 ID。
- 脚本默认在运行时拉取字段 schema，把字段显示名解析成字段 ID。
- `unique_key` 必须能唯一定位一行，用于幂等 create/update。
- 默认只创建缺失记录、更新差异字段，不做删除。
- `--apply` 之前不会写入远端。

## 字段值

不同字段类型需要传入飞书 OpenAPI 接受的 cell value 形状。这个骨架不强行猜测业务字段，只做透传和基础比较。

常见形状示例：

```json
{
  "text_plain": "plain text",
  "text_rich": [{ "type": "text", "text": "rich text" }],
  "number": 123,
  "single_select": "option_id_or_supported_value",
  "attachment": []
}
```

单选、人员、附件等字段建议先用 API Explorer、SDK 或 MCP 读取一条已知正确记录，确认远端返回和写入所需结构后，再补充字段适配器。

## 参考入口

- Feishu/Lark OpenAPI docs: <https://open.feishu.cn/document/>
- Lark OpenAPI Python SDK: <https://github.com/larksuite/oapi-sdk-python>
- Lark OpenAPI MCP server: <https://github.com/larksuite/lark-openapi-mcp>
- Lark/Feishu CLI: <https://github.com/larksuite/cli>

## 安全检查

不要提交以下内容：

- `config.local.json`、真实数据文件、试跑日志。
- tenant token、user token、app secret、cookie、CSRF token。
- 私有 `app_token`、`table_id`、`view_id`、`field_id`、`record_id`。
- 含业务数据的截图、附件、导出的 API 响应。
