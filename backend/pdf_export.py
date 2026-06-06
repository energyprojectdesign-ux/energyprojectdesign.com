"""PDF export for a project — generates a comprehensive A4 PDF report
with project data, technical data, calc results and verification status.

Uses reportlab (pure-Python, no system deps).
"""
import io
from datetime import datetime
from typing import Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER


# Palette matching the Swiss / brutalist UI
COL_ACCENT = colors.HexColor("#FFB300")
COL_BLACK = colors.HexColor("#0A0A0A")
COL_GRAY = colors.HexColor("#4B5563")
COL_LIGHT = colors.HexColor("#F9FAFB")
COL_OK = colors.HexColor("#16A34A")
COL_WARN = colors.HexColor("#FFB300")
COL_MISSING = colors.HexColor("#DC2626")


def _styles():
    base = getSampleStyleSheet()
    s = {
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontSize=20, leading=24, textColor=COL_BLACK, spaceAfter=10),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=13, leading=18, textColor=COL_BLACK, spaceBefore=14, spaceAfter=8, borderPadding=4),
        "label": ParagraphStyle("label", parent=base["Normal"], fontSize=8, leading=10, textColor=COL_GRAY, spaceBefore=2),
        "body": ParagraphStyle("body", parent=base["Normal"], fontSize=10, leading=14, textColor=COL_BLACK),
        "small": ParagraphStyle("small", parent=base["Normal"], fontSize=8, leading=10, textColor=COL_GRAY),
        "mono": ParagraphStyle("mono", parent=base["Normal"], fontName="Courier", fontSize=8, leading=10, textColor=COL_GRAY),
    }
    return s


def _header(canvas, doc, project_name):
    canvas.saveState()
    # Top bar
    canvas.setFillColor(COL_BLACK)
    canvas.rect(0, A4[1] - 1.6 * cm, A4[0], 1.6 * cm, fill=1, stroke=0)
    canvas.setFillColor(COL_ACCENT)
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawString(2 * cm, A4[1] - 1.0 * cm, "ENERGY PROJECT DESIGN")
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2 * cm, A4[1] - 1.35 * cm, f"Raport proiect — {project_name[:80]}")
    canvas.setFillColor(COL_ACCENT)
    canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 1.0 * cm, "v4.7")
    # Footer
    canvas.setFillColor(COL_GRAY)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(2 * cm, 1.0 * cm, f"Generat: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    canvas.drawRightString(A4[0] - 2 * cm, 1.0 * cm, f"Pagina {doc.page}")
    canvas.drawCentredString(A4[0] / 2, 1.0 * cm, "ENERGY PROJECT DESIGN SRL · CUI 43151074 · J40/12982/2020")
    canvas.restoreState()


def _kv_table(rows, col_widths=(5.5 * cm, 11 * cm)):
    """Build a simple 2-column key-value table."""
    data = [[k, v if v else "—"] for k, v in rows]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), COL_GRAY),
        ("TEXTCOLOR", (1, 0), (1, -1), COL_BLACK),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, COL_LIGHT]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")),
    ]))
    return t


def _section_header(text, styles):
    p = Paragraph(f'<font color="#FFB300">▍</font> <b>{text}</b>', styles["h2"])
    return KeepTogether([Spacer(1, 0.1 * cm), p, Spacer(1, 0.15 * cm)])


