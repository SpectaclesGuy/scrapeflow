from pydantic import BaseModel, Field


class RecoveredValue(BaseModel):
    value: str | None = None
    confidence: float | None = None
    reason: str | None = None


class SLMRepairResult(BaseModel):
    suggested_selectors: dict[str, str] = Field(default_factory=dict)
    recovered_values: dict[str, RecoveredValue] = Field(default_factory=dict)
