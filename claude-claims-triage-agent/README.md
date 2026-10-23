# Claude Claims Triage Agent (reference build)

A small, runnable reference for document-heavy workflows with Claude: extract fields from a claim, look up the policy over MCP, route with auditable rules, draft a reply, and hold everything for human approval.

Status: internal demo asset. It is not a client deployment and carries no partner endorsement.

## What it shows

| Step | How |
|---|---|
| Structured extraction | Claude forced tool call (`record_claim`) validated by pydantic |
| Policy lookup | Plain function, also exposed as an MCP server (`mcp_server.py`) |
| Routing | Deterministic rules in `rules.py` (fast track, adjuster review, SIU escalation) with recorded reasons |
| Reply drafting | Claude drafts an acknowledgement that never states approval, denial or payout |
| Human control | `ApprovalQueue`: nothing is released without a recorded approval; every event is audit-logged |
| Evaluation | `evaluate.py` scores field extraction and routing on a labelled set |

The LLM extracts and drafts. It does not make the routing decision, by design.

## Run it

```
pip install -e .[dev]
pytest
python -m claims_triage.cli --eval            # offline, deterministic mock
python -m claims_triage.cli --eval --live     # real Claude (needs ANTHROPIC_API_KEY)
python -m claims_triage.cli --file claim.txt  # queue one claim for approval
python -m claims_triage.mcp_server            # policy lookup over MCP
```

Model defaults to `claude-sonnet-5-5`; override with `CLAUDE_MODEL`.

## Read the numbers honestly

- The 100% in offline mode comes from a rule-based mock on 8 synthetic claims written alongside it. It proves the pipeline, routing rules and approval gate work. It says nothing about Claude's accuracy.
- Run `--live` against a larger labelled set before quoting any extraction accuracy or handle-time figure. The 40-60% handle-time reduction in our planning notes is a target, not a measurement.
- All data is synthetic. Do not load real claims or personal data without a data-handling review.

## Next steps before showing a partner

1. Run `--live` on 50+ varied claims and record real accuracy, cost per claim and latency.
2. Add PDF/image ingestion (Claude document input).
3. Add a reviewer UI in place of the CLI queue.
4. Record a 3-minute demo video.

## Partner programme this supports

- Apply: https://claude.com/partners (Claude Partner Network; free to join, confirm Services Track details on the page).
- Source repo: https://github.com/gtprepository/partner-assets/tree/main/claude-claims-triage-agent
- Status to state when applying: "applying", not "partner" or "certified".
