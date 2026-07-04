from __future__ import annotations

from bs4 import BeautifulSoup

from app.core.text_cleaner import clean_text
from app.services.evidence_service import build_field_evidence

COMMON_FALLBACK_CONTAINERS = [
    '[data-component-type="s-search-result"]',
    '.s-result-item',
    '[data-asin]',
    '.product-card',
    '.product',
    '.product-item',
    '.product-tile',
    '.grid-item',
    '.collection-item',
    '.listing',
    '.search-result',
    'article',
    'li',
    '.item',
    '.card',
    'tr',
]


def _extract_value(node, field):
    field_type = field.type
    if field_type == 'html':
        return str(node)
    if field_type == 'href':
        return node.get('href')
    if field_type == 'src':
        return node.get('src')
    if field_type == 'attribute':
        return node.get(field.attribute_name or 'value')
    return node.get_text(' ', strip=True)


def _record_has_meaningful_value(record: dict) -> bool:
    for value in record.get('data', {}).values():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return True
    return False


def _container_has_required_signal(record: dict, config) -> bool:
    data = record.get('data', {})
    required_fields = [field for field in config.fields if field.required]
    if not required_fields:
        return _record_has_meaningful_value(record)
    satisfied = 0
    for field in required_fields:
        value = data.get(field.name)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        satisfied += 1
    return satisfied > 0


def _build_record(container, config, source_url: str, page_number: int) -> dict:
    data: dict = {}
    evidence: dict = {}
    warnings: list[str] = []
    for field in config.fields:
        node = container.select_one(field.selector) if field.selector else None
        raw_value = _extract_value(node, field) if node else None
        cleaned_value = clean_text(raw_value) if isinstance(raw_value, str) else raw_value
        if field.required and not cleaned_value:
            warnings.append(f'Missing required field: {field.name}')
        data[field.name] = cleaned_value
        evidence[field.name] = build_field_evidence(
            field_name=field.name,
            selector=field.selector,
            raw_value=raw_value if isinstance(raw_value, str) else None,
            cleaned_value=cleaned_value if isinstance(cleaned_value, str) else None,
            source_url=source_url,
            page_number=page_number,
            method='selector',
            confidence=1.0 if cleaned_value else 0.0,
            reason='Matched configured selector' if cleaned_value else 'Selector returned no value',
        )
    return {'data': data, 'evidence': evidence, 'warnings': warnings}


def _extract_with_selector(soup: BeautifulSoup, selector: str | None, config, source_url: str, page_number: int) -> list[dict]:
    containers = soup.select(selector) if selector else [soup]
    records = [_build_record(container, config, source_url, page_number) for container in containers]
    return [record for record in records if _record_has_meaningful_value(record)]


def _candidate_container_selectors(config) -> list[str | None]:
    selectors: list[str | None] = []
    if config.container_selector:
        selectors.append(config.container_selector)
    for selector in COMMON_FALLBACK_CONTAINERS:
        if selector != config.container_selector:
            selectors.append(selector)
    selectors.append(None)
    return selectors


def extract_records_from_html(html: str, config, source_url: str, page_number: int) -> list[dict]:
    soup = BeautifulSoup(html, 'lxml')
    best_records: list[dict] = []

    for selector in _candidate_container_selectors(config):
        records = _extract_with_selector(soup, selector, config, source_url, page_number)
        if not records:
            continue

        usable_records = [record for record in records if _container_has_required_signal(record, config)]
        if usable_records:
            return usable_records

        if not best_records:
            best_records = records

    return best_records


async def extract_records_from_page(page, config, page_number: int) -> list[dict]:
    html = await page.content()
    return extract_records_from_html(html, config, page.url, page_number)


def detect_failed_fields(record: dict, config) -> list[str]:
    failed: list[str] = []
    data = record.get('data', {})
    for field in config.fields:
        value = data.get(field.name)
        if not field.required:
            continue
        if value is None:
            failed.append(field.name)
            continue
        if isinstance(value, str) and not value.strip():
            failed.append(field.name)
            continue
        if field.name.lower() == 'price' and isinstance(value, str) and not any(char.isdigit() for char in value):
            failed.append(field.name)
    return failed
