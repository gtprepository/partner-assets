"""
CodeParserTool — CrewAI tool that reads Python source files, builds an AST-based
structural profile, calculates cyclomatic complexity, and surfaces code smells
for downstream security auditing and refactoring agents.
"""

from __future__ import annotations

import ast
import json
import os
import re
from typing import Any

from crewai.tools import tool


# ── Deprecated standard library modules removed in Python 3.11–3.13 ──────────
_DEPRECATED_STDLIB: frozenset[str] = frozenset({
    "telnetlib", "cgi", "cgitb", "aifc", "audioop", "crypt", "chunk",
    "imghdr", "mailcap", "msilib", "nis", "nntplib", "ossaudiodev",
    "pipes", "sndhdr", "spwd", "sunau", "uu", "xdrlib", "formatter",
    "distutils",
})

# ── Modules that are insecure regardless of deprecation status ─────────────────
_INSECURE_MODULES: frozenset[str] = frozenset({
    "pickle", "shelve", "marshal",
})


def _calculate_cyclomatic_complexity(node: ast.AST) -> int:
    """
    Approximate McCabe cyclomatic complexity for a function node.
    Counts branching constructs: if, elif, while, for, except handler,
    with, assert, boolean sub-expressions, and comprehension conditionals.
    """
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                               ast.With, ast.Assert, ast.comprehension)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            # Each additional operand in an `and`/`or` adds a branch
            complexity += len(child.values) - 1
        elif isinstance(child, ast.IfExp):
            # Ternary expressions also add a branch
            complexity += 1
    return complexity


def _extract_functions(tree: ast.Module) -> list[dict[str, Any]]:
    """Extract all function definitions (sync and async) from the AST."""
    functions: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        args = node.args
        params = [arg.arg for arg in args.args + args.posonlyargs + args.kwonlyargs]
        if args.vararg:
            params.append(f"*{args.vararg.arg}")
        if args.kwarg:
            params.append(f"**{args.kwarg.arg}")

        has_hints = any(
            arg.annotation is not None
            for arg in args.args + args.posonlyargs + args.kwonlyargs
        )
        return_type: str | None = None
        if node.returns:
            try:
                return_type = ast.unparse(node.returns)
            except Exception:
                return_type = "unknown"

        functions.append({
            "name": node.name,
            "line_start": node.lineno,
            "line_end": getattr(node, "end_lineno", node.lineno),
            "cyclomatic_complexity": _calculate_cyclomatic_complexity(node),
            "has_type_hints": has_hints,
            "parameters": params,
            "return_type": return_type,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
        })

    return functions


