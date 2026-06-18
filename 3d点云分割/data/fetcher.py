import json
import urllib.request
from pathlib import Path
from typing import Optional, List
from playwright.async_api import Page

import numpy as np

from data.parser import parse_pcd_file, parse_bin_file, parse_las_file


class DataFetcher:
    def __init__(self, config: dict):
        self.config = config

    async def fetch(self, page: Page) -> Optional[np.ndarray]:
        data = await self._try_api(page)
        if data is not None:
            return data
        data = await self._try_js_state(page)
        if data is not None:
            return data
        data = await self._try_resource_cache(page)
        if data is not None:
            return data
        data = await self._try_webgl(page)
        if data is not None:
            return data
        return None

    async def _try_api(self, page: Page) -> Optional[np.ndarray]:
        c = self.config["page"]
        url = (
            f"https://ui.appen.com.cn/api/v1/tdl?"
            f"stepId={c['step_id']}&pageIndex=0&pageSize=1&"
            f"tdlId={c['tdl_id']}&workerId={c['worker_id']}&"
            f"projectId={c['project_id']}&dataSource=TDL&"
            f"recruitmentId={c['recruitment_id']}"
        )
        try:
            cookies = await page.context.cookies()
            cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": await page.evaluate("() => navigator.userAgent"),
                    "Accept": "application/json, text/plain, */*",
                    "Referer": "https://ui.appen.com.cn/ssr/tdl",
                    "Cookie": cookie_str,
                },
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read()
            if raw[:1] == b"{":
                data = json.loads(raw.decode("utf-8"))
                return self._extract_points_from_api(data)
        except Exception:
            pass
        return None

    def _extract_points_from_api(self, data: dict) -> Optional[np.ndarray]:
        # Placeholder: actual extraction depends on API response schema
        return None

    async def _try_js_state(self, page: Page) -> Optional[np.ndarray]:
        try:
            result = await page.evaluate("""
                () => {
                    const keys = Object.keys(window).filter(k => /point|cloud|frame|pcd|task|annotation/i.test(k));
                    for (const k of keys) {
                        const v = window[k];
                        if (v && typeof v === 'object' && v.points && Array.isArray(v.points)) {
                            return v.points.slice(0, 100000);
                        }
                    }
                    return null;
                }
            """)
            if result:
                return np.array(result, dtype=np.float32).reshape(-1, 3)
        except Exception:
            pass
        return None

    async def _try_resource_cache(self, page: Page) -> Optional[np.ndarray]:
        try:
            resources = await page.evaluate(
                "() => performance.getEntriesByType('resource').map(r => r.name)"
            )
            for url in resources:
                if url.endswith(".pcd"):
                    return self._download(url, page)
                if url.endswith(".bin"):
                    return self._download(url, page)
                if url.endswith(".las"):
                    return self._download(url, page)
        except Exception:
            pass
        return None

    async def _try_webgl(self, page: Page) -> Optional[np.ndarray]:
        return None

    async def _download(self, url: str, page: Page) -> Optional[np.ndarray]:
        try:
            cookies = await page.context.cookies()
            cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": await page.evaluate("() => navigator.userAgent"),
                    "Cookie": cookie_str,
                },
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
            path = Path("/tmp") / Path(url).name
            path.write_bytes(raw)
            if url.endswith(".pcd"):
                return parse_pcd_file(str(path))
            if url.endswith(".bin"):
                return parse_bin_file(str(path))
            if url.endswith(".las"):
                return parse_las_file(str(path))
        except Exception:
            pass
        return None
