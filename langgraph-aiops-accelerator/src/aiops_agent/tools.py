"""Observability and remediation tools. Backed by fixtures here; swap the bodies for
Datadog, CloudWatch, Prometheus or Kubernetes calls in a real engagement."""
from __future__ import annotations

import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data"

# Only these actions can ever be executed. Anything else a model proposes is refused.
ALLOWED_ACTIONS = {"scale_db_pool", "rollback_deploy", "scale_out_service", "none"}


def load_scenarios() -> list[dict]:
    return json.loads((DATA / "scenarios.json").read_text(encoding="utf-8"))


class Observability:
    def __init__(self, scenario: dict):
        self.s = scenario

    def logs(self) -> list[str]:
        return self.s["logs"]

    def metrics(self) -> dict:
        return self.s["metrics"]

    def deploys(self) -> list[dict]:
        return self.s["recent_deploys"]


def execute_action(action: str, service: str, dry_run: bool = True) -> str:
    if action not in ALLOWED_ACTIONS:
        raise PermissionError(f"action '{action}' is not on the allowlist")
    if action == "none":
        return "no action required"
    prefix = "[dry-run] would run" if dry_run else "ran"
    return f"{prefix} {action} on {service}"
