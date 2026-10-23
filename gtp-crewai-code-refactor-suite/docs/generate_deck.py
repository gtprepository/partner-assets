"""
generate_deck.py — Creates the GTP CrewAI sales one-pager as a .pptx file.
Run from the repo root: python docs/generate_deck.py
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import os

# ── Colour palette ─────────────────────────────────────────────────────────────
NAVY       = RGBColor(0x0D, 0x1B, 0x2A)   # slide background
DARK_BLUE  = RGBColor(0x10, 0x2A, 0x4A)   # section header bars
GOLD       = RGBColor(0xF5, 0xA6, 0x23)   # accent / highlights
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GREY = RGBColor(0xD0, 0xD8, 0xE8)
MID_GREY   = RGBColor(0x8A, 0x9B, 0xB4)
GREEN      = RGBColor(0x2E, 0xCC, 0x71)
RED        = RGBColor(0xE7, 0x4C, 0x3C)

W = Inches(13.33)   # widescreen 16:9
H = Inches(7.5)


def new_prs() -> Presentation:
    prs = Presentation()
    prs.slide_width  = W
    prs.slide_height = H
    return prs


def blank_slide(prs: Presentation):
    blank_layout = prs.slide_layouts[6]   # completely blank
    return prs.slides.add_slide(blank_layout)


def bg(slide, color: RGBColor = NAVY):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_rect(slide, left, top, width, height, fill_color, alpha=None):
    shape = slide.shapes.add_shape(
        1,   # MSO_SHAPE_TYPE.RECTANGLE
        left, top, width, height,
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()
    return shape


def add_text(slide, text, left, top, width, height,
             font_size=18, bold=False, color=WHITE,
             align=PP_ALIGN.LEFT, wrap=True, italic=False):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return txBox


def add_bullet_box(slide, items, left, top, width, height,
                   font_size=16, title=None, title_color=GOLD,
                   bullet_color=WHITE, indent=True):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    first = True
    if title:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        run = p.add_run()
        run.text = title
        run.font.size = Pt(font_size + 2)
        run.font.bold = True
        run.font.color.rgb = title_color

    for item in items:
        p = tf.add_paragraph() if not first else tf.paragraphs[0]
        first = False
        p.space_before = Pt(4)
        if indent:
            p.level = 1
        run = p.add_run()
        run.text = ("▸  " if indent else "") + item
        run.font.size = Pt(font_size)
        run.font.color.rgb = bullet_color
    return txBox


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE
# ══════════════════════════════════════════════════════════════════════════════
def slide_title(prs):
    sl = blank_slide(prs)
    bg(sl, NAVY)

    # Gold accent bar left edge
    add_rect(sl, Inches(0), Inches(0), Inches(0.12), H, GOLD)

    # Top stripe
    add_rect(sl, Inches(0.12), Inches(0), W - Inches(0.12), Inches(0.06), DARK_BLUE)

    # GTP badge
    add_rect(sl, Inches(0.35), Inches(0.25), Inches(2.8), Inches(0.55), GOLD)
    add_text(sl, "GTP ACCELERATORS", Inches(0.4), Inches(0.27), Inches(2.7), Inches(0.5),
             font_size=13, bold=True, color=NAVY, align=PP_ALIGN.CENTER)

    # Main headline
    add_text(sl,
             "Autonomous Code Security\n& Refactoring",
             Inches(0.5), Inches(1.1), Inches(8), Inches(1.9),
             font_size=44, bold=True, color=WHITE)

    # Sub-headline
    add_text(sl,
             "Powered by Multi-Agent AI  ·  CrewAI  ·  Anthropic Claude",
             Inches(0.5), Inches(2.9), Inches(9), Inches(0.6),
             font_size=20, bold=False, color=GOLD)

    # Divider
    add_rect(sl, Inches(0.5), Inches(3.6), Inches(6), Inches(0.04), GOLD)

    # Tagline
    add_text(sl,
             "From legacy vulnerability to production-ready secure code —\n"
             "audit-mapped, tested, and PR-packaged in one automated run.",
             Inches(0.5), Inches(3.75), Inches(9.5), Inches(1.2),
             font_size=18, color=LIGHT_GREY)

    # Bottom right — partnership strip
    add_rect(sl, Inches(8.5), Inches(6.5), Inches(4.7), Inches(0.75), DARK_BLUE)
    add_text(sl, "Built on CrewAI  ·  Powered by Claude",
             Inches(8.6), Inches(6.58), Inches(4.5), Inches(0.55),
             font_size=12, color=GOLD, align=PP_ALIGN.CENTER)

    # Bottom left — confidential
    add_text(sl, "Confidential — For Client Discussion Only",
             Inches(0.3), Inches(7.15), Inches(5), Inches(0.3),
             font_size=10, color=MID_GREY)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — THE PROBLEM
# ══════════════════════════════════════════════════════════════════════════════
def slide_problem(prs):
    sl = blank_slide(prs)
    bg(sl, NAVY)
    add_rect(sl, Inches(0), Inches(0), Inches(0.12), H, GOLD)

    # Header bar
    add_rect(sl, Inches(0.12), Inches(0), W - Inches(0.12), Inches(1.05), DARK_BLUE)
    add_text(sl, "THE PROBLEM", Inches(0.4), Inches(0.08), Inches(6), Inches(0.45),
             font_size=11, bold=True, color=GOLD)
    add_text(sl, "Legacy Code is a Growing Security & Compliance Liability",
             Inches(0.4), Inches(0.42), Inches(12), Inches(0.6),
             font_size=24, bold=True, color=WHITE)

    # Stat boxes
    stats = [
        ("$4.88M", "Average cost of a\ndata breach — 2024\n(IBM Report)"),
        ("17", "Security rules in the\nbuilt-in scanner\n(CWE / OWASP mapped)"),
        ("3", "Specialist agents:\narchitect, security\nassessor, refactorer"),
        ("100%", "Of SOC 2 / ISO 27001 audits\nrequire documented\nremediation evidence"),
    ]
    for i, (stat, label) in enumerate(stats):
        x = Inches(0.35 + i * 3.22)
        add_rect(sl, x, Inches(1.25), Inches(3.0), Inches(2.1), DARK_BLUE)
        add_rect(sl, x, Inches(1.25), Inches(3.0), Inches(0.06), GOLD)
        add_text(sl, stat, x, Inches(1.35), Inches(3.0), Inches(0.85),
                 font_size=36, bold=True, color=GOLD, align=PP_ALIGN.CENTER)
        add_text(sl, label, x, Inches(2.1), Inches(3.0), Inches(1.2),
                 font_size=13, color=LIGHT_GREY, align=PP_ALIGN.CENTER)

    # Pain points
    add_rect(sl, Inches(0.25), Inches(3.55), Inches(12.8), Inches(0.04), DARK_BLUE)

    pains = [
        ("SQL Injection, hardcoded secrets, unsafe deserialization",
         "The most common critical vulnerabilities — all detectable and fixable, yet routinely missed in manual reviews"),
        ("Manual audits don't scale",
         "A senior security engineer reviewing code manually costs $200–400/hr and covers 50–100 lines/hour"),
        ("Compliance gap = audit risk",
         "Undocumented vulnerability remediation exposes organisations to failed SOC 2, ISO 27001, and FedRAMP audits"),
    ]
    for i, (title, body) in enumerate(pains):
        x = Inches(0.35 + i * 4.3)
        add_text(sl, f"▸  {title}", x, Inches(3.75), Inches(4.1), Inches(0.45),
                 font_size=13, bold=True, color=GOLD)
        add_text(sl, body, x, Inches(4.15), Inches(4.1), Inches(0.9),
                 font_size=12, color=LIGHT_GREY)

    # Footer
    add_rect(sl, Inches(0.12), Inches(7.2), W - Inches(0.12), Inches(0.04), GOLD)
    add_text(sl, "GTP Accelerators  ·  Confidential",
             Inches(0.4), Inches(7.25), Inches(5), Inches(0.22),
             font_size=9, color=MID_GREY)
    add_text(sl, "2 / 6",
             Inches(12.5), Inches(7.25), Inches(0.7), Inches(0.22),
             font_size=9, color=MID_GREY, align=PP_ALIGN.RIGHT)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — WHAT GTP HAS BUILT
# ══════════════════════════════════════════════════════════════════════════════
def slide_solution(prs):
    sl = blank_slide(prs)
    bg(sl, NAVY)
    add_rect(sl, Inches(0), Inches(0), Inches(0.12), H, GOLD)
    add_rect(sl, Inches(0.12), Inches(0), W - Inches(0.12), Inches(1.05), DARK_BLUE)
    add_text(sl, "THE SOLUTION", Inches(0.4), Inches(0.08), Inches(6), Inches(0.45),
             font_size=11, bold=True, color=GOLD)
    add_text(sl, "One Command. Five Enterprise-Grade Outputs.",
             Inches(0.4), Inches(0.42), Inches(12), Inches(0.6),
             font_size=24, bold=True, color=WHITE)

    # Output cards
    outputs = [
        ("Security Audit Report", GREEN,
         "Every finding mapped to\nNIST CSF 2.0, OWASP Top 10,\nand CWE — line-precise,\nseverity graded"),
        ("Refactored Source Code", GREEN,
         "Complete, runnable, type-hinted\nsecure replacement module.\nZero placeholders."),
        ("Pytest Suite (15+ tests)", GREEN,
         "Full test coverage of the\nrefactored module — ready\nfor your CI/CD pipeline"),
        ("Unified Git Diff Patch", GREEN,
         "Standard .patch file\nreviewable in GitHub,\nGitLab, Bitbucket"),
        ("PR + Jira Audit Package", GREEN,
         "Full PR description, HITL\nchecklist, and Jira panel\ncomment — audit-ready"),
    ]
    for i, (title, color, body) in enumerate(outputs):
        x = Inches(0.28 + i * 2.6)
        add_rect(sl, x, Inches(1.2), Inches(2.45), Inches(3.3), DARK_BLUE)
        add_rect(sl, x, Inches(1.2), Inches(2.45), Inches(0.07), color)
        add_text(sl, title, x + Inches(0.1), Inches(1.35), Inches(2.25), Inches(0.6),
                 font_size=13, bold=True, color=color)
        add_text(sl, body, x + Inches(0.1), Inches(1.9), Inches(2.25), Inches(2.4),
                 font_size=12, color=LIGHT_GREY)

    # Flow arrow
    add_rect(sl, Inches(0.28), Inches(4.7), Inches(12.75), Inches(0.06), DARK_BLUE)
    add_text(sl, "LEGACY FILE IN  ──────────────────────────────────────────────────────────────────────────  SECURE, TESTED, DOCUMENTED CODE OUT",
             Inches(0.3), Inches(4.82), Inches(12.7), Inches(0.4),
             font_size=11, color=GOLD, align=PP_ALIGN.CENTER)

    # Time stamp
    add_rect(sl, Inches(4.5), Inches(5.35), Inches(4.33), Inches(0.75), GOLD)
    add_text(sl, "End-to-End in One Automated Run",
             Inches(4.5), Inches(5.48), Inches(4.33), Inches(0.5),
             font_size=16, bold=True, color=NAVY, align=PP_ALIGN.CENTER)

    # Before/after snippet
    add_text(sl,
             'BEFORE:  cursor.execute("SELECT * FROM users WHERE id=\'" + user_id + "\'")',
             Inches(0.4), Inches(6.25), Inches(12.5), Inches(0.35),
             font_size=11, color=RED, italic=True)
    add_text(sl,
             "AFTER:   cursor.execute(\"SELECT * FROM users WHERE id = %s\", (user_id,))",
             Inches(0.4), Inches(6.6), Inches(12.5), Inches(0.35),
             font_size=11, color=GREEN, italic=True)

    add_rect(sl, Inches(0.12), Inches(7.2), W - Inches(0.12), Inches(0.04), GOLD)
    add_text(sl, "GTP Accelerators  ·  Confidential", Inches(0.4), Inches(7.25),
             Inches(5), Inches(0.22), font_size=9, color=MID_GREY)
    add_text(sl, "3 / 6", Inches(12.5), Inches(7.25), Inches(0.7), Inches(0.22),
             font_size=9, color=MID_GREY, align=PP_ALIGN.RIGHT)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — HOW CREWAI POWERS THIS
# ══════════════════════════════════════════════════════════════════════════════
def slide_crewai(prs):
    sl = blank_slide(prs)
    bg(sl, NAVY)
    add_rect(sl, Inches(0), Inches(0), Inches(0.12), H, GOLD)
    add_rect(sl, Inches(0.12), Inches(0), W - Inches(0.12), Inches(1.05), DARK_BLUE)
    add_text(sl, "THE TECHNOLOGY", Inches(0.4), Inches(0.08), Inches(8), Inches(0.45),
             font_size=11, bold=True, color=GOLD)
    add_text(sl, "How CrewAI Multi-Agent Orchestration Powers This Pipeline",
             Inches(0.4), Inches(0.42), Inches(12), Inches(0.6),
             font_size=24, bold=True, color=WHITE)

    # Agent pipeline
    agents = [
        ("01", "Principal Software\nArchitect", "AST-based structural analysis\nCyclomatic complexity scoring\nCode smell detection\nTechnical debt quantification"),
        ("02", "Lead Cybersecurity\nArchitect & CISO Advisor", "NIST CSF 2.0 category mapping\nOWASP Top 10 (2021) grading\nCWE identifier assignment\nSeverity & risk scoring"),
        ("03", "Senior AI-Native\nRefactoring Engineer", "Full remediation implementation\nType-hinted, secure code output\nComplete pytest suite generation\nConventional commits PR title"),
    ]
    for i, (num, title, details) in enumerate(agents):
        x = Inches(0.28 + i * 4.35)
        add_rect(sl, x, Inches(1.2), Inches(4.1), Inches(3.8), DARK_BLUE)
        add_rect(sl, x, Inches(1.2), Inches(0.55), Inches(3.8), GOLD)
        add_text(sl, f"AGENT {num}", x + Inches(0.08), Inches(1.26),
                 Inches(0.9), Inches(0.42), font_size=13, bold=True, color=NAVY)
        add_text(sl, title, x + Inches(0.12), Inches(1.72), Inches(3.8), Inches(0.65),
                 font_size=14, bold=True, color=GOLD)
        add_text(sl, details, x + Inches(0.15), Inches(2.32), Inches(3.75), Inches(2.5),
                 font_size=12, color=LIGHT_GREY)

    # Arrows between agents
    for x in [Inches(4.38), Inches(8.73)]:
        add_text(sl, "▶", x, Inches(2.6), Inches(0.28), Inches(0.45),
                 font_size=22, color=GOLD, align=PP_ALIGN.CENTER)

    # Why CrewAI row
    add_rect(sl, Inches(0.25), Inches(5.2), Inches(12.8), Inches(0.04), DARK_BLUE)
    add_text(sl, "WHY CREWAI", Inches(0.4), Inches(5.35), Inches(12), Inches(0.35),
             font_size=11, bold=True, color=GOLD)

    reasons = [
        ("Role-based Specialisation", "Each agent is optimised for its domain — no single model doing everything"),
        ("Context Chaining", "Downstream agents receive full upstream output as grounded context — eliminates hallucination"),
        ("Deterministic Workflow", "Sequential execution with built-in Human-in-the-Loop checkpoints"),
        ("Tool Extensibility", "Plug in SAST/DAST scanners, Jira API, GitHub API — no re-architecture"),
    ]
    for i, (title, body) in enumerate(reasons):
        x = Inches(0.28 + i * 3.27)
        add_text(sl, f"▸  {title}", x, Inches(5.75), Inches(3.1), Inches(0.38),
                 font_size=12, bold=True, color=WHITE)
        add_text(sl, body, x, Inches(6.12), Inches(3.1), Inches(0.75),
                 font_size=11, color=MID_GREY)

    add_rect(sl, Inches(0.12), Inches(7.2), W - Inches(0.12), Inches(0.04), GOLD)
    add_text(sl, "GTP Accelerators  ·  Confidential", Inches(0.4), Inches(7.25),
             Inches(5), Inches(0.22), font_size=9, color=MID_GREY)
    add_text(sl, "4 / 6", Inches(12.5), Inches(7.25), Inches(0.7), Inches(0.22),
             font_size=9, color=MID_GREY, align=PP_ALIGN.RIGHT)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — HOW GTP HELPS ORGANISATIONS
# ══════════════════════════════════════════════════════════════════════════════
def slide_value(prs):
    sl = blank_slide(prs)
    bg(sl, NAVY)
    add_rect(sl, Inches(0), Inches(0), Inches(0.12), H, GOLD)
    add_rect(sl, Inches(0.12), Inches(0), W - Inches(0.12), Inches(1.05), DARK_BLUE)
    add_text(sl, "BUSINESS VALUE", Inches(0.4), Inches(0.08), Inches(8), Inches(0.45),
             font_size=11, bold=True, color=GOLD)
    add_text(sl, "How GTP Helps Organisations Leverage CrewAI at Enterprise Scale",
             Inches(0.4), Inches(0.42), Inches(12), Inches(0.6),
             font_size=24, bold=True, color=WHITE)

    personas = [
        ("Engineering Teams", GOLD, [
            "Eliminate weeks of refactoring backlog in hours",
            "Enforce consistent security patterns across all codebases",
            "Plug-and-play with existing PR and CI/CD workflows",
            "Reduce code review cycles — diffs are clean and annotated",
        ]),
        ("Security & Compliance", GOLD, [
            "Every finding documented for SOC 2 / ISO 27001 / FedRAMP",
            "Reduce mean-time-to-remediation from days to minutes",
            "Consistent, repeatable audit trail for every code change",
            "17-rule scanner extensible with your internal standards",
        ]),
        ("CISOs & Engineering Leadership", GOLD, [
            "Quantify and track technical debt reduction over time",
            "Free senior engineers from repetitive audit work",
            "Demonstrate proactive security posture to regulators",
            "Board-ready metrics: risk score, findings fixed, MTTR",
        ]),
        ("GTP Delivery Model", GREEN, [
            "On-premise — source code never leaves your VPC",
            "CI/CD integration via GitHub Actions / Azure DevOps",
            "Custom rule sets for internal coding standards",
            "Java, TypeScript, Go — roadmapped via tree-sitter",
        ]),
    ]
    for i, (title, accent, items) in enumerate(personas):
        x = Inches(0.28 + i * 3.27)
        add_rect(sl, x, Inches(1.2), Inches(3.1), Inches(5.1), DARK_BLUE)
        add_rect(sl, x, Inches(1.2), Inches(3.1), Inches(0.06), accent)
        add_text(sl, title, x + Inches(0.12), Inches(1.33), Inches(2.9), Inches(0.55),
                 font_size=13, bold=True, color=accent)
        for j, item in enumerate(items):
            add_text(sl, f"▸  {item}", x + Inches(0.12),
                     Inches(1.95 + j * 0.98), Inches(2.9), Inches(0.85),
                     font_size=11, color=LIGHT_GREY)

    add_rect(sl, Inches(0.12), Inches(7.2), W - Inches(0.12), Inches(0.04), GOLD)
    add_text(sl, "GTP Accelerators  ·  Confidential", Inches(0.4), Inches(7.25),
             Inches(5), Inches(0.22), font_size=9, color=MID_GREY)
    add_text(sl, "5 / 6", Inches(12.5), Inches(7.25), Inches(0.7), Inches(0.22),
             font_size=9, color=MID_GREY, align=PP_ALIGN.RIGHT)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — PARTNERSHIPS + CTA
# ══════════════════════════════════════════════════════════════════════════════
def slide_cta(prs):
    sl = blank_slide(prs)
    bg(sl, NAVY)
    add_rect(sl, Inches(0), Inches(0), Inches(0.12), H, GOLD)
    add_rect(sl, Inches(0.12), Inches(0), W - Inches(0.12), Inches(1.05), DARK_BLUE)
    add_text(sl, "TECHNOLOGY & NEXT STEPS", Inches(0.4), Inches(0.08),
             Inches(10), Inches(0.45), font_size=11, bold=True, color=GOLD)
    add_text(sl, "Built on Leading AI Technology",
             Inches(0.4), Inches(0.42), Inches(12), Inches(0.6),
             font_size=24, bold=True, color=WHITE)

    # Partner cards
    partners = [
        ("CrewAI", "Framework",
         "Multi-agent orchestration framework powering the pipeline.\n"
         "GTP builds on CrewAI, adding production\n"
         "hardening, custom tooling, and enterprise implementation expertise\n"
         "that takes CrewAI from framework to business outcome."),
        ("Anthropic Claude", "Model",
         "Foundation model powering all three specialist agents.\n"
         "Claude claude-sonnet-4-6 provides enterprise-grade reasoning with\n"
         "data privacy guarantees critical for code that touches\n"
         "production security controls."),
    ]
    for i, (name, badge, body) in enumerate(partners):
        x = Inches(0.35 + i * 6.4)
        add_rect(sl, x, Inches(1.25), Inches(6.1), Inches(3.2), DARK_BLUE)
        add_rect(sl, x, Inches(1.25), Inches(6.1), Inches(0.07), GOLD)
        add_rect(sl, x + Inches(4.3), Inches(1.38), Inches(1.65), Inches(0.38), GOLD)
        add_text(sl, badge, x + Inches(4.35), Inches(1.41), Inches(1.55), Inches(0.32),
                 font_size=10, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
        add_text(sl, name, x + Inches(0.15), Inches(1.38), Inches(4.1), Inches(0.55),
                 font_size=20, bold=True, color=GOLD)
        add_text(sl, body, x + Inches(0.15), Inches(1.95), Inches(5.8), Inches(2.3),
                 font_size=13, color=LIGHT_GREY)

    # Quote
    add_rect(sl, Inches(0.35), Inches(4.65), Inches(12.6), Inches(1.1), DARK_BLUE)
    add_rect(sl, Inches(0.35), Inches(4.65), Inches(0.06), Inches(1.1), GOLD)
    add_text(sl,
             '"We don\'t just implement AI frameworks. We engineer AI systems that deliver '
             'measurable outcomes your security and compliance teams can stand behind."',
             Inches(0.6), Inches(4.8), Inches(12.1), Inches(0.65),
             font_size=14, italic=True, color=WHITE)
    add_text(sl, "— GTP Accelerators", Inches(0.6), Inches(5.45),
             Inches(6), Inches(0.28), font_size=12, color=GOLD)

    # CTA box
    add_rect(sl, Inches(0.35), Inches(5.95), Inches(12.6), Inches(1.05), GOLD)
    add_text(sl, "Ready to audit your first codebase?",
             Inches(0.55), Inches(6.0), Inches(7), Inches(0.45),
             font_size=16, bold=True, color=NAVY)
    add_text(sl,
             "GTP offers a complimentary 1-hour discovery session — "
             "we'll demonstrate the crew against a real file from your codebase.",
             Inches(0.55), Inches(6.42), Inches(8.5), Inches(0.5),
             font_size=12, color=NAVY)
    add_text(sl, "pjjeevan@gmail.com",
             Inches(9.8), Inches(6.0), Inches(3.0), Inches(0.45),
             font_size=14, bold=True, color=NAVY, align=PP_ALIGN.RIGHT)
    add_text(sl, "github.com/gtprepository/gtp-crewai-code-refactor-suite",
             Inches(7.5), Inches(6.42), Inches(5.3), Inches(0.45),
             font_size=11, color=NAVY, align=PP_ALIGN.RIGHT)

    add_rect(sl, Inches(0.12), Inches(7.2), W - Inches(0.12), Inches(0.04), GOLD)
    add_text(sl, "GTP Accelerators  ·  Confidential", Inches(0.4), Inches(7.25),
             Inches(5), Inches(0.22), font_size=9, color=MID_GREY)
    add_text(sl, "6 / 6", Inches(12.5), Inches(7.25), Inches(0.7), Inches(0.22),
             font_size=9, color=MID_GREY, align=PP_ALIGN.RIGHT)


# ══════════════════════════════════════════════════════════════════════════════
# BUILD
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    prs = new_prs()
    slide_title(prs)
    slide_problem(prs)
    slide_solution(prs)
    slide_crewai(prs)
    slide_value(prs)
    slide_cta(prs)

    out = os.path.join(os.path.dirname(__file__), "GTP_CrewAI_Solution_Brief.pptx")
    prs.save(out)
    print(f"Saved: {out}")
