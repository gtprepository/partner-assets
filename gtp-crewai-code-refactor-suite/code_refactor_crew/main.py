#!/usr/bin/env python3
"""
main.py — Entry point for the Multi-Agent Code Refactoring & Audit Crew.

Usage:
    python main.py                          # Runs with built-in sample legacy code
    python main.py path/to/legacy_file.py  # Runs with your own file

Outputs land in the ./outputs/ directory:
    - refactored_code_<timestamp>.py
    - test_refactored_<timestamp>.py
    - security_refactor_<timestamp>.patch
    - pull_request_<timestamp>.md
    - crew_result_<timestamp>.json
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# SAMPLE LEGACY CODE — intentionally contains every major vulnerability class
# used to demonstrate the crew's detection and remediation capabilities.
# ─────────────────────────────────────────────────────────────────────────────
SAMPLE_LEGACY_CODE = '''\
"""
mini_auth.py — Minimal legacy auth module for pipeline testing.
Contains one representative instance of each major vulnerability class.
"""

import hashlib
import pickle
import random
import sqlite3
import subprocess

import requests

# CWE-798: Hardcoded credentials
SECRET_KEY = "hardcoded-secret-abc123"
DB_URL = "postgresql://admin:s3cr3t@prod-db:5432/users"


def login(username, password):
    """CWE-89: SQL injection via string concatenation."""
    conn = sqlite3.connect("app.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE name='" + username + "' AND pass='" + password + "'")
    row = cur.fetchone()
    conn.close()
    return row


def hash_pw(password):
    """CWE-327: Weak hash (MD5)."""
    return hashlib.md5(password.encode()).hexdigest()


def make_token():
    """CWE-338: Insecure random for security token."""
    return str(random.randint(100000, 999999))


def load_profile(data):
    """CWE-502: Unsafe pickle deserialization."""
    return pickle.loads(data)


def run_cmd(path):
    """CWE-78: Command injection via shell=True."""
    return subprocess.run("ls " + path, shell=True, capture_output=True).stdout.decode()


def fetch(url):
    """CWE-295: TLS verification disabled."""
    return requests.get(url, verify=False).json()


def parse_cfg(cfg):
    """CWE-78: eval() on untrusted input."""
    return eval(cfg)


def get_user(uid):
    """CWE-89: SQL injection via f-string; CWE-390: bare except."""
    conn = sqlite3.connect("app.db")
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM users WHERE id = {uid}")
        return cur.fetchall()
    except:
        pass
    finally:
        conn.close()
'''


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_engineer_output(raw: str) -> dict:
    """
    Extract refactored_code, unit_tests, pr_title, risk_rating from the
    engineer agent's structured text output (delimited by ==SECTION== markers).
    Returns a plain dict — no Pydantic conversion, no extra API calls.
    """
    def _extract(marker: str, text: str) -> str:
        pattern = rf"=={re.escape(marker)}==\s*```python\s*\n(.*?)```"
        m = re.search(pattern, text, re.DOTALL)
        if m:
            return m.group(1).rstrip()
        # Fallback: grab everything between this marker and the next ==...==
        pattern2 = rf"=={re.escape(marker)}==\s*\n(.*?)(?===\w|$)"
        m2 = re.search(pattern2, text, re.DOTALL)
        return m2.group(1).strip() if m2 else ""

    def _extract_line(marker: str, text: str) -> str:
        m = re.search(rf"=={re.escape(marker)}==\s*\n(.+)", text)
        return m.group(1).strip() if m else ""

    return {
        "refactored_code": _extract("REFACTORED_CODE", raw),
        "unit_tests": _extract("UNIT_TESTS", raw),
        "pr_title": _extract_line("PR_TITLE", raw),
        "risk_rating": _extract_line("RISK_RATING", raw) or "Critical",
    }


def _write_temp_file(code: str) -> str:
    """Persist code to a named temporary file and return its path."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        encoding="utf-8",
        prefix="legacy_audit_",
    ) as tmp:
        tmp.write(code)
        return tmp.name


