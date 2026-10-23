"""
crew.py — Assembles and orchestrates the Multi-Agent Code Refactoring & Audit Crew.

Instantiates the three specialist agents, constructs their sequential tasks,
wires the Pydantic output schemas, and returns a ready-to-kickoff Crew object.
"""

from __future__ import annotations

import os

import litellm
from crewai import Agent, Crew, Process, Task
from crewai.llm import LLM
from dotenv import load_dotenv


load_dotenv()

# ── Claude 4 prefill compatibility patch ──────────────────────────────────────
# CrewAI appends a trailing assistant message to prime JSON output (prefill).
# Claude 3.x supports this; Claude 4 models (claude-sonnet-4-6, claude-opus-4-8)
# reject it with "This model does not support assistant message prefill."
# Intercept litellm.completion and strip the trailing assistant message for
# all Anthropic model calls before they reach the API.
_original_litellm_completion = litellm.completion


def _claude4_safe_completion(**kwargs):
    model: str = kwargs.get("model", "")
    is_anthropic = (
        "anthropic" in model.lower()
        or model.startswith("claude")
    )
    if is_anthropic:
        messages: list = kwargs.get("messages", [])
        # Strip any trailing assistant prefill messages
        while messages and messages[-1].get("role") == "assistant":
            messages = messages[:-1]
        kwargs["messages"] = messages
    return _original_litellm_completion(**kwargs)


litellm.completion = _claude4_safe_completion
litellm.drop_params = True  # silently ignore unsupported provider params


# ── LLM Factory ───────────────────────────────────────────────────────────────

def _build_llm(temperature: float | None = None, max_tokens_override: int | None = None) -> LLM:
    """
    Construct the LLM from environment config.

    Anthropic usage: set OPENAI_MODEL_NAME=claude-sonnet-4-6 (or with the
    anthropic/ LiteLLM prefix) and ANTHROPIC_API_KEY. The Claude 4 prefill
    incompatibility is handled by the _claude4_safe_completion patch above.

    max_tokens_override bypasses LLM_MAX_TOKENS — use for the engineer agent
    whose Pydantic JSON output (refactored_code + unit_tests) exceeds 8 192 tokens.
    """
    model = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o")
    temp = temperature if temperature is not None else float(
        os.environ.get("LLM_TEMPERATURE", "0.1")
    )
    max_tokens = max_tokens_override if max_tokens_override is not None else int(
        os.environ.get("LLM_MAX_TOKENS", "8192")
    )

    is_anthropic = (
        "anthropic" in model.lower() or model.startswith("claude")
    )
    api_key = (
        os.environ.get("ANTHROPIC_API_KEY")
        if is_anthropic and not os.environ.get("OPENAI_API_KEY")
        else os.environ.get("OPENAI_API_KEY")
    )

    kwargs: dict = {
        "model": model,
        "temperature": temp,
        "max_tokens": max_tokens,
    }
    if api_key:
        kwargs["api_key"] = api_key

    return LLM(**kwargs)


# ── Agent Factories ───────────────────────────────────────────────────────────

def _build_code_parser_agent(llm: LLM) -> Agent:
    return Agent(
        role="Principal Software Architect & Codebase Discovery Specialist",
        goal=(
            "Parse legacy source code files, extract a precise AST-driven structural profile, "
            "map all import dependencies (flagging deprecated and insecure modules), calculate "
            "per-function cyclomatic complexity, and surface every code smell with exact line numbers. "
            "Your output enables the compliance auditor to perform a targeted, zero-miss security audit."
        ),
        backstory=(
            "A veteran software architect with 20+ years modernizing monolithic enterprise codebases "
            "at Fortune 500 companies across banking, healthcare, and defense sectors. Expert in Python, "
            "Java, Go, and TypeScript design patterns, dependency analysis, and static analysis tooling. "
            "Has led multiple large-scale digital transformation programs, converting legacy systems into "
            "clean, testable microservices without a single production outage. Sees code structure the way "
            "a forensic accountant reads financial ledgers — nothing is hidden, every dependency tells a "
            "story, and technical debt is always quantified rather than hand-waved away. Pioneered AST-driven "
            "debt-scoring frameworks that are now standard practice across multiple engineering organizations."
        ),
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
        memory=True,
        respect_context_window=True,
    )


