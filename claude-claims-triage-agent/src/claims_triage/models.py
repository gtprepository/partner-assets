from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

IncidentType = Literal["auto", "property", "health", "liability", "other"]
Route = Literal["fast_track", "adjuster_review", "escalate_siu"]


class ExtractedClaim(BaseModel):
    claimant_name: Optional[str] = None
    policy_number: Optional[str] = None
    incident_date: Optional[str] = Field(None, description="ISO date, YYYY-MM-DD")
    incident_type: IncidentType = "other"
    loss_amount: Optional[float] = Field(None, description="Claimed loss in USD")
    summary: str = ""


class PolicyInfo(BaseModel):
    policy_number: str
    active: bool
    coverage_types: list[str]
    deductible: float
    limit: float


class TriageDecision(BaseModel):
    route: Route
    priority: int = Field(ge=1, le=3, description="1 = highest")
    reasons: list[str]


class DraftReply(BaseModel):
    subject: str
    body: str


class ClaimResult(BaseModel):
    claim_id: str
    extracted: ExtractedClaim
    policy: Optional[PolicyInfo]
    decision: TriageDecision
    reply: DraftReply
    status: Literal["pending_approval"] = "pending_approval"
