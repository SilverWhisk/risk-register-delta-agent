from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import date
import io

# ── Medable Brand Palette ─────────────────────────────────────
PURPLE          = colors.HexColor("#7B52C1")
PURPLE_LIGHT    = colors.HexColor("#F0EBFA")
DARK            = colors.HexColor("#1C1C2E")
MID_GREY        = colors.HexColor("#6B6B7B")
LIGHT_GREY      = colors.HexColor("#F6F6F8")
CREAM           = colors.HexColor("#FAF8F4")
CAMEL           = colors.HexColor("#C9A96E")
RULE_GREY       = colors.HexColor("#E2E2E8")
WHITE           = colors.white

CRITICAL_COLOR  = colors.HexColor("#C0392B")
HIGH_COLOR      = colors.HexColor("#D4691E")
MEDIUM_COLOR    = colors.HexColor("#E8B84B")
LOW_COLOR       = colors.HexColor("#27AE60")
ESCALATED_COLOR = colors.HexColor("#C0392B")
DE_ESC_COLOR    = colors.HexColor("#27AE60")
CLOSED_COLOR    = colors.HexColor("#7B52C1")
NEW_COLOR       = colors.HexColor("#2471A3")
NO_CHANGE_COLOR = colors.HexColor("#6B6B7B")

def rating_color(r):
    return {"Critical": CRITICAL_COLOR, "High": HIGH_COLOR,
            "Medium": MEDIUM_COLOR, "Low": LOW_COLOR}.get(r, MID_GREY)

def delta_color(d):
    return {"ESCALATED": ESCALATED_COLOR, "DE-ESCALATED": DE_ESC_COLOR,
            "CLOSED": CLOSED_COLOR, "NEW": NEW_COLOR,
            "NO CHANGE": NO_CHANGE_COLOR}.get(d, MID_GREY)

def decision_color(d):
    return {"accepted": LOW_COLOR, "rejected": CRITICAL_COLOR,
            "pending": MEDIUM_COLOR}.get(d, MID_GREY)

def styles():
    S = {}
    def ps(name, **kw):
        S[name] = ParagraphStyle(name, **kw)

    ps("h_title",     fontName="Helvetica-Bold",   fontSize=20, textColor=WHITE,    leading=24)
    ps("h_sub",       fontName="Helvetica",         fontSize=9,  textColor=colors.HexColor("#CDC0F0"), leading=13)
    ps("sec",         fontName="Helvetica-Bold",    fontSize=11, textColor=PURPLE,   spaceBefore=14, spaceAfter=5)
    ps("label",       fontName="Helvetica-Bold",    fontSize=7,  textColor=MID_GREY, spaceAfter=1, leading=10)
    ps("value",       fontName="Helvetica-Bold",    fontSize=9,  textColor=DARK,     leading=13)
    ps("body",        fontName="Helvetica",         fontSize=8.5,textColor=DARK,     leading=13, spaceAfter=3)
    ps("body_bold",   fontName="Helvetica-Bold",    fontSize=8.5,textColor=DARK,     leading=13)
    ps("score_lbl",   fontName="Helvetica-Bold",    fontSize=8,  textColor=MID_GREY, alignment=TA_CENTER)
    ps("score_num",   fontName="Helvetica-Bold",    fontSize=26, textColor=PURPLE,   alignment=TA_CENTER, leading=30)
    ps("score_rtg",   fontName="Helvetica-Bold",    fontSize=11, textColor=WHITE,    alignment=TA_CENTER)
    ps("rationale",   fontName="Helvetica-Oblique", fontSize=8.5,textColor=MID_GREY, alignment=TA_CENTER, leading=13)
    ps("tbl_hdr",     fontName="Helvetica-Bold",    fontSize=7.5,textColor=WHITE,    alignment=TA_CENTER)
    ps("tbl_cell",    fontName="Helvetica",         fontSize=7.5,textColor=DARK,     leading=11)
    ps("tbl_badge",   fontName="Helvetica-Bold",    fontSize=7,  textColor=WHITE,    alignment=TA_CENTER)
    ps("flag_title",  fontName="Helvetica-Bold",    fontSize=9,  textColor=WHITE,    leading=13)
    ps("flag_meta",   fontName="Helvetica",         fontSize=8,  textColor=colors.HexColor("#E8E0FF"), leading=11)
    ps("footer",      fontName="Helvetica",         fontSize=7,  textColor=MID_GREY, alignment=TA_CENTER, leading=10)
    ps("metric_lbl",  fontName="Helvetica-Bold",    fontSize=7.5,textColor=WHITE,    alignment=TA_CENTER, leading=10)
    ps("metric_lbl_dark", fontName="Helvetica-Bold",fontSize=7.5,textColor=MID_GREY, alignment=TA_CENTER, leading=10)
    ps("metric_val",  fontName="Helvetica-Bold",    fontSize=20, textColor=WHITE,    alignment=TA_CENTER, leading=24)
    ps("metric_val_dark", fontName="Helvetica-Bold",fontSize=20, textColor=DARK,     alignment=TA_CENTER, leading=24)
    ps("audit_cell",  fontName="Helvetica",         fontSize=7.5,textColor=DARK,     leading=11)
    ps("audit_hdr",   fontName="Helvetica-Bold",    fontSize=7.5,textColor=WHITE,    alignment=TA_CENTER)
    return S

