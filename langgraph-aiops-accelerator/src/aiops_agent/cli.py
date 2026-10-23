from __future__ import annotations

import argparse

from .diagnose import ClaudeDiagnoser, RuleDiagnoser
from .graph import build_graph, run_incident
from .tools import load_scenarios


def main() -> None:
    ap = argparse.ArgumentParser(prog="aiops-agent")
    ap.add_argument("--live", action="store_true", help="diagnose with Claude (needs ANTHROPIC_API_KEY)")
    ap.add_argument("--eval", action="store_true", help="score root-cause and action accuracy on the scenarios")
    ap.add_argument("--auto-approve", action="store_true", help="demo only: approve every proposed action (still dry-run)")
    a = ap.parse_args()

    graph = build_graph(ClaudeDiagnoser() if a.live else RuleDiagnoser(), dry_run=True)
    cause_hits = action_hits = 0
    scenarios = load_scenarios()
    for sc in scenarios:
        out = run_incident(graph, sc, sc["id"], approve=True if a.auto_approve else None, approver="demo")
        if "__interrupt__" in out:
            p = out["__interrupt__"][0].value
            print(f"{sc['id']}: PAUSED for approval -> {p['proposed_action']} on {p['service']} ({p['root_cause']})")
        else:
            print(out["report"], "\n")
        if a.eval:
            snap = graph.get_state({"configurable": {"thread_id": sc["id"]}}).values
            cause_hits += snap["diagnosis"]["root_cause"] == sc["expected"]["root_cause"]
            action_hits += snap["action"] == sc["expected"]["action"]
    if a.eval:
        n = len(scenarios)
        print(f"root_cause_accuracy={cause_hits / n:.0%} action_accuracy={action_hits / n:.0%} (n={n}, synthetic)")


if __name__ == "__main__":
    main()
