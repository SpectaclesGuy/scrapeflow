"""
Tests for the Planner Agent.

These use an in-memory SQLite DB so you can run them immediately, without
needing your real Postgres `scrapeflow_context` DB set up yet. Once you've
copied these files into the actual repo, you can also add an integration
test that goes through the real `get_db` dependency + Postgres.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base  # <-- ADJUST to match actual Base location
from app.models.site_profile import SiteProfile  # noqa: F401 (ensures table is registered)
from app.schemas.planner import JobSpecification, StrategyName
from app.services import planner_service


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    yield session
    session.close()


def test_unknown_domain_starts_at_top_of_ladder(db_session):
    assignment = planner_service.assign_worker_for_domain(db_session, "example.com")
    assert assignment.assigned_strategy == StrategyName.HTTP_REQUEST
    assert assignment.reason == "unknown_domain_start_of_ladder"
    assert len(assignment.fallback_chain) == 7


def test_known_working_strategy_is_reused(db_session):
    planner_service.record_outcome(
        db_session, "shop.example.com", StrategyName.DOM_PATTERN_MINING, success=True
    )
    assignment = planner_service.assign_worker_for_domain(db_session, "shop.example.com")
    assert assignment.assigned_strategy == StrategyName.DOM_PATTERN_MINING
    assert assignment.reason == "reusing_known_working_strategy"
    # fallback chain should start from the known strategy onward, not the whole ladder
    assert assignment.fallback_chain[0] == StrategyName.DOM_PATTERN_MINING


def test_escalates_after_error_threshold_exceeded(db_session):
    domain = "flaky.example.com"
    planner_service.record_outcome(db_session, domain, StrategyName.HTTP_REQUEST, success=True)

    # default error_threshold is 3 -> three consecutive failures should trigger escalation
    for _ in range(3):
        planner_service.record_outcome(db_session, domain, StrategyName.HTTP_REQUEST, success=False)

    assignment = planner_service.assign_worker_for_domain(db_session, domain)
    assert assignment.assigned_strategy == StrategyName.METADATA_EXTRACTION
    assert assignment.reason == "error_threshold_exceeded_escalating"


def test_a_single_success_resets_consecutive_failures(db_session):
    domain = "recovering.example.com"
    planner_service.record_outcome(db_session, domain, StrategyName.API_DISCOVERY, success=True)
    planner_service.record_outcome(db_session, domain, StrategyName.API_DISCOVERY, success=False)
    planner_service.record_outcome(db_session, domain, StrategyName.API_DISCOVERY, success=True)

    profile = planner_service.get_or_create_profile(db_session, domain)
    assert profile.consecutive_failures == 0
    assert profile.last_successful_strategy == StrategyName.API_DISCOVERY.value


def test_build_plan_handles_multiple_domains_in_one_job(db_session):
    job_spec = JobSpecification(
        project_id="proj-1",
        urls=["https://a.example.com/page", "https://b.example.com/page"],
        entity="product",
        fields=["name", "price"],
    )
    plan = planner_service.build_plan(db_session, job_spec)
    domains_in_plan = {a.domain for a in plan.assignments}
    assert domains_in_plan == {"a.example.com", "b.example.com"}