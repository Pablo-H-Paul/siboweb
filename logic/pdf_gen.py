"""
Generación de PDF — v7.0
- Logo de institución (JPG/PNG)
- Firma digital (JPG/PNG) con espacio generoso antes de la línea de firma
- Nombre, apellido y matrícula debajo de la firma
- Sin DNI, email ni nro. afiliado del paciente
- Retorna bytes (no escribe a disco)
"""

import io, os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, Image as RLImage, KeepTogether, Paragraph,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)

from logic.auc import calcular_auc
from logic.interpretacion import interpretar

EFECTOS = ["Flatulencia", "Dolor Abdominal", "Diarrea", "Estreñimiento", "Distensión"]
TODAY   = datetime.now().strftime("%d/%m/%Y")


def generate_pdf(data: dict, logo_path: str | None = None, firma_path: str | None = None) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=1.5*cm, bottomMargin=2*cm,
    )
    W, _  = A4
    cw    = W - 4*cm
    story = []

    DARK  = colors.HexColor("#1E3A5F")
    BLUE  = colors.HexColor("#2563EB")
    GREEN = colors.HexColor("#10B981")
    GREY  = colors.HexColor("#64748B")
    LGREY = colors.HexColor("#F5F7FA")
    RED   = colors.HexColor("#DC2626")
    base  = getSampleStyleSheet()

    def ps(n, **k):
        return ParagraphStyle(n, parent=base["Normal"], **k)

    sT  = ps("T",  fontSize=14, textColor=DARK,  fontName="Helvetica-Bold",  spaceAfter=3,  alignment=TA_CENTER)
    sSu = ps("Su", fontSize=9,  textColor=GREY,  fontName="Helvetica",       spaceAfter=2,  alignment=TA_CENTER)
    sSH = ps("SH", fontSize=9,  textColor=BLUE,  fontName="Helvetica-Bold",  spaceBefore=7, spaceAfter=3)
    sLb = ps("Lb", fontSize=8,  textColor=GREY,  fontName="Helvetica")
    sVl = ps("Vl", fontSize=9,  textColor=DARK,  fontName="Helvetica-Bold")
    sBo = ps("Bo", fontSize=9,  textColor=DARK,  fontName="Helvetica",       leading=14, spaceAfter=4, alignment=TA_JUSTIFY)
    sIP = ps("IP", fontSize=10, textColor=RED,   fontName="Helvetica-Bold",  spaceAfter=5,  alignment=TA_CENTER)
    sIN = ps("IN", fontSize=10, textColor=GREEN, fontName="Helvetica-Bold",  spaceAfter=5,  alignment=TA_CENTER)
    sAU = ps("AU", fontSize=9,  textColor=DARK,  fontName="Helvetica",       leading=14)
    sCo = ps("Co", fontSize=8,  textColor=RED,   fontName="Helvetica-BoldOblique", spaceAfter=4, alignment=TA_CENTER)
    sFt = ps("Ft", fontSize=7,  textColor=GREY,  fontName="Helvetica",       alignment=TA_CENTER)
    sSig= ps("Sg", fontSize=9,  textColor=DARK,  fontName="Helvetica-Bold",  alignment=TA_CENTER)
    sSub= ps("Sb", fontSize=8,  textColor=GREY,  fontName="Helvetica",       alignment=TA_CENTER)

    fv = data.get("fields", {})

    def full(prefix):
        n = fv.get(f"{prefix}_nombre",   "").strip()
        a = fv.get(f"{prefix}_apellido", "").strip()
        return f"{n} {a}".strip() or "—"

    # ── Logo ─────────────────────────────────────────────────────────
    logo = None
    if logo_path and os.path.exists(logo_path):
        try:
            logo = RLImage(logo_path, width=4.5*cm, height=1.6*cm, kind="proportional")
        except Exception:
            pass

    # ── Encabezado ───────────────────────────────────────────────────
    hdr = Table([[
        logo if logo else Paragraph("CIMEQ", sT),
        [
            Paragraph("INFORME DE PRUEBA DE HIDRÓGENO ESPIRADO", sT),
            Paragraph(f"Estudio: {data.get('tipo_analisis','SIBO')} — Sustrato: {data.get('sustrato','')}", sSu),
            Paragraph(f"Fecha: {fv.get('pac_fecha', TODAY)}", sSu),
        ],
    ]], colWidths=[5*cm, cw - 5*cm])
    hdr.setStyle(TableStyle([
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",         (1,0), (1,0),   "CENTER"),
        ("LINEBELOW",     (0,0), (-1,-1), 1.2, DARK),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story += [hdr, Spacer(1, 6)]

    # ── Info block ───────────────────────────────────────────────────
    def ib(pairs):
        t = Table(
            [[Paragraph(l, sLb), Paragraph(str(v) if v else "—", sVl)] for l, v in pairs],
            colWidths=[3.5*cm, None],
        )
        t.setStyle(TableStyle([
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
            ("ROWBACKGROUNDS",(0,0), (-1,-1), [LGREY, colors.white]),
            ("LEFTPADDING",   (0,0), (-1,-1), 4),
            ("RIGHTPADDING",  (0,0), (-1,-1), 4),
            ("TOPPADDING",    (0,0), (-1,-1), 2),
            ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ]))
        return t

    pb = [Paragraph("PROFESIONAL MÉDICO", sSH), ib([
        ("Nombre",       full("prof")),
        ("Especialidad", fv.get("prof_esp", "")),
        ("Matrícula",    fv.get("prof_mat", "")),
        ("Institución",  fv.get("prof_inst", "")),
    ])]
    # Paciente sin DNI, email ni nro. afiliado
    pcb = [Paragraph("DATOS DEL PACIENTE", sSH), ib([
        ("Nombre",      full("pac")),
        ("Fecha Nac.",  fv.get("pac_fnac", "")),
        ("Edad / Sexo", f"{fv.get('pac_edad','')} / {fv.get('pac_sexo','')}"),
        ("Obra social", fv.get("pac_obra_social", "")),
    ])]

    story.append(Table(
        [[pb, pcb]], colWidths=[cw/2, cw/2],
        style=[("VALIGN",(0,0),(-1,-1),"TOP"),
               ("LEFTPADDING",(0,0),(-1,-1),0),
               ("RIGHTPADDING",(0,0),(-1,-1),4)],
    ))
    story += [Spacer(1,4), HRFlowable(width="100%", thickness=0.5, color=BLUE), Spacer(1,6)]

    # ── Síntomas ─────────────────────────────────────────────────────
    sint_txt = ", ".join(data.get("sint_pre", [])) or "Ninguno"
    if data.get("sint_otros"):
        sint_txt += f"  |  Otros: {data['sint_otros']}"
    story += [Paragraph("SÍNTOMAS ANTERIORES A LA PRUEBA", sSH),
              Paragraph(sint_txt, sBo), Spacer(1,4)]

    # ── Tabla PPM ────────────────────────────────────────────────────
    h2_vals   = data.get("h2_vals",    [])
    ch4_vals  = data.get("ch4_vals",   [])
    tiempos   = data.get("tiempos",    [])
    time_lbls = data.get("time_labels",[])
    umbral    = data.get("umbral",      20)

    auc_h2  = calcular_auc(h2_vals,  tiempos)
    auc_ch4 = calcular_auc(ch4_vals, tiempos)
    h2s  = f"{auc_h2:.0f}"  if auc_h2  is not None else "N/D"
    ch4s = f"{auc_ch4:.0f}" if auc_ch4 is not None else "N/D"

    def phc(txt, col=colors.white, bold=True):
        return Paragraph(txt, ps("_p", fontSize=8, textColor=col,
                                  fontName="Helvetica-Bold" if bold else "Helvetica",
                                  alignment=TA_CENTER))

    pr = [[phc("Tiempo"), phc("H₂ (ppm)"), phc("CH₄ (ppm)")]]
    for i, tl in enumerate(time_lbls):
        pr.append([
            phc(tl, DARK, False),
            phc(str(h2_vals[i])  if i < len(h2_vals)  and h2_vals[i]  is not None else "—",
                colors.HexColor("#2563EB"), False),
            phc(str(ch4_vals[i]) if i < len(ch4_vals) and ch4_vals[i] is not None else "—",
                colors.HexColor("#10B981"), False),
        ])
    wc = cw / 3
    pt = Table(pr, colWidths=[wc, wc, wc])
    pt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  DARK),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [LGREY, colors.white]),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("GRID",          (0,0),(-1,-1), 0.3, colors.HexColor("#CBD5E1")),
        ("TOPPADDING",    (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
    ]))
    story.append(Paragraph("VALORES PPM — H₂ y CH₄", sSH))
    story.append(KeepTogether([
        pt, Spacer(1,4),
        Paragraph(
            f"<b>AUC H₂:</b> {h2s} ppm·min &nbsp;|&nbsp; "
            f"<b>AUC CH₄:</b> {ch4s} ppm·min &nbsp;|&nbsp; Umbral: {umbral} ppm",
            ps("_au", fontSize=9, textColor=DARK, alignment=TA_CENTER),
        ),
    ]))
    story.append(Spacer(1, 8))

    # ── Gráfico ──────────────────────────────────────────────────────
    chart_bytes = data.get("chart_bytes")
    if chart_bytes:
        story += [
            Paragraph("CURVA DE EVOLUCIÓN PPM / TIEMPO", sSH),
            RLImage(io.BytesIO(chart_bytes), width=cw, height=6*cm, kind="proportional"),
            Spacer(1, 8),
        ]

    # ── Interpretación ───────────────────────────────────────────────
    story += [HRFlowable(width="100%", thickness=0.5, color=BLUE),
              Spacer(1, 6),
              Paragraph("RESULTADO E INTERPRETACIÓN", sSH)]

    tit, cpo, pos = interpretar(
        h2_vals, ch4_vals,
        data.get("tipo_analisis", "SIBO"),
        data.get("sustrato", "Lactulosa"),
        tiempos, umbral,
    )
    story.append(Paragraph(tit, sIP if pos else sIN))
    for line in cpo.strip().split("\n"):
        line = line.strip()
        if line:
            story.append(Paragraph(line, sCo if "CONSULTE" in line.upper() else sAU))

    if data.get("interpretacion", "").strip():
        story += [Spacer(1,6), Paragraph("OBSERVACIONES DEL PROFESIONAL", sSH),
                  Paragraph(data["interpretacion"].strip(), sBo)]

    story += [Spacer(1,8), HRFlowable(width="100%", thickness=0.5, color=BLUE), Spacer(1,6)]

    # ── Efectos adversos ─────────────────────────────────────────────
    ef_raw   = data.get("ef_vars", {})
    ef_found = [
        (time_lbls[i], ", ".join(s for s in EFECTOS if ef_raw.get(i,{}).get(s, False)))
        for i in range(len(time_lbls))
        if any(ef_raw.get(i,{}).get(s, False) for s in EFECTOS)
    ]
    story.append(Paragraph("EFECTOS ADVERSOS DURANTE LA PRUEBA", sSH))
    if ef_found:
        def pth(tx):
            return Paragraph(tx, ps("_th", fontSize=8, textColor=colors.white,
                                     fontName="Helvetica-Bold"))
        et = Table(
            [[pth("Tiempo"), pth("Síntomas")]] +
            [[Paragraph(tl, sBo), Paragraph(sx, sBo)] for tl, sx in ef_found],
            colWidths=[3*cm, cw-3*cm],
        )
        et.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0),  DARK),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [LGREY, colors.white]),
            ("GRID",          (0,0),(-1,-1), 0.3, colors.HexColor("#CBD5E1")),
            ("TOPPADDING",    (0,0),(-1,-1), 2),
            ("BOTTOMPADDING", (0,0),(-1,-1), 2),
            ("LEFTPADDING",   (0,0),(-1,-1), 4),
        ]))
        story.append(et)
    else:
        story.append(Paragraph("Sin efectos adversos registrados.", sBo))

    if data.get("ef_otros","").strip():
        story.append(Paragraph(f"Otros: {data['ef_otros'].strip()}", sBo))

    # ── Medicación ───────────────────────────────────────────────────
    story += [Spacer(1,6), Paragraph("MEDICACIÓN", sSH),
              Paragraph(data.get("medicacion","").strip() or "Sin registro.", sBo)]

    # ── Firma digital + datos del profesional ────────────────────────
    # Espacio generoso antes de la firma
    story.append(Spacer(1, 36))

    prof_nombre_completo = full("prof")
    prof_mat = fv.get("prof_mat","")
    prof_esp = fv.get("prof_esp","")

    # Firma digital (imagen) si está disponible
    if firma_path and os.path.exists(firma_path):
        try:
            firma_img = RLImage(firma_path, width=5*cm, height=2*cm, kind="proportional")
            firma_tbl = Table(
                [[firma_img, ""]],
                colWidths=[cw * 0.4, cw * 0.6],
            )
            firma_tbl.setStyle(TableStyle([
                ("ALIGN",  (0,0),(0,0), "CENTER"),
                ("VALIGN", (0,0),(-1,-1), "BOTTOM"),
            ]))
            story.append(firma_tbl)
            story.append(Spacer(1, 4))
        except Exception:
            pass

    # Línea de firma + datos
    sig_data = [
        ["", ""],
        [
            Paragraph(f"<b>{prof_nombre_completo}</b>", sSig),
            "",
        ],
        [
            Paragraph(f"{prof_esp}  —  Mat. {prof_mat}", sSub),
            "",
        ],
    ]
    sig = Table(sig_data, colWidths=[cw * 0.5, cw * 0.5])
    sig.setStyle(TableStyle([
        ("LINEABOVE",    (0,0),(0,0), 0.8, DARK),
        ("TOPPADDING",   (0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
    ]))
    story.append(sig)

    # ── Pie de página ────────────────────────────────────────────────
    story += [
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=0.3, color=GREY),
        Paragraph(
            f"Informe generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')} "
            f"— SIBO Analyzer v7.0",
            sFt,
        ),
    ]

    doc.build(story)
    buf.seek(0)
    return buf.read()