def _build_compliance_auditor_agent(llm: LLM) -> Agent:
    return Agent(
        role="Lead Cybersecurity Architect & Compliance Assessor",
        goal=(
            "Audit the parsed code structure and raw source against NIST CSF 2.0 (Govern/Protect), "
            "OWASP Top 10 (2021), and CWE standards. Identify every hardcoded secret, injection vector, "
            "unsafe deserialization, weak cryptographic primitive, and access-control bypass. "
            "Grade each finding with severity, CWE ID, NIST mapping, and specific remediation guidance. "
            "Compute an overall risk score and produce a structured AuditReport."
        ),
        backstory=(
            "A former enterprise CISO advisor and principal security architect with 15+ years identifying "
            "zero-day vulnerabilities in enterprise software stacks across regulated industries including "
            "financial services, healthcare (HIPAA), and critical infrastructure. Has performed hundreds "
            "of code security reviews and penetration tests. Dissects code paths with mathematical precision "
            "to eliminate compliance drift before it reaches production. Author of internal CWE-to-NIST CSF "
            "mapping frameworks adopted by three Fortune 100 companies. Operates with an uncompromising "
            "zero-tolerance policy for hardcoded secrets, SQL injection, and broken authentication. "
            "Trusted by legal and compliance teams to produce audit-ready evidence packages for SOC 2, "
            "ISO 27001, and FedRAMP certifications."
        ),
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
        memory=True,
        respect_context_window=True,
    )


def _build_refactor_engineer_agent(llm: LLM) -> Agent:
    return Agent(
        role="Senior AI-Native Staff Refactoring Engineer",
        goal=(
            "Implement a complete, deterministic, backward-compatible refactoring of the audited source code "
            "that eliminates all Critical and High severity vulnerabilities. Produce a fully runnable refactored "
            "module with type hints, proper exception handling, context managers, secure cryptography, and "
            "parameterized queries. Generate a comprehensive pytest test suite (≥10 test functions, ≥80% "
            "coverage of refactored code), a standard unified git diff patch, and a production-grade GitHub "
            "PR description with HITL checklist and Jira comment block."
        ),
        backstory=(
            "A master of clean code, test-driven development, and automated continuous delivery. Has contributed "
            "to hundreds of open-source projects and enterprise codebases — transforming fragile legacy systems "
            "into modern, secure, observable architectures with zero regression tolerance. Applies SOLID "
            "principles, DRY, and defensive programming patterns instinctively. Believes every line of code "
            "is a liability until proven otherwise by a failing test. Generates git diffs that tell a "
            "complete, coherent story reviewers can approve with full confidence. Instrumental in establishing "
            "automated security gate policies and shift-left security practices at multiple engineering "
            "organizations. Never delivers 'placeholder' code — every output is production-ready."
        ),
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=10,
        memory=True,
        respect_context_window=True,
    )


# ── Task Factories ────────────────────────────────────────────────────────────
# Task descriptions use {source_input} and {source_code} as CrewAI input
# placeholders — interpolated at kickoff(inputs=...) time, NOT f-string literals.
# This keeps the crew template small and avoids embedding code at construction.

def _build_parse_task(agent: Agent) -> Task:
    return Task(
        description="""
You are reviewing the structural analysis of the Python source file: {source_input}

The AST-based structural profile has already been computed and is provided below.
Do NOT attempt to call any tools — all data you need is in the JSON below.

=== STRUCTURAL ANALYSIS JSON ===
{parse_result}
=== END STRUCTURAL ANALYSIS ===

From the JSON data above, write a comprehensive structural audit narrative covering:
1. File metadata: path, total lines, language, character count
2. Functions inventory: name, line range, cyclomatic_complexity — flag any CC > 5 as
   high-complexity and explain the refactoring risk
3. Code smells: each item with its line number, type, and security significance
4. Technical debt score: what drives it and which findings contribute most
5. Imports: list any marked [DEPRECATED] or [INSECURE], explain the risk of each
6. structural_observations: a 3–5 sentence paragraph the compliance auditor will use
   to prioritise the most dangerous code areas for security review

Your Final Answer must be the complete narrative report. Do not call any tools.
""",
        expected_output="""
A detailed structural audit narrative containing:
- File metadata: path, total lines, language, total_characters
- Functions inventory with cyclomatic_complexity scores; high-CC functions flagged
- Code smells list with line numbers and security significance
- Technical debt score analysis with top contributing factors
- Deprecated/insecure imports with risk explanations
- structural_observations paragraph for the compliance auditor
""",
        agent=agent,
    )


