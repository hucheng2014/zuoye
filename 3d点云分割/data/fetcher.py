import json
import base64
import urllib.request
from pathlib import Path
from typing import Optional, List, Dict
from playwright.async_api import Page

import numpy as np

from data.parser import parse_pcd_file, parse_bin_file, parse_las_file


class DataFetcher:
    def __init__(self, config: dict):
        self.config = config
        self._task_data: Optional[dict] = None
        self._pcd_urls: Optional[List[str]] = None

    async def fetch_task_data(self, page: Page) -> Optional[dict]:
        """Fetch and decode taskData from /api/v1/tdl using browser credentials.

        Uses Playwright route interception to capture the page's own API call,
        which carries the correct cookies and headers.
        """
        if self._task_data is not None:
            return self._task_data

        c = self.config["page"]
        api_url_marker = "/api/v1/tdl?"

        captured_body: Optional[bytes] = None

        async def route_handler(route, request):
            nonlocal captured_body
            if api_url_marker in request.url and "submit" not in request.url:
                try:
                    response = await route.fetch()
                    captured_body = await response.body()
                    await route.fulfill(response=response)
                except Exception:
                    await route.continue_()
            else:
                await route.continue_()

        await page.route("**/*", route_handler)
        try:
            await page.reload(wait_until="domcontentloaded", timeout=60000)
            for _ in range(45):
                await page.wait_for_timeout(1000)
                if captured_body is not None:
                    break
        finally:
            await page.unroute("**/*", route_handler)

        if captured_body is None:
            return None

        try:
            api_data = json.loads(captured_body.decode("utf-8"))
            task_data_b64 = api_data.get("taskData")
            if not task_data_b64:
                return None
            decoded = base64.b64decode(task_data_b64).decode("utf-8")
            self._task_data = json.loads(decoded)
            return self._task_data
        except Exception:
            return None

    async def fetch(self, page: Page, frame_index: int = 0) -> Optional[np.ndarray]:
        task_data = await self.fetch_task_data(page)
        if task_data is None:
            return None
        urls = self._get_pcd_urls(task_data)
        if not urls or frame_index >= len(urls):
            return None
        return await self._download_pcd(urls[frame_index])

    def _get_pcd_urls(self, task_data: dict) -> List[str]:
        if self._pcd_urls is not None:
            return self._pcd_urls
        urls = []
        try:
            results = task_data.get("results", [])
            if not results:
                return urls
            source = json.loads(results[0].get("source", "{}"))
            base_url_json = json.loads(source.get("base_url", "{}"))
            for sensor in base_url_json.get("sensors", []):
                if sensor.get("type") == "points":
                    urls = sensor.get("urls", [])
                    break
        except Exception:
            pass
        self._pcd_urls = urls
        return urls

    async def _download_pcd(self, url: str) -> Optional[np.ndarray]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read()
            path = Path("/tmp") / Path(url.split("?")[0]).name
            path.write_bytes(raw)
            return parse_pcd_file(str(path))
        except Exception:
            return None

    async def fetch_annotation_template(self, page: Page) -> Optional[dict]:
        """Download a previous annotation result if available to use as template."""
        task_data = await self.fetch_task_data(page)
        if task_data is None:
            return None
        try:
            results = task_data.get("results", [])
            if not results:
                return None
            source = json.loads(results[0].get("source", "{}"))
            annotation_url = source.get("annotation")
            if not annotation_url:
                return None
            req = urllib.request.Request(annotation_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None

    async def _try_js_state(self, page: Page) -> Optional[np.ndarray]:
        return None

    async def _try_resource_cache(self, page: Page) -> Optional[np.ndarray]:
        return None

    async def _try_webgl(self, page: Page) -> Optional[np.ndarray]:
        return None
