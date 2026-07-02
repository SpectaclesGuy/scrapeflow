import html
import re

WHITESPACE_RE = re.compile(r'\s+')
CURRENCY_SPACE_RE = re.compile(r'([\u20b9$\u20ac\u00a3])\s+')


def clean_text(value: str | None) -> str:
    if not value:
        return ''
    text = html.unescape(value)
    text = text.replace('\xa0', ' ')
    text = WHITESPACE_RE.sub(' ', text).strip()
    return CURRENCY_SPACE_RE.sub(r'\1', text)