def _extract_classes(tree: ast.Module) -> list[dict[str, Any]]:
    """Extract class definitions with method counts and line ranges."""
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = [
                n.name for n in ast.walk(node)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            classes.append({
                "name": node.name,
                "line_start": node.lineno,
                "method_count": len(methods),
                "methods": methods[:30],  # cap for readability
            })
    return classes


def _extract_imports(tree: ast.Module) -> list[str]:
    """Extract all imports, flagging deprecated or insecure modules."""
    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                flags = []
                if top in _DEPRECATED_STDLIB:
                    flags.append("DEPRECATED")
                if top in _INSECURE_MODULES:
                    flags.append("INSECURE")
                flag_str = f" [{', '.join(flags)}]" if flags else ""
                imports.append(f"{alias.name}{flag_str}")

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            top = module.split(".")[0]
            flags = []
            if top in _DEPRECATED_STDLIB:
                flags.append("DEPRECATED")
            if top in _INSECURE_MODULES:
                flags.append("INSECURE")
            names = ", ".join(a.name for a in (node.names or []))
            flag_str = f" [{', '.join(flags)}]" if flags else ""
            imports.append(f"from {module} import {names}{flag_str}")

    return imports


def _detect_code_smells(source: str, tree: ast.Module) -> list[str]:
    """Scan source text and AST for common anti-patterns and code smells."""
    smells: list[str] = []
    lines = source.splitlines()
    sql_keywords = re.compile(
        r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE)\b",
        re.IGNORECASE,
    )
    magic_num = re.compile(r"(?<!\w)(?!0\b|1\b)\d{3,}(?!\w)")
    credential_names = re.compile(
        r"\b(password|passwd|pwd|secret|api_key|apikey|token|auth_token"
        r"|access_key|private_key|client_secret)\b",
        re.IGNORECASE,
    )
    string_literal = re.compile(r"""['"][^'"]{4,}['"]""")

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Bare except
        if re.match(r"^except\s*:", stripped):
            smells.append(
                f"Line {i}: Bare except clause — catches all exceptions including "
                "SystemExit and KeyboardInterrupt; use specific exception types."
            )

        # SQL string concatenation
        if sql_keywords.search(stripped):
            if any(op in stripped for op in ["%", " + ", ".format(", 'f"', "f'"]):
                smells.append(
                    f"Line {i}: SQL string concatenation detected — critical injection risk; "
                    "use parameterized queries."
                )

        # Mutable default arguments
        if re.search(r"def \w+\(.*=\s*(\[\]|\{\}|\(\))", stripped):
            smells.append(
                f"Line {i}: Mutable default argument (list/dict/set) — "
                "shared across all callers; use None sentinel."
            )

        # eval / exec usage
        if re.search(r"\beval\s*\(|\bexec\s*\(", stripped):
            smells.append(
                f"Line {i}: eval()/exec() detected — arbitrary code execution risk; "
                "replace with ast.literal_eval() or explicit dispatch."
            )

        # pickle usage
        if re.search(r"\bpickle\.(loads?|Unpickler)\b", stripped):
            smells.append(
                f"Line {i}: pickle.load/loads() detected — unsafe deserialization; "
                "use json.loads() or validate with HMAC."
            )

        # subprocess shell=True
        if re.search(r"subprocess\.(call|run|Popen)", stripped) and "shell=True" in stripped:
            smells.append(
                f"Line {i}: subprocess with shell=True — command injection risk; "
                "pass command as list with shell=False."
            )

        # Hardcoded credential-like assignment
        if credential_names.search(stripped) and "=" in stripped:
            if string_literal.search(stripped) and "os.environ" not in stripped:
                smells.append(
                    f"Line {i}: Potential hardcoded credential — move to environment variable."
                )

        # Magic numbers
        if "=" in stripped and not stripped.startswith("#"):
            if magic_num.search(stripped):
                smells.append(
                    f"Line {i}: Magic number detected — extract to named constant."
                )

        # assert for security / auth checks
        if stripped.startswith("assert") and credential_names.search(stripped):
            smells.append(
                f"Line {i}: assert() used for security check — stripped by Python -O flag; "
                "use explicit if/raise."
            )

    # God class check (via AST)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            method_count = sum(
                1 for n in ast.walk(node)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
            if method_count > 20:
                smells.append(
                    f"Line {node.lineno}: God class '{node.name}' has {method_count} methods "
                    f"(>20) — violates Single Responsibility Principle."
                )

    # Missing type hints on public functions
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                no_hints = all(
                    arg.annotation is None for arg in node.args.args
                )
                if no_hints and node.args.args:
                    smells.append(
                        f"Line {node.lineno}: Public function '{node.name}' has no type hints "
                        "— add annotations for static analysis and IDE support."
                    )

    return smells


def _calculate_debt_score(
    functions: list[dict[str, Any]],
    smells: list[str],
    imports: list[str],
) -> int:
    """Compute a technical debt score 0–100 from complexity, smells, and imports."""
    score = 0

    for fn in functions:
        cc = fn["cyclomatic_complexity"]
        if cc > 10:
            score += 15
        elif cc > 7:
            score += 8
        elif cc > 5:
            score += 4
        if not fn["has_type_hints"] and not fn["name"].startswith("_"):
            score += 3

    score += len(smells) * 6

    score += sum(
        4 for imp in imports
        if "DEPRECATED" in imp or "INSECURE" in imp
    )

    return min(score, 100)


