from __future__ import annotations

import httpx


async def fetch_html(url: str, timeout: int = 30) -> str:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
    }
    async with httpx.AsyncClient(headers=headers, timeout=timeout, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text
