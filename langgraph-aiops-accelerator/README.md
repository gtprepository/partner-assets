# LangGraph AIOps Accelerator (reference build)

A runnable incident-response agent built as a LangGraph state graph: gather context, diagnose, propose a fix, pause for human approval, execute from an allowlist, report.

Status: internal demo asset on synthetic scenarios. Not a client deployment and not endorsed by LangChain.

## Graph

```
alert -> gather_context -> diagnose -> propose --(no action / info)--> report
                                          |
                                      approval (interrupt) --(rejected)--> report
                                          |
                                       execute (dry-run) -> report
```

## What it shows

- Stateful graph with conditional routing and a checkpointer (`MemorySaver`; swap for Postgres/SQLite in production).
- Human-in-the-loop via LangGraph `interrupt()` and `Command(resume=...)`: the run pauses until an on-call engineer approves or rejects.
- Safety: only actions on `ALLOWED_ACTIONS` can ever run, execution defaults to dry-run, low-confidence diagnoses and info alerts never propose action.
- Pluggable diagnosis: `ClaudeDiagnoser` (forced tool call, enum-constrained root cause) or the offline `RuleDiagnoser`.
- Tools are fixture-backed; replace `tools.py` bodies with Datadog, CloudWatch, Prometheus or Kubernetes calls.

## Run it

```
pip install -e .[dev]
pytest
python -m aiops_agent.cli --eval                 # pauses at approval for actionable alerts
python -m aiops_agent.cli --eval --auto-approve  # demo: approve all, still dry-run
python -m aiops_agent.cli --eval --live          # Claude diagnosis (needs ANTHROPIC_API_KEY)
```

## Read the numbers honestly

- 100% accuracy is the keyword-rule diagnoser on 4 synthetic scenarios written alongside it. It validates the graph, approval gate and allowlist, not diagnostic quality.
- Run `--live` on real or realistic incident data before quoting any root-cause accuracy or MTTR improvement.
- Real use needs read-only credentials first, narrow action scopes, and an incident-review process.

## Next steps before showing a partner

1. Add 20+ realistic scenarios (including ambiguous ones) and score `--live`.
2. Add a Slack/Teams approval step instead of the CLI pause.
3. Add LangSmith tracing and publish a sample trace.
4. Record a 3-minute demo video.

## Partner programme this supports

- Apply: https://www.langchain.com/langchain-partner-network-form (business email required; link https://github.com/gtprepository/partner-assets/tree/main/langgraph-aiops-accelerator in the form once the repo is public).
- Source repo: https://github.com/gtprepository/partner-assets/tree/main/langgraph-aiops-accelerator
- Status to state when applying: "applying", not "partner" or "certified".
