"""
Pydantic v2 schemas for the Planner Agent.

JobSpecification is the INPUT contract (Task 3): this is the JSON shape the
Planner expects to receive — it should line up with what the Context Service
exposes as `project_context` (see their README: urls, domain, entity, fields,
filters, export_format). If their actual project_context schema differs once
you check app/schemas/ in the repo, adjust the field names here to match —
don't invent a second, incompatible contract.

WorkerAssignment / PlanResponse are the OUTPUT contract: what the Planner
hands downstream to the (future) Multi-Strategy Extraction Engine.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class StrategyName(str, Enum):
    HTTP_REQUEST = "http_request"
    METADATA_EXTRACTION = "metadata_extraction"
    API_DISCOVERY = "api_discovery"
    DOM_PATTERN_MINING = "dom_pattern_mining"
    LOCAL_LLM = "local_llm"
    HOSTED_LLM = "hosted_llm"
    BROWSER_AUTOMATION = "browser_automation"


# Cheapest → most expensive, matching the extraction ladder discussed earlier.
STRATEGY_LADDER: list[StrategyName] = [
    StrategyName.HTTP_REQUEST,
    StrategyName.METADATA_EXTRACTION,
    StrategyName.API_DISCOVERY,
    StrategyName.DOM_PATTERN_MINING,
    StrategyName.LOCAL_LLM,
    StrategyName.HOSTED_LLM,
    StrategyName.BROWSER_AUTOMATION,
]


class JobSpecification(BaseModel):
    """Input to the Planner — derived from project_context + latest message."""

    project_id: str
    urls: list[str] = Field(default_factory=list)
    domain: Optional[str] = None  # if already resolved upstream; else derived from urls
    entity: str
    fields: list[str]
    filters: dict = Field(default_factory=dict)
    export_format: Optional[str] = "csv"
    operation: str = "one_time"  # "one_time" | "scheduled"


class WorkerAssignment(BaseModel):
    """One domain's worker assignment within a plan."""

    domain: str
    assigned_strategy: StrategyName
    fallback_chain: list[StrategyName]
    reason: str  # human-readable: why this strategy was picked
    error_budget: int


class PlanResponse(BaseModel):
    """Output of the Planner — handed to the Extraction Engine."""

    project_id: str
    assignments: list[WorkerAssignment]


class OutcomeReport(BaseModel):
    """Sent back by the Extraction Engine after a job finishes, to update memory."""

    domain: str
    strategy: StrategyName
    success: bool
    confidence: Optional[float] = None