def _banner() -> None:
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║   MULTI-AGENT CODE REFACTORING & AUDIT CREW — ENTERPRISE EDITION            ║
║   Autonomous Security Analysis · NIST CSF 2.0 · OWASP Top 10 (2021)       ║
║   Powered by CrewAI + Claude claude-sonnet-4-6 / GPT-4o                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")


def _section(title: str) -> None:
    width = 78
    print(f"\n{'═' * width}")
    print(f"  {title}")
    print(f"{'═' * width}")


def _save_outputs(result: object, output_dir: Path) -> Path:
    """Write all result artefacts to output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # ── Canonical JSON result ─────────────────────────────────────────────────
    raw_path = output_dir / f"crew_result_{ts}.json"
    try:
        if hasattr(result, "model_dump"):
            payload = result.model_dump()
        elif hasattr(result, "__dict__"):
            payload = result.__dict__
        else:
            payload = {"raw_output": str(result)}
        raw_path.write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
    except Exception as exc:
        raw_path.write_text(
            json.dumps({"raw_output": str(result), "serialization_error": str(exc)}, indent=2),
            encoding="utf-8",
        )
    print(f"\n[✓] Full result JSON  → {raw_path}")

    # ── Refactored source ─────────────────────────────────────────────────────
    if getattr(result, "refactored_code", None):
        p = output_dir / f"refactored_code_{ts}.py"
        p.write_text(result.refactored_code, encoding="utf-8")
        print(f"[✓] Refactored code   → {p}")

    # ── Unit tests ────────────────────────────────────────────────────────────
    if getattr(result, "unit_tests", None):
        p = output_dir / f"test_refactored_{ts}.py"
        p.write_text(result.unit_tests, encoding="utf-8")
        print(f"[✓] Unit test suite   → {p}")

    # ── Git diff patch ────────────────────────────────────────────────────────
    if getattr(result, "git_diff", None):
        p = output_dir / f"security_refactor_{ts}.patch"
        p.write_text(result.git_diff, encoding="utf-8")
        print(f"[✓] Git diff patch    → {p}")

    # ── PR description ────────────────────────────────────────────────────────
    if getattr(result, "pr_body_markdown", None):
        p = output_dir / f"pull_request_{ts}.md"
        p.write_text(result.pr_body_markdown, encoding="utf-8")
        print(f"[✓] PR description    → {p}")

    return raw_path


def _print_result_summary(result: object) -> None:
    """Print a human-readable summary of the refactor output."""
    _section("EXECUTION RESULT SUMMARY")

    pr_title = getattr(result, "pr_title", None)
    risk_rating = getattr(result, "risk_rating", None)
    lines_added = getattr(result, "lines_added", None)
    lines_removed = getattr(result, "lines_removed", None)
    jira_comment = getattr(result, "jira_comment", None)

    if pr_title:
        print(f"\n  PR Title      : {pr_title}")
    if risk_rating:
        print(f"  Risk Rating   : {risk_rating}")
    if lines_added is not None and lines_removed is not None:
        print(f"  Diff Stats    : +{lines_added} lines added / -{lines_removed} lines removed")

    if jira_comment:
        print("\n  ── Jira Comment Block ──────────────────────────────────────────────────")
        print(jira_comment[:800] + ("..." if len(jira_comment) > 800 else ""))
        print("  ────────────────────────────────────────────────────────────────────────")


def _hitl_checkpoint() -> None:
    _section("HUMAN-IN-THE-LOOP (HITL) APPROVAL CHECKPOINT")
    print("""
  The crew has completed static analysis, compliance auditing, refactoring,
  test generation, diff production, and PR package creation.

  ┌─────────────────────────────────────────────────────────────────────────┐
  │  REQUIRED HUMAN ACTIONS BEFORE MERGING TO MAIN                         │
  ├─────────────────────────────────────────────────────────────────────────┤
  │  Security Team                                                          │
  │  [ ] Review refactored code  → outputs/refactored_code_*.py            │
  │  [ ] Verify SQL parameterization matches production DB driver syntax    │
  │  [ ] Confirm env var names match deployment config (K8s, Vault, etc.)  │
  │  [ ] Approve crypto upgrade path (SHA-256 / bcrypt output format)      │
  │                                                                         │
  │  Engineering Team                                                       │
  │  [ ] Validate unit tests     → outputs/test_refactored_*.py            │
  │  [ ] Inspect git diff        → outputs/security_refactor_*.patch       │
  │  [ ] Review PR description   → outputs/pull_request_*.md               │
  │  [ ] Run tests in staging environment before production merge           │
  │                                                                         │
  │  Compliance / Governance                                                │
  │  [ ] Create Jira ticket entry from Jira block in PR description        │
  │  [ ] Document findings in SOC 2 / ISO 27001 evidence package           │
  │  [ ] Security architect sign-off on NIST CSF 2.0 remediation mapping  │
  └─────────────────────────────────────────────────────────────────────────┘

  ⚠️  DO NOT merge without completing all Security Team items above.
