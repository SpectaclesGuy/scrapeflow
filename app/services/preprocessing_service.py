from __future__ import annotations

import re
from bs4 import BeautifulSoup, Comment

NOISE_TAGS = {
    'script', 'style', 'noscript', 'svg', 'canvas', 'iframe', 'nav', 'footer', 'header', 'form'
}
KEEP_ATTRIBUTES = {
    'class', 'id', 'href', 'src', 'alt', 'title', 'aria-label', 'data-testid', 'data-test', 'itemprop'
}


def strip_noise(html: str) -> str:
    soup = BeautifulSoup(html, 'lxml')
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()
    for tag in soup.find_all(NOISE_TAGS):
        tag.decompose()
    for tag in soup.find_all(True):
        attrs = dict(tag.attrs)
        for attr_name in attrs:
            if attr_name not in KEEP_ATTRIBUTES:
                del tag.attrs[attr_name]
        style_value = attrs.get('style')
        if isinstance(style_value, str) and 'display:none' in style_value.replace(' ', '').lower():
            tag.decompose()
            continue
        if tag.name in {'div', 'section'} and len(tag.get_text(strip=True)) == 0:
            tag.decompose()
    cleaned = str(soup)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def extract_relevant_text_blocks(html: str, failed_fields: list[str]) -> list[str]:
    text = BeautifulSoup(html, 'lxml').get_text('\n', strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    keywords = set(failed_fields) | {'price', 'rating', 'title', 'name', '$', '\u20b9', '\u20ac', '\u00a3'}
    selected: list[str] = []
    for line in lines:
        lowered = line.lower()
        if any(keyword.lower() in lowered for keyword in keywords) or re.search(r'[\u20b9$\u20ac\u00a3]\s?\d|\d+(\.\d+)?', line):
            selected.append(line)
    return selected[:20]


def compress_html_snippet(html: str, max_chars: int) -> str:
    compact = re.sub(r'\s+', ' ', html).strip()
    return compact[:max_chars]


def preprocess_html_for_slm(
    html: str,
    config,
    failed_fields: list[str],
    max_chars: int = 12000,
) -> str:
    cleaned_html = strip_noise(html)
    soup = BeautifulSoup(cleaned_html, 'lxml')
    if getattr(config, 'container_selector', None):
        containers = soup.select(config.container_selector)
        if containers:
            focused = ''.join(str(container) for container in containers[:3])
        else:
            focused = cleaned_html
    else:
        focused = cleaned_html
    relevant_text = '\n'.join(extract_relevant_text_blocks(focused, failed_fields))
    combined = f'{focused}\n\n{relevant_text}'.strip()
    return compress_html_snippet(combined, max_chars)
