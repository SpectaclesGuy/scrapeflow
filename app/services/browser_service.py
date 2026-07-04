from __future__ import annotations

import asyncio
from pathlib import Path


def _capture_browser_failure(page) -> None:
    screenshot_dir = Path('outputs') / 'evidence'
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(screenshot_dir / 'browser_failure.png'))


def _goto_with_fallback(page, url: str, wait_until: str, timeout: int) -> None:
    strategies = []
    for state in (wait_until, 'load', 'domcontentloaded', 'commit'):
        if state and state not in strategies:
            strategies.append(state)

    last_error = None
    for state in strategies:
        try:
            page.goto(url, wait_until=state, timeout=timeout)
            return
        except Exception as exc:
            last_error = exc

    raise last_error or RuntimeError(f'Navigation failed for {url}')


def _wait_for_selector_if_needed(page, selector: str | None, timeout: int) -> None:
    if not selector:
        return
    try:
        page.wait_for_selector(selector, timeout=timeout)
    except Exception:
        # Selector readiness is helpful but should not fail the entire extraction.
        return


def _render_page_sync(url: str, headless: bool = True, timeout: int = 30000, wait_until: str = 'load') -> str:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise RuntimeError('Playwright is not installed') from exc

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        page = browser.new_page()
        try:
            _goto_with_fallback(page, url, wait_until, timeout)
            return page.content()
        except Exception:
            _capture_browser_failure(page)
            raise
        finally:
            browser.close()


async def render_page(url: str, headless: bool = True, timeout: int = 30000, wait_until: str = 'load') -> str:
    return await asyncio.to_thread(_render_page_sync, url, headless, timeout, wait_until)


def _render_pages_with_browser_sync(url: str, browser_config: dict, pagination_config: dict) -> list[dict[str, str]]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise RuntimeError('Playwright is not installed') from exc

    headless = browser_config.get('headless', True)
    wait_until = browser_config.get('wait_until', 'load')
    timeout = browser_config.get('timeout', 30000)
    wait_for_selector = browser_config.get('wait_for_selector')
    pagination_enabled = pagination_config.get('enabled', False)
    pagination_type = pagination_config.get('type', 'none')
    next_selector = pagination_config.get('next_selector')
    max_pages = max(int(pagination_config.get('max_pages', 1) or 1), 1)

    pages: list[dict[str, str]] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        page = browser.new_page()
        try:
            _goto_with_fallback(page, url, wait_until, timeout)
            _wait_for_selector_if_needed(page, wait_for_selector, timeout)
            pages.append({'url': page.url, 'html': page.content()})

            if pagination_enabled and pagination_type == 'next_button' and next_selector:
                for _ in range(1, max_pages):
                    button = page.query_selector(next_selector)
                    if button is None:
                        break
                    button.click()
                    try:
                        page.wait_for_load_state('load', timeout=timeout)
                    except Exception:
                        pass
                    _wait_for_selector_if_needed(page, wait_for_selector, timeout)
                    pages.append({'url': page.url, 'html': page.content()})

            return pages
        except Exception:
            _capture_browser_failure(page)
            raise
        finally:
            browser.close()


async def render_pages_with_browser(url: str, browser_config: dict, pagination_config: dict) -> list[dict[str, str]]:
    return await asyncio.to_thread(
        _render_pages_with_browser_sync,
        url,
        browser_config,
        pagination_config,
    )
