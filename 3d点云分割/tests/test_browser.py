import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from browser.controller import BrowserController


@pytest.mark.asyncio
async def test_find_annotation_page():
    ctrl = BrowserController("http://test", "点云", "ui.appen.com.cn")
    ctrl.context = MagicMock()
    good = MagicMock()
    good.url = "https://ui.appen.com.cn/ssr/tdl"
    good.title = AsyncMock(return_value="点云语义分割")
    bad = MagicMock()
    bad.url = "https://eliteai.appen.com.cn/"
    bad.title = AsyncMock(return_value="EliteAI")
    ctrl.context.pages = [bad, good]
    found = await ctrl._find_annotation_page()
    assert found is good
