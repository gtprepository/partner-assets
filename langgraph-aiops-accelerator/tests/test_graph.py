import pytest

from aiops_agent.diagnose import RuleDiagnoser
from aiops_agent.graph import build_graph, run_incident
from aiops_agent.tools import execute_action, load_scenarios

SCEN = {s["id"]: s for s in load_scenarios()}


@pytest.fixture
def graph():
    return build_graph(RuleDiagnoser(), dry_run=True)


def test_critical_incident_pauses_for_approval(graph):
    out = run_incident(graph, SCEN["S2"], "t1")
    assert out["__interrupt__"][0].value["proposed_action"] == "rollback_deploy"


def test_approved_action_executes_as_dry_run(graph):
    out = run_incident(graph, SCEN["S2"], "t2", approve=True, approver="alice")
    assert "dry-run" in out["execution"]
    assert "alice" in out["report"]


def test_rejected_action_is_not_executed(graph):
    out = run_incident(graph, SCEN["S1"], "t3", approve=False)
    assert "execution" not in out
    assert "rejected" in out["report"]


def test_info_alert_never_asks_to_act(graph):
    out = run_incident(graph, SCEN["S4"], "t4")
    assert "__interrupt__" not in out
    assert "No automated action" in out["report"]


def test_allowlist_blocks_unknown_actions():
    with pytest.raises(PermissionError):
        execute_action("drop_database", "checkout-api")


def test_rule_diagnoser_matches_all_scenarios(graph):
    for i, sc in SCEN.items():
        run_incident(graph, sc, f"e-{i}")
        v = graph.get_state({"configurable": {"thread_id": f"e-{i}"}}).values
        assert v["diagnosis"]["root_cause"] == sc["expected"]["root_cause"]
        assert v["action"] == sc["expected"]["action"]
