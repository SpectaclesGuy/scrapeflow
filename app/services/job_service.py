from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.job import Job
from app.models.project import Project
from app.schemas.job_schema import JobCreate, JobUpdate


def create_job(db: Session, payload: JobCreate) -> Job:
    project = db.get(Project, payload.project_id)
    if project is None:
        raise ValueError("Project not found")

    if payload.conversation_id:
        conversation = db.get(Conversation, payload.conversation_id)
        if conversation is None:
            raise ValueError("Conversation not found")

    job = Job(**payload.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: str) -> Job | None:
    return db.get(Job, job_id)


def update_job(db: Session, job: Job, payload: JobUpdate) -> Job:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(job, field, value)
    db.commit()
    db.refresh(job)
    return job


def list_project_jobs(db: Session, project_id: str) -> list[Job]:
    return db.query(Job).filter(Job.project_id == project_id).order_by(Job.created_at).all()
