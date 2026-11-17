"""
NERO Enterprise DevOps Standard — CTO Executive Presentation Generator
Generates a 16:9 high-impact executive presentation (.pptx) tailored for a Chief Technology Officer.
Includes rich visual cards, KPI metrics, architecture diagrams, comparison tables, and full speaker notes.
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ---------------------------------------------------------------------------
# COLOR PALETTE (Enterprise Executive Navy & Slate Design System)
# ---------------------------------------------------------------------------
BG_DARK = RGBColor(10, 17, 40)          # Deep Navy #0A1128
BG_LIGHT = RGBColor(248, 250, 252)     # Off-white / Slate 50 #F8FAFC
CARD_BG = RGBColor(255, 255, 255)      # Pure White #FFFFFF
CARD_BORDER = RGBColor(226, 232, 240)  # Light Slate Border #E2E8F0
CARD_BG_ALT = RGBColor(241, 245, 249)  # Slate 100 #F1F5F9

TEXT_PRIMARY_DARK = RGBColor(255, 255, 255)
TEXT_MUTED_DARK = RGBColor(148, 163, 184)    # Slate 400
TEXT_PRIMARY_LIGHT = RGBColor(15, 23, 42)    # Slate 900
TEXT_SECONDARY_LIGHT = RGBColor(71, 85, 105) # Slate 600

ACCENT_BLUE = RGBColor(37, 99, 235)    # Royal Blue #2563EB
ACCENT_CYAN = RGBColor(6, 182, 212)    # Cyan #06B6D4
ACCENT_TEAL = RGBColor(13, 148, 136)   # Teal #0D9488
ACCENT_GOLD = RGBColor(217, 119, 6)    # Amber/Gold #D97706
ACCENT_GREEN = RGBColor(22, 163, 74)   # Green #16A34A
ACCENT_RED = RGBColor(220, 38, 38)     # Crimson #DC2626
BADGE_BG = RGBColor(238, 242, 255)     # Indigo 50

FONT_HEADING = "Segoe UI"
FONT_BODY = "Segoe UI"

def set_slide_background(slide, color):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_header(slide, tracker_text, title_text, subtitle_text=None, is_dark=False):
    """Adds a standard executive header to a slide."""
    header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(1.2))
    tf = header_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    # Category Tracker Badge
    p0 = tf.paragraphs[0]
    p0.text = tracker_text.upper()
    p0.font.name = FONT_HEADING
    p0.font.size = Pt(10)
    p0.font.bold = True
    p0.font.color.rgb = ACCENT_CYAN if is_dark else ACCENT_BLUE
    p0.space_after = Pt(2)

    # Main Slide Title
    p1 = tf.add_paragraph()
    p1.text = title_text
    p1.font.name = FONT_HEADING
    p1.font.size = Pt(22)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_PRIMARY_DARK if is_dark else TEXT_PRIMARY_LIGHT
    p1.space_after = Pt(2)

    # Optional Subtitle
    if subtitle_text:
        p2 = tf.add_paragraph()
        p2.text = subtitle_text
        p2.font.name = FONT_BODY
        p2.font.size = Pt(11)
        p2.font.color.rgb = TEXT_MUTED_DARK if is_dark else TEXT_SECONDARY_LIGHT

def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=CARD_BORDER):
    """Draws a rectangular container card."""
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.2)
    else:
        shape.line.fill.background()
    return shape

def add_speaker_notes(slide, notes_text):
    """Sets speaker notes on the slide."""
    notes_slide = slide.notes_slide
    text_frame = notes_slide.notes_text_frame
    text_frame.text = notes_text

def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # =========================================================================
    # SLIDE 1: Title Slide (Dark Theme)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, BG_DARK)

    # Decorative accent bar
    bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.8), Inches(0.12), Inches(3.6))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT_CYAN
    bar.line.fill.background()

    tb = s1.shapes.add_textbox(Inches(1.2), Inches(1.7), Inches(11.0), Inches(3.8))
    tf = tb.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "NERO ENTERPRISE DEVOPS STANDARD"
    p.font.name = FONT_HEADING
    p.font.size = Pt(38)
    p.font.bold = True
    p.font.color.rgb = TEXT_PRIMARY_DARK
    p.space_after = Pt(12)

    p2 = tf.add_paragraph()
    p2.text = "Universal Application Delivery, Supply-Chain Governance & Deterministic Operations"
    p2.font.name = FONT_BODY
    p2.font.size = Pt(18)
    p2.font.color.rgb = ACCENT_CYAN
    p2.space_after = Pt(20)

    p3 = tf.add_paragraph()
    p3.text = "An Architectural & Strategic Briefing for Chief Technology Officer (CTO)"
    p3.font.name = FONT_BODY
    p3.font.size = Pt(13)
    p3.font.color.rgb = TEXT_MUTED_DARK

    # Bottom Metadata Box
    meta_box = s1.shapes.add_textbox(Inches(1.2), Inches(5.8), Inches(11.0), Inches(1.0))
    mtf = meta_box.text_frame
    mp = mtf.paragraphs[0]
    mp.text = "Enterprise Architecture & Platform Engineering  |  Core Principle: 'Build Once, Promote Everywhere, Zero-Rebuild Rollback'"
    mp.font.name = FONT_BODY
    mp.font.size = Pt(11)
    mp.font.color.rgb = TEXT_MUTED_DARK

    add_speaker_notes(s1,
        "EXECUTIVE OPENING:\n"
        "CTO, thank you for your time. Today, I am not presenting a project-specific deployment or a single app's pipeline. "
        "I am presenting the NERO Enterprise DevOps Standard—a platform-level engineering standard and operating model. "
        "Our core thesis is simple: in modern enterprise software, building custom CI/CD pipelines for every service is an anti-pattern. "
        "It leads to pipeline sprawl, security vulnerabilities, and unpredictable downtime. "
        "NERO shifts us from fragmented, bespoke pipelines to a single, hardened, universal operating standard."
    )

    # =========================================================================
    # SLIDE 2: The Enterprise Challenge (The Problem We Solve)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, BG_LIGHT)
    add_header(s2, "Executive Problem Statement", "The Enterprise Delivery Crisis: The Fragmentation Trap",
               "Why traditional, decentralized DevOps fails to scale and creates acute executive risk.")

    cards_data_s2 = [
        ("Pipeline Sprawl & Snowflakes",
         "50 services typically mean 50 bespoke Jenkinsfiles, GitHub Action workflows, or GitLab configs. Every team reinvents deployment logic, creating unmaintainable tech debt.",
         ACCENT_RED, "DEVOPS OVERHEAD: +300%"),
        ("Mutable Artifact Promotion",
         "Teams rebuild code between Dev, QA, and Prod. A freshly compiled artifact in Prod is NOT the artifact tested in QA. Subtle compiler and dependency drift cause production outages.",
         ACCENT_GOLD, "REBUILD RISK: HIGH"),
        ("Software Supply Chain Blindness",
         "Untracked third-party dependencies, unverified container digests, and mutable tags expose the enterprise to SolarWinds/Log4j style supply-chain injection attacks.",
         ACCENT_RED, "SECURITY EXPOSURE: SEVERE"),
        ("Compliance & Audit Scramble",
         "Proving SOC2, ISO27001, or SOX compliance requires weeks of manual screenshot gathering. No cryptographic verification exists to prove an artifact hasn't been tampered with.",
         ACCENT_GOLD, "AUDIT READINESS: REACTIVE")
    ]

    for i, (title, desc, accent, kpi) in enumerate(cards_data_s2):
        col = i % 2
        row = i // 2
        left = Inches(0.8 + col * 5.9)
        top = Inches(1.8 + row * 2.5)
        add_card(s2, left, top, Inches(5.6), Inches(2.2))

        # Accent header pill
        pill = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left + Inches(0.3), top + Inches(0.25), Inches(5.0), Inches(0.35))
        pill.fill.solid()
        pill.fill.fore_color.rgb = BADGE_BG
        pill.line.fill.background()
        ptf = pill.text_frame
        ptf.margin_left = Inches(0.1)
        pp = ptf.paragraphs[0]
        pp.text = kpi
        pp.font.name = FONT_HEADING
        pp.font.size = Pt(9)
        pp.font.bold = True
        pp.font.color.rgb = accent

        tb = s2.shapes.add_textbox(left + Inches(0.3), top + Inches(0.7), Inches(5.0), Inches(1.3))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.name = FONT_HEADING
        p1.font.size = Pt(14)
        p1.font.bold = True
        p1.font.color.rgb = TEXT_PRIMARY_LIGHT
        p1.space_after = Pt(4)

        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.name = FONT_BODY
        p2.font.size = Pt(10.5)
        p2.font.color.rgb = TEXT_SECONDARY_LIGHT

    add_speaker_notes(s2,
        "TALKING POINTS FOR CTO:\n"
        "- As an enterprise scales beyond 10-20 microservices, decentralized CI/CD breaks down.\n"
        "- When developers write their own deployment scripts, you inherit 50 variations of Terraform, 50 different Docker practices, and zero central visibility.\n"
        "- Rebuilding artifacts across stages is a critical hidden flaw in most enterprises: Dev builds image A, QA rebuilds image B, Prod rebuilds image C. They are not byte-for-byte identical.\n"
        "- When an auditor asks 'Can you prove this exact container image in production was tested in QA and not tampered with?', most teams cannot answer with cryptographic certainty."
    )

    # =========================================================================
    # SLIDE 3: The NERO Strategic Paradigm
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, BG_LIGHT)
    add_header(s3, "Strategic Solution", "The NERO Paradigm: From Snowflake Pipelines to Universal Standard",
               "A centralized, golden-path platform decoupling application code from delivery mechanics.")

    # Left: Paradigm Shift Box
    add_card(s3, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.9), bg_color=CARD_BG)
    tb_left = s3.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.0), Inches(4.5))
    tf_left = tb_left.text_frame
    tf_left.word_wrap = True

    p = tf_left.paragraphs[0]
    p.text = "The Core Architecture Principle"
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE
    p.space_after = Pt(10)

    p_quote = tf_left.add_paragraph()
    p_quote.text = "“Build the platform once. Register applications through declarative specs. Automate delivery through universal, policy-controlled workflows. Build once, verify, promote everywhere, and rollback without rebuilding.”"
    p_quote.font.name = FONT_BODY
    p_quote.font.size = Pt(12)
    p_quote.font.italic = True
    p_quote.font.color.rgb = TEXT_PRIMARY_LIGHT
    p_quote.space_after = Pt(16)

    bullets_left = [
        "10-Minute Onboarding: Developers provide one declarative 'app.spec.yaml'; zero pipeline code written.",
        "Zero Snowflake Pipelines: A single universal engine orchestrates all applications across all stacks.",
        "Strict Separation of Concerns: Developers code features; the platform enforces security, infrastructure, and compliance."
    ]
    for b in bullets_left:
        bp = tf_left.add_paragraph()
        bp.text = "• " + b
        bp.font.name = FONT_BODY
        bp.font.size = Pt(11)
        bp.font.color.rgb = TEXT_SECONDARY_LIGHT
        bp.space_after = Pt(8)

    # Right: Division of Responsibilities Table/Cards
    add_card(s3, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.9), bg_color=CARD_BG)
    tb_right = s3.shapes.add_textbox(Inches(7.1), Inches(2.0), Inches(5.1), Inches(4.5))
    tf_right = tb_right.text_frame
    tf_right.word_wrap = True

    pr = tf_right.paragraphs[0]
    pr.text = "Clean Separation of Enterprise Roles"
    pr.font.name = FONT_HEADING
    pr.font.size = Pt(16)
    pr.font.bold = True
    pr.font.color.rgb = TEXT_PRIMARY_LIGHT
    pr.space_after = Pt(14)

    roles = [
        ("Application Teams (100% Feature Velocity)",
         "Declare application metadata, exposed ports, health endpoints, and environment variables in app.spec.yaml. Zero CI/CD maintenance."),
        ("Platform & SRE Teams (Centralized Control)",
         "Maintain the universal Python engine, shared Terraform modules, Jenkins pipelines, and deployment orchestration. Changes propagate instantly."),
        ("Security & Governance (Automated Trust)",
         "Central Application Catalog enforces authorization, non-root execution, vulnerability thresholds, and cryptographic Merkle audit logs.")
    ]
    for r_title, r_desc in roles:
        rp1 = tf_right.add_paragraph()
        rp1.text = "✔ " + r_title
        rp1.font.name = FONT_HEADING
        rp1.font.size = Pt(12)
        rp1.font.bold = True
        rp1.font.color.rgb = ACCENT_TEAL
        rp1.space_after = Pt(2)

        rp2 = tf_right.add_paragraph()
        rp2.text = r_desc
        rp2.font.name = FONT_BODY
        rp2.font.size = Pt(10.5)
        rp2.font.color.rgb = TEXT_SECONDARY_LIGHT
        rp2.space_after = Pt(10)

    add_speaker_notes(s3,
        "TALKING POINTS FOR CTO:\n"
        "- This is our strategic shift: Treat DevOps as an Enterprise Platform Product, not an ad-hoc project deliverable.\n"
        "- In the legacy model, every new app requires a DevOps engineer to spend 2-3 weeks writing Jenkinsfiles, Dockerfiles, and Terraform.\n"
        "- In NERO, onboarding takes 10 minutes. The developer only declares WHAT their app is (ports, health check, runtime). The platform knows HOW to build, secure, and deploy it.\n"
        "- Central platform engineering updates automatically apply to all 50+ services without asking application teams to update 50 separate repositories."
    )

    # =========================================================================
    # SLIDE 4: Technical Architecture: The 4 Pillars
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, BG_LIGHT)
    add_header(s4, "Technical Architecture", "The 4-Pillar Universal Platform Foundation",
               "A modular, extensible system architecture decoupled across specification, orchestration, and infrastructure.")

    pillars = [
        ("1. Declarative Catalog",
         "app.spec.yaml + Central Catalog",
         ["Strict Pydantic schema validation", "Central applications.yaml trust registry", "Prevents unauthorized shadow deployments", "Declares components, ports, dependencies"],
         ACCENT_BLUE),
        ("2. Universal Engine",
         "platform_core Python Orchestrator",
         ["Unified CLI for build, release, deploy", "Pluggable runtime adapters (ECS, S3, RDS)", "Dynamic multi-cloud parameter resolver", "Error hierarchy with standardized exit codes"],
         ACCENT_CYAN),
        ("3. Modular IaC",
         "Reusable Terraform Modules",
         ["State isolation across environments", "Standardized VPC, ALB, ECS, S3, RDS", "IAM least-privilege role boundaries", "Zero hardcoded infrastructure IDs"],
         ACCENT_TEAL),
        ("4. Universal Pipeline",
         "Single Declarative Jenkinsfile",
         ["One pipeline handles 100% of apps", "Dynamic parameter injection", "Two-person production approval gates", "Zero custom pipeline maintenance"],
         ACCENT_GOLD)
    ]

    for i, (p_title, p_sub, points, accent) in enumerate(pillars):
        left = Inches(0.8 + i * 2.95)
        top = Inches(1.8)
        width = Inches(2.8)
        height = Inches(4.9)
        add_card(s4, left, top, width, height)

        # Header bar
        hbar = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, Inches(0.12))
        hbar.fill.solid()
        hbar.fill.fore_color.rgb = accent
        hbar.line.fill.background()

        tb = s4.shapes.add_textbox(left + Inches(0.2), top + Inches(0.3), width - Inches(0.4), height - Inches(0.5))
        tf = tb.text_frame
        tf.word_wrap = True

        pt = tf.paragraphs[0]
        pt.text = p_title
        pt.font.name = FONT_HEADING
        pt.font.size = Pt(13)
        pt.font.bold = True
        pt.font.color.rgb = TEXT_PRIMARY_LIGHT
        pt.space_after = Pt(2)

        ps = tf.add_paragraph()
        ps.text = p_sub
        ps.font.name = FONT_BODY
        ps.font.size = Pt(9.5)
        ps.font.bold = True
        ps.font.color.rgb = accent
        ps.space_after = Pt(14)

        for pt_text in points:
            p_bullet = tf.add_paragraph()
            p_bullet.text = "• " + pt_text
            p_bullet.font.name = FONT_BODY
            p_bullet.font.size = Pt(9.5)
            p_bullet.font.color.rgb = TEXT_SECONDARY_LIGHT
            p_bullet.space_after = Pt(8)

    add_speaker_notes(s4,
        "TALKING POINTS FOR CTO:\n"
        "- Here is the technical anatomy of NERO:\n"
        "- Pillar 1 is the Declarative Catalog: It establishes our organizational contract. If an application is not registered in the catalog with approved team ownership, it cannot be deployed.\n"
        "- Pillar 2 is the Universal Platform Engine: Written in modern Python, it contains the core business logic—how to validate manifests, resolve environment endpoints, and call deployment adapters.\n"
        "- Pillar 3 is Modular Terraform: Pre-approved, hardened infrastructure modules with state isolation between Dev, QA, and Prod.\n"
        "- Pillar 4 is the Universal Pipeline: Instead of 50 different Jenkinsfiles, we maintain ONE. It accepts the application ID and environment as parameters and calls the platform engine."
    )

    # =========================================================================
    # SLIDE 5: Immutable Releases & Zero-Rebuild Promotion
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, BG_LIGHT)
    add_header(s5, "Release Engineering", "Immutable Release Manifests & Zero-Rebuild Promotion",
               "Eliminating environmental drift and deployment unpredictability with bit-for-bit identical promotion.")

    # Left Container: Workflow
    add_card(s5, Inches(0.8), Inches(1.8), Inches(6.5), Inches(4.9))
    tb_w = s5.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.9), Inches(4.5))
    tf_w = tb_w.text_frame
    tf_w.word_wrap = True

    p = tf_w.paragraphs[0]
    p.text = "The 'Build Once, Promote Everywhere' Lifecycle"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE
    p.space_after = Pt(12)

    steps = [
        ("1. Build & Seal (Develop)", "Docker images and static bundles are compiled ONCE. A cryptographic release-manifest.json is minted with full 64-char SHA-256 digests."),
        ("2. Qualification & Verification (QA)", "The EXACT same container digest and static bundle are deployed to QA. Automated synthetic health checks verify integrity. Zero recompilation."),
        ("3. Two-Person Production Gate (Prod)", "Upon QA sign-off and SRE Change Ticket validation, the EXACT SAME manifest is deployed to Production. Rebuilding in Prod is physically prevented."),
        ("4. Sub-Minute Rollback", "If an incident occurs, the platform rolls back to a previous verified release manifest instantly with zero rebuilding.")
    ]
    for s_title, s_desc in steps:
        sp1 = tf_w.add_paragraph()
        sp1.text = s_title
        sp1.font.name = FONT_HEADING
        sp1.font.size = Pt(11.5)
        sp1.font.bold = True
        sp1.font.color.rgb = TEXT_PRIMARY_LIGHT
        sp1.space_after = Pt(2)

        sp2 = tf_w.add_paragraph()
        sp2.text = s_desc
        sp2.font.name = FONT_BODY
        sp2.font.size = Pt(10)
        sp2.font.color.rgb = TEXT_SECONDARY_LIGHT
        sp2.space_after = Pt(8)

    # Right Container: Value Comparison Box
    add_card(s5, Inches(7.6), Inches(1.8), Inches(4.9), Inches(4.9))
    tb_c = s5.shapes.add_textbox(Inches(7.9), Inches(2.0), Inches(4.3), Inches(4.5))
    tf_c = tb_c.text_frame
    tf_c.word_wrap = True

    pc = tf_c.paragraphs[0]
    pc.text = "Architectural Invariant Comparison"
    pc.font.name = FONT_HEADING
    pc.font.size = Pt(15)
    pc.font.bold = True
    pc.font.color.rgb = TEXT_PRIMARY_LIGHT
    pc.space_after = Pt(14)

    comparisons = [
        ("Traditional CI/CD", "NERO Standard", ACCENT_RED, ACCENT_GREEN),
        ("Builds separate image per env", "Single image SHA-256 promoted", ACCENT_RED, ACCENT_GREEN),
        ("Mutable tags (:latest, :v1)", "Pinned immutable SHA-256 digests", ACCENT_RED, ACCENT_GREEN),
        ("Rollback requires git revert & build", "Instant pointer swap to previous manifest", ACCENT_RED, ACCENT_GREEN),
        ("MTTR: 25 - 45 minutes", "MTTR: < 90 seconds", ACCENT_RED, ACCENT_GREEN),
        ("Environment drift: Frequent", "Environment drift: 0% Mathematically Impossible", ACCENT_RED, ACCENT_GREEN)
    ]
    for trad, nero, c_trad, c_nero in comparisons[1:]:
        cp1 = tf_c.add_paragraph()
        cp1.text = "❌ " + trad
        cp1.font.name = FONT_BODY
        cp1.font.size = Pt(10)
        cp1.font.color.rgb = c_trad

        cp2 = tf_c.add_paragraph()
        cp2.text = "✔ " + nero
        cp2.font.name = FONT_HEADING
        cp2.font.size = Pt(10)
        cp2.font.bold = True
        cp2.font.color.rgb = c_nero
        cp2.space_after = Pt(8)

    add_speaker_notes(s5,
        "TALKING POINTS FOR CTO:\n"
        "- This slide addresses one of the most critical engineering invariants: Zero-Rebuild Promotion.\n"
        "- In legacy systems, teams rebuild their code when deploying to production. That introduces dependency changes, package manager drift, and compiler variations.\n"
        "- Under NERO, an artifact is sealed at the commit stage into an immutable release manifest with 64-character SHA-256 digests.\n"
        "- What runs in Production is bit-for-bit identical to what was verified in QA. If something fails, rollback takes under 90 seconds because we simply stage the previous qualified release manifest without triggering another build."
    )

    # =========================================================================
    # SLIDE 6: Supply Chain Security & Zero-Trust Governance
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, BG_LIGHT)
    add_header(s6, "Cybersecurity & Governance", "Software Supply Chain Security & NIST SSDF Alignment",
               "Built-in compliance with NIST SP 800-218 and SLSA Level 3 supply-chain integrity standards.")

    sec_cards = [
        ("Admission Preflight Gate",
         "Rejects untrusted repositories, unauthorized branches, and unregistered applications before any deployment code executes.",
         "ZERO-TRUST ADMISSION"),
        ("Strict Path Confinement",
         "Enforces canonical directory boundary releases/{app_id}/{release_tag}/, eliminating directory traversal and symlink escapes.",
         "DEFENSE-IN-DEPTH"),
        ("Cryptographic Manifests",
         "RFC 8785 canonical JSON formatting guarantees byte-for-byte reproducible checksums across platforms and architectures.",
         "TAMPER-PROOF MINTING"),
        ("Policy & Waiver Control",
         "Cryptographically signed vulnerability waivers with mandatory expiration dates and ticket linkage. Zero unmanaged CVEs.",
         "AUDITABLE EXEMPTIONS")
    ]

    for i, (title, desc, badge) in enumerate(sec_cards):
        left = Inches(0.8 + i * 2.95)
        top = Inches(1.8)
        width = Inches(2.8)
        height = Inches(4.9)
        add_card(s6, left, top, width, height)

        # Badge pill
        bpill = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left + Inches(0.2), top + Inches(0.3), width - Inches(0.4), Inches(0.35))
        bpill.fill.solid()
        bpill.fill.fore_color.rgb = BADGE_BG
        bpill.line.fill.background()
        btf = bpill.text_frame
        bp = btf.paragraphs[0]
        bp.text = badge
        bp.font.name = FONT_HEADING
        bp.font.size = Pt(8.5)
        bp.font.bold = True
        bp.font.color.rgb = ACCENT_BLUE

        tb = s6.shapes.add_textbox(left + Inches(0.2), top + Inches(0.8), width - Inches(0.4), height - Inches(1.0))
        tf = tb.text_frame
        tf.word_wrap = True

        pt = tf.paragraphs[0]
        pt.text = title
        pt.font.name = FONT_HEADING
        pt.font.size = Pt(13)
        pt.font.bold = True
        pt.font.color.rgb = TEXT_PRIMARY_LIGHT
        pt.space_after = Pt(10)

        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.name = FONT_BODY
        pd.font.size = Pt(10.5)
        pd.font.color.rgb = TEXT_SECONDARY_LIGHT

    add_speaker_notes(s6,
        "TALKING POINTS FOR CTO:\n"
        "- Supply chain attacks like SolarWinds and Codecov demonstrated that CI/CD pipelines are prime targets for malicious infiltration.\n"
        "- NERO builds zero-trust admission directly into the ingestion engine.\n"
        "- An artifact cannot enter our environment unless it passes strict preflight validation: authorized repository, verified git commit, canonical RFC 8785 JSON manifest, and valid SHA-256 digests.\n"
        "- Artifact storage is strictly confined to scoped directory namespaces, preventing traversal or sibling-prefix attacks.\n"
        "- This natively satisfies NIST SP 800-218 (Secure Software Development Framework) and aligns with SLSA Level 3 supply chain integrity."
    )

    # =========================================================================
    # SLIDE 7: High-Availability Reliability & Crash Safety
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, BG_LIGHT)
    add_header(s7, "System Reliability", "Crash-Safe State Machines & Write-Ahead Audit Logging",
               "Defensive engineering guarantees consistency during hardware, network, or power interruptions.")

    # Left: Protocol Flow
    add_card(s7, Inches(0.8), Inches(1.8), Inches(6.0), Inches(4.9))
    tb_wal = s7.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.4), Inches(4.5))
    tf_wal = tb_wal.text_frame
    tf_wal.word_wrap = True

    p = tf_wal.paragraphs[0]
    p.text = "Write-Ahead Audit & Publication Protocol"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE
    p.space_after = Pt(10)

    wal_steps = [
        ("1. Isolated Staging", "Writes payload to private .staging/.tmp_{id}.json and executes fsync() to guarantee non-volatile disk persistence."),
        ("2. Two-Phase Staging Rename", "Renames temporary file to .staging/{id}.json.staged. Invisible to public consumers."),
        ("3. Write-Ahead Audit Commitment", "Appends CANDIDATE_INGEST_SUCCESS to the immutable audit ledger BEFORE publishing."),
        ("4. Atomic Public Publication", "Executes atomic os.replace to staging_dir/{id}.json. Consumers only discover fully audited candidates.")
    ]
    for st, sd in wal_steps:
        sp1 = tf_wal.add_paragraph()
        sp1.text = st
        sp1.font.name = FONT_HEADING
        sp1.font.size = Pt(11)
        sp1.font.bold = True
        sp1.font.color.rgb = TEXT_PRIMARY_LIGHT
        sp1.space_after = Pt(2)

        sp2 = tf_wal.add_paragraph()
        sp2.text = sd
        sp2.font.name = FONT_BODY
        sp2.font.size = Pt(9.5)
        sp2.font.color.rgb = TEXT_SECONDARY_LIGHT
        sp2.space_after = Pt(6)

    # Right: Recovery & Anti-Corruption
    add_card(s7, Inches(7.1), Inches(1.8), Inches(5.4), Inches(4.9))
    tb_rec = s7.shapes.add_textbox(Inches(7.4), Inches(2.0), Inches(4.8), Inches(4.5))
    tf_rec = tb_rec.text_frame
    tf_rec.word_wrap = True

    pr = tf_rec.paragraphs[0]
    pr.text = "Automated Recovery & Quarantine"
    pr.font.name = FONT_HEADING
    pr.font.size = Pt(15)
    pr.font.bold = True
    pr.font.color.rgb = TEXT_PRIMARY_LIGHT
    pr.space_after = Pt(12)

    rec_features = [
        ("Forward Reconciliation", "If a crash interrupts publication after the audit commit, the reconciler automatically detects the staged file and finishes publication."),
        ("Automatic Orphan Quarantine", "Incomplete stages or corrupted temp files lacking success audit events are quarantined to .orphans/ without manual intervention."),
        ("Advisory Concurrency Locks", "Prevents race conditions during simultaneous identical retries via atomic filesystem locks on .staging/{id}.lock."),
        ("Un-Audited Artifact Defense", "Any rogue or manually placed file in staging lacking an audit record is immediately quarantined.")
    ]
    for rf_title, rf_desc in rec_features:
        rp1 = tf_rec.add_paragraph()
        rp1.text = "✔ " + rf_title
        rp1.font.name = FONT_HEADING
        rp1.font.size = Pt(11)
        rp1.font.bold = True
        rp1.font.color.rgb = ACCENT_TEAL
        rp1.space_after = Pt(2)

        rp2 = tf_rec.add_paragraph()
        rp2.text = rf_desc
        rp2.font.name = FONT_BODY
        rp2.font.size = Pt(9.5)
        rp2.font.color.rgb = TEXT_SECONDARY_LIGHT
        rp2.space_after = Pt(8)

    add_speaker_notes(s7,
        "TALKING POINTS FOR CTO:\n"
        "- In enterprise DevOps, race conditions and crash failures during deployments leave systems in unpredictable, corrupted states.\n"
        "- NERO incorporates transactional database engineering into pipeline operations: Write-Ahead Logging (WAL).\n"
        "- Notice Step 3: We commit the success audit record BEFORE the final atomic publication. If the machine dies at any millisecond, the platform reconciler knows exactly how to forward-recover or quarantine.\n"
        "- An un-audited or rogue artifact can never be published to downstream systems. Everything is mathematically recoverable."
    )

    # =========================================================================
    # SLIDE 8: Developer Experience (DevEx) & 10-Minute Onboarding
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, BG_LIGHT)
    add_header(s8, "Developer Experience", "Polyglot Self-Service & 10-Minute Onboarding",
               "Freeing product engineering teams from DevOps toil through declarative specifications.")

    # 3 Column Layout
    devex_cols = [
        ("Polyglot Runtimes",
         "Native support for all major enterprise technology stacks:",
         ["Java / Spring Boot (Maven & Gradle)", "Node.js (Express, Nest, Next)", "Python (FastAPI, Django, SQS Workers)", "SPA Frontends (React, Vite, Angular)"],
         ACCENT_BLUE),
        ("Declarative Spec",
         "Simple app.spec.yaml replaces thousands of lines of pipeline code:",
         ["Declares component architecture", "Exposed HTTP ports & health URLs", "Environment variables & Secrets", "Dependencies & deployment strategies"],
         ACCENT_CYAN),
        ("Self-Service Workflow",
         "Developer onboarding in 4 seamless self-service steps:",
         ["1. Copy starter template", "2. Edit app.spec.yaml (10 mins)", "3. Validate via local platform CLI", "4. Register in Central Catalog"],
         ACCENT_TEAL)
    ]

    for i, (col_title, col_sub, items, accent) in enumerate(devex_cols):
        left = Inches(0.8 + i * 3.95)
        top = Inches(1.8)
        width = Inches(3.7)
        height = Inches(4.9)
        add_card(s8, left, top, width, height)

        tb = s8.shapes.add_textbox(left + Inches(0.3), top + Inches(0.3), width - Inches(0.6), height - Inches(0.6))
        tf = tb.text_frame
        tf.word_wrap = True

        pt = tf.paragraphs[0]
        pt.text = col_title
        pt.font.name = FONT_HEADING
        pt.font.size = Pt(14)
        pt.font.bold = True
        pt.font.color.rgb = accent
        pt.space_after = Pt(4)

        ps = tf.add_paragraph()
        ps.text = col_sub
        ps.font.name = FONT_BODY
        ps.font.size = Pt(10)
        ps.font.color.rgb = TEXT_PRIMARY_LIGHT
        ps.space_after = Pt(14)

        for it in items:
            pi = tf.add_paragraph()
            pi.text = "✔ " + it
            pi.font.name = FONT_BODY
            pi.font.size = Pt(10)
            pi.font.color.rgb = TEXT_SECONDARY_LIGHT
            pi.space_after = Pt(8)

    add_speaker_notes(s8,
        "TALKING POINTS FOR CTO:\n"
        "- From a developer perspective, DevOps should be invisible. Developers want to write code, not debug Jenkins Groovy scripts or Terraform provider errors.\n"
        "- NERO supports our polyglot engineering landscape out of the box—Java, Node, Python, and modern Frontends.\n"
        "- Instead of spending 2 weeks waiting for platform engineers to write infrastructure code, an engineering team onboards in 10 minutes by creating an app.spec.yaml.\n"
        "- They test locally using the platform CLI, run their unit tests, and submit their PR. Delivery velocity increases dramatically."
    )

    # =========================================================================
    # SLIDE 9: Multi-Environment Cloud Parity & FinOps
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, BG_LIGHT)
    add_header(s9, "Cloud Parity & FinOps", "Local Simulation to Enterprise AWS Multi-Account Parity",
               "Slashing cloud development costs to $0.00 while guaranteeing zero environmental drift in production.")

    # Left: Local Cloud Simulator (Floci)
    add_card(s9, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.9))
    tb_floci = s9.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.0), Inches(4.5))
    tf_floci = tb_floci.text_frame
    tf_floci.word_wrap = True

    p = tf_floci.paragraphs[0]
    p.text = "Local Cloud Emulation (Floci / LocalStack)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_TEAL
    p.space_after = Pt(10)

    floci_points = [
        ("$0.00 Cloud Spend: Full AWS simulation (S3, SQS, Secrets Manager, ECS) running locally in Docker.", ACCENT_GREEN),
        ("Instant Developer Feedback: Run full integration pipelines locally in seconds without cloud latency or quotas.", TEXT_SECONDARY_LIGHT),
        ("Isolated Test Enclaves: Ephemeral environments for CI pull-request validation with zero cloud resource leakage.", TEXT_SECONDARY_LIGHT),
        ("Offline Development: Engineers can build and verify entire multi-service systems without internet connectivity.", TEXT_SECONDARY_LIGHT)
    ]
    for pt_text, pt_color in floci_points:
        p_item = tf_floci.add_paragraph()
        p_item.text = "• " + pt_text
        p_item.font.name = FONT_BODY
        p_item.font.size = Pt(10.5)
        p_item.font.color.rgb = pt_color
        p_item.space_after = Pt(10)

    # Right: Production AWS
    add_card(s9, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.9))
    tb_aws = s9.shapes.add_textbox(Inches(7.1), Inches(2.0), Inches(5.1), Inches(4.5))
    tf_aws = tb_aws.text_frame
    tf_aws.word_wrap = True

    pa = tf_aws.paragraphs[0]
    pa.text = "Enterprise AWS Multi-Account Topology"
    pa.font.name = FONT_HEADING
    pa.font.size = Pt(15)
    pa.font.bold = True
    pa.font.color.rgb = ACCENT_BLUE
    pa.space_after = Pt(10)

    aws_points = [
        ("Multi-Account Isolation: Physical separation of accounts for CI Tooling, Develop, QA, and Production.", TEXT_SECONDARY_LIGHT),
        ("Automated Context Resolver: Platform CLI dynamically resolves STS AssumeRole ARNs, Account IDs, and VPC Subnets.", TEXT_SECONDARY_LIGHT),
        ("Zero Code Changes: The identical application artifact and engine scripts run seamlessly on both Floci and AWS.", ACCENT_BLUE),
        ("FinOps Governance: Automatic idle resource tagging, automated cleanup of untagged resources, and cost attribution.", TEXT_SECONDARY_LIGHT)
    ]
    for pt_text, pt_color in aws_points:
        p_item = tf_aws.add_paragraph()
        p_item.text = "• " + pt_text
        p_item.font.name = FONT_BODY
        p_item.font.size = Pt(10.5)
        p_item.font.color.rgb = pt_color
        p_item.space_after = Pt(10)

    add_speaker_notes(s9,
        "TALKING POINTS FOR CTO:\n"
        "- One of the biggest expenses in modern engineering organizations is development and QA cloud environments running 24/7.\n"
        "- NERO incorporates a Floci-first architecture: a local AWS emulator running in lightweight Docker containers.\n"
        "- Developers run full end-to-end integration tests, SQS queues, Secrets Manager, and S3 deployments on their laptops or local CI with ZERO cloud spend.\n"
        "- When promoted to AWS, our dynamic Context Resolver binds the necessary IAM STS roles, VPC subnets, and Secrets without a single line of application code changing."
    )

    # =========================================================================
    # SLIDE 10: Continuous Compliance & Cryptographic Audit Ledger
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, BG_LIGHT)
    add_header(s10, "Compliance & Auditing", "Cryptographic Audit Ledger & Production Governance",
               "Automated compliance with zero audit friction through SHA-256 Merkle-chained event logs.")

    # Top: Audit Ledger Formula Card
    add_card(s10, Inches(0.8), Inches(1.8), Inches(11.7), Inches(1.8), bg_color=CARD_BG_ALT)
    tb_math = s10.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(11.1), Inches(1.4))
    tf_math = tb_math.text_frame
    tf_math.word_wrap = True

    p = tf_math.paragraphs[0]
    p.text = "Cryptographic Blockchain-Style Hash Chaining"
    p.font.name = FONT_HEADING
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE
    p.space_after = Pt(4)

    p_f = tf_math.add_paragraph()
    p_f.text = "record_hash_i = SHA-256( record_payload_i  ||  record_hash_{i-1} )"
    p_f.font.name = "Consolas"
    p_f.font.size = Pt(13)
    p_f.font.bold = True
    p_f.font.color.rgb = TEXT_PRIMARY_LIGHT
    p_f.space_after = Pt(4)

    p_exp = tf_math.add_paragraph()
    p_exp.text = "Every build, plan, deploy, verification, governance approval, and rollback is recorded in an immutable ledger. Any modification, truncation, or reordering breaks the hash chain instantly."
    p_exp.font.name = FONT_BODY
    p_exp.font.size = Pt(10.5)
    p_exp.font.color.rgb = TEXT_SECONDARY_LIGHT

    # Bottom 3 Cards: Governance Controls
    gov_cards = [
        ("Two-Person Production Rule",
         "Production deployment strictly mandates QA Lead approval plus SRE Change Ticket (CHG-*) verification. No single engineer can push to prod.",
         ACCENT_BLUE),
        ("Automated SOC2 / ISO Evidence",
         "Audit logs capture actor identity, git commit, test results, scanner outputs, and deployment approvals. Zero manual audit compilation.",
         ACCENT_TEAL),
        ("Instant Tamper Detection",
         "The platform verifier verifies all historical records in milliseconds. Non-repudiation is guaranteed mathematically across the enterprise.",
         ACCENT_GOLD)
    ]
    for i, (title, desc, accent) in enumerate(gov_cards):
        left = Inches(0.8 + i * 3.95)
        top = Inches(3.8)
        width = Inches(3.7)
        height = Inches(2.9)
        add_card(s10, left, top, width, height)

        tb_g = s10.shapes.add_textbox(left + Inches(0.3), top + Inches(0.3), width - Inches(0.6), height - Inches(0.6))
        tf_g = tb_g.text_frame
        tf_g.word_wrap = True

        gt = tf_g.paragraphs[0]
        gt.text = title
        gt.font.name = FONT_HEADING
        gt.font.size = Pt(13)
        gt.font.bold = True
        gt.font.color.rgb = accent
        gt.space_after = Pt(8)

        gd = tf_g.add_paragraph()
        gd.text = desc
        gd.font.name = FONT_BODY
        gd.font.size = Pt(10)
        gd.font.color.rgb = TEXT_SECONDARY_LIGHT

    add_speaker_notes(s10,
        "TALKING POINTS FOR CTO:\n"
        "- For enterprise leadership, audit compliance is often an expensive distraction. External auditors demand proof that nobody pushed unapproved code to production.\n"
        "- NERO incorporates a cryptographically chained audit ledger inspired by Merkle trees.\n"
        "- Every single event—from build to approval to deployment—is hashed with the hash of the preceding event.\n"
        "- If an engineer or malicious insider modifies an old audit entry, the hash chain breaks instantly.\n"
        "- Furthermore, production deployments enforce the Two-Person Rule: a QA lead must sign off, and an SRE must provide an active ITIL Change Ticket. Compliance is continuous, automated, and tamper-proof."
    )

    # =========================================================================
    # SLIDE 11: Business Impact & Strategic ROI Metrics
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11, BG_LIGHT)
    add_header(s11, "Business Value", "Quantifiable Business Impact & Operational ROI",
               "Transforming DevOps from an unpredictable cost center into a strategic competitive advantage.")

    # 4 Big KPI Metric Cards across the top
    kpi_metrics = [
        ("80% LESS", "Onboarding Time", "Weeks ➔ 10 Minutes per application", ACCENT_BLUE),
        ("90% DROP", "Pipeline Sprawl", "50+ bespoke files ➔ 1 universal engine", ACCENT_TEAL),
        ("< 90 SEC", "Recovery (MTTR)", "Zero-rebuild rollback to qualified manifest", ACCENT_GREEN),
        ("100%", "Audit Traceability", "Continuous cryptographic compliance", ACCENT_GOLD)
    ]

    for i, (metric, label, subtext, color) in enumerate(kpi_metrics):
        left = Inches(0.8 + i * 2.95)
        top = Inches(1.8)
        width = Inches(2.8)
        height = Inches(2.1)
        add_card(s11, left, top, width, height)

        tb_k = s11.shapes.add_textbox(left + Inches(0.2), top + Inches(0.2), width - Inches(0.4), height - Inches(0.4))
        tf_k = tb_k.text_frame
        tf_k.word_wrap = True

        km = tf_k.paragraphs[0]
        km.text = metric
        km.font.name = FONT_HEADING
        km.font.size = Pt(22)
        km.font.bold = True
        km.font.color.rgb = color
        km.space_after = Pt(2)

        kl = tf_k.add_paragraph()
        kl.text = label
        kl.font.name = FONT_HEADING
        kl.font.size = Pt(11)
        kl.font.bold = True
        kl.font.color.rgb = TEXT_PRIMARY_LIGHT
        kl.space_after = Pt(2)

        ks = tf_k.add_paragraph()
        ks.text = subtext
        ks.font.name = FONT_BODY
        ks.font.size = Pt(9.5)
        ks.font.color.rgb = TEXT_SECONDARY_LIGHT

    # Bottom Business Benefit Summary Card
    add_card(s11, Inches(0.8), Inches(4.1), Inches(11.7), Inches(2.6))
    tb_b = s11.shapes.add_textbox(Inches(1.1), Inches(4.3), Inches(11.1), Inches(2.2))
    tf_b = tb_b.text_frame
    tf_b.word_wrap = True

    pb_title = tf_b.paragraphs[0]
    pb_title.text = "Strategic Executive Returns"
    pb_title.font.name = FONT_HEADING
    pb_title.font.size = Pt(14)
    pb_title.font.bold = True
    pb_title.font.color.rgb = TEXT_PRIMARY_LIGHT
    pb_title.space_after = Pt(6)

    returns = [
        ("Engineering Headcount Efficiency", "Eliminates the need to assign dedicated DevOps engineers to individual feature teams. Platform engineers maintain the core standard; developers self-serve."),
        ("Drastic Risk & Outage Reduction", "Zero-rebuild promotion and automated synthetic verification prevent bad releases from reaching production. MTTR drops from hours to under 90 seconds."),
        ("Cloud Infrastructure Optimization", "Floci-first local testing prevents expensive cloud resource sprawl during dev and PR qualification, saving tens of thousands in annual AWS spend.")
    ]
    for r_head, r_text in returns:
        p_ret = tf_b.add_paragraph()
        p_ret.text = "• " + r_head + ": " + r_text
        p_ret.font.name = FONT_BODY
        p_ret.font.size = Pt(10)
        p_ret.font.color.rgb = TEXT_SECONDARY_LIGHT
        p_ret.space_after = Pt(4)

    add_speaker_notes(s11,
        "TALKING POINTS FOR CTO:\n"
        "- Here is the bottom-line ROI for executive leadership:\n"
        "- Onboarding: We cut onboarding from 2 weeks of Jira back-and-forth down to 10 minutes.\n"
        "- DevOps Maintenance: Instead of maintaining 50 separate pipelines, we maintain one universal platform engine. That's a 90% reduction in pipeline maintenance toil.\n"
        "- MTTR: When an outage strikes in production, rollback is under 90 seconds because we stage the previous release manifest with zero recompilation.\n"
        "- FinOps: Developers test locally against Floci at $0.00 cloud cost, avoiding AWS bill shock.\n"
        "- Platform engineering stops being a bottleneck and becomes a strategic business accelerant."
    )

    # =========================================================================
    # SLIDE 12: Strategic Roadmap: Deterministic First, AI Second
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12, BG_LIGHT)
    add_header(s12, "Technology Strategy", "The AI-Ready Platform: Deterministic Foundation to Autonomous Ops",
               "Why a rigorous deterministic platform is the non-negotiable prerequisite for enterprise DevOps AI.")

    # Two Major Programme Cards
    # Programme 1
    add_card(s12, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.9))
    tb_p1 = s12.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.0), Inches(4.5))
    tf_p1 = tb_p1.text_frame
    tf_p1.word_wrap = True

    p = tf_p1.paragraphs[0]
    p.text = "Programme 1: Deterministic Foundation"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE
    p.space_after = Pt(2)

    ps1 = tf_p1.add_paragraph()
    ps1.text = "Phases A0 — A9 (Core Engineering Standard)"
    ps1.font.name = FONT_BODY
    ps1.font.size = Pt(10)
    ps1.font.bold = True
    ps1.font.color.rgb = ACCENT_CYAN
    ps1.space_after = Pt(12)

    p1_items = [
        "100% Deterministic: Rules, schemas, typed contracts, and immutable manifests.",
        "Zero AI Dependencies: Robust, battle-tested Python orchestrator and Terraform modules.",
        "Clean Data & Telemetry: Complete audit trails, structured JSON event logs, and metric sinks.",
        "Guaranteed Guardrails: Separation of duties, two-person rules, and hard failure barriers."
    ]
    for item in p1_items:
        pi = tf_p1.add_paragraph()
        pi.text = "✔ " + item
        pi.font.name = FONT_BODY
        pi.font.size = Pt(10.5)
        pi.font.color.rgb = TEXT_SECONDARY_LIGHT
        pi.space_after = Pt(8)

    # Programme 2
    add_card(s12, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.9))
    tb_p2 = s12.shapes.add_textbox(Inches(7.1), Inches(2.0), Inches(5.1), Inches(4.5))
    tf_p2 = tb_p2.text_frame
    tf_p2.word_wrap = True

    pa = tf_p2.paragraphs[0]
    pa.text = "Programme 2: AI-Enhanced Operations"
    pa.font.name = FONT_HEADING
    pa.font.size = Pt(15)
    pa.font.bold = True
    pa.font.color.rgb = ACCENT_TEAL
    pa.space_after = Pt(2)

    ps2 = tf_p2.add_paragraph()
    ps2.text = "Phases B0 — B6 (Evolutionary Intelligence)"
    ps2.font.name = FONT_BODY
    ps2.font.size = Pt(10)
    ps2.font.bold = True
    ps2.font.color.rgb = ACCENT_GOLD
    ps2.space_after = Pt(12)

    p2_items = [
        "B0-B2 (Observe & Recommend): AI agents analyze failure logs, detect anomalies, and suggest optimal resource sizing.",
        "B3-B4 (Supervised SRE): AI proposes runbook remediations subject to explicit human-in-the-loop authorization.",
        "B5-B6 (Autonomous Self-Healing): Safe autonomous remediations executed within strict, typed platform tool boundaries.",
        "Crucial Insight: AI agents cannot safely operate in chaotic, unstructured environments. NERO provides the trusted substrate."
    ]
    for item in p2_items:
        pi = tf_p2.add_paragraph()
        pi.text = "★ " + item
        pi.font.name = FONT_BODY
        pi.font.size = Pt(10)
        pi.font.color.rgb = TEXT_SECONDARY_LIGHT
        pi.space_after = Pt(8)

    add_speaker_notes(s12,
        "TALKING POINTS FOR CTO:\n"
        "- Many organizations attempt to sprinkle 'DevOps AI' on top of messy, bespoke pipelines. That is dangerous and creates hallucination-driven outages.\n"
        "- Our strategic vision is governed by a strict two-programme architecture:\n"
        "- Programme 1 builds the deterministic foundation: typed APIs, schemas, immutable release manifests, and cryptographic audit ledgers. Zero AI dependency.\n"
        "- Once this platform standard is mature, Programme 2 introduces AI safely.\n"
        "- Why? Because an AI agent cannot safely manage a cloud environment unless it calls strongly typed, schema-validated, audited platform tools with hard boundaries.\n"
        "- By adopting NERO today, we are future-proofing our entire enterprise for safe, autonomous AI operations tomorrow."
    )

    # =========================================================================
    # SLIDE 13: Target Operating Model & Phased Enterprise Rollout
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13, BG_LIGHT)
    add_header(s13, "Implementation Plan", "Target Operating Model & Phased Enterprise Rollout",
               "A pragmatic, low-risk adoption roadmap delivering immediate value without disrupting active feature delivery.")

    phases = [
        ("Phase 1: Foundation & Pilot",
         "Weeks 1 — 4",
         ["Deploy NERO Platform Core & Universal Pipeline", "Establish Central Application Catalog", "Onboard 2-3 representative pilot services (Java, Node, SPA)", "Validate Floci and AWS multi-account deployment paths"],
         ACCENT_BLUE),
        ("Phase 2: Scale & Migration",
         "Weeks 5 — 10",
         ["Launch 10-Minute Onboarding self-service workshops", "Migrate core product tier applications to app.spec.yaml", "Deprecate legacy bespoke Jenkinsfiles/actions", "Integrate automated SOC2 compliance reporting"],
         ACCENT_TEAL),
        ("Phase 3: Full Standardization",
         "Weeks 11+",
         ["100% application delivery governed by NERO standard", "Enable automated zero-rebuild rollback across all tiers", "Implement FinOps automated idle resource reclamation", "Initiate Phase B0 AI Observational Telemetry"],
         ACCENT_GOLD)
    ]

    for i, (title, timeline, actions, accent) in enumerate(phases):
        left = Inches(0.8 + i * 3.95)
        top = Inches(1.8)
        width = Inches(3.7)
        height = Inches(4.9)
        add_card(s13, left, top, width, height)

        tb = s13.shapes.add_textbox(left + Inches(0.3), top + Inches(0.3), width - Inches(0.6), height - Inches(0.6))
        tf = tb.text_frame
        tf.word_wrap = True

        pt = tf.paragraphs[0]
        pt.text = title
        pt.font.name = FONT_HEADING
        pt.font.size = Pt(13.5)
        pt.font.bold = True
        pt.font.color.rgb = accent
        pt.space_after = Pt(2)

        ptime = tf.add_paragraph()
        ptime.text = timeline.upper()
        ptime.font.name = FONT_BODY
        ptime.font.size = Pt(9.5)
        ptime.font.bold = True
        ptime.font.color.rgb = TEXT_PRIMARY_LIGHT
        ptime.space_after = Pt(12)

        for a in actions:
            pa = tf.add_paragraph()
            pa.text = "• " + a
            pa.font.name = FONT_BODY
            pa.font.size = Pt(10)
            pa.font.color.rgb = TEXT_SECONDARY_LIGHT
            pa.space_after = Pt(8)

    add_speaker_notes(s13,
        "TALKING POINTS FOR CTO:\n"
        "- How do we get there? We do not propose a disruptive 'big bang' migration that halts product delivery.\n"
        "- We follow a structured 3-phase rollout:\n"
        "- Phase 1 establishes the platform foundation and onboard 2-3 pilot applications across different runtimes.\n"
        "- Phase 2 expands across the engineering organization using our 10-minute onboarding model, systematically sunsetting old bespoke pipelines.\n"
        "- Phase 3 achieves full enterprise standardization, automated compliance reporting, and unlocks the AI-enhanced roadmap.\n"
        "- Risk is strictly contained, and value is demonstrated from Week 1."
    )

    # =========================================================================
    # SLIDE 14: Executive Decision & CTO Call to Action (Dark Theme)
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14, BG_DARK)

    # Decorative header
    add_header(s14, "Executive Decision", "Recommendations & Immediate Next Steps",
               "Establishing NERO as the foundational technology delivery standard for our enterprise.", is_dark=True)

    # 3 Recommendation Boxes
    recs = [
        ("1. Standard Mandate",
         "Formally endorse the NERO Enterprise DevOps Standard as the mandatory baseline for all new and existing applications across product engineering.",
         ACCENT_CYAN),
        ("2. Dedicated Platform Guild",
         "Empower the Platform Engineering team to own and extend the universal core engine, shared Terraform modules, and governance catalog.",
         ACCENT_BLUE),
        ("3. Sunset Snowflake CI/CD",
         "Initiate the phased deprecation of legacy custom pipelines, transitioning feature teams to declarative 10-minute self-service onboarding.",
         ACCENT_GOLD)
    ]

    for i, (title, desc, accent) in enumerate(recs):
        left = Inches(0.8 + i * 3.95)
        top = Inches(1.8)
        width = Inches(3.7)
        height = Inches(3.6)
        add_card(s14, left, top, width, height, bg_color=RGBColor(20, 30, 55), border_color=RGBColor(35, 50, 85))

        tb = s14.shapes.add_textbox(left + Inches(0.3), top + Inches(0.3), width - Inches(0.6), height - Inches(0.6))
        tf = tb.text_frame
        tf.word_wrap = True

        pt = tf.paragraphs[0]
        pt.text = title
        pt.font.name = FONT_HEADING
        pt.font.size = Pt(14)
        pt.font.bold = True
        pt.font.color.rgb = accent
        pt.space_after = Pt(10)

        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.name = FONT_BODY
        pd.font.size = Pt(10.5)
        pd.font.color.rgb = TEXT_PRIMARY_DARK

    # Bottom Summary Banner
    banner = s14.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(5.8), Inches(11.7), Inches(1.0))
    banner.fill.solid()
    banner.fill.fore_color.rgb = RGBColor(15, 23, 42)
    banner.line.color.rgb = ACCENT_CYAN
    banner.line.width = Pt(1.5)

    tb_ban = s14.shapes.add_textbox(Inches(1.0), Inches(5.9), Inches(11.3), Inches(0.8))
    tf_ban = tb_ban.text_frame
    tf_ban.word_wrap = True
    pban = tf_ban.paragraphs[0]
    pban.text = "NERO transforms DevOps from an unpredictable operational cost into an institutional competitive advantage — faster, safer, compliant, and AI-ready."
    pban.font.name = FONT_HEADING
    pban.font.size = Pt(13)
    pban.font.bold = True
    pban.font.color.rgb = ACCENT_CYAN

    add_speaker_notes(s14,
        "CLOSING TALKING POINTS FOR CTO:\n"
        "- CTO, in summary: Adopting the NERO DevOps Standard is not just a tactical pipeline upgrade. It is an executive decision to eliminate delivery risk and empower our developers.\n"
        "- With NERO, we gain:\n"
        "  1. Massive developer velocity via 10-minute self-service onboarding.\n"
        "  2. Mathematical release certainty with zero-rebuild promotion and sub-90-second rollback.\n"
        "  3. Continuous audit compliance with cryptographic Merkle-chained logging.\n"
        "  4. A trusted, typed foundation ready for the coming wave of autonomous AI SRE agents.\n"
        "- We request your executive approval to establish NERO as our corporate standard and begin Phase 1 rollout. Thank you."
    )

    output_dir = os.path.join("nero_devops_standard", "docs")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "NERO_DevOps_Standard_CTO_Executive_Presentation.pptx")
    prs.save(output_path)
    print(f"Presentation saved successfully to: {os.path.abspath(output_path)}")
    return output_path

if __name__ == "__main__":
    build_presentation()
