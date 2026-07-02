from __future__ import annotations

from datetime import UTC, datetime


def build_field_evidence(
    field_name: str,
    selector: str | None,
    raw_value: str | None,
    cleaned_value: str | None,
    source_url: str,
    page_number: int,
    method: str,
    confidence: float | None = None,
    reason: str | None = None,
) -> dict:
    return {
        'field': field_name,
        'selector': selector,
        'raw_value': raw_value,
        'cleaned_value': cleaned_value,
        'source_url': source_url,
        'page_number': page_number,
        'method': method,
        'confidence': confidence,
        'reason': reason,
        'extracted_at': datetime.now(UTC).isoformat(),
    }
