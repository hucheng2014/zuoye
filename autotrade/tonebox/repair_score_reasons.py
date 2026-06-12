import asyncio
import json
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright


BASE_TOKEN = "B4SgbbhcyaJfwWsWHvcc1AtgnYd"
TABLE_ID = "tblcXB0RGGaHGm1r"
VIEW_ID = "vewxWP7trZ"

FIELDS = {
    "prompt_index": "fldW6rO2LU",
    "rollout_id": "fldqgS0GPQ",
    "session_id": "fldaMDOOJL",
    "model_name": "fldPxbX1x9",
    "score": "fldvFVIm4O",
    "score_reason": "fld7hrms66",
    "score_check": "fldpClY5fM",
    "git_diff": "fld3Jhw2G1",
}


REASONS = {
    "6a205b186b996e39953eb918": "本轮为代码修改类 Prompt 2 的 Doubao-Seed 前置筛选 rollout，按作业规则 seed 未作为可采纳实现时记录 0 分。该任务要求把内存计时器持久化到数据库并覆盖 start/stop/重复启动流程；此 seed 结果仅作为区分度基线保留，score=0 合理。",
    "6a205da96b996e39953eb9a9": "完整满足 Prompt 2：围绕 TimeEntry、entry_repo、entry_service 实现计时器数据库持久化，处理 start_time_iso、is_active_timer、重复启动校验和 stop_timer 落库，并补充 tests/test_entries.py；pytest 73 passed，功能闭环且测试覆盖充分，评 2 分。",
    "6a205eaf6b996e39953eb9f9": "基本完成 Prompt 2 的持久化计时器逻辑，TimeEntry、entry_repo、entry_service 均有对应改动，测试 73 passed；但实现范围较基础，未同步 schema 输出字段，边界与兼容性覆盖弱于满分实现，因此评 1 分。",
    "6a20618e6b996e39953ebaa0": "满足 Prompt 2 核心要求：新增持久化计时器字段，start_timer 会检查同一用户激活计时器，stop_timer 从数据库读取并生成正式工时记录，相关仓储和服务层均已改动；pytest 全部通过，代码质量稳定，评 2 分。",
    "6a20600c6b996e39953eba34": "完整满足 Prompt 2：除模型、仓储、服务层外同步更新 entry schema，并补充数据库持久化计时器测试；73 passed 说明原有与新增用例均通过，覆盖 start/stop/重复启动路径，评 2 分。",
    "6a20eaad6b996e39953ebb02": "本轮为代码修改类 Prompt 3 的 Doubao-Seed 前置筛选 rollout，按作业规则 seed 作为无效基线记录 0 分。该任务要求今日累计工时上限校验并补测试，seed 结果不作为可采纳满分实现提交，score=0 合理。",
    "6a20ef561ceaa60b3bb21022": "完整满足 Prompt 3：在 create_entry 中按用户和日期累计数据库已有 duration，再与本次工时相加比较 settings.max_hours_per_day，超限抛出指定 ValueError，并在 tests/test_entries.py 增加覆盖；pytest 73 passed，评 2 分。",
    "6a20f2921ceaa60b3bb210b5": "满足 Prompt 3：entry_service 增加今日累计工时校验，测试覆盖已录入工时加本次工时超过上限时抛出 ValueError；pytest 73 passed，改动集中且符合需求，评 2 分。",
    "6a20f3f01ceaa60b3bb210d2": "满足 Prompt 3：服务层按日期统计用户已录入 duration，并在创建前执行累计上限校验，补充 tests/test_entries.py 验证异常路径；pytest 74 passed，需求闭环，评 2 分。",
    "6a20f52a1ceaa60b3bb21107": "完整满足 Prompt 3：补充仓储查询能力并在 entry_service 中实现今日累计总工时校验，覆盖超过 settings.max_hours_per_day 时的指定 ValueError，同时新增测试；pytest 76 passed，评 2 分。",
    "6a20f6111ceaa60b3bb21145": "本轮为代码修改类 Prompt 4 的 Doubao-Seed 前置筛选 rollout，按作业规则 seed 作为无效基线记录 0 分。该任务要求 Excel 汇总行、公式和样式验证，seed 结果仅用于区分度筛选，score=0 合理。",
    "6a20f7901ceaa60b3bb21184": "完整满足 Prompt 4：在 export.py 导出的明细后加入空行和汇总行，duration 列写入 SUM(D2:Dn) 公式并设置加粗、填充、对齐等样式，同时在 tests/test_reports.py 验证公式与样式；pytest 73 passed，评 2 分。",
    "6a20f8751ceaa60b3bb211bf": "满足 Prompt 4：Excel 导出新增美化汇总行和 duration 求和公式，测试覆盖生成文件中的公式与样式字段；pytest 73 passed，功能与验证都对应 prompt 要求，评 2 分。",
    "6a20f9401ceaa60b3bb211e8": "完整满足 Prompt 4：export.py 生成带空行、SUM 公式和加粗/填充/边框等样式的汇总行，tests/test_reports.py 覆盖公式位置和样式；pytest 76 passed，改动完整，评 2 分。",
    "6a20fac91ceaa60b3bb21220": "满足 Prompt 4：导出 Excel 明细后追加汇总行，duration 列使用 SUM 范围公式，并补充报告测试校验公式与样式定义；pytest 77 passed，需求闭环且无回归，评 2 分。",
    "6a20fbc41ceaa60b3bb2127f": "本轮为代码修改类 Prompt 5 的 Doubao-Seed 前置筛选 rollout，按作业规则 seed 作为无效基线记录 0 分。该任务要求项目 manager_id 与审批权限闭环，seed 结果仅用于前置筛选，score=0 合理。",
    "6a20fe161ceaa60b3bb212ed": "完整满足 Prompt 5：Project 模型/schema/service 支持 manager_id，timesheet approve/reject 接收 operator_id 并校验项目负责人，不匹配抛出 PermissionError；API 与 tests/test_projects.py、tests/test_timesheets.py 同步更新，pytest 74 passed，评 2 分。",
    "6a20ff6f1ceaa60b3bb21373": "满足 Prompt 5：新增 Project.manager_id，审批和驳回流程要求 operator_id 并校验是否为项目负责人，无权时抛出 PermissionError，相关 API/schema/test 均有修改；pytest 74 passed，评 2 分。",
    "6a2101211ceaa60b3bb213e4": "完整满足 Prompt 5：项目负责人字段、创建/更新 schema、审批服务和 API 调用链均同步改动，覆盖 approve/reject 授权与拒绝路径；pytest 76 passed，权限闭环完整，评 2 分。",
    "6a2104931ceaa60b3bb21452": "满足 Prompt 5：Project 与 Timesheet 相关模型/schema/service/API 均围绕 manager_id 和 operator_id 做了联动，审批无权路径抛出 PermissionError，测试覆盖同步更新；pytest 74 passed，评 2 分。",
    "6a2107181ceaa60b3bb214fc": "本轮为代码修改类 Prompt 6 的 Doubao-Seed 前置筛选 rollout，按作业规则 seed 作为无效基线记录 0 分。该任务要求 Project 状态枚举、查询语义和任务/工时禁用规则，seed 结果仅用于区分度筛选，score=0 合理。",
    "6a210b431ceaa60b3bb2157c": "完整满足 Prompt 6：将 Project.is_active 迁移为 status 枚举，覆盖 DRAFT/ONGOING/COMPLETED/SUSPENDED，更新仓储、schema、项目服务、任务和工时创建限制，并同步多组测试；pytest 78 passed，评 2 分。",
    "6a21134be0b94db7064126d7": "部分满足 Prompt 6：完成 Project status 枚举替换并调整任务/工时相关限制，pytest 72 passed；但实现偏基础，状态流转、仓储查询和兼容边界覆盖不足，未达到完整生命周期管理要求，因此评 1 分。",
    "6a2116eb517dbb2a2bff43f9": "满足 Prompt 6：Project 状态枚举、schema、project_service、task_service、entry_service 和相关测试均已更新，COMPLETED/SUSPENDED 下禁止创建任务或工时；pytest 78 passed，生命周期规则闭环，评 2 分。",
    "6a2119a7517dbb2a2bff44d3": "满足 Prompt 6：用 DRAFT/ONGOING/COMPLETED/SUSPENDED 状态替代布尔 is_active，并更新项目查询、任务创建、工时创建和测试；pytest 77 passed，改动覆盖主要业务路径，评 2 分。",
    "6a211cd7517dbb2a2bff455f": "本轮为代码修改类 Prompt 7 的 Doubao-Seed 前置筛选 rollout，按作业规则 seed 作为无效基线记录 0 分。该任务要求报表加班统计和 1.5 倍加权逻辑，seed 结果仅用于前置筛选，score=0 合理。",
    "6a211f6b517dbb2a2bff45b8": "完整满足 Prompt 7：Report schema 新增 overtime_hours、weighted_billable_hours，generate_report 按用户每日 billable 超过 8 小时部分计 overtime，并按 1.5 倍计入 weighted_billable_hours；tests/test_reports.py 覆盖计算，pytest 74 passed，评 2 分。",
    "6a212133d6093219993a0ce8": "满足 Prompt 7：报表 schema 与 report_service 同步新增加班小时和加权可计费小时计算，超过 8 小时的 billable 部分按 1.5 倍处理，并补充报告测试；pytest 74 passed，评 2 分。",
    "6a212498d6093219993a0d63": "完整满足 Prompt 7：generate_report 对每日 billable 工时进行正常 8 小时和超额加班拆分，输出 overtime_hours 与 weighted_billable_hours，测试覆盖 10 小时示例类场景；pytest 77 passed，评 2 分。",
    "6a2126e5d6093219993a0dba": "满足 Prompt 7：schema 新字段、报表服务加班计算和 tests/test_reports.py 均已更新，超过每日 8 小时的 billable 部分计入 overtime 并按 1.5 倍加权；pytest 77 passed，评 2 分。",
}


