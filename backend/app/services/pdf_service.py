"""
Generates a rescue/medical report PDF for a single Report record:
animal details, injury/severity assessment, assigned volunteer,
hospital, and full status timeline. Uses reportlab (no external
service or API key required).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

FOREST_GREEN = colors.HexColor("#1B5E3A")
LIGHT_GREEN = colors.HexColor("#E7F3EC")


def generate_medical_report_pdf(report, hospital, volunteer, tracking_events, output_path: str) -> str:
    """report, hospital, volunteer are ORM objects (hospital/volunteer may be None).
    tracking_events is an iterable of TrackingEvent ORM objects."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("SHIELDTitle", parent=styles["Title"], textColor=FOREST_GREEN, fontSize=20)
    heading_style = ParagraphStyle("SHIELDHeading", parent=styles["Heading2"], textColor=FOREST_GREEN, spaceBefore=14)
    body_style = ParagraphStyle("SHIELDBody", parent=styles["Normal"], fontSize=10, leading=14)

    analysis = json.loads(report.analysis_json)
    story = []

    story.append(Paragraph("SHIELD AI - Rescue &amp; Medical Report", title_style))
    story.append(Paragraph(f"Report ID: {report.display_id}", body_style))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%d %b %Y, %H:%M UTC')}", body_style))
    story.append(Spacer(1, 10))

    def kv_table(rows: list[tuple[str, str]]) -> Table:
        table = Table(rows, colWidths=[45 * mm, 120 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), LIGHT_GREEN),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD9D1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        return table

    story.append(Paragraph("Report Details", heading_style))
    story.append(kv_table([
        ("Reporter", report.reporter_name),
        ("Phone", report.phone),
        ("Animal Type", report.animal_type),
        ("Landmark", report.landmark or "-"),
        ("Location", f"{report.latitude:.5f}, {report.longitude:.5f}"),
        ("Description", report.description),
    ]))

    story.append(Paragraph("AI / Veterinary Assessment", heading_style))
    story.append(kv_table([
        ("Injury", analysis.get("injury", "-")),
        ("Visible Signs", analysis.get("visible_signs", "-")),
        ("Severity", analysis.get("severity", "-")),
        ("Confidence", f"{float(analysis.get('confidence', 0)) * 100:.0f}%"),
        ("Bleeding Detected", "Yes" if analysis.get("bleeding_detected") else "No"),
        ("Fracture Suspected", "Yes" if analysis.get("fracture_suspected") else "No"),
        ("First Aid Given", analysis.get("first_aid", "-")),
        ("Recommendation", analysis.get("recommendation", "-")),
        ("Assessment Source", analysis.get("source", "-")),
        ("Priority Score", str(report.priority_score)),
    ]))

    story.append(Paragraph("Assigned Team", heading_style))
    team_rows = [("Volunteer", volunteer.user.full_name if (volunteer and volunteer.user) else "Not yet assigned")]
    if hospital:
        team_rows.append(("Hospital / NGO", hospital.name))
        team_rows.append(("Hospital Address", hospital.address))
    story.append(kv_table(team_rows))

    story.append(Paragraph("Rescue Timeline", heading_style))
    timeline_rows = [["Status", "Note", "Timestamp"]]
    for event in tracking_events:
        timeline_rows.append([event.status, event.note or "-", event.created_at.strftime("%d %b %Y, %H:%M")])
    timeline_table = Table(timeline_rows, colWidths=[45 * mm, 80 * mm, 40 * mm])
    timeline_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), FOREST_GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD9D1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREEN]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(timeline_table)

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "Disclaimer: AI-assisted assessments are preliminary and do not replace a licensed veterinary diagnosis.",
        ParagraphStyle("Disclaimer", parent=styles["Normal"], fontSize=8, textColor=colors.grey),
    ))

    doc.build(story)
    return output_path