def generate_pdf(final_report: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.6*inch, rightMargin=0.6*inch,
        topMargin=0.45*inch, bottomMargin=0.65*inch,
    )
    S = styles()
    W = 7.3 * inch
    story = []

    meta     = final_report.get("report_metadata", {})
    overall  = final_report.get("overall_assessment", {})
    summary  = final_report.get("delta_summary", {})
    accepted = final_report.get("accepted_changes", [])
    rejected = final_report.get("rejected_changes", [])
    audit    = final_report.get("audit_trail", {})
    new_risks= final_report.get("new_risks_accepted", [])

    # ── HEADER ────────────────────────────────────────────────
    hdr = Table([[
        Paragraph("Risk Register Delta Report", S["h_title"]),
        Paragraph(f"Generated: {date.today().strftime('%B %d, %Y')}", S["h_sub"]),
    ]], colWidths=[W*0.72, W*0.28])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), PURPLE),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (0,0),(-1,-1), 18),
        ("RIGHTPADDING",  (0,0),(-1,-1), 18),
        ("TOPPADDING",    (0,0),(-1,-1), 20),
        ("BOTTOMPADDING", (0,0),(-1,-1), 20),
        ("ALIGN",         (1,0),(1,0),   "RIGHT"),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 8))

    # ── STUDY METADATA ────────────────────────────────────────
    meta_tbl = Table([
        [Paragraph("STUDY / DRUG",      S["label"]),
         Paragraph("STUDY ID",          S["label"]),
         Paragraph("REVIEW PERIOD",     S["label"]),
         Paragraph("SNAPSHOT DATE",     S["label"])],
        [Paragraph(meta.get("drug_name", "N/A"),       S["value"]),
         Paragraph(meta.get("study_id", "N/A"),        S["value"]),
         Paragraph(meta.get("review_period", "N/A"),   S["value"]),
         Paragraph(meta.get("snapshot_date", "N/A"),   S["value"])],
    ], colWidths=[W*0.25, W*0.20, W*0.30, W*0.25])
    meta_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), CREAM),
        ("LINEBELOW",     (0,1),(-1,1),  1.5, CAMEL),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("RIGHTPADDING",  (0,0),(-1,-1), 10),
        ("TOPPADDING",    (0,0),(-1,-1), 7),
        ("BOTTOMPADDING", (0,0),(-1,-1), 7),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 10))

    # ── OVERALL SCORE CHANGE ──────────────────────────────────
    prev_score    = overall.get("previous_study_risk_score", 0)
    updated_score = overall.get("updated_study_risk_score", 0)
    direction     = overall.get("score_direction", "STABLE")
    narrative     = overall.get("narrative", "")
    arrow         = {"INCREASED": "▲", "DECREASED": "▼", "STABLE": "→"}.get(direction, "")
    dir_color     = {"INCREASED": CRITICAL_COLOR, "DECREASED": LOW_COLOR,
                     "STABLE": MID_GREY}.get(direction, MID_GREY)

    sc_tbl = Table([[
        Paragraph(f"PREVIOUS SCORE\n{prev_score}/100", S["score_lbl"]),
        Paragraph(f"{arrow} {direction}",              ParagraphStyle("dir", fontName="Helvetica-Bold",
                                                        fontSize=14, textColor=WHITE, alignment=TA_CENTER)),
        Paragraph(f"UPDATED SCORE\n{updated_score}/100", S["score_lbl"]),
    ]], colWidths=[W*0.33, W*0.34, W*0.33])
    sc_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(0,0), PURPLE_LIGHT),
        ("BACKGROUND",    (1,0),(1,0), dir_color),
        ("BACKGROUND",    (2,0),(2,0), PURPLE_LIGHT),
        ("TEXTCOLOR",     (0,0),(0,0), PURPLE),
        ("TEXTCOLOR",     (2,0),(2,0), PURPLE),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 14),
        ("BOTTOMPADDING", (0,0),(-1,-1), 14),
        ("LEFTPADDING",   (0,0),(-1,-1), 12),
        ("RIGHTPADDING",  (0,0),(-1,-1), 12),
    ]))
    story.append(sc_tbl)
    story.append(Spacer(1, 5))
    story.append(Paragraph(narrative, S["rationale"]))
    story.append(Spacer(1, 8))

    # ── DELTA SUMMARY METRICS ─────────────────────────────────
    story.append(Paragraph("Delta Summary", S["sec"]))

    metric_labels = Table([[
        Paragraph("ESCALATED",    S["metric_lbl"]),
        Paragraph("DE-ESCALATED", S["metric_lbl"]),
        Paragraph("CLOSED",       S["metric_lbl"]),
        Paragraph("NO CHANGE",    S["metric_lbl_dark"]),
        Paragraph("NEW RISKS",    S["metric_lbl"]),
    ]], colWidths=[W/5]*5)
    metric_labels.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(0,0), ESCALATED_COLOR),
        ("BACKGROUND",    (1,0),(1,0), DE_ESC_COLOR),
        ("BACKGROUND",    (2,0),(2,0), CLOSED_COLOR),
        ("BACKGROUND",    (3,0),(3,0), LIGHT_GREY),
        ("BACKGROUND",    (4,0),(4,0), NEW_COLOR),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 4),
        ("RIGHTPADDING",  (0,0),(-1,-1), 4),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("LINEBEFORE",    (1,0),(4,0),   0.5, WHITE),
    ]))

    metric_values = Table([[
        Paragraph(str(summary.get("escalated", 0)),    S["metric_val"]),
        Paragraph(str(summary.get("de_escalated", 0)), S["metric_val"]),
        Paragraph(str(summary.get("closed", 0)),       S["metric_val"]),
        Paragraph(str(summary.get("no_change", 0)),    S["metric_val_dark"]),
        Paragraph(str(summary.get("new_risks", 0)),    S["metric_val"]),
    ]], colWidths=[W/5]*5)
    metric_values.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(0,0), ESCALATED_COLOR),
        ("BACKGROUND",    (1,0),(1,0), DE_ESC_COLOR),
        ("BACKGROUND",    (2,0),(2,0), CLOSED_COLOR),
        ("BACKGROUND",    (3,0),(3,0), LIGHT_GREY),
        ("BACKGROUND",    (4,0),(4,0), NEW_COLOR),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("LEFTPADDING",   (0,0),(-1,-1), 4),
        ("RIGHTPADDING",  (0,0),(-1,-1), 4),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("LINEBEFORE",    (1,0),(4,0),   0.5, WHITE),
    ]))
    story.append(metric_labels)
    story.append(metric_values)
    story.append(Spacer(1, 12))

    # ── ACCEPTED CHANGES ──────────────────────────────────────
    if accepted:
        story.append(Paragraph(f"Accepted Changes  ({len(accepted)})", S["sec"]))
        story.append(Spacer(1, 4))

        for change in accepted:
            dtype    = change.get("delta_type", "NEW")
            dc       = delta_color(dtype)
            reviewer = change.get("reviewer_name", "N/A")
            role     = change.get("reviewer_role", "")

            hdr_row = Table([[
                Paragraph(f"{change.get('risk_id')}  ·  {change.get('risk_title', '')}", S["flag_title"]),
                Paragraph(f"{dtype}  |  ✅ Accepted", S["flag_meta"]),
            ]], colWidths=[W*0.65, W*0.35])
            hdr_row.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,-1), dc),
                ("LEFTPADDING",   (0,0),(-1,-1), 10),
                ("RIGHTPADDING",  (0,0),(-1,-1), 10),
                ("TOPPADDING",    (0,0),(-1,-1), 7),
                ("BOTTOMPADDING", (0,0),(-1,-1), 7),
                ("ALIGN",         (1,0),(1,0),   "RIGHT"),
                ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
            ]))

            prev = change.get("previous_rating", "")
            rec  = change.get("recommended_rating", change.get("recommended_rating", ""))
            body_items = []
            if prev:
                body_items.append(f"<b>Rating Change:</b> {prev} → {rec}")
            else:
                body_items.append(f"<b>Recommended Rating:</b> {rec}")
            if change.get("reason"):
                body_items.append(f"<b>Reason:</b> {change.get('reason')}")
            if change.get("supporting_data"):
                body_items.append(f"<b>Supporting Data:</b> {change.get('supporting_data')}")
            body_items.append(f"<b>Action:</b> {change.get('recommended_action', '')}")
            body_items.append(f"<b>Owner:</b> {change.get('owner', '')}")
            body_items.append(f"<b>Reviewed by:</b> {reviewer}" + (f", {role}" if role else ""))

            body_rows = [[Paragraph(t, S["body"])] for t in body_items]
            body_tbl  = Table(body_rows, colWidths=[W])
            body_tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,-1), PURPLE_LIGHT),
                ("LEFTPADDING",   (0,0),(-1,-1), 10),
                ("RIGHTPADDING",  (0,0),(-1,-1), 10),
                ("TOPPADDING",    (0,0),(0,0),   8),
                ("BOTTOMPADDING", (0,-1),(0,-1), 8),
                ("TOPPADDING",    (0,1),(-1,-1), 3),
                ("BOTTOMPADDING", (0,0),(-1,-2), 3),
            ]))
            story.append(KeepTogether([hdr_row, body_tbl]))
            story.append(Spacer(1, 6))

    # ── REJECTED CHANGES ──────────────────────────────────────
    if rejected:
        story.append(Paragraph(f"Rejected Changes  ({len(rejected)})", S["sec"]))
        story.append(Spacer(1, 4))

        for change in rejected:
            dtype    = change.get("delta_type", "NEW")
            reviewer = change.get("reviewer_name", "N/A")
            role     = change.get("reviewer_role", "")

            hdr_row = Table([[
                Paragraph(f"{change.get('risk_id')}  ·  {change.get('risk_title', '')}", S["flag_title"]),
                Paragraph(f"{dtype}  |  ❌ Rejected", S["flag_meta"]),
            ]], colWidths=[W*0.65, W*0.35])
            hdr_row.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,-1), MID_GREY),
                ("LEFTPADDING",   (0,0),(-1,-1), 10),
                ("RIGHTPADDING",  (0,0),(-1,-1), 10),
                ("TOPPADDING",    (0,0),(-1,-1), 7),
                ("BOTTOMPADDING", (0,0),(-1,-1), 7),
                ("ALIGN",         (1,0),(1,0),   "RIGHT"),
                ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
            ]))

            body_items = [
                f"<b>Reason:</b> {change.get('reason', '')}",
                f"<b>Reviewed by:</b> {reviewer}" + (f", {role}" if role else ""),
            ]
            body_rows = [[Paragraph(t, S["body"])] for t in body_items]
            body_tbl  = Table(body_rows, colWidths=[W])
            body_tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,-1), LIGHT_GREY),
                ("LEFTPADDING",   (0,0),(-1,-1), 10),
                ("RIGHTPADDING",  (0,0),(-1,-1), 10),
                ("TOPPADDING",    (0,0),(0,0),   8),
                ("BOTTOMPADDING", (0,-1),(0,-1), 8),
                ("TOPPADDING",    (0,1),(-1,-1), 3),
                ("BOTTOMPADDING", (0,0),(-1,-2), 3),
            ]))
            story.append(KeepTogether([hdr_row, body_tbl]))
            story.append(Spacer(1, 6))

    # ── AUDIT TRAIL ───────────────────────────────────────────
    decisions = audit.get("decisions", [])
    if decisions:
        story.append(Paragraph("Audit Trail", S["sec"]))
        story.append(Paragraph(
            "Complete record of all review decisions for TMF filing and regulatory compliance.",
            S["body"]))
        story.append(Spacer(1, 4))

        audit_hdr = [
            Paragraph("RISK ID",    S["audit_hdr"]),
            Paragraph("RISK TITLE", S["audit_hdr"]),
            Paragraph("CHANGE TYPE",S["audit_hdr"]),
            Paragraph("DECISION",   S["audit_hdr"]),
            Paragraph("REVIEWER",   S["audit_hdr"]),
            Paragraph("ROLE",       S["audit_hdr"]),
            Paragraph("DATE",       S["audit_hdr"]),
        ]
        audit_rows = [audit_hdr]
        for d in decisions:
            dec_color = {"accepted": LOW_COLOR, "rejected": CRITICAL_COLOR,
                         "pending": MEDIUM_COLOR}.get(d.get("decision"), MID_GREY)
            audit_rows.append([
                Paragraph(d.get("risk_id", ""),       S["audit_cell"]),
                Paragraph(d.get("risk_title", ""),    S["audit_cell"]),
                Paragraph(d.get("delta_type", ""),    S["audit_cell"]),
                Paragraph(d.get("decision", "").upper(), ParagraphStyle("dec",
                    fontName="Helvetica-Bold", fontSize=7.5,
                    textColor=WHITE, alignment=TA_CENTER)),
                Paragraph(d.get("reviewer_name", "N/A"), S["audit_cell"]),
                Paragraph(d.get("reviewer_role", ""),    S["audit_cell"]),
                Paragraph(d.get("timestamp", ""),        S["audit_cell"]),
            ])

        cw = [W*0.09, W*0.25, W*0.13, W*0.10, W*0.17, W*0.13, W*0.13]
        at = Table(audit_rows, colWidths=cw, repeatRows=1)
        ts = TableStyle([
            ("BACKGROUND",    (0,0),(-1,0),  DARK),
            ("TEXTCOLOR",     (0,0),(-1,0),  WHITE),
            ("ALIGN",         (0,0),(-1,-1), "LEFT"),
            ("ALIGN",         (3,0),(3,-1),  "CENTER"),
            ("VALIGN",        (0,0),(-1,-1), "TOP"),
            ("LEFTPADDING",   (0,0),(-1,-1), 5),
            ("RIGHTPADDING",  (0,0),(-1,-1), 5),
            ("TOPPADDING",    (0,0),(-1,-1), 5),
            ("BOTTOMPADDING", (0,0),(-1,-1), 5),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, LIGHT_GREY]),
            ("GRID",          (0,0),(-1,-1), 0.25, RULE_GREY),
            ("LINEBELOW",     (0,0),(-1,0),  1, CAMEL),
        ])
        for i, d in enumerate(decisions, 1):
            dc = {"accepted": LOW_COLOR, "rejected": CRITICAL_COLOR,
                  "pending": MEDIUM_COLOR}.get(d.get("decision"), MID_GREY)
            ts.add("BACKGROUND", (3,i),(3,i), dc)
        at.setStyle(ts)
        story.append(at)

    # ── FOOTER ────────────────────────────────────────────────
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width=W, thickness=0.75, color=CAMEL))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "This Risk Register Delta Report was generated by an AI-assisted agent and requires qualified clinical review "
        "before use in regulated environments. Accepted changes should be used to update the study risk register in "
        "the RBQM system. This document is intended for TMF filing per ICH E6(R2) requirements.  ·  "
        f"Report Date: {date.today().strftime('%B %d, %Y')}",
        S["footer"]
    ))

    doc.build(story)
    return buf.getvalue()