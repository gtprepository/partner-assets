# GTP partner assets

Reference builds used when approaching AI product companies for technology partnerships. Each folder is self-contained. See `Tech PArtnerships.docx` (Quadraforce / New Pushes) for why each exists.

| Folder | Partner angle | Apply here | GitHub | Status |
|---|---|---|---|---|
| `claude-claims-triage-agent` | Claude Partner Network | https://claude.com/partners | https://github.com/gtprepository/partner-assets/tree/main/claude-claims-triage-agent | Built; offline tests pass; live run on Claude not yet done |
| `langgraph-aiops-accelerator` | LangChain Partner Network | https://www.langchain.com/langchain-partner-network-form | https://github.com/gtprepository/partner-assets/tree/main/langgraph-aiops-accelerator | Built; offline tests pass; live run on Claude not yet done |
| `gtp-crewai-code-refactor-suite` | CrewAI (no formal partner programme found) and Anthropic | n/a | https://github.com/gtprepository/gtp-crewai-code-refactor-suite | Built earlier; partner claims removed from README, one-pager and decks; scanner/parser tests added; live run not repeated |

Rules for anything shown externally:
- Do not claim certifications or partner status GTP does not hold.
- Quote only measured numbers from a `--live` run on stated data, not the offline mock scores.
- Synthetic data only.

Repository: https://github.com/gtprepository/partner-assets

Before pushing further changes: run `git status` to confirm no `.env`, `runtime/` or API keys are included (both assets already ignore them), and add a LICENSE of your choice.
