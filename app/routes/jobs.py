from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.job_schema import JobCreate, JobRead, JobUpdate
from app.schemas.scrape_schema import JobResultResponse, ScrapeJobConfig
from app.services.job_service import create_job, get_job, list_jobs, list_project_jobs, update_job
from app.services.scraper_service import run_scrape_job
from app.utils.response import success_response

router = APIRouter(tags=['jobs'])


@router.post('/jobs')
def create_job_route(payload: JobCreate, db: Session = Depends(get_db)) -> dict:
    try:
        job = create_job(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return success_response('Job created successfully', JobRead.model_validate(job).model_dump())


@router.get('/jobs')
def list_jobs_route(db: Session = Depends(get_db)) -> dict:
    jobs = [JobRead.model_validate(item).model_dump() for item in list_jobs(db)]
    return success_response('Jobs fetched successfully', jobs)


@router.get('/jobs/{job_id}')
def get_job_route(job_id: str, db: Session = Depends(get_db)) -> dict:
    job = get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Job not found')
    return success_response('Job fetched successfully', JobRead.model_validate(job).model_dump())


@router.patch('/jobs/{job_id}')
def patch_job_route(job_id: str, payload: JobUpdate, db: Session = Depends(get_db)) -> dict:
    job = get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Job not found')
    updated = update_job(db, job, payload)
    return success_response('Job updated successfully', JobRead.model_validate(updated).model_dump())


@router.get('/projects/{project_id}/jobs')
def list_project_jobs_route(project_id: str, db: Session = Depends(get_db)) -> dict:
    jobs = [JobRead.model_validate(item).model_dump() for item in list_project_jobs(db, project_id)]
    return success_response('Jobs fetched successfully', jobs)


@router.post('/jobs/{job_id}/run')
async def run_job_route(job_id: str, db: Session = Depends(get_db)) -> dict:
    job = get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Job not found')
    if not job.config:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Job has no config')
    config = ScrapeJobConfig.model_validate(job.config)
    config.job_id = job.id
    config.project_id = job.project_id
    summary = await run_scrape_job(config, job=job, db=db)
    return success_response('Job run completed', summary.model_dump())


@router.post('/jobs/{job_id}/retry')
async def retry_job_route(job_id: str, db: Session = Depends(get_db)) -> dict:
    job = get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Job not found')
    if not job.config:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Job has no config')
    updated = update_job(db, job, JobUpdate(status='queued', error_message=None, progress=0))
    config = ScrapeJobConfig.model_validate(updated.config)
    config.job_id = updated.id
    config.project_id = updated.project_id
    summary = await run_scrape_job(config, job=updated, db=db)
    return success_response('Job retried successfully', summary.model_dump())


@router.get('/jobs/{job_id}/results')
def get_job_results_route(job_id: str, db: Session = Depends(get_db)) -> dict:
    job = get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Job not found')
    records = []
    if job.result_location:
        import json
        from pathlib import Path

        path = Path(job.result_location)
        if path.exists():
            records = json.loads(path.read_text(encoding='utf-8'))[:20]
    payload = JobResultResponse(
        job_id=job.id,
        status=job.status,
        records=records,
        output_paths=job.output_paths or {},
    )
    return success_response('Job results fetched successfully', payload.model_dump())
