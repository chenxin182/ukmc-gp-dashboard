import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie

# ── Colours ──────────────────────────────────────────────────────────────────
GREEN = colors.HexColor("#2E7D32")
LIGHT_GREEN = colors.HexColor("#E8F5E9")
BLUE = colors.HexColor("#1565C0")
LIGHT_BLUE = colors.HexColor("#E3F2FD")
GREY = colors.HexColor("#BDBDBD")

CHART_COLORS = [
    colors.HexColor("#4CAF50"),
    colors.HexColor("#2196F3"),
    colors.HexColor("#FF9800"),
    colors.HexColor("#9C27B0"),
    colors.HexColor("#F44336"),
    colors.HexColor("#00BCD4"),
]

# ── Industry benchmarks (tCO2e/year for an average SME) ──────────────────────
BENCHMARKS = {
    "Singapore": 45.0,
    "Malaysia": 60.0,
}


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("RTitle", parent=base["Title"],
                                fontSize=22, textColor=GREEN, spaceAfter=4),
        "subtitle": ParagraphStyle("RSub", parent=base["Normal"],
                                   fontSize=11, textColor=colors.grey, spaceAfter=3),
        "h2": ParagraphStyle("RH2", parent=base["Heading2"],
                              fontSize=13, textColor=GREEN, spaceBefore=14, spaceAfter=6),
        "body": ParagraphStyle("RBody", parent=base["Normal"],
                               fontSize=10, spaceAfter=6),
        "small": ParagraphStyle("RSmall", parent=base["Normal"],
                                fontSize=7.5, textColor=colors.grey, spaceAfter=2),
        "cell": ParagraphStyle("RCell", parent=base["Normal"], fontSize=8),
    }