def _build_audit_task(agent: Agent, parse_task: Task) -> Task:
    return Task(
        description="""
Conduct a comprehensive security and compliance audit of: **{source_input}**

The static security scan has already been completed. Findings are provided below.
Do NOT attempt to call any tools — all vulnerability data you need is in the JSON below.
Also use the structural analysis narrative from the Code Parser Agent as additional context.

=== STATIC SECURITY SCAN RESULTS JSON ===
{security_result}
=== END SECURITY SCAN RESULTS ===

Using the findings above, produce a complete AuditReport by:

1. Mapping each finding to the correct OWASP Top 10 (2021) category:
   - A01 Broken Access Control: assert-based auth, IDOR
   - A02 Cryptographic Failures: MD5, SHA1, ECB, verify=False, weak random
   - A03 Injection: SQL (%, +, f-string, .format in execute()), eval, exec, shell=True
   - A07 Auth Failures: hardcoded passwords/keys/tokens/connection strings (CWE-798)
   - A08 Data Integrity: pickle.loads, marshal, shelve

2. Assigning each finding to a NIST CSF 2.0 category:
   GV-Govern | ID-Identify | PR-Protect | DE-Detect | RS-Respond | RC-Recover

3. Grading severity:
   - Critical: RCE / auth bypass / plaintext credential in code
   - High: SQL injection, unsafe deserialization, broken crypto in auth, shell injection
   - Medium: weak hash for non-auth, bare except, insecure random, verify=False
   - Low: style smells on security-adjacent functions

4. For every finding: confirm exact line numbers, vulnerable snippet (max 300 chars),
   specific actionable remediation, false_positive_likelihood (0.0–1.0).

5. Computing overall_risk_score (0.0–10.0), building nist_coverage map, writing a 3–5
   sentence executive compliance_summary.

Output must conform to the AuditReport Pydantic schema. Do not call any tools.
""",
        expected_output="""
A structured AuditReport (Pydantic-compatible JSON) containing:
- scanned_file: file path
- scan_timestamp: ISO 8601 UTC timestamp
- total_vulnerabilities: integer
- critical_count, high_count, medium_count, low_count
- findings: ordered list (Critical first) of VulnerabilityFinding objects, each with:
    title, severity, cwe_id, nist_mapping, owasp_category,
    line_numbers, vulnerable_code_snippet, remediation_suggestion,
    false_positive_likelihood, rule_id
- overall_risk_score: float 0.0–10.0
- compliance_summary: executive narrative (3–5 sentences)
- nist_coverage: {category_string: finding_count} dict
""",
        agent=agent,
        context=[parse_task],
    )


