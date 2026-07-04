from __future__ import annotations

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.job_schema import JobUpdate
from app.schemas.scrape_schema import ScrapeJobConfig
from app.services.job_service import get_job, update_job
from app.services.message_service import store_message
from app.services.scraper_service import run_scrape_job


async def run_job_background(job_id: str) -> None:
    db: Session = SessionLocal()
    try:
        job = get_job(db, job_id)
        if job is None or not job.config:
            return
        update_job(db, job, JobUpdate(status='running', progress=5, error_message=None))
        config = ScrapeJobConfig.model_validate(job.config)
        config.job_id = job.id
        config.project_id = job.project_id
        summary = await run_scrape_job(config, job=job, db=db)
        if job.conversation_id:
            if summary.status == 'completed':
                preview = ''
                if summary.records:
                    preview_data = (
                        summary.records[0].data
                        if hasattr(summary.records[0], 'data')
                        else summary.records[0].get('data', {})
                    )
                    preview = f"\nPreview: {preview_data}" if preview_data else ''
                store_message(
                    db,
                    conversation_id=job.conversation_id,
                    role='assistant',
                    content=f"Extraction completed in {summary.pages_processed} page(s). Records found: {summary.records_found}.{preview}",
                    metadata={'job_id': job.id, 'status': summary.status},
                    update_context=False,
                )
            else:
                store_message(
                    db,
                    conversation_id=job.conversation_id,
                    role='assistant',
                    content=f"Extraction failed: {'; '.join(summary.errors) or 'Unknown error'}",
                    metadata={'job_id': job.id, 'status': summary.status},
                    update_context=False,
                )
    finally:
        db.close()
