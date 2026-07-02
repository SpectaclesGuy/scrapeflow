from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from app.config import get_settings


def _ensure_output_dirs() -> Path:
    base_dir = get_settings().output_path
    for child in ('json', 'csv', 'evidence'):
        (base_dir / child).mkdir(parents=True, exist_ok=True)
    return base_dir


def save_json(job_id: str, records: list[dict[str, Any]]) -> str:
    base_dir = _ensure_output_dirs()
    path = base_dir / 'json' / f'{job_id}.json'
    path.write_text(json.dumps(records, indent=2), encoding='utf-8')
    return str(path)


def save_csv(job_id: str, records: list[dict[str, Any]]) -> str:
    base_dir = _ensure_output_dirs()
    path = base_dir / 'csv' / f'{job_id}.csv'
    rows = [record.get('data', {}) for record in records]
    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if fieldnames:
            writer.writeheader()
            writer.writerows(rows)
    return str(path)


def save_evidence(job_id: str, records: list[dict[str, Any]]) -> str:
    base_dir = _ensure_output_dirs()
    path = base_dir / 'evidence' / f'{job_id}_evidence.json'
    evidence_payload = [record.get('evidence', {}) for record in records]
    path.write_text(json.dumps(evidence_payload, indent=2), encoding='utf-8')
    return str(path)
