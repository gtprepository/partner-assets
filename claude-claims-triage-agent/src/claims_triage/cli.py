from __future__ import annotations

import argparse
from pathlib import Path

from .agent import ClaimsAgent
from .approval import ApprovalQueue
from .evaluate import evaluate
from .llm import ClaudeLLM, MockLLM


def main() -> None:
    ap = argparse.ArgumentParser(prog="claims-triage")
    ap.add_argument("--live", action="store_true", help="use the Claude API (needs ANTHROPIC_API_KEY); default is offline mock")
    ap.add_argument("--eval", action="store_true", help="run the labelled evaluation")
    ap.add_argument("--file", type=Path, help="process one claim text file and queue it for approval")
    ap.add_argument("--runtime", type=Path, default=Path("runtime"))
    a = ap.parse_args()

    agent = ClaimsAgent(ClaudeLLM() if a.live else MockLLM())
    if a.eval:
        r = evaluate(agent)
        print(f"claims={r['claims']} field_accuracy={r['field_accuracy']:.1%} "
              f"route_accuracy={r['route_accuracy']:.1%} avg_latency={r['avg_latency_s']*1000:.0f}ms")
        for m in r["misses"]:
            print("  miss:", m)
    if a.file:
        res = agent.process(a.file.stem, a.file.read_text(encoding="utf-8"))
        ApprovalQueue(a.runtime).submit(res)
        print(res.model_dump_json(indent=2))
        print(f"\nQueued for human approval in {a.runtime}/queue.jsonl. Nothing has been sent.")


if __name__ == "__main__":
    main()
