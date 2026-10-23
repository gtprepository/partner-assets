import pytest

from claims_triage.agent import ClaimsAgent
from claims_triage.approval import ApprovalQueue, NotApproved
from claims_triage.evaluate import evaluate
from claims_triage.llm import MockLLM


@pytest.fixture
def agent():
    return ClaimsAgent(MockLLM())


def test_eval_set_scores_perfectly_with_mock(agent):
    r = evaluate(agent)
    assert r["claims"] == 8
    assert r["misses"] == []


def test_inactive_policy_never_fast_tracked(agent):
    res = agent.process("x", "Claimant: A B\nPOL-10003\n2026-06-11 car collision $500")
    assert res.decision.route == "adjuster_review"
    assert "policy inactive" in res.decision.reasons


def test_fraud_phrase_escalates_even_for_small_amount(agent):
    res = agent.process("x", "Claimant: A B\nPOL-10001\n2026-06-11 car collision $300, cash only")
    assert res.decision.route == "escalate_siu"


def test_reply_never_sent_without_approval(agent, tmp_path):
    q = ApprovalQueue(tmp_path)
    res = agent.process("C1", "Claimant: A B\nPOL-10001\n2026-06-11 car collision $300")
    q.submit(res)
    with pytest.raises(NotApproved):
        q.send("C1")
    q.decide("C1", reviewer="adjuster1", approve=True)
    assert "released" in q.send("C1")


def test_rejected_claim_cannot_be_sent(agent, tmp_path):
    q = ApprovalQueue(tmp_path)
    q.submit(agent.process("C2", "Claimant: A B\nPOL-10001\n2026-06-11 car collision $300"))
    q.decide("C2", reviewer="adjuster1", approve=False, note="needs call")
    with pytest.raises(NotApproved):
        q.send("C2")
