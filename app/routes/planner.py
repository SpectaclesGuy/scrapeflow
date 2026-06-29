"""
Planner API routes.

NOTE ON IMPORTS: adjust `get_db` below to match wherever your teammates
defined the DB session dependency (likely app/database.py — check how
their other routers, e.g. app/routes/projects.py or similar, import it,
and mirror that exactly).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db  # <-- ADJUST to match actual session dependency
from app.schemas.planner import JobSpecification, OutcomeReport, PlanResponse
from app.services import planner_service

router = APIRouter(prefix="/planner", tags=["planner"])


@router.post("/plan", response_model=PlanResponse)
def create_plan(job_spec: JobSpecification, db: Session = Depends(get_db)):
    """
    Takes a job specification (the JSON derived from project_context) and
    returns a worker assignment plan — one assignment per domain involved.
    """
    return planner_service.build_plan(db, job_spec)


@router.post("/outcome")
def report_outcome(report: OutcomeReport, db: Session = Depends(get_db)):
    """
    Called by the Extraction Engine after a job finishes, so the Planner's
    memory stays current for future requests against the same domain.
    """
    profile = planner_service.record_outcome(
        db, report.domain, report.strategy, report.success, report.confidence
    )
    return {
        "domain": profile.domain,
        "last_successful_strategy": profile.last_successful_strategy,
        "consecutive_failures": profile.consecutive_failures,
        "success_count": profile.success_count,
        "failure_count": profile.failure_count,
    }


@router.get("/profile/{domain}")
def get_profile(domain: str, db: Session = Depends(get_db)):
    """Inspect what the Planner currently knows about a domain."""
    profile = planner_service.get_or_create_profile(db, domain)
    return {
        "domain": profile.domain,
        "last_successful_strategy": profile.last_successful_strategy,
        "success_count": profile.success_count,
        "failure_count": profile.failure_count,
        "consecutive_failures": profile.consecutive_failures,
        "error_threshold": profile.error_threshold,
        "strategy_history": profile.strategy_history,
    }