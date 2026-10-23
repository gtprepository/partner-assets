"""
Pydantic v2 structured output schemas for the Multi-Agent Code Refactoring & Audit Crew.
All models enforce strict validation to ensure type-safe data exchange between agents.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class SeverityLevel(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class NISTCategory(str, Enum):
    GOVERN = "GV - Govern"
    IDENTIFY = "ID - Identify"
    PROTECT = "PR - Protect"
    DETECT = "DE - Detect"
    RESPOND = "RS - Respond"
    RECOVER = "RC - Recover"


class RiskRating(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFORMATIONAL = "Informational"


class VulnerabilityFinding(BaseModel):
    """A single security vulnerability finding from the compliance audit."""

    title: str = Field(
        ...,
        min_length=5,
        description="Short, descriptive title of the vulnerability",
    )
    severity: SeverityLevel = Field(
        ...,
        description="Severity grade: Critical, High, Medium, or Low",
    )
    cwe_id: str = Field(
        ...,
        pattern=r"^CWE-\d+$",
        description="CWE identifier in format CWE-NNN (e.g. CWE-89)",
    )
    nist_mapping: NISTCategory = Field(
        ...,
        description="Primary NIST CSF 2.0 category this finding maps to",
    )
    owasp_category: Optional[str] = Field(
        default=None,
        description="OWASP Top 10 (2021) category if applicable (e.g. A03:2021 – Injection)",
    )
    line_numbers: List[int] = Field(
        default_factory=list,
        description="Source line numbers where the vulnerability was detected",
    )
    vulnerable_code_snippet: Optional[str] = Field(
        default=None,
        max_length=500,
        description="The vulnerable code excerpt (max 500 chars)",
    )
    remediation_suggestion: str = Field(
        ...,
        min_length=20,
        description="Specific, actionable remediation guidance for this finding",
    )
    false_positive_likelihood: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Estimated probability this is a false positive (0.0 = definite, 1.0 = certain FP)",
    )
    rule_id: Optional[str] = Field(
        default=None,
        description="Internal rule identifier that triggered this finding",
    )

    @field_validator("line_numbers")
    @classmethod
    def validate_line_numbers(cls, v: List[int]) -> List[int]:
        return [ln for ln in v if ln > 0]


class AuditReport(BaseModel):
    """Complete security and compliance audit report for a scanned source file."""

    scanned_file: str = Field(
        ...,
        description="Path to the scanned source file",
    )
    scan_timestamp: str = Field(
        ...,
        description="ISO 8601 UTC timestamp of when the scan was performed",
    )
    total_vulnerabilities: int = Field(
        ...,
        ge=0,
        description="Total count of unique vulnerability findings",
    )
    critical_count: int = Field(default=0, ge=0)
    high_count: int = Field(default=0, ge=0)
    medium_count: int = Field(default=0, ge=0)
    low_count: int = Field(default=0, ge=0)
    findings: List[VulnerabilityFinding] = Field(
        default_factory=list,
        description="Ordered list of vulnerability findings (Critical first)",
    )
    overall_risk_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Weighted overall risk score from 0.0 (clean) to 10.0 (critical)",
    )
    compliance_summary: str = Field(
        ...,
        description="Executive-level narrative summary of the compliance posture",
    )
    nist_coverage: Dict[str, int] = Field(
        default_factory=dict,
        description="Map of NIST CSF 2.0 category to finding count",
    )

    @model_validator(mode="after")
    def validate_counts_match(self) -> "AuditReport":
        computed = self.critical_count + self.high_count + self.medium_count + self.low_count
        if self.findings and computed == 0:
            from collections import Counter

            counts = Counter(f.severity for f in self.findings)
            self.critical_count = counts.get(SeverityLevel.CRITICAL, 0)
            self.high_count = counts.get(SeverityLevel.HIGH, 0)
            self.medium_count = counts.get(SeverityLevel.MEDIUM, 0)
            self.low_count = counts.get(SeverityLevel.LOW, 0)
        return self

    def severity_breakdown(self) -> Dict[str, int]:
        return {
            "Critical": self.critical_count,
            "High": self.high_count,
            "Medium": self.medium_count,
            "Low": self.low_count,
        }

    def critical_and_high_findings(self) -> List[VulnerabilityFinding]:
        return [
            f for f in self.findings
            if f.severity in (SeverityLevel.CRITICAL, SeverityLevel.HIGH)
        ]


class FunctionProfile(BaseModel):
    """AST-extracted profile of a single function or method."""

    name: str = Field(..., description="Function or method name")
    line_start: int = Field(..., gt=0)
    line_end: int = Field(..., gt=0)
    cyclomatic_complexity: int = Field(
        ...,
        ge=1,
        description="McCabe cyclomatic complexity score (1 = simplest)",
    )
    has_type_hints: bool = Field(
        ...,
        description="True if at least one parameter has a type annotation",
    )
    parameters: List[str] = Field(default_factory=list)
    return_type: Optional[str] = Field(
        default=None,
        description="Return type annotation as string, or None if absent",
    )

    @property
    def complexity_grade(self) -> str:
        if self.cyclomatic_complexity <= 4:
            return "Good"
        if self.cyclomatic_complexity <= 7:
            return "Moderate"
        if self.cyclomatic_complexity <= 10:
            return "High"
        return "Critical"


class ParsedCodeContext(BaseModel):
    """Structural analysis output from the code parser agent."""

    file_path: str
    language: str = Field(default="Python")
    total_lines: int = Field(..., ge=0)
    functions: List[FunctionProfile] = Field(default_factory=list)
    class_names: List[str] = Field(default_factory=list)
    imports: List[str] = Field(default_factory=list)
    code_smells: List[str] = Field(default_factory=list)
    technical_debt_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Aggregate technical debt score (0 = clean, 100 = maximum debt)",
    )
    ast_summary: Dict[str, Any] = Field(default_factory=dict)
    source_preview: Optional[str] = Field(default=None)

    def high_complexity_functions(self, threshold: int = 10) -> List[FunctionProfile]:
        return [f for f in self.functions if f.cyclomatic_complexity >= threshold]

    def untyped_functions(self) -> List[FunctionProfile]:
        return [f for f in self.functions if not f.has_type_hints]


class RefactorOutput(BaseModel):
    """Complete output package from the refactoring engineer agent."""

    original_code: str = Field(
        default="",
        description="Complete original source code before any refactoring (filled by main.py)",
    )
    refactored_code: str = Field(
        ...,
        description="Complete, fully runnable refactored source code (no placeholders)",
    )
    unit_tests: str = Field(
        ...,
        description="Complete, runnable pytest test file covering the refactored code",
    )
    git_diff: str = Field(
        default="",
        description="Unified git diff patch in standard format (--- a/ +++ b/ headers)",
    )
    pr_title: str = Field(
        default="",
        description="Pull request title following conventional commits format",
    )
    pr_body_markdown: str = Field(
        default="",
        description="Full GitHub/GitLab PR description in Markdown with all required sections",
    )
    jira_comment: Optional[str] = Field(
        default=None,
        description="Jira panel markup comment block for the linked issue",
    )
    risk_rating: RiskRating = Field(
        default=RiskRating.CRITICAL,
        description="Overall pre-refactor risk rating for the file",
    )
    files_changed: int = Field(default=1, ge=1)
    lines_added: int = Field(default=0, ge=0)
    lines_removed: int = Field(default=0, ge=0)

    @property
    def net_line_change(self) -> int:
        return self.lines_added - self.lines_removed

    @field_validator("refactored_code")
    @classmethod
    def refactored_must_differ(cls, v: str, info: Any) -> str:
        original = (info.data or {}).get("original_code", "")
        if original and v.strip() == original.strip():
            raise ValueError("refactored_code must differ from original_code")
        return v
