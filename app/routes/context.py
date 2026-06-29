from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.context_schema import ProjectContextRead, ProjectContextUpdate
from app.services.context_service import get_context, patch_context, replace_context
from app.utils.response import success_response

router = APIRouter(tags=["context"])


@router.get("/projects/{project_id}/context")
def get_project_context(project_id: str, db: Session = Depends(get_db)) -> dict:
    context = get_context(db, project_id)
    if context is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project context not found")
    return success_response(
        "Project context fetched successfully",
        ProjectContextRead.model_validate(context).model_dump(),
    )


@router.put("/projects/{project_id}/context")
def replace_project_context(project_id: str, payload: ProjectContextUpdate, db: Session = Depends(get_db)) -> dict:
    context = get_context(db, project_id)
    if context is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project context not found")
    updated = replace_context(db, context, payload)
    return success_response(
        "Project context replaced successfully",
        ProjectContextRead.model_validate(updated).model_dump(),
    )


@router.patch("/projects/{project_id}/context")
def patch_project_context(project_id: str, payload: ProjectContextUpdate, db: Session = Depends(get_db)) -> dict:
    context = get_context(db, project_id)
    if context is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project context not found")
    updated = patch_context(db, context, payload)
    return success_response(
        "Project context updated successfully",
        ProjectContextRead.model_validate(updated).model_dump(),
    )
