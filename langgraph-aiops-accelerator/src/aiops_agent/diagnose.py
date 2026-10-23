"""Root-cause diagnosers. ClaudeDiagnoser uses the Anthropic API; RuleDiagnoser is a
deterministic offline stand-in for tests and evaluation."""
from __future__ import annotations

import os
from typing import Protocol, TypedDict

DEFAULT_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")
CAUSES = ["db_pool_exhaustion", "bad_deploy", "capacity_saturation", "unknown"]
ACTION_FOR = {
    "db_pool_exhaustion": "scale_db_pool",
    "bad_deploy": "rollback_deploy",
    "capacity_saturation": "scale_out_service",
    "unknown": "none",
}


class Diagnosis(TypedDict):
    root_cause: str
    confidence: float
    evidence: list[str]


class Diagnoser(Protocol):
    def diagnose(self, alert: dict, logs: list[str], metrics: dict, deploys: list[dict]) -> Diagnosis: ...


class RuleDiagnoser:
    def diagnose(self, alert, logs, metrics, deploys) -> Diagnosis:
        text = " ".join(logs).lower()
        recent = [d for d in deploys if d["minutes_ago"] <= 60]
        if "pool exhausted" in text or (
            metrics.get("db_connections_in_use") and metrics.get("db_connections_in_use") >= metrics.get("db_pool_size", 1 << 30)
        ):
            return {"root_cause": "db_pool_exhaustion", "confidence": 0.85,
                    "evidence": ["connection pool at capacity", "pool timeout errors in logs"]}
        if recent and metrics.get("error_rate_pct", 0) > 5:
            return {"root_cause": "bad_deploy", "confidence": 0.8,
                    "evidence": [f"deploy {recent[0]['version']} {recent[0]['minutes_ago']} min ago", "error rate elevated"]}
        if metrics.get("cpu_pct", 0) >= 90 and metrics.get("queue_depth", 0) > 10_000:
            return {"root_cause": "capacity_saturation", "confidence": 0.75,
                    "evidence": ["CPU saturated", "queue backlog growing"]}
        return {"root_cause": "unknown", "confidence": 0.3, "evidence": ["no matching pattern"]}


class ClaudeDiagnoser:
    def __init__(self, model: str = DEFAULT_MODEL, client=None):
        if client is None:
            import anthropic

            client = anthropic.Anthropic()
        self.client = client
        self.model = model

    def diagnose(self, alert, logs, metrics, deploys) -> Diagnosis:
        tool = {
            "name": "record_diagnosis",
            "description": "Record the most likely root cause with evidence.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "root_cause": {"type": "string", "enum": CAUSES},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["root_cause", "confidence", "evidence"],
            },
        }
        prompt = (
            "You are an SRE assistant. Pick the most likely root cause from the allowed list; "
            "use 'unknown' when evidence is weak. Cite evidence from the data only.\n\n"
            f"Alert: {alert}\nLogs: {logs}\nMetrics: {metrics}\nRecent deploys: {deploys}"
        )
        msg = self.client.messages.create(
            model=self.model, max_tokens=600, tools=[tool],
            tool_choice={"type": "tool", "name": "record_diagnosis"},
            messages=[{"role": "user", "content": prompt}],
        )
        block = next(b for b in msg.content if b.type == "tool_use")
        return block.input