def _info_box(text: str, bg: colors.Color, fg: colors.Color) -> Table:
    """Returns a single-cell Table that renders as a coloured info box."""
    tbl = Table([[Paragraph(text, ParagraphStyle(
        "IB", fontSize=8.5, textColor=fg, leading=13))]],
        colWidths=[17 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return tbl


def _bar_chart(scope1: float, scope2: float) -> Drawing:
    drawing = Drawing(440, 200)
    bc = VerticalBarChart()
    bc.x = 70
    bc.y = 20
    bc.height = 150
    bc.width = 310
    max_val = max(scope1, scope2, 0.001)
    bc.data = [[scope1, scope2]]
    bc.bars[0].fillColor = CHART_COLORS[0]
    bc.bars[0].strokeColor = GREEN
    bc.bars[0].strokeWidth = 0.5
    bc.categoryAxis.categoryNames = ["Scope 1\n(Direct Combustion)", "Scope 2\n(Grid Electricity)"]
    bc.categoryAxis.labels.fontSize = 9
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = max_val * 1.4
    bc.valueAxis.labels.fontSize = 8
    bc.valueAxis.labelTextFormat = "%.4f"
    drawing.add(bc)
    return drawing


def _pie_chart(details: list) -> Drawing:
    active = [d for d in details if d["emissions"] > 0]
    if not active:
        return Drawing(1, 1)

    drawing = Drawing(440, 200)
    pie = Pie()
    pie.x = 80
    pie.y = 20
    pie.width = 160
    pie.height = 160
    pie.data = [d["emissions"] for d in active]
    pie.labels = [d["name"][:22] for d in active]
    pie.sideLabels = 1
    pie.sideLabelsOffset = 0.08
    for i in range(len(active)):
        pie.slices[i].fillColor = CHART_COLORS[i % len(CHART_COLORS)]
        pie.slices[i].strokeWidth = 0.5
        pie.slices[i].label_fontSize = 8
    drawing.add(pie)
    return drawing


def generate_pdf_report(company_name: str, country: str, result: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2.5 * cm,
        title=f"Carbon Emissions Report – {company_name}",
    )

    S = _styles()
    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("Carbon Emissions Report", S["title"]))
    story.append(Paragraph(f"Prepared for: <b>{company_name}</b>", S["subtitle"]))
    story.append(Paragraph(
        f"Country / Region: <b>{country}</b>&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"Report Date: <b>{datetime.now().strftime('%d %B %Y')}</b>",
        S["subtitle"],
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=GREEN, spaceAfter=10))

    # ── Standards banner ──────────────────────────────────────────────────────
    story.append(_info_box(
        "Methodology: GHG Protocol Corporate Accounting &amp; Reporting Standard (Scope 1 &amp; 2)  |  "
        "Aligned with ISSB IFRS S2 Climate-related Disclosures  |  "
        "Singapore NEA &amp; Malaysia GHG Reporting Guidelines",
        LIGHT_BLUE, BLUE,
    ))
    story.append(Spacer(1, 0.4 * cm))

    # ── Executive summary ─────────────────────────────────────────────────────
    story.append(Paragraph("Executive Summary", S["h2"]))

    benchmark = BENCHMARKS.get(country, 50.0)
    pct = (result["total_emissions"] / benchmark) * 100 if benchmark else 0

    rows = [
        ["Metric", "Value", "Unit"],
        ["Total GHG Emissions", f"{result['total_emissions']:.4f}", "tCO\u2082e"],
        ["Scope 1 \u2014 Direct Emissions", f"{result['scope1_emissions']:.4f}", "tCO\u2082e"],
        ["Scope 2 \u2014 Electricity (Market-based)", f"{result['scope2_emissions']:.4f}", "tCO\u2082e"],
        [f"Industry Benchmark ({country} SME Average)", f"{benchmark:.1f}", "tCO\u2082e / yr"],
        ["Your Footprint vs Benchmark", f"{pct:.1f}%", "\u00b1 of avg"],
    ]
    tbl = Table(rows, colWidths=[9 * cm, 4.5 * cm, 3.5 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 1), (-1, 1), LIGHT_GREEN),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, GREY),
        ("ROWBACKGROUNDS", (0, 2), (-1, -1), [colors.white, colors.HexColor("#F9FBE7")]),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.5 * cm))

    # ── Scope bar chart ───────────────────────────────────────────────────────
    story.append(Paragraph("Emissions by Scope (tCO\u2082e)", S["h2"]))
    story.append(_bar_chart(result["scope1_emissions"], result["scope2_emissions"]))
    story.append(Spacer(1, 0.3 * cm))

    # ── Pie chart (only when >1 activity) ────────────────────────────────────
    if len(result["details"]) > 1:
        story.append(Paragraph("Emissions by Energy Source", S["h2"]))
        story.append(_pie_chart(result["details"]))
        story.append(Spacer(1, 0.3 * cm))

    # ── Activity detail table ─────────────────────────────────────────────────
    story.append(Paragraph("Activity-Level Emission Details", S["h2"]))
    detail_rows = [["Energy Type", "Consumption", "Unit", "Factor\n(tCO\u2082e/unit)", "Emissions\n(tCO\u2082e)", "Scope"]]
    for d in result["details"]:
        detail_rows.append([
            Paragraph(d["name"], S["cell"]),
            f"{d['consumption']:,.2f}",
            d["unit"],
            f"{d['emission_factor']:.7f}",
            f"{d['emissions']:.4f}",
            f"Scope {d['scope']}",
        ])
    detail_tbl = Table(detail_rows, colWidths=[5.5 * cm, 2.5 * cm, 1.5 * cm, 3 * cm, 2.5 * cm, 2 * cm])
    detail_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, GREY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F8E9")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(detail_tbl)
    story.append(Spacer(1, 0.5 * cm))

    # ── Benchmark commentary ──────────────────────────────────────────────────
    story.append(Paragraph("Benchmark Analysis", S["h2"]))
    if pct < 100:
        comment = (
            f"Your company emits <b>{result['total_emissions']:.4f} tCO\u2082e</b>, "
            f"which is <b>{100 - pct:.1f}% below</b> the {country} SME average "
            f"of {benchmark:.1f} tCO\u2082e/yr. Commendable performance. "
            "Consider renewable energy certificates (RECs) or verified carbon credits "
            "to further reduce your net footprint."
        )
    else:
        comment = (
            f"Your company emits <b>{result['total_emissions']:.4f} tCO\u2082e</b>, "
            f"which is <b>{pct - 100:.1f}% above</b> the {country} SME average "
            f"of {benchmark:.1f} tCO\u2082e/yr. "
            "Consider energy efficiency audits, lower-carbon energy sources, or "
            "purchasing verified carbon credits to offset excess emissions."
        )
    story.append(Paragraph(comment, S["body"]))

    # ── Reduction recommendations ─────────────────────────────────────────────
    story.append(Paragraph("Recommended Next Steps", S["h2"]))
    for rec in [
        "1. Conduct an energy audit to identify high-consumption areas.",
        "2. Explore solar PV installation or green tariff options from your utility.",
        "3. Transition company vehicles to hybrid / electric to reduce Scope 1 emissions.",
        "4. Engage a carbon credit broker to offset residual emissions (VCS / Gold Standard).",
        "5. Set a Science-Based Target (SBT) aligned with the 1.5\u00b0C pathway.",
    ]:
        story.append(Paragraph(rec, S["body"]))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=GREY, spaceBefore=16))
    story.append(Paragraph(
        "Disclaimer: Generated using GHG Protocol Corporate Accounting &amp; Reporting Standard (Scope 1 &amp; 2). "
        "Emission factors: EMA Singapore 2025, Suruhanjaya Tenaga Malaysia 2025, IPCC 2006 Guidelines. "
        "Aligned with ISSB IFRS S2. Results are indicative and should be verified by a qualified "
        "sustainability professional before external disclosure.",
        S["small"],
    ))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%d %B %Y %H:%M')} UTC  |  "
        "ESG Carbon Accounting Platform  |  Confidential",
        S["small"],
    ))

    doc.build(story)
    return buf.getvalue()
