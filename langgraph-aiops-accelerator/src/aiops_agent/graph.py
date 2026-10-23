"""The incident-response graph.

alert -> gather_context -> diagnose -> propose -> (approval gate) -> execute -> report

Informational alerts and low-confidence diagnoses skip execution. Everything else
pauses at `approval` via a LangGraph interrupt until a human resumes the run.
"""
from __future__ import annotations

from typing import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from .diagnose import ACTION_FOR, Diagnoser
from .tools import Observability, execute_action

MIN_CONFIDENCE = 0.6


class State(TypedDict, total=False):
    scenario: dict
    logs: list[str]
    metrics: dict
    deploys: list[dict]
    diagnosis: dict
    action: str
    approved: bool
    approver: str
    execution: str
    report: str


def build_graph(diagnoser: Diagnoser, dry_run: bool = True):
    def gather_context(s: State) -> State:
        obs = Observability(s["scenario"])
        return {"logs": obs.logs(), "metrics": obs.metrics(), "deploys": obs.deploys()}

    def diagnose(s: State) -> State:
        d = diagnoser.diagnose(s["scenario"]["alert"], s["logs"], s["metrics"], s["deploys"])
        return {"diagnosis": dict(d)}

    def propose(s: State) -> State:
        d = s["diagnosis"]
        action = ACTION_FOR.get(d["root_cause"], "none") if d["confidence"] >= MIN_CONFIDENCE else "none"
        return {"action": action}

    def route_after_propose(s: State) -> str:
        if s["action"] == "none" or s["scenario"]["alert"]["severity"] == "info":
            return "report"
        return "approval"

    def approval(s: State) -> State:
        decision = interrupt({
            "service": s["scenario"]["alert"]["service"],
            "proposed_action": s["action"],
            "root_cause": s["diagnosis"]["root_cause"],
            "evidence": s["diagnosis"]["evidence"],
        })
        return {"approved": bool(decision.get("approve")), "approver": decision.get("approver", "")}

    def route_after_approval(s: State) -> str:
        return "execute" if s["approved"] else "report"

    def execute(s: State) -> State:
        return {"execution": execute_action(s["action"], s["scenario"]["alert"]["service"], dry_run)}

    def report(s: State) -> State:
        a = s["scenario"]["alert"]
        d = s["diagnosis"]
        if s.get("execution"):
            outcome = f"Executed after approval by {s.get('approver')}: {s['execution']}"
        elif s.get("approved") is False:
            outcome = "Proposed action rejected by human reviewer; no change made."
        else:
            outcome = "No automated action taken; left for on-call review."
        text = (
            f"[{a['severity'].upper()}] {a['service']}: {a['title']}\n"
            f"Root cause: {d['root_cause']} (confidence {d['confidence']:.0%})\n"
            f"Evidence: {'; '.join(d['evidence'])}\n{outcome}"
        )
        return {"report": text}

    g = StateGraph(State)
    for name, fn in [("gather_context", gather_context), ("diagnose", diagnose), ("propose", propose),
                     ("approval", approval), ("execute", execute), ("report", report)]:
        g.add_node(name, fn)
    g.add_edge(START, "gather_context")
    g.add_edge("gather_context", "diagnose")
    g.add_edge("diagnose", "propose")
    g.add_conditional_edges("propose", route_after_propose, {"approval": "approval", "report": "report"})
    g.add_conditional_edges("approval", route_after_approval, {"execute": "execute", "report": "report"})
    g.add_edge("execute", "report")
    g.add_edge("report", END)
    return g.compile(checkpointer=MemorySaver())


def run_incident(graph, scenario: dict, thread_id: str, approve: bool | None = None, approver: str = "oncall"):
    """Run to completion or to the approval gate. If `approve` is given and the run is
    paused, resume it with that decision."""
    cfg = {"configurable": {"thread_id": thread_id}}
    out = graph.invoke({"scenario": scenario}, cfg)
    if "__interrupt__" in out and approve is not None:
        out = graph.invoke(Command(resume={"approve": approve, "approver": approver}), cfg)
    return out
