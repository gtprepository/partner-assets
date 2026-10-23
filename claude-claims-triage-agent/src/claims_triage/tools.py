"""Policy lookup. The same function backs the in-process call and the MCP server."""
from __future__ import annotations

import json
from pathlib import Path

from .models import PolicyInfo

DATA = Path(__file__).resolve().parents[2] / "data"


def load_policies(path: Path | None = None) -> dict[str, PolicyInfo]:
    raw = json.loads((path or DATA / "policies.json").read_text(encoding="utf-8"))
    return {p["policy_number"]: PolicyInfo(**p) for p in raw}


class PolicyLookup:
    def __init__(self, policies: dict[str, PolicyInfo] | None = None):
        self.policies = policies if policies is not None else load_policies()

    def get(self, policy_number: str | None) -> PolicyInfo | None:
        return self.policies.get(policy_number) if policy_number else None
