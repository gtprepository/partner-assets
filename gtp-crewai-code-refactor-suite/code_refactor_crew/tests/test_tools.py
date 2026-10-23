"""Offline tests for the pure-Python parts of the pipeline (no LLM calls)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.code_parser_tool import compute_parse_result  # noqa: E402
from tools.static_analyzer_tool import compute_security_analysis  # noqa: E402

MINI = ROOT / "mini_auth.py"


def _scan(src: str) -> dict:
    return json.loads(compute_security_analysis(src, "t.py"))


def _ids(report: dict) -> set[str]:
    return {f["rule_id"] for f in report["findings"]}


def test_demo_file_has_critical_findings():
    r = _scan(MINI.read_text(encoding="utf-8"))
    assert r["total_vulnerabilities"] >= 9
    assert r["critical_count"] >= 1


def test_detects_pickle_and_shell_true():
    r = _scan("import pickle, subprocess\npickle.loads(b)\nsubprocess.run('ls ' + p, shell=True)\n")
    cwes = {f["cwe_id"] for f in r["findings"]}
    assert "CWE-502" in cwes and "CWE-78" in cwes


def test_detects_tls_verification_disabled():
    r = _scan("import requests\nrequests.get(u, verify=False)\n")
    assert "CWE-295" in {f["cwe_id"] for f in r["findings"]}


def test_clean_code_has_no_findings():
    r = _scan("def add(a: int, b: int) -> int:\n    return a + b\n")
    assert r["total_vulnerabilities"] == 0


def test_empty_source_returns_error():
    assert "error" in _scan("   ")


def test_parser_reports_structure():
    r = json.loads(compute_parse_result(str(MINI)))
    assert r["language"].lower().startswith("python")
    assert len(r["functions"]) >= 5
    assert 0 <= r["technical_debt_score"] <= 100


def test_parser_rejects_non_python_and_missing(tmp_path):
    assert "error" in json.loads(compute_parse_result(str(tmp_path / "nope.py")))
    f = tmp_path / "x.js"
    f.write_text("var a;")
    assert "error" in json.loads(compute_parse_result(str(f)))
