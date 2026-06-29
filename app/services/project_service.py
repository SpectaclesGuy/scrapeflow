from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_context import ProjectContext
from app.models.user import User
from app.schemas.project_schema import ProjectCreate


def create_project(db: Session, payload: ProjectCreate) -> Project:
    user = db.get(User, payload.user_id)
    if user is None:
        raise ValueError("User not found")

    project = Project(**payload.model_dump())
    db.add(project)
    db.flush()

    context = ProjectContext(project_id=project.id, fields=[], filters=[])
    db.add(context)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id: str) -> Project | None:
    return db.get(Project, project_id)


def list_user_projects(db: Session, user_id: str) -> list[Project]:
    return db.query(Project).filter(Project.user_id == user_id).order_by(Project.created_at).all()
