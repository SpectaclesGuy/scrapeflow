from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.project_schema import ProjectCreate, ProjectRead
from app.services.project_service import create_project, get_project, list_user_projects
from app.utils.response import success_response

router = APIRouter(tags=["projects"])


@router.post("/projects")
def create_project_route(payload: ProjectCreate, db: Session = Depends(get_db)) -> dict:
    try:
        project = create_project(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return success_response("Project created successfully", ProjectRead.model_validate(project).model_dump())


@router.get("/projects/{project_id}")
def get_project_route(project_id: str, db: Session = Depends(get_db)) -> dict:
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return success_response("Project fetched successfully", ProjectRead.model_validate(project).model_dump())


@router.get("/users/{user_id}/projects")
def list_projects_route(user_id: str, db: Session = Depends(get_db)) -> dict:
    projects = [ProjectRead.model_validate(item).model_dump() for item in list_user_projects(db, user_id)]
    return success_response("Projects fetched successfully", projects)
