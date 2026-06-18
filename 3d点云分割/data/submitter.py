import json
import base64
import urllib.request
from pathlib import Path
from typing import Optional
from playwright.async_api import Page


class Submitter:
    def __init__(self, config: dict):
        self.config = config

    async def submit_via_api(
        self,
        page: Page,
        task_data_b64: str,
    ) -> Optional[dict]:
        """Submit taskData to /api/v1/tdl/submit using browser credentials."""
        c = self.config["page"]
        url = (
            f"https://ui.appen.com.cn/api/v1/tdl/submit?"
            f"requestStepId={c['step_id']}&tdlId={c['tdl_id']}"
        )
        try:
            resp = await page.evaluate(
                f"""async () => {{
                    const fd = new FormData();
                    fd.append('taskData', '{task_data_b64}');
                    const r = await fetch("{url}", {{
                        method: 'POST',
                        credentials: 'include',
                        body: fd,
                    }});
                    const text = await r.text();
                    return {{status: r.status, text: text}};
                }}"""
            )
            if resp.get("status") != 200:
                return None
            return json.loads(resp["text"])
        except Exception:
            return None

    async def submit_via_ui(self, page: Page) -> bool:
        """Click the '确认完成' button as fallback."""
        try:
            btn = page.locator("button:has-text('确认完成')")
            if await btn.count() and await btn.is_visible():
                await btn.click()
                await page.wait_for_timeout(2000)
                return True
        except Exception:
            pass
        return False
