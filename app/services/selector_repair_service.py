from __future__ import annotations

from bs4 import BeautifulSoup

from app.services.preprocessing_service import preprocess_html_for_slm
from app.services.slm_service import SLMService


async def repair_failed_selectors(html: str, config, failed_fields: list[str]) -> dict:
    cleaned = preprocess_html_for_slm(html, config, failed_fields, config.slm.max_input_chars)
    service = SLMService()
    result = await service.repair_extraction(
        cleaned,
        failed_fields,
        {'provider': config.slm.provider, 'model': config.slm.model},
    )
    soup = BeautifulSoup(cleaned, 'lxml')
    valid_selectors: dict[str, str] = {}
    for field_name, selector in result.get('suggested_selectors', {}).items():
        if selector and soup.select_one(selector):
            valid_selectors[field_name] = selector
    valid_values: dict = {}
    text = soup.get_text(' ', strip=True)
    for field_name, recovered in result.get('recovered_values', {}).items():
        value = recovered.get('value')
        if value and value in text:
            valid_values[field_name] = recovered
    return {'suggested_selectors': valid_selectors, 'recovered_values': valid_values, 'cleaned_html': cleaned}