def _build_ast_summary(tree: ast.Module) -> dict[str, int]:
    """Build a counts dictionary of key AST node types."""
    return {
        "total_nodes": sum(1 for _ in ast.walk(tree)),
        "function_defs": sum(
            1 for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ),
        "class_defs": sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef)),
        "try_blocks": sum(1 for n in ast.walk(tree) if isinstance(n, ast.Try)),
        "assignments": sum(1 for n in ast.walk(tree) if isinstance(n, ast.Assign)),
        "comprehensions": sum(
            1 for n in ast.walk(tree)
            if isinstance(n, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp))
        ),
        "lambda_exprs": sum(1 for n in ast.walk(tree) if isinstance(n, ast.Lambda)),
        "global_stmts": sum(1 for n in ast.walk(tree) if isinstance(n, ast.Global)),
    }


def compute_parse_result(file_path: str) -> str:
    """
    Run the full AST-based structural analysis on a Python file and return JSON.

    This is the callable form used by main.py to pre-compute the parse result
    before crew kickoff, avoiding the ReAct tool-loop problem with Claude 4.
    The @tool-decorated parse_code_file below delegates to this function.
    """
    if not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"})

    if not file_path.endswith(".py"):
        return json.dumps({
            "error": "Only Python (.py) files are supported by CodeParserTool v1.",
            "tip": "For Java/Go/TypeScript files, extend this tool with tree-sitter.",
        })

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            source = fh.read()
    except OSError as exc:
        return json.dumps({"error": f"Cannot read file: {exc}"})

    if not source.strip():
        return json.dumps({"error": "Source file is empty."})

    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError as exc:
        return json.dumps({
            "error": f"Syntax error — cannot parse file: {exc}",
            "line": exc.lineno,
            "offset": exc.offset,
        })

    functions = _extract_functions(tree)
    classes = _extract_classes(tree)
    imports = _extract_imports(tree)
    smells = _detect_code_smells(source, tree)
    debt_score = _calculate_debt_score(functions, smells, imports)
    ast_summary = _build_ast_summary(tree)

    avg_complexity = (
        round(sum(f["cyclomatic_complexity"] for f in functions) / len(functions), 1)
        if functions else 0
    )
    high_cc_fns = [f["name"] for f in functions if f["cyclomatic_complexity"] > 10]
    untyped_fns = [f["name"] for f in functions if not f["has_type_hints"]]

    structural_observations = (
        f"File has {len(functions)} functions with average cyclomatic complexity {avg_complexity}. "
        + (f"HIGH COMPLEXITY ALERT — {len(high_cc_fns)} functions exceed CC>10: {high_cc_fns}. " if high_cc_fns else "")
        + (f"{len(untyped_fns)} public functions lack type hints. " if untyped_fns else "All public functions are type-hinted. ")
        + f"Technical debt score: {debt_score}/100. "
        + f"Detected {len(smells)} code smells requiring remediation. "
        + (f"INSECURE/DEPRECATED imports found: {[i for i in imports if '[' in i]}." if any('[' in i for i in imports) else "No deprecated imports detected.")
    )

    result = {
        "file_path": file_path,
        "language": "Python",
        "total_lines": len(source.splitlines()),
        "total_characters": len(source),
        "functions": functions,
        "classes": classes,
        "class_names": [c["name"] for c in classes],
        "imports": imports,
        "code_smells": smells,
        "technical_debt_score": debt_score,
        "avg_cyclomatic_complexity": avg_complexity,
        "high_complexity_functions": high_cc_fns,
        "untyped_public_functions": untyped_fns,
        "ast_summary": ast_summary,
        "structural_observations": structural_observations,
    }

    return json.dumps(result, indent=2, default=str)


@tool("CodeParserTool")
def parse_code_file(file_path: str) -> str:
    """
    Parse a Python source file to produce a comprehensive structural analysis.

    Extracts the Abstract Syntax Tree (AST), inventories all functions and classes
    with cyclomatic complexity scores and type-hint coverage, maps import dependencies
    (flagging deprecated/insecure modules), and surfaces code smells with exact line
    numbers. Calculates an aggregate technical debt score (0–100).

    Args:
        file_path: Absolute or relative path to the Python (.py) source file.

    Returns:
        JSON string with keys: file_path, language, total_lines, functions,
        class_names (with method_count), imports (with flags), code_smells,
        technical_debt_score, ast_summary, structural_observations.
    """
    return compute_parse_result(file_path)
