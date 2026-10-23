"""LLM backends. ClaudeLLM calls the Anthropic API; MockLLM is a deterministic
rule-based stand-in so the pipeline, tests and evaluation run offline."""
from __future__ import annotations

import os
import re
from typing import Protocol

from .models import DraftReply, ExtractedClaim, PolicyInfo, TriageDecision

DEFAULT_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")


class LLM(Protocol):
    def extract(self, text: str) -> ExtractedClaim: ...

    def draft_reply(
        self, claim: ExtractedClaim, policy: PolicyInfo | None, decision: TriageDecision
    ) -> DraftReply: ...


class ClaudeLLM:
    def __init__(self, model: str = DEFAULT_MODEL, client=None):
        if client is None:
            import anthropic

            client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
        self.client = client
        self.model = model

    def extract(self, text: str) -> ExtractedClaim:
        # A forced tool call returns schema-valid JSON, which pydantic re-validates.
        tool = {
            "name": "record_claim",
            "description": "Record the structured fields found in the claim document.",
            "input_schema": ExtractedClaim.model_json_schema(),
        }
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system="You extract fields from insurance claim documents. Use null for anything not stated. Never guess.",
            tools=[tool],
            tool_choice={"type": "tool", "name": "record_claim"},
            messages=[{"role": "user", "content": text}],
        )
        block = next(b for b in msg.content if b.type == "tool_use")
        return ExtractedClaim.model_validate(block.input)

    def draft_reply(self, claim, policy, decision) -> DraftReply:
        prompt = (
            "Draft a short, courteous acknowledgement email to the claimant. "
            "Do not state or imply approval, denial or payout amounts; a human adjuster will decide. "
            "Return the subject on the first line, then a blank line, then the body.\n\n"
            f"Claim: {claim.model_dump_json()}\nRoute: {decision.route}"
        )
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in msg.content if b.type == "text").strip()
        subject, _, body = text.partition("\n")
        return DraftReply(subject=subject.removeprefix("Subject:").strip(), body=body.strip())


class MockLLM:
    _TYPES = {
        "auto": ("car", "vehicle", "collision", "bumper", "windshield"),
        "property": ("house", "roof", "fire", "flood", "burst pipe", "storm"),
        "liability": ("sued", "lawsuit", "slipped", "liable", "third party"),
        "health": ("hospital", "surgery", "medical", "injury treatment"),
    }

    def extract(self, text: str) -> ExtractedClaim:
        low = text.lower()
        name = re.search(r"(?:claimant|name)\s*:\s*(.+)", text, re.I)
        pol = re.search(r"\b(POL-\d{4,})\b", text)
        date = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
        amt = re.search(r"\$\s?([\d,]+(?:\.\d+)?)", text)
        itype = next((t for t, kws in self._TYPES.items() if any(k in low for k in kws)), "other")
        return ExtractedClaim(
            claimant_name=name.group(1).strip() if name else None,
            policy_number=pol.group(1) if pol else None,
            incident_date=date.group(1) if date else None,
            incident_type=itype,
            loss_amount=float(amt.group(1).replace(",", "")) if amt else None,
            summary=" ".join(text.split())[:300],
        )

    def draft_reply(self, claim, policy, decision) -> DraftReply:
        who = claim.claimant_name or "Policyholder"
        return DraftReply(
            subject=f"We received your claim {claim.policy_number or ''}".strip(),
            body=(
                f"Dear {who},\n\nThank you for submitting your claim. It has been logged and "
                "assigned for review. A claims specialist will contact you within 2 business days "
                "if anything further is needed.\n\nRegards,\nClaims Team"
            ),
        )
