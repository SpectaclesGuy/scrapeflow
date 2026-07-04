from __future__ import annotations


async def paginate_with_browser(page, config):
    pages = [page]
    if not config.pagination.enabled or config.pagination.type != 'next_button' or not config.pagination.next_selector:
        return pages
    max_pages = max(config.pagination.max_pages, 1)
    current = page
    for _ in range(1, max_pages):
        button = await current.query_selector(config.pagination.next_selector)
        if button is None:
            break
        await button.click()
        await current.wait_for_load_state('networkidle')
        pages.append(current)
    return pages


def generate_paginated_urls(base_url: str, pattern: str, max_pages: int):
    return [pattern.format(page=page) for page in range(1, max_pages + 1)] if pattern else [base_url]
