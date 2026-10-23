from __future__ import annotations

from .llm import LLM
from .models import ClaimResult
from .rules import triage
from .tools import PolicyLookup


class ClaimsAgent:
    def __init__(self, llm: LLM, policies: PolicyLookup | None = None):
        self.llm = llm
        self.policies = policies or PolicyLookup()

    def process(self, claim_id: str, text: str) -> ClaimResult:
        claim = self.llm.extract(text)
        policy = self.policies.get(claim.policy_number)
        decision = triage(claim, policy)
        reply = self.llm.draft_reply(claim, policy, decision)
        return ClaimResult(claim_id=claim_id, extracted=claim, policy=policy, decision=decision, reply=reply)
