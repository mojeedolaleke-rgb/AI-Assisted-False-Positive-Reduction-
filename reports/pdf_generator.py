import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Preformatted
)
from reportlab.lib.enums import TA_LEFT


def _sev_color(sev):
    return {
        "CRITICAL": colors.HexColor("#b71c1c"),
        "HIGH":     colors.HexColor("#e65100"),
        "MEDIUM":   colors.HexColor("#f57f17"),
        "LOW":      colors.HexColor("#1565c0"),
    }.get(sev, colors.grey)


def _get(f, key, default=""):
    return f.get(key, default) if isinstance(f, dict) else getattr(f, key, default)


def generate_pdf(output_path: str, scan: dict, findings: list):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    title_s  = ParagraphStyle("T",  fontSize=22, fontName="Helvetica-Bold",
                               textColor=colors.HexColor("#1a1a2e"), alignment=TA_LEFT)
    h2_s     = ParagraphStyle("H2", fontSize=13, fontName="Helvetica-Bold",
                               textColor=colors.HexColor("#2E75B6"), spaceAfter=4, spaceBefore=10)
    h3_s     = ParagraphStyle("H3", fontSize=11, fontName="Helvetica-Bold",
                               textColor=colors.HexColor("#1a1a2e"), spaceAfter=3, spaceBefore=8)
    body_s   = ParagraphStyle("B",  fontSize=10, fontName="Helvetica", leading=14)
    code_s   = ParagraphStyle("C",  fontSize=8,  fontName="Courier", leading=11,
                               backColor=colors.HexColor("#f5f5f5"), borderPadding=6)
    ai_s     = ParagraphStyle("AI", fontSize=10, fontName="Helvetica",
                               leading=14, textColor=colors.HexColor("#1a1a2e"))
    ai_lbl_s = ParagraphStyle("AL", fontSize=10, fontName="Helvetica-Bold",
                               textColor=colors.HexColor("#6c63ff"))
    note_s   = ParagraphStyle("N",  fontSize=9,  fontName="Helvetica-Oblique",
                               textColor=colors.HexColor("#9CA3AF"))

    story = []

    # ── Cover page ──────────────────────────────────────────────
    story.append(Spacer(1, 1.5*cm))
    story.append(Paragraph("SentinelAI Security Report", title_s))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a1a2e")))
    story.append(Spacer(1, 0.5*cm))

    ts = scan.get("scan_timestamp", "")[:16].replace("T", " ")
    meta = [
        ["Project:",           scan.get("project_name", "")],
        ["Scan Date:",         ts],
        ["Total Findings:",    str(scan.get("total_findings", 0))],
        ["False Positives:",   str(scan.get("false_positives", 0))],
        ["Validated Findings:", str(scan.get("validated_findings", 0))],
        ["Critical:",          str(scan.get("critical_count", 0))],
        ["High:",              str(scan.get("high_count", 0))],
        ["Medium:",            str(scan.get("medium_count", 0))],
        ["Low:",               str(scan.get("low_count", 0))],
        ["Generated:",         datetime.now().strftime("%Y-%m-%d %H:%M")],
    ]
    mt = Table(meta, colWidths=[4*cm, 12*cm])
    mt.setStyle(TableStyle([
        ("FONTNAME", (0,0),(0,-1), "Helvetica-Bold"),
        ("FONTNAME", (1,0),(1,-1), "Helvetica"),
        ("FONTSIZE", (0,0),(-1,-1), 10),
        ("ROWBACKGROUNDS", (0,0),(-1,-1), [colors.white, colors.HexColor("#F0F4FF")]),
        ("GRID", (0,0),(-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING", (0,0),(-1,-1), 8),
    ]))
    story.append(mt)
    story.append(PageBreak())

    # ── Split validated vs FP vs unvalidated ─────────────────────
    # is_false_positive: 1 = FP, 0 = TP (validated), None = not yet validated
    true_findings = []
    fp_findings   = []
    unvalidated   = []

    for f in findings:
        is_fp = _get(f, "is_false_positive")
        fp_reason = _get(f, "fp_reason", "")
        # A finding is validated if fp_reason exists and is not an error message
        if fp_reason and not any(x in fp_reason.lower() for x in ("timed out", "failed", "error")):
            if is_fp:
                fp_findings.append(f)
            else:
                true_findings.append(f)
        else:
            # Not yet validated — include as true positive without AI content
            unvalidated.append(f)

    # ── True positive finding pages ──────────────────────────────
    all_findings_for_report = true_findings + unvalidated

    for i, f in enumerate(all_findings_for_report, 1):
        sev     = _get(f, "ai_severity") or _get(f, "severity", "LOW")
        cwe     = _get(f, "cwe_id", "")
        title   = _get(f, "title", "")
        fpath   = _get(f, "file_path", "")
        line    = _get(f, "line_number", 0)
        snippet = _get(f, "code_snippet", "")
        fp_r    = _get(f, "fp_reason", "")
        sev_r   = _get(f, "ai_severity_reason", "")
        validated = bool(fp_r and not any(
            x in fp_r.lower() for x in ("timed out", "failed", "error")
        ))

        story.append(Paragraph(f"Finding {i}: {title}", h2_s))
        story.append(HRFlowable(width="100%", thickness=1,
                                color=_sev_color(sev), spaceAfter=4))

        detail = [
            ["CWE:",         cwe],
            ["AI Severity:", sev],
            ["File:",        fpath],
            ["Line:",        str(line)],
        ]
        dt = Table(detail, colWidths=[3*cm, 13*cm])
        dt.setStyle(TableStyle([
            ("FONTNAME", (0,0),(0,-1), "Helvetica-Bold"),
            ("FONTSIZE", (0,0),(-1,-1), 9),
            ("TOPPADDING", (0,0),(-1,-1), 4),
            ("BOTTOMPADDING", (0,0),(-1,-1), 4),
            ("LEFTPADDING", (0,0),(-1,-1), 6),
        ]))
        story.append(dt)
        story.append(Spacer(1, 0.2*cm))

        if snippet:
            story.append(Paragraph("Vulnerable Code:", h3_s))
            story.append(Preformatted("\n".join(snippet.split("\n")[:15]), code_s))

        if validated and fp_r:
            story.append(Paragraph("AI Validation:", ai_lbl_s))
            story.append(Paragraph(fp_r, ai_s))
        elif not validated:
            story.append(Paragraph(
                "AI validation not yet run for this finding.", note_s
            ))

        if validated and sev_r:
            story.append(Paragraph("Severity Reasoning:", ai_lbl_s))
            story.append(Paragraph(sev_r, ai_s))

        cwe_num = cwe.replace("CWE-", "")
        story.append(Paragraph(
            f"CWE Reference: https://cwe.mitre.org/data/definitions/{cwe_num}.html",
            ParagraphStyle("ref", fontSize=8, textColor=colors.HexColor("#1565c0"))
        ))
        if i < len(all_findings_for_report):
            story.append(PageBreak())

    # ── False positives summary page ─────────────────────────────
    if fp_findings:
        story.append(PageBreak())
        story.append(Paragraph("False Positives Filtered by AI", h2_s))
        story.append(Spacer(1, 0.1*cm))
        story.append(Paragraph(
            f"The following {len(fp_findings)} finding(s) were determined to be false positives "
            "by AI analysis and excluded from the main report.",
            ParagraphStyle("sub", fontSize=10, fontName="Helvetica",
                           textColor=colors.HexColor("#6B7280"), spaceAfter=8)
        ))
        story.append(Spacer(1, 0.3*cm))

        fp_data = [["#", "Title", "CWE", "Original Severity", "AI Reason"]]
        for i, f in enumerate(fp_findings, 1):
            reason = _get(f, "fp_reason", "")[:80]
            fp_data.append([
                str(i),
                _get(f, "title", "")[:40],
                _get(f, "cwe_id", ""),
                _get(f, "severity", ""),
                reason,
            ])
        fpt = Table(fp_data, colWidths=[0.8*cm, 4*cm, 1.8*cm, 2.2*cm, 7.2*cm])
        fpt.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0,0),(-1,0), colors.white),
            ("FONTNAME", (0,0),(-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0),(-1,-1), 8),
            ("ROWBACKGROUNDS", (0,1),(-1,-1), [colors.white, colors.HexColor("#F0F4FF")]),
            ("GRID", (0,0),(-1,-1), 0.5, colors.HexColor("#CCCCCC")),
            ("TOPPADDING", (0,0),(-1,-1), 4),
            ("BOTTOMPADDING", (0,0),(-1,-1), 4),
            ("LEFTPADDING", (0,0),(-1,-1), 6),
            ("VALIGN", (0,0),(-1,-1), "TOP"),
            ("WORDWRAP", (4,1),(-1,-1), True),
        ]))
        story.append(fpt)

    doc.build(story)