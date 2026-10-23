"""Deterministic triage rules. Kept out of the LLM on purpose so every routing
decision is explainable and auditable."""
from __future__ import annotations

from .models import ExtractedClaim, PolicyInfo, TriageDecision

FAST_TRACK_MAX = 2_000.0
SIU_THRESHOLD = 25_000.0
FRAUD_PHRASES = ("prior similar claim", "no police report", "cash only", "unwitnessed")


def triage(claim: ExtractedClaim, policy: PolicyInfo | None) -> TriageDecision:
    reasons: list[str] = []
    text = claim.summary.lower()

    if any(p in text for p in FRAUD_PHRASES):
        reasons.append("fraud indicator phrase in claim text")
    if claim.loss_amount and claim.loss_amount >= SIU_THRESHOLD:
        reasons.append(f"loss amount {claim.loss_amount:,.0f} at or above SIU threshold")
    if reasons:
        return TriageDecision(route="escalate_siu", priority=1, reasons=reasons)

    if policy is None:
        return TriageDecision(route="adjuster_review", priority=2, reasons=["policy not found or missing"])
    if not policy.active:
        return TriageDecision(route="adjuster_review", priority=2, reasons=["policy inactive"])
    if claim.incident_type not in policy.coverage_types:
        return TriageDecision(
            route="adjuster_review", priority=2,
            reasons=[f"incident type '{claim.incident_type}' not in covered types"],
        )
    if claim.loss_amount is None:
        return TriageDecision(route="adjuster_review", priority=3, reasons=["loss amount missing"])
    if claim.loss_amount > policy.limit:
        return TriageDecision(route="adjuster_review", priority=2, reasons=["loss exceeds policy limit"])
    if claim.loss_amount <= FAST_TRACK_MAX:
        return TriageDecision(route="fast_track", priority=3, reasons=["covered, active policy, low value"])
    return TriageDecision(route="adjuster_review", priority=3, reasons=["covered claim above fast-track value"])