def _build_refactor_task(agent: Agent, parse_task: Task, audit_task: Task) -> Task:
    return Task(
        description="""
Perform a complete security refactoring of **{source_input}** and generate the
full Pull Request package. Use the parser and audit outputs from upstream agents.

Original source code to refactor:
```
{source_code}
```

DELIVERABLE 1 — FULLY REFACTORED SOURCE CODE (complete, runnable, no placeholders):

Apply ALL remediations from the audit:
- SQL Injection (CWE-89): replace string concat with cursor.execute(query, (param,))
- Hardcoded Secrets (CWE-798): replace with os.environ.get("VAR_NAME")
- Unsafe Deserialization (CWE-502): replace pickle.loads with json.loads
- eval/exec (CWE-78): replace with ast.literal_eval or explicit dispatch dict
- Weak Crypto (CWE-327): MD5/SHA1 -> hashlib.sha256; passwords -> bcrypt
- Insecure Random (CWE-338): random.randint -> secrets.token_hex(32)
- subprocess shell=True (CWE-78): convert to list form with shell=False
- SSL bypass (CWE-295): remove verify=False
- Bare except (CWE-390): replace with specific exception types + logging.exception
- assert for security (CWE-617): replace with explicit if/raise PermissionError
- Mutable default args: replace [] default with None sentinel
- Add type hints to ALL public function signatures
- Wrap ALL DB connections with context managers

DELIVERABLE 2 — COMPLETE PYTEST UNIT TEST SUITE (runnable, no placeholders, min 15 tests):
Cover: happy paths, SQL injection attempt inputs, None/empty edge cases,
mock-based isolation (unittest.mock.patch), pytest.raises for error cases.
Include tests for: authenticate_user, hash_password, generate_session_token,
load_user_profile, run_system_command, fetch_external_data, get_user_data,
process_config, compute_checksum, UserManager.verify_admin, UserManager.create_user.

IMPORTANT: Do NOT call any tools. Write your entire Final Answer inline.
The git diff, PR description, and Jira comment will be generated automatically
after you provide the refactored code. You do not need to produce them.

Structure your Final Answer using EXACTLY these section markers (required for parsing):

==REFACTORED_CODE==
```python
<complete refactored module here — no placeholders>
```

==UNIT_TESTS==
```python
<complete pytest file here — no placeholders, ≥15 test functions>
```

==PR_TITLE==
<one-line conventional-commits title, e.g. "security: refactor auth.py — fix 8 critical vulns">

==RISK_RATING==
Critical
""",
        expected_output="""
A structured text response with four clearly delimited sections:
==REFACTORED_CODE== — complete, runnable refactored Python module, all 13 remediation categories applied
==UNIT_TESTS== — complete pytest file, runnable, ≥15 test functions
==PR_TITLE== — conventional-commits PR title
==RISK_RATING== — Critical | High | Medium | Low
""",
        agent=agent,
        context=[parse_task, audit_task],
    )


# ── Crew Factory ──────────────────────────────────────────────────────────────

def build_crew() -> Crew:
    """
    Assemble and return a fully configured sequential multi-agent crew.

    Task descriptions use {source_input} and {source_code} as CrewAI input
    placeholders. Pass actual values at execution time:
        crew.kickoff(inputs={"source_input": path, "source_code": code})

    Returns:
        A CrewAI Crew object ready to kickoff(inputs=...).
    """
    llm = _build_llm()
    # Engineer output (refactored_code + unit_tests as Pydantic JSON) easily
    # exceeds 8 192 tokens. Use a separate LLM instance with 16 000 max_tokens
    # so the CrewAI Pydantic converter never hits the length limit.
    engineer_llm = _build_llm(max_tokens_override=16000)

    # Agents
    parser_agent = _build_code_parser_agent(llm)
    auditor_agent = _build_compliance_auditor_agent(llm)
    engineer_agent = _build_refactor_engineer_agent(engineer_llm)

    # Tasks — no source data embedded; injected via kickoff(inputs=...)
    parse_task = _build_parse_task(parser_agent)
    audit_task = _build_audit_task(auditor_agent, parse_task)
    refactor_task = _build_refactor_task(engineer_agent, parse_task, audit_task)

    # Memory with OpenAI embeddings requires OPENAI_API_KEY.
    # Fall back gracefully to memory=False for Anthropic-only setups.
    use_openai = bool(os.environ.get("OPENAI_API_KEY"))
    embedding_model = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    # planning=True triggers a CrewAI 0.86.x EventBus bug ('NoneType' has no
    # attribute 'key' on TaskStartedEvent). Disable until upstream fixes it.
    crew_kwargs: dict = {
        "agents": [parser_agent, auditor_agent, engineer_agent],
        "tasks": [parse_task, audit_task, refactor_task],
        "process": Process.sequential,
        "verbose": True,
        "memory": use_openai,
        "output_log_file": "crew_execution.log",
        "planning": False,
    }

    if use_openai:
        crew_kwargs["embedder"] = {
            "provider": "openai",
            "config": {"model": embedding_model},
        }

    if not use_openai:
        import warnings
        warnings.warn(
            "OPENAI_API_KEY not set — crew memory disabled. "
            "Set OPENAI_API_KEY to enable cross-task memory via ChromaDB.",
            stacklevel=2,
        )

    crew = Crew(**crew_kwargs)
    return crew
