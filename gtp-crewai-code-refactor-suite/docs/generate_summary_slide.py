"""
generate_summary_slide.py
Single executive-summary slide — GTP builds on CrewAI.
Run: python docs/generate_summary_slide.py
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── GTP Brand Palette (GTP SocialLink AI Flyer) ─────────────────────────────
NAVY      = RGBColor(0x01, 0x1D, 0x57)   # #011D57
BLUE      = RGBColor(0x00, 0x48, 0xE5)   # #0048E5
GREEN     = RGBColor(0x00, 0xE6, 0xA5)   # #00E6A5
LIGHT_BG  = RGBColor(0xF5, 0xF8, 0xFA)   # #F5F8FA
DARK_HDR  = RGBColor(0x10, 0x10, 0x10)   # #101010
CARD_BG   = RGBColor(0xEE, 0xF2, 0xFF)   # #EEF2FF
BODY_GRY  = RGBColor(0x6B, 0x72, 0x80)   # #6B7280
SUBTITLE  = RGBColor(0xCB, 0xD5, 0xE1)   # #CBD5E1
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
DARK_TXT  = RGBColor(0x01, 0x1D, 0x57)

# ── Slide dimensions — portrait flyer (7.27" x 10.30") ──────────────────────
W      = Inches(7.27)
H      = Inches(10.30)
PAD    = Inches(0.16)
INNER  = W - 2 * PAD      # 6.95"
STRIPE = Inches(0.06)


def _prs():
    prs = Presentation()
    prs.slide_width  = W
    prs.slide_height = H
    return prs


def _blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _rect(slide, left, top, w, h, color):
    s = slide.shapes.add_shape(1, left, top, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = color
    s.line.fill.background()
    return s


def _txt(slide, text, left, top, w, h,
         size=10, bold=False, color=WHITE,
         align=PP_ALIGN.LEFT, italic=False, wrap=True):
    box = slide.shapes.add_textbox(left, top, w, h)
    tf  = box.text_frame
    tf.word_wrap = wrap
    p   = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text           = text
    run.font.size      = Pt(size)
    run.font.bold      = bold
    run.font.italic    = italic
    run.font.color.rgb = color
    return box


# ============================================================================
# LAYOUT  (all tops in inches, verified to sum to 10.30")
#
#  0.00 → 1.05  Header (navy)
#  1.05 → 1.82  Partnership positioning strip (light)
#  1.82 → 2.08  Section HDR: THE CREWAI PLATFORM
#  2.08 → 3.00  CrewAI product cards (3)          [h=0.92]
#  3.00 → 3.26  Section HDR: HOW GTP DELIVERS
#  3.26 → 4.82  GTP delivery pillars (2×2)        [h=1.56]
#  4.82 → 5.08  Section HDR: PROOF POINT
#  5.08 → 5.30  Proof-point intro line (light)    [h=0.22]
#  5.30 → 5.88  3-Agent pipeline flow             [h=0.58]  ← NEW
#  5.88 → 7.78  5 output rows                     [h=1.90]
#  7.78 → 7.99  Section HDR: STATS
#  7.99 → 8.52  Stat cards (4)                    [h=0.53]
#  8.52 → 10.30 CTA footer (navy)                 [h=1.78]
# ============================================================================

def build(prs):
    sl = _blank(prs)

    # =========================================================================
    # 1. HEADER  0" → 1.05"
    # =========================================================================
    HDR_H = Inches(1.05)
    _rect(sl, Inches(0), Inches(0), W, HDR_H, NAVY)
    _rect(sl, Inches(0), Inches(0), STRIPE, HDR_H, BLUE)

    _txt(sl, "GLOBAL TECHNOLOGY PARTNERS",
         STRIPE + Inches(0.12), Inches(0.07), Inches(4.80), Inches(0.30),
         size=11, bold=True, color=WHITE)
    _txt(sl, "Enterprise AI Solutions  |  globaltechnologypartners.com",
         STRIPE + Inches(0.12), Inches(0.37), Inches(4.80), Inches(0.22),
         size=8, color=SUBTITLE)

    # Prominent CrewAI Technology Partner badge
    _rect(sl, Inches(4.90), Inches(0.10), Inches(2.20), Inches(0.80), GREEN)
    _txt(sl, "BUILT ON",
         Inches(4.92), Inches(0.12), Inches(2.16), Inches(0.22),
         size=7, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
    _txt(sl, "CrewAI Multi-Agent",
         Inches(4.92), Inches(0.32), Inches(2.16), Inches(0.24),
         size=10, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
    _txt(sl, "Platform",
         Inches(4.92), Inches(0.54), Inches(2.16), Inches(0.22),
         size=10, bold=True, color=NAVY, align=PP_ALIGN.CENTER)

    _txt(sl, "Delivering CrewAI's Multi-Agent Platform to Your Enterprise — Designed. Built. Production-Ready.",
         STRIPE + Inches(0.12), Inches(0.72), Inches(4.60), Inches(0.28),
         size=7.5, italic=True, color=GREEN)

    # =========================================================================
    # 2. PARTNERSHIP POSITIONING STRIP  1.05" → 1.82"
    # =========================================================================
    PS_TOP = Inches(1.05)
    PS_H   = Inches(0.77)
    _rect(sl, Inches(0), PS_TOP, W, PS_H, LIGHT_BG)
    _txt(sl,
         "GTP builds on CrewAI to translate CrewAI's multi-agent platform into "
         "production-ready AI systems for your business — rapidly, reliably, and at enterprise scale. "
         "We help you unlock CrewAI value across your operations.",
         PAD, PS_TOP + Inches(0.08), INNER, PS_H - Inches(0.12),
         size=8.5, color=DARK_TXT, wrap=True)

    # =========================================================================
    # 3. THE CREWAI PLATFORM  1.82" → 3.00"
    # =========================================================================
    CP_HDR_TOP = Inches(1.82)
    _rect(sl, Inches(0), CP_HDR_TOP, W, Inches(0.26), DARK_HDR)
    _txt(sl, "THE CREWAI PLATFORM — WHAT WE BRING TO YOUR ORGANISATION",
         PAD + Inches(0.05), CP_HDR_TOP + Inches(0.05), INNER, Inches(0.18),
         size=8, bold=True, color=GREEN)

    CP_TOP = Inches(2.08)
    CP_H   = Inches(0.92)
    CP_W   = (INNER - Inches(0.06)) / 3
    crewai_products = [
        ("Crews",
         "Self-organising teams of specialist AI agents — defined roles, goals, and full context "
         "sharing. They collaborate like a human team to solve complex problems autonomously."),
        ("Flows",
         "Event-driven workflow orchestration — manages state, conditional branching, and "
         "business logic. The control layer that coordinates Crews end-to-end."),
        ("Enterprise Platform",
         "Production runtime with centralised governance, monitoring, and guardrails. "
         "65% of Fortune 500 run on CrewAI. 450M+ agentic workflows executed per month."),
    ]
    for i, (title, body) in enumerate(crewai_products):
        cx = PAD + i * (CP_W + Inches(0.03))
        _rect(sl, cx, CP_TOP, CP_W, CP_H, CARD_BG)
        _rect(sl, cx, CP_TOP, Inches(0.05), CP_H, GREEN)
        _txt(sl, title,
             cx + Inches(0.10), CP_TOP + Inches(0.06), CP_W - Inches(0.14), Inches(0.24),
             size=9, bold=True, color=NAVY)
        _txt(sl, body,
             cx + Inches(0.10), CP_TOP + Inches(0.30), CP_W - Inches(0.14), CP_H - Inches(0.34),
             size=7.5, color=BODY_GRY)

    # =========================================================================
    # 4. HOW GTP DELIVERS  3.00" → 4.82"
    # =========================================================================
    GD_HDR_TOP = Inches(3.00)
    _rect(sl, Inches(0), GD_HDR_TOP, W, Inches(0.26), DARK_HDR)
    _txt(sl, "HOW GTP HELPS YOU LEVERAGE CREWAI — YOUR IMPLEMENTATION TEAM",
         PAD + Inches(0.05), GD_HDR_TOP + Inches(0.05), INNER, Inches(0.18),
         size=8, bold=True, color=GREEN)

    GD_TOP = Inches(3.26)
    GD_H   = Inches(1.56)
    PILL_W = (INNER - Inches(0.06)) / 2
    pillars = [
        ("Discover & Design",
         "We map your business process to a CrewAI architecture — defining agent roles, tasks, "
         "and tools. From use-case discovery to agent blueprint in days, not months."),
        ("Build & Integrate",
         "We build and deploy custom CrewAI crews into your environment — your VPC, your CI/CD, "
         "your existing tools (Jira, Salesforce, ServiceNow, Snowflake, GitHub, and more)."),
        ("Automate at Scale",
         "We operationalise multi-agent workflows for high-volume, repeatable tasks — support, "
         "data processing, code review, compliance checks — running autonomously 24/7."),
        ("Govern & Evolve",
         "We embed CrewAI Enterprise governance — audit trails, guardrails, human-in-the-loop "
         "checkpoints, and monitoring — so AI runs compliantly and continuously improves."),
    ]
    PILL_H = (GD_H - Inches(0.04)) / 2
    for i, (title, body) in enumerate(pillars):
        col = i % 2
        row = i // 2
        px  = PAD + col * (PILL_W + Inches(0.06))
        py  = GD_TOP + row * (PILL_H + Inches(0.04))
        _rect(sl, px, py, PILL_W, PILL_H, NAVY)
        _rect(sl, px, py, Inches(0.05), PILL_H, GREEN)
        _txt(sl, title,
             px + Inches(0.10), py + Inches(0.06), PILL_W - Inches(0.14), Inches(0.22),
             size=9, bold=True, color=GREEN)
        _txt(sl, body,
             px + Inches(0.10), py + Inches(0.28), PILL_W - Inches(0.14), PILL_H - Inches(0.32),
             size=7.5, color=SUBTITLE)

    # =========================================================================
    # 5. PROOF POINT  4.82" → 7.78"
    # =========================================================================
    PP_HDR_TOP = Inches(4.82)
    _rect(sl, Inches(0), PP_HDR_TOP, W, Inches(0.26), DARK_HDR)
    _txt(sl, "PROOF POINT — A LIVE CREWAI CREW WE BUILT: CODE REFACTORING & AUDIT",
         PAD + Inches(0.05), PP_HDR_TOP + Inches(0.05), INNER, Inches(0.18),
         size=8, bold=True, color=GREEN)

    # Intro line
    PP_INTRO_TOP = Inches(5.08)
    _rect(sl, Inches(0), PP_INTRO_TOP, W, Inches(0.22), LIGHT_BG)
    _txt(sl, "One command — your legacy file in, five enterprise-grade outputs out — in one automated run.",
         PAD, PP_INTRO_TOP + Inches(0.03), INNER, Inches(0.18),
         size=8.5, bold=True, color=NAVY)

    # -----------------------------------------------------------------
    # 3-AGENT PIPELINE FLOW  5.30" → 5.88"
    # -----------------------------------------------------------------
    AG_TOP  = Inches(5.30)
    AG_FULL = Inches(0.58)
    AG_H    = Inches(0.52)      # card height (0.03" margin top+bottom)
    AG_W    = Inches(2.15)      # each agent card
    ARR_W   = Inches(0.17)      # arrow gap
    AG_GAP  = (INNER - 3 * AG_W - 2 * ARR_W) / 2   # distribute remaining space

    _rect(sl, Inches(0), AG_TOP, W, AG_FULL, CARD_BG)

    agents = [
        ("AGENT 01", "Principal Software Architect",
         "AST analysis, complexity & debt scoring  >>  passes structured parse report to Agent 02"),
        ("AGENT 02", "Lead Cybersecurity Architect",
         "NIST CSF 2.0, OWASP, CWE mapping & risk grading  >>  passes full audit to Agent 03"),
        ("AGENT 03", "Staff Refactoring Engineer",
         "Writes secure code, Pytest suite, PR title & risk rating using full upstream context"),
    ]

    x_positions = [
        PAD,
        PAD + AG_W + ARR_W,
        PAD + 2 * AG_W + 2 * ARR_W,
    ]
    arrow_positions = [
        PAD + AG_W,
        PAD + 2 * AG_W + ARR_W,
    ]

    for ax in arrow_positions:
        _txt(sl, ">",
             ax, AG_TOP + Inches(0.13), ARR_W, Inches(0.30),
             size=14, bold=True, color=BLUE, align=PP_ALIGN.CENTER)

    for i, (num, title, detail) in enumerate(agents):
        ax = x_positions[i]
        ay = AG_TOP + Inches(0.03)
        _rect(sl, ax, ay, AG_W, AG_H, NAVY)
        _rect(sl, ax, ay, Inches(0.05), AG_H, BLUE)
        _txt(sl, num,
             ax + Inches(0.09), ay + Inches(0.04), AG_W - Inches(0.12), Inches(0.16),
             size=6.5, bold=True, color=BLUE)
        _txt(sl, title,
             ax + Inches(0.09), ay + Inches(0.18), AG_W - Inches(0.12), Inches(0.18),
             size=8, bold=True, color=WHITE)
        _txt(sl, detail,
             ax + Inches(0.09), ay + Inches(0.34), AG_W - Inches(0.12), Inches(0.20),
             size=6.5, color=SUBTITLE, wrap=True)

    # -----------------------------------------------------------------
    # 5 OUTPUT ROWS  5.88" → 7.78"
    # -----------------------------------------------------------------
    OUT_TOP   = Inches(5.88)
    OUT_TOTAL = Inches(1.90)
    OUT_H     = OUT_TOTAL / 5
    _rect(sl, Inches(0), OUT_TOP, W, OUT_TOTAL, WHITE)

    outputs = [
        ("Security Audit Report",
         "Every finding mapped to NIST CSF 2.0, OWASP Top 10 & CWE — line-precise, severity graded"),
        ("Refactored Source Code",
         "Complete, type-hinted, production-ready secure module — zero placeholders"),
        ("Pytest Suite  (15+ tests)",
         "Full automated test coverage — drop directly into your CI/CD pipeline"),
        ("Unified Git Diff Patch",
         "Standard .patch file reviewable in GitHub, GitLab, or Bitbucket"),
        ("PR + Jira Audit Package",
         "Full PR description with HITL checklist and SOC 2 / ISO 27001 evidence trail"),
    ]
    for i, (title, body) in enumerate(outputs):
        oy = OUT_TOP + i * OUT_H
        if i % 2 == 0:
            _rect(sl, Inches(0), oy, W, OUT_H, LIGHT_BG)
        _rect(sl, PAD, oy + Inches(0.04), Inches(0.05), OUT_H - Inches(0.08), BLUE)
        _txt(sl, title,
             PAD + Inches(0.10), oy + Inches(0.04), Inches(2.10), OUT_H - Inches(0.06),
             size=8, bold=True, color=NAVY)
        _txt(sl, body,
             PAD + Inches(2.24), oy + Inches(0.06), Inches(4.72), OUT_H - Inches(0.08),
             size=7.5, color=BODY_GRY)

    # =========================================================================
    # 6. STATS STRIP  7.78" → 8.52"
    # =========================================================================
    ST_HDR_TOP = Inches(7.78)
    _rect(sl, Inches(0), ST_HDR_TOP, W, Inches(0.21), DARK_HDR)
    _txt(sl, "THE SCALE OF THE PROBLEM WE SOLVE",
         PAD + Inches(0.05), ST_HDR_TOP + Inches(0.04), INNER, Inches(0.15),
         size=7.5, bold=True, color=GREEN)

    ST_TOP  = Inches(7.99)
    ST_H    = Inches(0.53)
    STAT_W  = (INNER - Inches(0.09)) / 4
    stats = [
        ("$4.88M",    "Avg. data breach cost\n(IBM 2024)"),
        ("17",        "Security rules in\nbuilt-in scanner"),
        ("3",         "Specialist\nagents"),
        ("65%",       "Fortune 500 already\nrun on CrewAI"),
    ]
    for i, (stat, label) in enumerate(stats):
        cx = PAD + i * (STAT_W + Inches(0.03))
        _rect(sl, cx, ST_TOP, STAT_W, ST_H, CARD_BG)
        _rect(sl, cx, ST_TOP, Inches(0.05), ST_H, BLUE)
        _txt(sl, stat,
             cx + Inches(0.09), ST_TOP + Inches(0.04), STAT_W - Inches(0.12), Inches(0.24),
             size=13, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
        _txt(sl, label,
             cx + Inches(0.09), ST_TOP + Inches(0.29), STAT_W - Inches(0.12), Inches(0.22),
             size=6.5, color=BODY_GRY, align=PP_ALIGN.CENTER)

    # =========================================================================
    # 7. CTA FOOTER  8.52" → 10.30"
    # =========================================================================
    CTA_TOP = Inches(8.52)
    CTA_H   = H - CTA_TOP
    _rect(sl, Inches(0), CTA_TOP, W, CTA_H, NAVY)
    _rect(sl, Inches(0), CTA_TOP, STRIPE, CTA_H, GREEN)

    _txt(sl, "Ready to put CrewAI to work in your organisation?",
         STRIPE + Inches(0.12), CTA_TOP + Inches(0.12), INNER - Inches(0.10), Inches(0.34),
         size=12, bold=True, color=WHITE)
    _txt(sl,
         "GTP offers a complimentary discovery session — we will map your use case to a\n"
         "CrewAI crew, demo a live build, and define a fast-track delivery plan.",
         STRIPE + Inches(0.12), CTA_TOP + Inches(0.48), INNER - Inches(0.10), Inches(0.46),
         size=8.5, color=SUBTITLE)

    _rect(sl, STRIPE + Inches(0.10), CTA_TOP + Inches(1.0), INNER, Inches(0.02), BLUE)

    _txt(sl, "contact@globaltechnologypartners.com",
         STRIPE + Inches(0.12), CTA_TOP + Inches(1.08), Inches(3.80), Inches(0.28),
         size=9, bold=True, color=GREEN)
    _txt(sl, "globaltechnologypartners.com",
         Inches(4.30), CTA_TOP + Inches(1.08), Inches(2.80), Inches(0.28),
         size=9, bold=True, color=GREEN, align=PP_ALIGN.RIGHT)
    _txt(sl, "github.com/gtprepository/partner-assets",
         STRIPE + Inches(0.12), CTA_TOP + Inches(1.36), Inches(5.20), Inches(0.24),
         size=7.5, color=SUBTITLE)

    _rect(sl, STRIPE + Inches(0.12), CTA_TOP + Inches(1.66), Inches(2.40), Inches(0.28), GREEN)
    _txt(sl, "Built on CrewAI + Claude",
         STRIPE + Inches(0.14), CTA_TOP + Inches(1.68), Inches(2.36), Inches(0.24),
         size=8, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
    _txt(sl, "Confidential — For Client Discussion Only",
         Inches(3.80), CTA_TOP + Inches(1.72), Inches(3.30), Inches(0.22),
         size=7, color=BODY_GRY, align=PP_ALIGN.RIGHT)


# ============================================================================
if __name__ == "__main__":
    prs = _prs()
    build(prs)

    docs_dir    = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(docs_dir)

    out_docs    = os.path.join(docs_dir,    "GTP_CrewAI_Summary_Slide.pptx")
    out_project = os.path.join(project_dir, "GTP_CrewAI_Summary_Slide.pptx")

    prs.save(out_docs)
    print(f"Saved (docs):    {out_docs}")
    prs.save(out_project)
    print(f"Saved (project): {out_project}")
