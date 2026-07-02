from __future__ import annotations

import re
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.config import get_settings
from app.schemas.slm_schema import RecoveredValue, SLMRepairResult


class SLMService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def suggest_selectors(self, cleaned_html_snippet: str, fields: list[dict[str, Any]]) -> dict:
        soup = BeautifulSoup(cleaned_html_snippet, 'lxml')
        suggestions: dict[str, str] = {}
        for field in fields:
            name = field['name'].lower()
            if name in {'title', 'name'}:
                for selector in ('h1', 'h2', 'h3', '.product-title', '.title', '.name'):
                    if soup.select_one(selector):
                        suggestions[field['name']] = selector
                        break
            if name == 'price':
                for selector in ('.product-price', '.price', '.wrong-price-class'):
                    if soup.select_one(selector):
                        suggestions[field['name']] = selector
                        break
            if name == 'rating':
                for selector in ('.rating', '[class*=rating]'):
                    if soup.select_one(selector):
                        suggestions[field['name']] = selector
                        break
        return suggestions

    async def repair_extraction(self, cleaned_html_snippet: str, failed_fields: list[str], context: dict) -> dict:
        provider = context.get('provider') or self.settings.slm_provider
        if provider == 'mock' or not self.settings.slm_api_url:
            return await self._mock_repair(cleaned_html_snippet, failed_fields)
        try:
            return await self._external_repair(cleaned_html_snippet, failed_fields, context)
        except Exception:
            return await self._mock_repair(cleaned_html_snippet, failed_fields)

    async def align_record_to_schema(self, raw_record: dict, schema: dict) -> dict:
        data = dict(raw_record)
        for field_name, field_type in schema.items():
            value = data.get(field_name)
            if value is None:
                continue
            if field_type == 'int':
                match = re.search(r'\d+', str(value))
                data[field_name] = int(match.group()) if match else None
            elif field_type == 'string':
                data[field_name] = str(value).strip()
        return data

    async def _external_repair(self, cleaned_html_snippet: str, failed_fields: list[str], context: dict) -> dict:
        payload = {
            'model': context.get('model') or self.settings.slm_model,
            'task': 'repair_extraction',
            'html': cleaned_html_snippet,
            'failed_fields': failed_fields,
            'context': context,
        }
        headers = {}
        if self.settings.slm_api_key:
            headers['Authorization'] = f'Bearer {self.settings.slm_api_key}'
        async with httpx.AsyncClient(timeout=self.settings.slm_timeout) as client:
            response = await client.post(self.settings.slm_api_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    async def _mock_repair(self, cleaned_html_snippet: str, failed_fields: list[str]) -> dict:
        result = SLMRepairResult()
        selector_suggestions = await self.suggest_selectors(
            cleaned_html_snippet,
            [{'name': field_name} for field_name in failed_fields],
        )
        result.suggested_selectors.update(selector_suggestions)
        text = BeautifulSoup(cleaned_html_snippet, 'lxml').get_text(' ', strip=True)
        for field_name in failed_fields:
            lowered = field_name.lower()
            if lowered == 'price':
                match = re.search(r'([\u20b9$\u20ac\u00a3]\s?\d[\d,]*(?:\.\d{1,2})?)', text)
                if match:
                    result.recovered_values[field_name] = RecoveredValue(
                        value=match.group(1),
                        confidence=0.72,
                        reason='Detected currency-like value near product title',
                    )
            elif lowered == 'rating':
                match = re.search(r'(\d(?:\.\d)?)\s*(?:out of 5|stars?)?', text, flags=re.IGNORECASE)
                if match:
                    result.recovered_values[field_name] = RecoveredValue(
                        value=match.group(1),
                        confidence=0.68,
                        reason='Detected rating-like value in visible text',
                    )
            elif lowered in {'title', 'name'}:
                soup = BeautifulSoup(cleaned_html_snippet, 'lxml')
                node = soup.select_one('h1, h2, h3, .product-title, .title, .name')
                if node:
                    result.recovered_values[field_name] = RecoveredValue(
                        value=node.get_text(' ', strip=True),
                        confidence=0.66,
                        reason='Detected likely heading node',
                    )
        return result.model_dump()
