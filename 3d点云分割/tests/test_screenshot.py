import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from utils.screenshot import save_screenshot


@pytest.mark.asyncio
async def test_save_screenshot_creates_file(tmp_path):
    page = MagicMock()
    page.screenshot = AsyncMock()
    path = await save_screenshot(page, "test", str(tmp_path))
    assert path.parent == tmp_path
    assert "test_" in path.name
    page.screenshot.assert_awaited_once()
