from __future__ import annotations

from pathlib import Path


async def render_page(url: str, headless: bool = True, timeout: int = 30000) -> str:
    try:
        from playwright.async_api import async_playwright
    except Exception as exc:
        raise RuntimeError('Playwright is not installed') from exc
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until='networkidle', timeout=timeout)
            html = await page.content()
        except Exception:
            screenshot_dir = Path('outputs') / 'evidence'
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(screenshot_dir / 'browser_failure.png'))
            raise
        finally:
            await browser.close()
    return html


async def get_page_with_browser(url: str, config: dict):
    try:
        from playwright.async_api import async_playwright
    except Exception as exc:
        raise RuntimeError('Playwright is not installed') from exc
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=config.get('headless', True))
    page = await browser.new_page()
    await page.goto(url, wait_until=config.get('wait_until', 'networkidle'), timeout=config.get('timeout', 30000))
    if config.get('wait_for_selector'):
        await page.wait_for_selector(config['wait_for_selector'], timeout=config.get('timeout', 30000))
    page._scrapeflow_browser = browser
    page._scrapeflow_playwright = playwright
    return page
