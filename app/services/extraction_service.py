from __future__ import annotations

from bs4 import BeautifulSoup

from app.core.text_cleaner import clean_text
from app.services.evidence_service import build_field_evidence


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


def extract_records_from_html(html: str, config, source_url: str, page_number: int) -> list[dict]:
    soup = BeautifulSoup(html, 'lxml')
    containers = soup.select(config.container_selector) if config.container_selector else [soup]
    records: list[dict] = []
    for container in containers:
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
        records.append({'data': data, 'evidence': evidence, 'warnings': warnings})
    return records


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
