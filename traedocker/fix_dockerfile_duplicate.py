#!/usr/bin/env python3
"""Fix B00001573 duplicate Dockerfile attachment."""

import asyncio
from playwright.async_api import async_playwright

BASE_TOKEN = "B4SgbbhcyaJfwWsWHvcc1AtgnYd"
TABLE_ID = "tblcXB0RGGaHGm1r"
VIEW_ID = "vewxWP7trZ"
CDP_URL = "http://127.0.0.1:9235"

ROOT_ID = "recvltHcbs9Y6q"
DOCKERFILE_FIELD = "fldluiW0W3"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CDP_URL)
        page = browser.contexts[0].pages[0]
        await page.wait_for_timeout(2000)

        # Fetch current Dockerfile attachments
        attachments = await page.evaluate(
            """async ({token, table, view, recordId, fieldId}) => {
                const tableObj = window.bitableStore.modelOperator.getTableById(table);
                if (!tableObj) return {error: 'no table'};
                const rev = tableObj.rev;
                const url = `/space/api/v1/bitable/${token}/records?tableId=${table}&viewId=${view}&tableRev=${rev}&depRev=%7B%7D&viewLazyLoad=true&offset=0&limit=3000&tableID=${table}&viewID=${view}&removeFmlExtra=true`;
                const json = await (await fetch(url, {credentials: 'include'})).json();
                const decoded = await window.unGzipBase64(json.data.records);
                const records = JSON.parse(decoded);
                const rec = records.recordMap[recordId];
                const cell = rec[fieldId];
                if (!cell || !cell.value) return [];
                return cell.value.map(a => ({name: a.name, token: a.attachmentToken}));
            }""",
            {"token": BASE_TOKEN, "table": TABLE_ID, "view": VIEW_ID, "recordId": ROOT_ID, "fieldId": DOCKERFILE_FIELD},
        )

        print(f"Current Dockerfile attachments: {len(attachments)}")
        for a in attachments:
            print(f"  - {a['name']} (token: {a['token']})")

        if len(attachments) <= 1:
            print("  ✓ Not duplicated, skipping")
            return

        # Keep only first attachment
        keep_token = attachments[0]["token"]
        keep_value = [{"attachmentToken": keep_token}]

        result = await page.evaluate(
            """async ({token, table, view, recordId, fieldId, value}) => {
                const url = `/space/api/v1/bitable/${token}/records`;
                const body = {
                    table: table,
                    view: view,
                    recordIds: [recordId],
                    records: [{
                        recordId: recordId,
                        fields: {
                            [fieldId]: {type: 17, value: value}
                        }
                    }]
                };
                const json = await (await fetch(url, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(body)
                })).json();
                return json;
            }""",
            {"token": BASE_TOKEN, "table": TABLE_ID, "view": VIEW_ID, "recordId": ROOT_ID, "fieldId": DOCKERFILE_FIELD, "value": keep_value},
        )

        print(f"Update result: code={result.get('code', '?')}, result={result.get('result', '?')}")
        await page.wait_for_timeout(3000)

        # Verify
        verify = await page.evaluate(
            """async ({token, table, view, recordId, fieldId}) => {
                const tableObj = window.bitableStore.modelOperator.getTableById(table);
                if (!tableObj) return {error: 'no table'};
                const rev = tableObj.rev;
                const url = `/space/api/v1/bitable/${token}/records?tableId=${table}&viewId=${view}&tableRev=${rev}&depRev=%7B%7D&viewLazyLoad=true&offset=0&limit=3000&tableID=${table}&viewID=${view}&removeFmlExtra=true`;
                const json = await (await fetch(url, {credentials: 'include'})).json();
                const decoded = await window.unGzipBase64(json.data.records);
                const records = JSON.parse(decoded);
                const rec = records.recordMap[recordId];
                const cell = rec[fieldId];
                if (!cell || !cell.value) return [];
                return cell.value.map(a => ({name: a.name, token: a.attachmentToken}));
            }""",
            {"token": BASE_TOKEN, "table": TABLE_ID, "view": VIEW_ID, "recordId": ROOT_ID, "fieldId": DOCKERFILE_FIELD},
        )

        print(f"Verified Dockerfile attachments: {len(verify)}")
        for a in verify:
            print(f"  - {a['name']} (token: {a['token']})")

        if len(verify) == 1:
            print("  ✓ Fixed!")
        else:
            print("  ✗ Still duplicated!")


if __name__ == "__main__":
    asyncio.run(main())
