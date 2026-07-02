from __future__ import annotations

from bs4 import BeautifulSoup

from app.schemas.job_schema import JobUpdate
from app.schemas.result_schema import JobRunSummary
from app.schemas.scrape_schema import ScrapeJobConfig
from app.services.browser_service import get_page_with_browser, render_page
from app.services.evidence_service import build_field_evidence
from app.services.extraction_service import detect_failed_fields, extract_records_from_html, extract_records_from_page
from app.services.fetch_service import fetch_html
from app.services.pagination_service import generate_paginated_urls, paginate_with_browser
from app.services.schema_alignment_service import normalize_records_with_slm
from app.services.selector_repair_service import repair_failed_selectors
from app.services.storage_service import save_csv, save_evidence, save_json
from uuid import uuid4


def should_use_browser(html: str, config: ScrapeJobConfig) -> bool:
    lowered = html.lower()
    soup = BeautifulSoup(html, 'lxml')
    missing_container = bool(config.container_selector) and soup.select_one(config.container_selector) is None
    dynamic_markers = ['__next', 'id="root"', 'id="app"']
    visible_text_length = len(soup.get_text(' ', strip=True))
    script_count = lowered.count('<script')
    return missing_container or visible_text_length < 200 or script_count > 10 or any(marker in lowered for marker in dynamic_markers)


async def _apply_slm_repairs(records: list[dict], html: str, config: ScrapeJobConfig, source_url: str, page_number: int) -> list[dict]:
    repaired_records: list[dict] = []
    for record in records:
        failed_fields = detect_failed_fields(record, config)
        if not failed_fields or not config.slm.enabled:
            repaired_records.append(record)
            continue
        repair = await repair_failed_selectors(html, config, failed_fields)
        for field in config.fields:
            if field.name in repair['suggested_selectors']:
                field.selector = repair['suggested_selectors'][field.name]
        if repair['suggested_selectors']:
            retried = extract_records_from_html(html, config, source_url, page_number)
            if retried:
                record = retried[0]
        for field_name, recovered in repair['recovered_values'].items():
            record['data'][field_name] = recovered['value']
            record['evidence'][field_name] = build_field_evidence(
                field_name=field_name,
                selector=None,
                raw_value=recovered['value'],
                cleaned_value=recovered['value'],
                source_url=source_url,
                page_number=page_number,
                method='slm_fallback',
                confidence=recovered.get('confidence'),
                reason=recovered.get('reason'),
            )
        repaired_records.append(record)
    return repaired_records


async def run_scrape_job(config: ScrapeJobConfig, job=None, db=None) -> JobRunSummary:
    job_id = config.job_id or (job.id if job is not None else f'job_{uuid4().hex[:8]}')
    output_paths: dict[str, str] = {}
    all_records: list[dict] = []
    errors: list[str] = []
    pages_processed = 0

    if job is not None and db is not None:
        from app.services.job_service import update_job
        update_job(db, job, JobUpdate(status='running', progress=10, error_message=None))

    try:
        if config.mode == 'browser':
            page = await get_page_with_browser(config.target_url, config.browser.model_dump())
            pages = await paginate_with_browser(page, config)
            for page_number, browser_page in enumerate(pages, start=1):
                page_records = await extract_records_from_page(browser_page, config, page_number)
                html = await browser_page.content()
                all_records.extend(await _apply_slm_repairs(page_records, html, config, browser_page.url, page_number))
                pages_processed += 1
            await page._scrapeflow_browser.close()
            await page._scrapeflow_playwright.stop()
        else:
            urls = [config.target_url]
            if config.pagination.enabled and config.pagination.type == 'url_pattern' and config.pagination.url_pattern:
                urls = generate_paginated_urls(config.target_url, config.pagination.url_pattern, config.pagination.max_pages)
            for page_number, url in enumerate(urls, start=1):
                html = await fetch_html(url, timeout=max(1, config.browser.timeout // 1000))
                if config.mode == 'auto' and should_use_browser(html, config):
                    html = await render_page(url, config.browser.headless, config.browser.timeout)
                page_records = extract_records_from_html(html, config, url, page_number)
                all_records.extend(await _apply_slm_repairs(page_records, html, config, url, page_number))
                pages_processed += 1

        schema = {}
        for field in config.fields:
            schema[field.name] = 'string'
        normalized_records = await normalize_records_with_slm(all_records, schema)
        if 'json' in config.output.formats:
            output_paths['json'] = save_json(job_id, normalized_records)
        if 'csv' in config.output.formats:
            output_paths['csv'] = save_csv(job_id, normalized_records)
        if config.output.include_evidence:
            output_paths['evidence'] = save_evidence(job_id, normalized_records)
        summary = JobRunSummary(
            job_id=job_id,
            project_id=config.project_id,
            status='completed',
            pages_processed=pages_processed,
            records_found=len(normalized_records),
            output_paths=output_paths,
            records=normalized_records,
            errors=errors,
        )
        if job is not None and db is not None:
            from app.services.job_service import update_job
            update_job(
                db,
                job,
                JobUpdate(
                    status='completed',
                    progress=100,
                    pages_processed=pages_processed,
                    records_found=len(normalized_records),
                    result_location=output_paths.get('json'),
                    output_paths=output_paths,
                ),
            )
        return summary
    except Exception as exc:
        errors.append(str(exc))
        if job is not None and db is not None:
            from app.services.job_service import update_job
            update_job(db, job, JobUpdate(status='failed', progress=100, error_message=str(exc)))
        return JobRunSummary(
            job_id=job_id,
            project_id=config.project_id,
            status='failed',
            pages_processed=pages_processed,
            records_found=len(all_records),
            output_paths=output_paths,
            records=all_records,
            errors=errors,
        )
