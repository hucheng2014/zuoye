from pathlib import Path
from datetime import datetime
from playwright.async_api import Page


async def save_screenshot(page: Page, prefix: str, base_dir: str) -> Path:
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = base / f"{prefix}_{ts}.png"
    await page.screenshot(path=str(path), full_page=False)
    return path
