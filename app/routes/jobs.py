from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.job_schema import JobCreate, JobRead, JobUpdate
from app.services.job_service import create_job, get_job, list_project_jobs, update_job
from app.utils.response import success_response

router = APIRouter(tags=["jobs"])


@router.post("/jobs")
def create_job_route(payload: JobCreate, db: Session = Depends(get_db)) -> dict:
    try:
        job = create_job(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return success_response("Job created successfully", JobRead.model_validate(job).model_dump())


@router.get("/jobs/{job_id}")
def get_job_route(job_id: str, db: Session = Depends(get_db)) -> dict:
    job = get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return success_response("Job fetched successfully", JobRead.model_validate(job).model_dump())


@router.patch("/jobs/{job_id}")
def patch_job_route(job_id: str, payload: JobUpdate, db: Session = Depends(get_db)) -> dict:
    job = get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    updated = update_job(db, job, payload)
    return success_response("Job updated successfully", JobRead.model_validate(updated).model_dump())


@router.get("/projects/{project_id}/jobs")
def list_jobs_route(project_id: str, db: Session = Depends(get_db)) -> dict:
    jobs = [JobRead.model_validate(item).model_dump() for item in list_project_jobs(db, project_id)]
    return success_response("Jobs fetched successfully", jobs)
