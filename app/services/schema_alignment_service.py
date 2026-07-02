from __future__ import annotations

from app.services.slm_service import SLMService


async def normalize_records_with_slm(records: list[dict], expected_schema: dict) -> list[dict]:
    service = SLMService()
    normalized: list[dict] = []
    for record in records:
        data = record.get('data', {})
        aligned = await service.align_record_to_schema(data, expected_schema)
        updated = dict(record)
        updated['data'] = aligned
        normalized.append(updated)
    return normalized