def build_project_pdf(project: dict, calc_results: dict = None, verification: dict = None) -> bytes:
    """Render a project to a styled A4 PDF and return the bytes."""
    buf = io.BytesIO()
    project_name = project.get("name") or project.get("beneficiar") or "Proiect"
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2.5 * cm, bottomMargin=1.8 * cm,
        title=f"Raport proiect — {project_name}",
        author="ENERGY PROJECT DESIGN SRL",
    )
    styles = _styles()
    story = []

    # Title block
    story.append(Paragraph(project_name, styles["h1"]))
    story.append(Paragraph(
        f'<font color="#6B7280">{project.get("industry", "—")} / {project.get("subdomain", "—")} · '
        f'Completare: {project.get("completion", 0)}%</font>',
        styles["small"],
    ))
    story.append(Spacer(1, 0.4 * cm))

    # General data
    story.append(_section_header("Date generale proiect", styles))
    story.append(_kv_table([
        ("Beneficiar", project.get("beneficiar")),
        ("Adresa lucrare", project.get("adresa_lucrare")),
        ("Localitate", project.get("localitate")),
        ("Județ", project.get("judet")),
        ("Telefon", project.get("telefon")),
        ("Email", project.get("email")),
        ("OSD", project.get("osd")),
        ("Tip lucrare", project.get("tip_lucrare")),
        ("Număr contract", project.get("numar_contract")),
        ("Data contract", project.get("data_contract")),
    ]))

    # Team
    story.append(_section_header("Echipa autorizată", styles))
    story.append(_kv_table([
        ("Proiectant", project.get("proiectant")),
        ("Executant", project.get("executant")),
        ("Verificator VGD", project.get("verificator_vgd")),
        ("Atestat VGD", project.get("atestat_vgd")),
        ("Data verificare VGD", project.get("data_verificare_vgd")),
        ("Status VGD", project.get("status_vgd")),
        ("Responsabil RTE", project.get("responsabil_rte")),
        ("Autorizație RTE", project.get("autorizatie_rte")),
        ("Data verificare RTE", project.get("data_verificare_rte")),
        ("Status RTE", project.get("status_rte")),
    ]))

    # Technical
    td = project.get("technical_data") or {}
    if td:
        story.append(_section_header("Date tehnice", styles))
        rows = []
        for key in ("debit_instalat", "presiune_regim", "diametru_conducta", "material_conducta",
                    "lungime_bransament", "punct_racordare", "post_reglare", "contor",
                    "categorie_consumator", "traseu", "observatii_tehnice"):
            v = td.get(key)
            if v not in (None, "", 0):
                rows.append((key.replace("_", " ").title(), str(v)))
        if rows:
            story.append(_kv_table(rows))

    # Calc results
    calc = calc_results or project.get("calc_results") or {}
    if calc:
        story.append(_section_header("Calcul inteligent", styles))
        data = [["Mărime", "Valoare", "Status", "Formulă"]]
        labels = {
            "debit_calculat_mc_h": "Debit calculat (mc/h)",
            "debit_recomandat_mc_h": "Debit recomandat (mc/h)",
            "putere_instalata_kw": "Putere instalată (kW)",
            "risc_presiune": "Risc presiune",
            "estimare_cost": "Estimare cost (RON)",
            "contor_orientativ": "Contor recomandat",
        }
        for k, r in calc.items():
            data.append([
                labels.get(k, k),
                str(r.get("value", "—")),
                r.get("status", "—"),
                r.get("formula", "—")[:42],
            ])
        t = Table(data, colWidths=(4.5 * cm, 3.5 * cm, 2.5 * cm, 6 * cm))
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COL_BLACK),
            ("TEXTCOLOR", (0, 0), (-1, 0), COL_ACCENT),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COL_LIGHT]),
            ("FONTNAME", (3, 1), (3, -1), "Courier"),
        ]))
        story.append(t)

    # Verification (if provided)
    if verification:
        story.append(_section_header("Verificare documentație", styles))
        story.append(Paragraph(
            f'Scor total: <b>{verification.get("overall_score", 0)}%</b> · '
            f'OK: {verification.get("summary", {}).get("ok", 0)} · '
            f'Atenție: {verification.get("summary", {}).get("warning", 0)} · '
            f'Lipsă: {verification.get("summary", {}).get("missing", 0)}',
            styles["body"],
        ))
        story.append(Spacer(1, 0.2 * cm))
        data = [["Categorie", "Status", "Scor"]]
        for c in verification.get("checks", []):
            data.append([c.get("label"), c.get("status"), f'{c.get("score", 0)}%'])
        t = Table(data, colWidths=(9 * cm, 4 * cm, 3.5 * cm))
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COL_BLACK),
            ("TEXTCOLOR", (0, 0), (-1, 0), COL_ACCENT),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COL_LIGHT]),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t)

    # Notes
    if project.get("observatii"):
        story.append(_section_header("Observații generale", styles))
        story.append(Paragraph(project["observatii"], styles["body"]))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        '<font color="#6B7280" size="7">Document generat automat de platforma Energy Project Design Services. '
        'Pentru orice clarificare contactați: <b>contact@energyprojectdesign.ro</b></font>',
        styles["small"],
    ))

    on_page = lambda c, d: _header(c, d, project_name)  # noqa: E731
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Tech Offer Photovoltaic — commercial-grade A4 PDF generated directly from
# /api/photovoltaic results. Designed for B2B sales handoff to end clients.
# ─────────────────────────────────────────────────────────────────────────────
def _tech_offer_header(canvas, doc, project_name, company_name):
    canvas.saveState()
    # Premium top bar with gradient look
    canvas.setFillColor(COL_BLACK)
    canvas.rect(0, A4[1] - 2.2 * cm, A4[0], 2.2 * cm, fill=1, stroke=0)
    canvas.setFillColor(COL_ACCENT)
    canvas.rect(0, A4[1] - 2.25 * cm, A4[0], 0.05 * cm, fill=1, stroke=0)
    canvas.setFillColor(COL_ACCENT)
    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawString(2 * cm, A4[1] - 1.1 * cm, "OFERTĂ TEHNICĂ — SISTEM FOTOVOLTAIC")
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2 * cm, A4[1] - 1.55 * cm, f"Beneficiar: {project_name[:60]}")
    canvas.drawString(2 * cm, A4[1] - 1.9 * cm, f"Emitent: {company_name[:60]}")
    canvas.setFillColor(COL_ACCENT)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 1.1 * cm, "ANRE Ord. 34/2024")
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 7)
    canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 1.55 * cm, "SR EN 50618 · I7-2011")
    canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 1.9 * cm, f"Generat: {datetime.now().strftime('%d.%m.%Y')}")
    # Footer
    canvas.setFillColor(COL_GRAY)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(2 * cm, 1.2 * cm, "Ofertă validă 30 zile · Documentul nu constituie angajament contractual.")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Pagina {doc.page}")
    canvas.setFillColor(COL_ACCENT)
    canvas.rect(0, 0.9 * cm, A4[0], 0.04 * cm, fill=1, stroke=0)
    canvas.setFillColor(COL_BLACK)
    canvas.setFont("Helvetica-Bold", 7)
    canvas.drawCentredString(A4[0] / 2, 0.55 * cm, "ENERGY PROJECT DESIGN SERVICES · contact@energyprojectdesign.ro")
    canvas.restoreState()


