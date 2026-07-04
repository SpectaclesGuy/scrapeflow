from __future__ import annotations

import json
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
        if provider == 'gemini' and self.settings.gemini_api_key:
            try:
                return await self._gemini_repair(cleaned_html_snippet, failed_fields, context)
            except Exception:
                return await self._mock_repair(cleaned_html_snippet, failed_fields)
        if provider in {'external_http', 'openai_compatible'} and self.settings.slm_api_url:
            try:
                return await self._external_repair(cleaned_html_snippet, failed_fields, context)
            except Exception:
                return await self._mock_repair(cleaned_html_snippet, failed_fields)
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

    async def _gemini_repair(self, cleaned_html_snippet: str, failed_fields: list[str], context: dict) -> dict:
        model = context.get('model') or self.settings.slm_model
        prompt = self._build_gemini_prompt(cleaned_html_snippet, failed_fields)
        payload = {
            'model': model,
            'messages': [
                {
                    'role': 'system',
                    'content': (
                        'You repair failed extraction fields from cleaned HTML snippets. '
                        'Return strict JSON only. Never hallucinate values. '
                        'Only recover values visible in the provided snippet.'
                    ),
                },
                {'role': 'user', 'content': prompt},
            ],
            'temperature': 0.1,
            'response_format': {'type': 'json_object'},
        }
        headers = {
            'Authorization': f'Bearer {self.settings.gemini_api_key}',
            'Content-Type': 'application/json',
        }
        url = f"{self.settings.gemini_base_url.rstrip('/')}/chat/completions"
        async with httpx.AsyncClient(timeout=self.settings.slm_timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        content = data['choices'][0]['message']['content']
        parsed = self._parse_json_payload(content)
        return self._normalize_repair_payload(parsed)

    def _build_gemini_prompt(self, cleaned_html_snippet: str, failed_fields: list[str]) -> str:
        return (
            'Return JSON with this shape: '
            '{"suggested_selectors": {"field": ".selector"}, '
            '"recovered_values": {"field": {"value": "text", "confidence": 0.7, "reason": "why"}}}.\n'
            'Rules:\n'
            '- Only include selectors that are likely valid CSS selectors from the snippet.\n'
            '- Only include recovered values that are present verbatim in the snippet text.\n'
            '- If uncertain, omit the field.\n\n'
            f'Failed fields: {failed_fields}\n\n'
            f'Cleaned HTML snippet:\n{cleaned_html_snippet}'
        )

    def _parse_json_payload(self, content: str) -> dict[str, Any]:
        text = content.strip()
        if text.startswith('```'):
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', text, flags=re.DOTALL)
            if not match:
                raise
            return json.loads(match.group(0))

    def _normalize_repair_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = SLMRepairResult()
        for field_name, selector in payload.get('suggested_selectors', {}).items():
            if selector:
                normalized.suggested_selectors[field_name] = str(selector)
        for field_name, recovered in payload.get('recovered_values', {}).items():
            value = recovered.get('value') if isinstance(recovered, dict) else None
            if not value:
                continue
            normalized.recovered_values[field_name] = RecoveredValue(
                value=str(value),
                confidence=float(recovered.get('confidence', 0.0) or 0.0),
                reason=str(recovered.get('reason', 'Gemini recovery')).strip(),
            )
        return normalized.model_dump()

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
                match = re.search(r'([\u20b9$\u20ac\u00a3?]\s?\d[\d,]*(?:\.\d{1,2})?)', text)
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
