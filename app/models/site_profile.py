"""
SiteProfile model — the Planner's "memory" of how a given domain has behaved
in the past.

Uses Base, UUIDMixin, TimestampMixin from app/database.py exactly as their
other models do (id as String(36) UUID, created_at/updated_at handled
automatically by TimestampMixin) -- no need to redeclare those columns here.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin, UUIDMixin


class SiteProfile(UUIDMixin, TimestampMixin, Base):
    """
    One row per domain. This is the Task 1 deliverable: stores which
    scraping technique worked last, how often it's failing, and the
    threshold at which the Planner should stop trusting it and escalate.
    """

    __tablename__ = "site_profiles"

    # The lookup key — e.g. "example.com"
    domain: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    # Which rung of the extraction ladder worked last time (e.g. "dom_pattern_mining")
    last_successful_strategy: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Rolling counters
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)

    # Consecutive failures *since the last success* — compared against
    # error_threshold to decide whether to keep trusting last_successful_strategy
    # or force an escalation (the "repair flow" trigger)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)

    # How many consecutive failures are tolerated before giving up on the
    # known strategy. Configurable per-domain (some sites are flakier than others).
    error_threshold: Mapped[int] = mapped_column(Integer, default=3)

    # Optional quality signal from the last successful run
    avg_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    last_attempted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_succeeded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Per-strategy success/failure breakdown, e.g.
    # {"http_request": {"success": 0, "failure": 4}, "dom_pattern_mining": {"success": 12, "failure": 1}}
    strategy_history: Mapped[dict] = mapped_column(JSON, default=dict)