def text_cell(value: str) -> dict:
    return {"type": 1, "value": [{"type": "text", "text": value}]}


async def fetch_rows(page):
    return await page.evaluate(
        """
        async ({ token, table, view, fields }) => {
          const tableObj = window.bitableStore.modelOperator.getTableById(table);
          const getField = (id) => tableObj.fields?.[id] || tableObj.fieldsMap?.get?.(id);
          const optionNames = {};
          for (const name of ['model_name', 'score']) {
            const field = getField(fields[name]);
            optionNames[name] = Object.fromEntries((field?.property?.options || []).map(opt => [opt.id, opt.name]));
          }
          const rev = tableObj.rev;
          const url = `/space/api/v1/bitable/${token}/records?tableId=${table}&viewId=${view}&tableRev=${rev}&depRev=%7B%7D&viewLazyLoad=true&offset=0&limit=3000&tableID=${table}&viewID=${view}&removeFmlExtra=true`;
          const json = await (await fetch(url, { credentials: 'include' })).json();
          const parsed = JSON.parse(await window.unGzipBase64(json.data.records));
          const baseValue = (cell) => {
            if (!cell) return null;
            if (typeof cell === 'object' && 'value' in cell) return cell.value;
            return cell;
          };
          const unwrapText = (cell) => {
            const value = baseValue(cell);
            if (value == null) return '';
            if (Array.isArray(value)) return value.map(x => x?.text ?? x?.name ?? x?.value ?? '').join('');
            if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value);
            if (typeof value === 'object') return value.text ?? value.name ?? '';
            return String(value);
          };
          const unwrapSelect = (name, cell) => {
            const value = baseValue(cell);
            if (value == null) return '';
            if (typeof value === 'string') return optionNames[name]?.[value] ?? value;
            if (Array.isArray(value)) return value.map(x => optionNames[name]?.[x] ?? x?.name ?? x?.text ?? x?.id ?? '').join('');
            return '';
          };
          const unwrapFiles = (cell) => {
            const value = baseValue(cell);
            if (!Array.isArray(value)) return [];
            return value.map(x => x.name ?? x.attachmentToken ?? x.id ?? '').filter(Boolean);
          };
          return Object.entries(parsed.recordMap || {}).map(([recordId, rec]) => ({
            recordId,
            prompt_index: unwrapText(rec[fields.prompt_index]),
            rollout_id: unwrapText(rec[fields.rollout_id]),
            session_id: unwrapText(rec[fields.session_id]),
            model_name: unwrapSelect('model_name', rec[fields.model_name]),
            score: unwrapSelect('score', rec[fields.score]),
            score_reason: unwrapText(rec[fields.score_reason]),
            score_check: unwrapText(rec[fields.score_check]),
            git_files: unwrapFiles(rec[fields.git_diff]),
          }));
        }
        """,
        {"token": BASE_TOKEN, "table": TABLE_ID, "view": VIEW_ID, "fields": FIELDS},
    )