def build_tech_offer_fv_pdf(project: dict, fv_results: dict, fv_data: dict, company: Optional[dict] = None) -> bytes:
    """Render a commercial Photovoltaic Tech Offer PDF and return bytes.

    Args:
        project: project dict (beneficiar, adresa_lucrare, etc.)
        fv_results: output of photovoltaic.calculate()
        fv_data: input data used for the calculation
        company: optional emitter company profile
    """
    buf = io.BytesIO()
    project_name = project.get("beneficiar") or project.get("name") or "Beneficiar"
    company_name = (company or {}).get("name") or "Energy Project Design SRL"

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=3.0 * cm, bottomMargin=2.0 * cm,
        title=f"Ofertă tehnică FV — {project_name}",
        author=company_name,
    )
    styles = _styles()
    story = []

    # ── Hero block ──
    pkwp = fv_results.get("p_kwp", "—")
    cat = (fv_results.get("categorie_anre") or {})
    hero_data = [[
        Paragraph(
            f'<font size="9" color="#6B7280">SISTEM FOTOVOLTAIC PROPUS</font><br/>'
            f'<font size="28" color="#0A0A0A"><b>{pkwp} kWp</b></font><br/>'
            f'<font size="10" color="#4B5563">Categorie ANRE <b>{cat.get("categorie", "—")}</b> · {cat.get("label", "")}</font>',
            styles["body"]
        ),
        Paragraph(
            f'<font size="8" color="#FFB300"><b>TIP RACORD</b></font><br/>'
            f'<font size="11" color="#0A0A0A">{cat.get("tip_racord", "—")}</font><br/><br/>'
            f'<font size="8" color="#FFB300"><b>AVIZ NECESAR</b></font><br/>'
            f'<font size="11" color="#0A0A0A">{cat.get("aviz", "—")}</font>',
            styles["body"]
        ),
    ]]
    hero = Table(hero_data, colWidths=(11 * cm, 6 * cm))
    hero.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COL_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, COL_ACCENT),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(hero)
    story.append(Spacer(1, 0.5 * cm))

    # ── Beneficiar & emitent ──
    story.append(_section_header("Părți contractante", styles))
    story.append(_kv_table([
        ("Beneficiar", project.get("beneficiar")),
        ("Adresa lucrării", f'{project.get("adresa_lucrare", "")}, {project.get("localitate", "")} {project.get("judet", "")}'.strip(", ")),
        ("Telefon contact", project.get("telefon")),
        ("Email contact", project.get("email")),
        ("Emitent ofertă", company_name),
        ("CUI emitent", (company or {}).get("cui") or "RO43151074"),
        ("Reprezentant", project.get("proiectant") or (company or {}).get("rep") or "—"),
    ]))

    # ── Componente sistem ──
    panouri = fv_results.get("panouri", {})
    string_ = fv_results.get("string", {})
    invertor = fv_results.get("invertor", {})
    story.append(_section_header("Configurație tehnică propusă", styles))
    comp_data = [
        ["#", "Componentă", "Specificație", "Cantitate"],
        ["1", "Panouri fotovoltaice", f'{panouri.get("putere_unitara_wp", "—")} Wp mono TOPCon', f'{panouri.get("n_panouri", "—")} buc'],
        ["2", "Configurație string", f'{string_.get("n_serie_optim", "—")} module/string · {string_.get("u_string_stc_v", "—")} V STC', f'{string_.get("n_string", "—")} string'],
        ["3", "Invertor", f'{invertor.get("p_invertor_recomandat_kw", "—")} kW · raport DC/AC {invertor.get("raport_dc_ac", "—")}', "1 buc"],
        ["4", "Cablu DC", f'{fv_results.get("cablu_dc", {}).get("tip_cablu", "—")} · {fv_results.get("cablu_dc", {}).get("sectiune_standard_mm2", "—")} mm²', f'{fv_data.get("lungime_dc_m", "—")} m'],
        ["5", "Cablu AC", f'{fv_results.get("cablu_ac", {}).get("tip_cablu", "—")} · {fv_results.get("cablu_ac", {}).get("sectiune_standard_mm2", "—")} mm²', f'{fv_data.get("lungime_ac_m", "—")} m'],
    ]
    # Add protections as additional rows
    protectii = fv_results.get("protectii", [])
    for idx, p in enumerate(protectii, start=6):
        comp_data.append([str(idx), p.get("nume", "Protecție"), f'{p.get("tip", "")} — {p.get("rol", "")}'[:60], "1 buc"])

    comp_table = Table(comp_data, colWidths=(1 * cm, 4.5 * cm, 8.5 * cm, 3 * cm))
    comp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COL_BLACK),
        ("TEXTCOLOR", (0, 0), (-1, 0), COL_ACCENT),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COL_LIGHT]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")),
    ]))
    story.append(comp_table)

    # ── Producție estimată ──
    productie = fv_results.get("productie", {})
    story.append(_section_header("Producție energetică estimată", styles))
    prod_rows = [
        ("Producție anuală", f'{int(productie.get("productie_anuala_kwh") or 0):,} kWh/an'.replace(",", ".")),
        ("Producție specifică", f'{productie.get("productie_specifica_kwh_kwp", "—")} kWh/kWp/an'),
        ("Zonă iradiație PVGIS", f'{fv_data.get("zona_geografica", "implicit")}'),
        ("Performance Ratio (PR)", f'{productie.get("pr", "—")}'),
        ("CO₂ evitat anual (estimare)", f'{int((productie.get("productie_anuala_kwh") or 0) * 0.43):,} kg'.replace(",", ".")),
    ]
    story.append(_kv_table(prod_rows))

    # ── Conformitate normativă ──
    story.append(_section_header("Conformitate normativă", styles))
    norms = [
        "✓ ANRE Ord. 34/2024 — categorii prosumator/producător",
        "✓ SR EN 50618 — cabluri solar DC",
        "✓ I7-2011 — instalații electrice de joasă tensiune",
        "✓ SR EN 62446 — punere în funcțiune & verificări periodice",
        "✓ HG 162/2024 — schema de sprijin pentru prosumatori",
    ]
    for n in norms:
        story.append(Paragraph(f'<font color="#16A34A">{n[0]}</font> <font color="#0A0A0A">{n[2:]}</font>', styles["body"]))
        story.append(Spacer(1, 0.05 * cm))

    # ── Termeni comerciali ──
    story.append(Spacer(1, 0.3 * cm))
    story.append(_section_header("Termeni comerciali", styles))
    terms = Table([
        ["Validitate ofertă", "30 zile calendaristice de la data emiterii"],
        ["Termen execuție", "Estimat 30-60 zile lucrătoare de la avansarea contractului"],
        ["Garanție echipamente", "Panouri: 25 ani liniară · Invertor: 10 ani (extensibil)"],
        ["Documentație inclusă", "Proiect tehnic, dosar racordare OSD/DEER, dosar prosumator ANRE"],
        ["Modalitate plată", "30% avans · 40% livrare materiale · 30% PIF"],
    ], colWidths=(5.5 * cm, 11 * cm))
    terms.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), COL_GRAY),
        ("TEXTCOLOR", (1, 0), (1, -1), COL_BLACK),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("BACKGROUND", (0, 0), (-1, -1), COL_LIGHT),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")),
    ]))
    story.append(terms)

    # ── Semnături ──
    story.append(Spacer(1, 0.8 * cm))
    sig = Table([
        [
            Paragraph('<font size="8" color="#6B7280">EMITENT OFERTĂ</font><br/><br/><br/><br/>_____________________<br/>'
                      f'<font size="9"><b>{company_name}</b></font>', styles["body"]),
            Paragraph('<font size="8" color="#6B7280">BENEFICIAR — ACCEPT</font><br/><br/><br/><br/>_____________________<br/>'
                      f'<font size="9"><b>{project_name}</b></font>', styles["body"]),
        ],
    ], colWidths=(8.5 * cm, 8.5 * cm))
    sig.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(sig)

    def on_page(c, d):
        return _tech_offer_header(c, d, project_name, company_name)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buf.getvalue()
