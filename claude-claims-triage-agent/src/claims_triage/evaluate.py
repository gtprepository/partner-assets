"""Scores the agent against the labelled synthetic set in data/claims.jsonl."""
from __future__ import annotations

import json
import time
from pathlib import Path

from .agent import ClaimsAgent
from .tools import DATA

FIELDS = ("policy_number", "incident_date", "incident_type", "loss_amount")


def evaluate(agent: ClaimsAgent, path: Path | None = None) -> dict:
    lines = (path or DATA / "claims.jsonl").read_text(encoding="utf-8").splitlines()
    rows = [json.loads(l) for l in lines if l.strip()]
    field_hits = field_total = route_hits = 0
    latencies, misses = [], []
    for r in rows:
        t0 = time.perf_counter()
        res = agent.process(r["id"], r["text"])
        latencies.append(time.perf_counter() - t0)
        for f in FIELDS:
            field_total += 1
            if getattr(res.extracted, f) == r["expected"][f]:
                field_hits += 1
            else:
                misses.append((r["id"], f, getattr(res.extracted, f), r["expected"][f]))
        if res.decision.route == r["expected"]["route"]:
            route_hits += 1
        else:
            misses.append((r["id"], "route", res.decision.route, r["expected"]["route"]))
    return {
        "claims": len(rows),
        "field_accuracy": field_hits / field_total,
        "route_accuracy": route_hits / len(rows),
        "avg_latency_s": sum(latencies) / len(latencies),
        "misses": misses,
    }