async def set_records(page, updates):
    return await page.evaluate(
        """
        async ({ table, view, updates }) => {
          const result = await Promise.resolve(window.bitableStore.commandManager.execute({
            cmd: 'SetRecords',
            tableId: table,
            viewId: view,
            data: updates,
            ignoreCheckRecordLoaded: true,
          }));
          return JSON.parse(JSON.stringify(result, (key, value) => typeof value === 'function' ? '[function]' : value));
        }
        """,
        {"table": TABLE_ID, "view": VIEW_ID, "updates": updates},
    )


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://127.0.0.1:9235")
        pages = [page for ctx in browser.contexts for page in ctx.pages if BASE_TOKEN in page.url]
        if not pages:
            raise RuntimeError("Bitable page is not open in the Chrome debugging session")
        page = pages[0]
        await page.wait_for_function(
            "({ table }) => !!window.bitableStore?.modelOperator?.getTableById(table)",
            arg={"table": TABLE_ID},
            timeout=30000,
        )

        before = await fetch_rows(page)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        Path(f"score_reason_before_{stamp}.json").write_text(
            json.dumps(before, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        by_sid = {row["session_id"]: row for row in before if row.get("session_id")}
        missing = sorted(set(REASONS) - set(by_sid))
        if missing:
            raise RuntimeError(f"Missing rollout rows for session_id values: {missing}")

        updates = {}
        for sid, reason in REASONS.items():
            row = by_sid[sid]
            if row.get("score_reason") != reason:
                updates[row["recordId"]] = {FIELDS["score_reason"]: text_cell(reason)}

        print(f"rollout_rows={len(by_sid)} updates={len(updates)}")
        if updates:
            for batch_start in range(0, len(updates), 10):
                batch_items = list(updates.items())[batch_start : batch_start + 10]
                batch = dict(batch_items)
                result = await set_records(page, batch)
                print(
                    f"batch {batch_start // 10 + 1}: result={result.get('result')} "
                    f"records={len(batch)} actions={len(result.get('operation', {}).get('actions', []))}"
                )
                if result.get("result") != 2:
                    raise RuntimeError(f"SetRecords failed: {result}")
                await page.wait_for_timeout(2500)

        await page.wait_for_timeout(5000)
        after = await fetch_rows(page)
        Path(f"score_reason_after_{stamp}.json").write_text(
            json.dumps(after, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        after_by_sid = {row["session_id"]: row for row in after if row.get("session_id")}
        mismatches = [
            sid
            for sid, reason in REASONS.items()
            if after_by_sid.get(sid, {}).get("score_reason") != reason
        ]
        counts = {}
        for row in after_by_sid.values():
            check = row.get("score_check") or "空"
            if "不合理" in check:
                key = "不合理"
            elif "合理" in check:
                key = "合理"
            else:
                key = check[:60] or "空"
            counts[key] = counts.get(key, 0) + 1

        print(f"verify_mismatches={len(mismatches)}")
        if mismatches:
            print("mismatches:", ", ".join(mismatches))
        print("score_check_counts:", json.dumps(counts, ensure_ascii=False))
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