""")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> object | None:
    _banner()

    # ── Environment validation ────────────────────────────────────────────────
    missing_vars = [v for v in ["OPENAI_API_KEY"] if not os.environ.get(v)]
    if missing_vars:
        # Allow Anthropic-only setups where no OPENAI_API_KEY is needed
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print(
                f"[ERROR] Missing required environment variables: {missing_vars}\n"
                "        Copy .env.example to .env and add your API key(s).\n"
                "        OpenAI: set OPENAI_API_KEY\n"
                "        Anthropic: set ANTHROPIC_API_KEY and "
                "OPENAI_MODEL_NAME=anthropic/claude-sonnet-4-6"
            )
            sys.exit(1)

    # ── Resolve source input ──────────────────────────────────────────────────
    temp_path: str | None = None
    use_sample = False

    if len(sys.argv) > 1:
        provided = sys.argv[1]
        if os.path.isfile(provided):
            source_file = provided
            with open(source_file, "r", encoding="utf-8") as fh:
                source_code = fh.read()
            print(f"[✓] Analyzing provided file: {source_file}")
        else:
            print(f"[WARN] '{provided}' not found — falling back to built-in sample code.")
            use_sample = True
    else:
        use_sample = True

    if use_sample:
        print(
            "[INFO] No file argument provided. Running with built-in mini sample code.\n"
            "       The sample covers one instance of each vulnerability class:\n"
            "       CWE-89 (SQLi), CWE-78 (eval/shell), CWE-798 (hardcoded secrets),\n"
            "       CWE-327 (MD5), CWE-502 (pickle), CWE-338 (random), CWE-295 (TLS),\n"
            "       CWE-390 (bare except). ~55 lines — cheap to process.\n"
            "       Usage: python main.py path/to/your/file.py\n"
        )
        temp_path = _write_temp_file(SAMPLE_LEGACY_CODE)
        source_file = temp_path
        source_code = SAMPLE_LEGACY_CODE
        print(f"[✓] Sample code written to: {temp_path}")

    # ── Pre-analysis summary ──────────────────────────────────────────────────
    _section("TARGET FILE SUMMARY")
    print(f"  File:          {source_file}")
    print(f"  Lines:         {len(source_code.splitlines())}")
    print(f"  Characters:    {len(source_code)}")
    print(f"  Scan Start:    {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")

    _section("LAUNCHING MULTI-AGENT CREW")
    print("  ┌─────────────────────────────────────────────────────────────────┐")
    print("  │  Agent 1 → Code Parser & Architecture Analyst                  │")
    print("  │  Agent 2 → Security & NIST/OWASP Compliance Auditor            │")
    print("  │  Agent 3 → Refactoring Engineer & PR Generator                 │")
    print("  ├─────────────────────────────────────────────────────────────────┤")
    mem_status = "Enabled" if os.environ.get("OPENAI_API_KEY") else "Disabled"
    print(f"  │  Process: Sequential  │  Memory: {mem_status:<8} │  Verbose: True     │")
    print("  └─────────────────────────────────────────────────────────────────┘")
    print("\n  Starting crew execution...\n")

    # ── Import crew here so env validation runs first ─────────────────────────
    from crew import build_crew
    from tools.code_parser_tool import compute_parse_result
    from tools.static_analyzer_tool import compute_security_analysis
    from tools.pr_generator_tool import compute_pr_package

    try:
        # Pre-compute structural parse and security scan outside the crew.
        # This avoids the Claude 4 ReAct tool-loop problem: agents receive
        # data via {parse_result}/{security_result} input placeholders and
        # produce their Final Answer without needing any tool calls.
        _section("PRE-COMPUTING ANALYSIS (before crew kickoff)")
        print("  Running AST structural parser...")
        parse_result = compute_parse_result(source_file)
        print("  Running static security scanner (17 rules)...")
        security_result = compute_security_analysis(source_code, source_file)
        print("  Pre-computation complete. Handing data to crew agents.\n")

        crew = build_crew()
        result = crew.kickoff(inputs={
            "source_input": source_file,
            "source_code": source_code,
            "parse_result": parse_result,
            "security_result": security_result,
        })

        _section("CREW EXECUTION COMPLETE")

        output_dir = Path("outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        # Parse the engineer's structured text output (no Pydantic conversion needed).
        raw_output = getattr(result, "raw", str(result))
        parsed = _parse_engineer_output(raw_output)
        refactored_code = parsed["refactored_code"]
        unit_tests = parsed["unit_tests"]
        pr_title = parsed["pr_title"]
        risk_rating = parsed["risk_rating"]

        # Save raw crew output JSON
        raw_path = output_dir / f"crew_result_{ts}.json"
        raw_path.write_text(
            json.dumps({
                "raw_output": raw_output,
                "pr_title": pr_title,
                "risk_rating": risk_rating,
            }, indent=2, default=str),
            encoding="utf-8",
        )
        print(f"\n[✓] Full result JSON  → {raw_path}")

        if refactored_code:
            p = output_dir / f"refactored_code_{ts}.py"
            p.write_text(refactored_code, encoding="utf-8")
            print(f"[✓] Refactored code   → {p}")

        if unit_tests:
            p = output_dir / f"test_refactored_{ts}.py"
            p.write_text(unit_tests, encoding="utf-8")
            print(f"[✓] Unit test suite   → {p}")

        # Generate git diff and PR package from the refactored code.
        if refactored_code:
            _section("GENERATING GIT DIFF & PR PACKAGE")
            print("  Computing unified diff and PR description...")
            pr_data = compute_pr_package(
                original_code=source_code,
                refactored_code=refactored_code,
                file_path=source_file,
                audit_summary_json=security_result,
                risk_rating=risk_rating,
            )
            diff_path = output_dir / f"security_refactor_{ts}.patch"
            pr_path = output_dir / f"pull_request_{ts}.md"
            diff_path.write_text(pr_data["git_diff"], encoding="utf-8")
            pr_path.write_text(pr_data["pr_body_markdown"], encoding="utf-8")
            print(f"[✓] Git diff patch    → {diff_path}")
            print(f"[✓] PR description    → {pr_path}")
            print(f"    Diff: +{pr_data['lines_added']} lines added / -{pr_data['lines_removed']} lines removed")

        print(f"\n  All artefacts saved to: {output_dir.resolve()}/")

        _hitl_checkpoint()

        print(
            f"[✓] Completed at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            "[✓] Multi-Agent Code Refactoring & Audit Crew finished successfully.\n"
        )

        return parsed

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user. Partial outputs may exist in ./outputs/.")
        sys.exit(0)

    except Exception as exc:
        print(f"\n[ERROR] Crew execution failed: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


if __name__ == "__main__":
    main()
