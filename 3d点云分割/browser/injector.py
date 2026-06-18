from typing import Dict
import numpy as np
from playwright.async_api import Page


class ResultInjector:
    def __init__(self, page: Page):
        self.page = page

    async def inject_labels(self, labels: Dict[str, np.ndarray]) -> bool:
        """labels keys: ground, non_ground, noise; values are boolean masks."""
        try:
            return await self._inject_via_internal_api(labels)
        except Exception:
            pass
        return await self._inject_via_ui(labels)

    async def _inject_via_internal_api(self, labels: Dict[str, np.ndarray]) -> bool:
        result = await self.page.evaluate(
            """
            (labels) => {
                for (const key of Object.keys(window)) {
                    const obj = window[key];
                    if (obj && typeof obj.setPointLabels === 'function') {
                        obj.setPointLabels(labels);
                        return true;
                    }
                }
                return false;
            }
            """,
            {k: v.tolist() for k, v in labels.items()},
        )
        return bool(result)

    async def _inject_via_ui(self, labels: Dict[str, np.ndarray]) -> bool:
        # Fallback: select category and trigger selection tool
        # TODO: implement when internal API unavailable
        return False

    async def submit(self) -> bool:
        try:
            btn = self.page.locator("button:has-text('确认完成')")
            if await btn.count() and await btn.is_visible():
                await btn.click()
                await self.page.wait_for_timeout(2000)
            return True
        except Exception:
            return False
