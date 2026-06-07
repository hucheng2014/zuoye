#!/usr/bin/env python3
"""Probe Feishu/Lark Drive upload SDK from the authenticated Bitable page.

This uploads a local file to Drive and prints the SDK events. It does not write
any Bitable record fields.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

import submit_new_task_group as group


BASE_DIR = Path(__file__).resolve().parent


async def main() -> int:
    path = BASE_DIR / "Dockerfile"
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://127.0.0.1:9235")
        pages = [page for ctx in browser.contexts for page in ctx.pages if group.BASE_TOKEN in page.url]
        if not pages:
            raise RuntimeError("target Bitable page is not open")
        page = pages[0]
        await page.bring_to_front()
        await page.wait_for_function(
            "({ table }) => !!window.bitableStore?.modelOperator?.getTableById(table)",
            arg={"table": group.TABLE_ID},
            timeout=30000,
        )
        file_input = await page.evaluate_handle(
            """
            () => {
              let input = document.querySelector('#codex-drive-upload-probe');
              if (!input) {
                input = document.createElement('input');
                input.type = 'file';
                input.id = 'codex-drive-upload-probe';
                input.style.position = 'fixed';
                input.style.left = '-10000px';
                input.style.top = '0';
                document.body.appendChild(input);
              }
              input.value = '';
              return input;
            }
            """
        )
        await file_input.as_element().set_input_files(str(path))
        result = await page.evaluate(
            """
            async () => {
              const input = document.querySelector('#codex-drive-upload-probe');
              const file = input.files[0];
              const { SuiteUploader } = await window.BitableDep.DriveHelper.getUploadSDK();
              const events = [];
              const env = window.BitableDep.DriveHelper.getUploadSDKEnvConfig();
              const uploader = new SuiteUploader({
                envConfigs: env,
                featureFlags: {
                  smallFileDirectUpload: true,
                  largeFileFastUpload: false,
                  fileSizeChecker: false,
                  concurrentAndRetryableUpload: false,
                },
                maxSimultaneousUploads: 1,
                riskDetectionExtra: window.BitableDep.DriveHelper.getUploadRiskDetectionExtra(),
              });
              const names = ['success', 'error', 'progress', 'retry', 'finish', 'runtime_incident_occurred'];
              for (const name of names) {
                uploader.on(name, (payload) => {
                  events.push({
                    event: name,
                    payload: JSON.parse(JSON.stringify(payload, (key, value) => {
                      if (value instanceof File) return { name: value.name, size: value.size, type: value.type };
                      if (typeof value === 'function') return '[function]';
                      return value;
                    })),
                  });
                });
              }
              uploader.loadFile(file, {
                jobType: 1,
                parentToken: window.bitableStore.token,
                mountPoint: 'bitable',
                businessType: 1,
                shouldAddToRecents: false,
                sizeLimit: 1024 * 1024 * 1024,
                extensions: [],
                bizExtra: { extra: JSON.stringify({ table_id: window.bitableStore.bitableConfig.activeTableId }) },
                bizPayload: { source: 'codex_probe' },
              });
              uploader.upload();
              const started = Date.now();
              while (Date.now() - started < 60000) {
                if (events.some((item) => item.event === 'success' || item.event === 'error')) break;
                await new Promise((resolve) => setTimeout(resolve, 500));
              }
              return {
                events,
                progress: uploader.progress,
                isUploading: uploader.isUploading,
                taskCount: uploader.tasks?.length,
              };
            }
            """
        )
        print(result)
        await browser.close()
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
