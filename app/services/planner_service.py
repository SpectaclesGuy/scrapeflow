"""
Planner Agent service.

This is where Task 1 (store metadata) and Task 2 (assign workers dynamically)
actually live.

- get_or_create_profile / record_outcome  -> Task 1 (metadata storage)
- assign_worker_for_domain / build_plan    -> Task 2 (dynamic worker assignment)

Per their README: "Planner Agent can replace the temporary rule-based updater
in app/services/context_service.py" — build_plan() is the function intended
to be called wherever that hand-off happens, once project_context is ready.
"""

from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models.site_profile import SiteProfile
from app.schemas.planner import (
    JobSpecification,
    PlanResponse,
    StrategyName,
    WorkerAssignment,
    STRATEGY_LADDER,
)


def _extract_domain(url: str) -> str:
    """Pull just the domain out of a full URL, e.g. https://x.com/a -> x.com"""
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


# ---------------------------------------------------------------------------
# Task 1: metadata storage
# ---------------------------------------------------------------------------

def get_or_create_profile(db: Session, domain: str) -> SiteProfile:
    """Fetch a domain's stored memory, creating a fresh blank record if unseen."""
    profile = db.query(SiteProfile).filter(SiteProfile.domain == domain).first()
    if profile is None:
        profile = SiteProfile(domain=domain)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def record_outcome(
    db: Session,
    domain: str,
    strategy: StrategyName,
    success: bool,
    confidence: Optional[float] = None,
) -> SiteProfile:
    """
    Called by the Extraction Engine after a job finishes for a domain.
    Updates rolling success/failure stats and decides whether the
    "known working strategy" should still be trusted.
    """
    profile = get_or_create_profile(db, domain)
    profile.last_attempted_at = datetime.now(timezone.utc)

    history = dict(profile.strategy_history or {})
    stats = history.get(strategy.value, {"success": 0, "failure": 0})

    if success:
        stats["success"] += 1
        profile.success_count += 1
        profile.consecutive_failures = 0  # reset — strategy proved itself again
        profile.last_successful_strategy = strategy.value
        profile.last_succeeded_at = datetime.now(timezone.utc)
        if confidence is not None:
            profile.avg_confidence = confidence
    else:
        stats["failure"] += 1
        profile.failure_count += 1
        profile.consecutive_failures += 1

    history[strategy.value] = stats
    profile.strategy_history = history

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


# ---------------------------------------------------------------------------
# Task 2: dynamic worker assignment
# ---------------------------------------------------------------------------

def _next_strategy_after(strategy_value: Optional[str]) -> StrategyName:
    """Escalate one rung up the ladder from the given strategy."""
    if strategy_value is None:
        return STRATEGY_LADDER[0]
    try:
        idx = STRATEGY_LADDER.index(StrategyName(strategy_value))
    except ValueError:
        return STRATEGY_LADDER[0]
    return STRATEGY_LADDER[min(idx + 1, len(STRATEGY_LADDER) - 1)]


def assign_worker_for_domain(db: Session, domain: str) -> WorkerAssignment:
    """
    The core dynamic-assignment decision. Three cases:

    1. Never seen this domain  -> start at the cheapest rung, full ladder available.
    2. Known strategy is broken (consecutive_failures >= error_threshold)
       -> don't trust it anymore, escalate past it.
    3. Known strategy still works -> skip straight to it, no wasted attempts.
    """
    profile = get_or_create_profile(db, domain)

    if profile.last_successful_strategy is None:
        return WorkerAssignment(
            domain=domain,
            assigned_strategy=STRATEGY_LADDER[0],
            fallback_chain=STRATEGY_LADDER,
            reason="unknown_domain_start_of_ladder",
            error_budget=profile.error_threshold,
        )

    if profile.consecutive_failures >= profile.error_threshold:
        escalated = _next_strategy_after(profile.last_successful_strategy)
        start_idx = STRATEGY_LADDER.index(escalated)
        return WorkerAssignment(
            domain=domain,
            assigned_strategy=escalated,
            fallback_chain=STRATEGY_LADDER[start_idx:],
            reason="error_threshold_exceeded_escalating",
            error_budget=profile.error_threshold,
        )

    known = StrategyName(profile.last_successful_strategy)
    start_idx = STRATEGY_LADDER.index(known)
    return WorkerAssignment(
        domain=domain,
        assigned_strategy=known,
        fallback_chain=STRATEGY_LADDER[start_idx:],
        reason="reusing_known_working_strategy",
        error_budget=profile.error_threshold,
    )


def build_plan(db: Session, job_spec: JobSpecification) -> PlanResponse:
    """
    Top-level entry point: takes the JSON job specification (Task 3) and
    returns a full plan covering every domain referenced by the job.
    """
    if job_spec.domain:
        domains = {job_spec.domain}
    else:
        domains = {_extract_domain(u) for u in job_spec.urls if u}

    assignments = [assign_worker_for_domain(db, d) for d in domains if d]
    return PlanResponse(project_id=job_spec.project_id, assignments=assignments)