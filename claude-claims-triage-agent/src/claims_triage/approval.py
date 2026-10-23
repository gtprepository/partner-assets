"""Human-in-the-loop gate and audit log. Nothing is sent without an approval record."""
from __future__ import annotations

import json
import time
from pathlib import Path

from .models import ClaimResult


class NotApproved(Exception):
    pass


class ApprovalQueue:
    def __init__(self, directory: Path):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.queue = self.dir / "queue.jsonl"
        self.audit = self.dir / "audit.jsonl"

    def _log(self, event: str, claim_id: str, **extra) -> None:
        rec = {"ts": time.time(), "event": event, "claim_id": claim_id, **extra}
        with self.audit.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")

    def submit(self, result: ClaimResult) -> None:
        with self.queue.open("a", encoding="utf-8") as f:
            f.write(result.model_dump_json() + "\n")
        self._log("queued", result.claim_id, route=result.decision.route)

    def _state(self) -> dict[str, str]:
        state: dict[str, str] = {}
        if self.audit.exists():
            for line in self.audit.read_text(encoding="utf-8").splitlines():
                r = json.loads(line)
                if r["event"] in ("approved", "rejected"):
                    state[r["claim_id"]] = r["event"]
        return state

    def decide(self, claim_id: str, reviewer: str, approve: bool, note: str = "") -> None:
        self._log("approved" if approve else "rejected", claim_id, reviewer=reviewer, note=note)

    def send(self, claim_id: str) -> str:
        if self._state().get(claim_id) != "approved":
            raise NotApproved(f"claim {claim_id} has no approval on record")
        self._log("sent", claim_id)
        return f"reply for {claim_id} released"
