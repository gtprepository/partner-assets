# Multi-Agent Code Refactoring & Audit Crew — Enterprise Edition

> Autonomous security analysis, compliance mapping, and production-ready refactoring powered by **CrewAI** + **Claude claude-sonnet-4-6**.

---

## What It Does

Drop in a legacy Python file. Three specialist AI agents collaborate sequentially to:

1. **Parse** — AST-based structural analysis: cyclomatic complexity, code smells, deprecated imports, technical debt score
2. **Audit** — Map every vulnerability to NIST CSF 2.0, OWASP Top 10 (2021), and CWE standards with severity grading and actionable remediation
3. **Refactor** — Produce a fully runnable, type-hinted, secure replacement module + a complete pytest suite (≥15 tests)

Then automatically generates a **unified git diff**, a **production-grade GitHub PR description** with HITL checklist, and a **Jira audit panel comment** — all without touching your repo.

---

## Architecture

```
main.py
  ├── compute_parse_result()       AST analysis        (pure Python, no LLM)
  ├── compute_security_analysis()  17-rule OWASP scan  (pure Python, no LLM)
  │
  └── CrewAI — Sequential Pipeline
        │
        ├── Agent 1 · Principal Software Architect
        │     Reads pre-computed AST JSON → writes structural audit narrative
        │
        ├── Agent 2 · Lead Cybersecurity Architect & Compliance Assessor
        │     Reads pre-computed scan JSON → maps findings to NIST / OWASP / CWE
        │
        └── Agent 3 · Senior AI-Native Staff Refactoring Engineer
              Reads original source + audit context
              → writes refactored code + pytest suite
  │
  ├── compute_pr_package()         Diff + PR markdown  (pure Python, no LLM)
  └── outputs/
        ├── refactored_code_<ts>.py
        ├── test_refactored_<ts>.py
        ├── security_refactor_<ts>.patch
        ├── pull_request_<ts>.md
        └── crew_result_<ts>.json
```

**Only 3 LLM calls per run** — the computationally expensive analysis (AST parsing, regex security scanning, diff generation, PR formatting) runs as pure Python before and after the crew, keeping latency and cost predictable.

---

## Security Rules Covered

| ID | Vulnerability | CWE | OWASP |
|----|--------------|-----|-------|
| SQLI-001/002/003 | SQL Injection (concat, f-string, %) | CWE-89 | A03 |
| CMD-001/002/003 | Command Injection (shell=True, eval, exec) | CWE-78 | A03 |
| SEC-001/002/003/004 | Hardcoded Secrets & Credentials | CWE-798 | A07 |
| DESER-001/002 | Unsafe Deserialization (pickle, marshal) | CWE-502 | A08 |
| CRYPTO-001/002/003 | Weak Hash (MD5, SHA-1), Insecure Random | CWE-327/338 | A02 |
| NET-001 | TLS Certificate Verification Disabled | CWE-295 | A02 |
| AUTH-001 | assert() for Security Checks | CWE-617 | A01 |
| WEB-001 | Open Redirect | CWE-601 | A01 |
| ERR-001 | Bare except Clause | CWE-390 | — |

---

## Quick Start

### Prerequisites

- Python 3.12 (CrewAI requires `<3.14`)
- Anthropic API key (`claude-sonnet-4-6`)

### Install

```bash
git clone https://github.com/gtprepository/partner-assets.git
cd partner-assets/gtp-crewai-code-refactor-suite
cd code_refactor_crew

py -3.12 -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
```

Edit `.env`:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_MODEL_NAME=claude-sonnet-4-6
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=8192
```

### Run

```bash
# Built-in mini demo (covers all 9 CWE classes, ~55 lines)
python main.py

# Your own file
python main.py path/to/legacy_module.py
```

---

## Sample Output

**Refactoring summary for `mini_auth.py`:**

```
Agent 1 ✅  Structural analysis complete — 8 functions, debt score 76/100
Agent 2 ✅  Audit complete — 11 findings (6 Critical, 3 High, 1 Medium, 1 Low)
Agent 3 ✅  Refactoring complete — 15 tests generated

[✓] Refactored code   → outputs/refactored_code_20260815_025454.py
[✓] Unit test suite   → outputs/test_refactored_20260815_025454.py
[✓] Git diff patch    → outputs/security_refactor_20260815_025454.patch
[✓] PR description    → outputs/pull_request_20260815_025454.md
[✓] Full result JSON  → outputs/crew_result_20260815_025454.json

Diff: +187 lines added / -42 lines removed
```

**Remediations applied automatically:**

| Before | After |
|--------|-------|
| `cursor.execute("SELECT * FROM users WHERE name='" + username + "'")` | `cursor.execute("SELECT * FROM users WHERE name = %s", (username,))` |
| `hashlib.md5(password.encode()).hexdigest()` | `bcrypt.hashpw(password.encode(), bcrypt.gensalt())` |
| `pickle.loads(data)` | `json.loads(data)` |
| `subprocess.run("ls " + path, shell=True)` | `subprocess.run(["ls", path], shell=False)` |
| `requests.get(url, verify=False)` | `requests.get(url, verify=True)` |
| `return str(random.randint(100000, 999999))` | `return secrets.token_hex(32)` |
| `return eval(cfg)` | `return ast.literal_eval(cfg)` |

---

## Tests

```bash
cd code_refactor_crew
pip install pytest
pytest tests
```

These cover the pure-Python scanner and parser only (no LLM calls, no API key needed).

---

## Project Structure

```
gtp-crewai-code-refactor-suite/
└── code_refactor_crew/
    ├── tools/
    │   ├── code_parser_tool.py      # AST parser + cyclomatic complexity
    │   ├── static_analyzer_tool.py  # 17-rule security scanner
    │   └── pr_generator_tool.py     # Unified diff + PR markdown generator
    ├── models/
    │   └── schema.py                # Pydantic v2: VulnerabilityFinding, AuditReport, RefactorOutput
    ├── crew.py                      # Agent + Task + Crew assembly
    ├── main.py                      # Entry point + output orchestration
    ├── requirements.txt
    └── .env.example
```

---

## HITL Approval Workflow

The generated PR description includes a mandatory Human-in-the-Loop checklist that gates merging:

- **Security Team** — verify parameterized query syntax, env var names, crypto upgrade path
- **Engineering Team** — validate refactored logic, run generated tests in staging
- **Compliance / Governance** — create Jira ticket, update SOC 2 / ISO 27001 evidence package

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent Framework | [CrewAI](https://github.com/crewAIInc/crewAI) 0.203.x |
| LLM | Anthropic Claude claude-sonnet-4-6 via LiteLLM |
| Static Analysis | Python `ast` module + regex rule engine |
| Schema Validation | Pydantic v2 |
| Diff Generation | Python `difflib.unified_diff` |
| Testing Framework | pytest |

---

## License

MIT — see [LICENSE](LICENSE)

---

*Built with [CrewAI](https://crewai.com) · Powered by [Anthropic Claude](https://anthropic.com)*
