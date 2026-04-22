"""
Generación de PDF — v8.0
- Logo: cargado desde assets/logo.png automáticamente
- Firma: cargado desde assets/firma.png automáticamente
- Firma alineada al margen DERECHO con espacio generoso
- Sin DNI, email ni nro. afiliado del paciente
- Retorna bytes
"""

import io
import os
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, Image as RLImage, KeepTogether, Paragraph,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)

from logic.auc import calcular_auc

EFECTOS = ["Flatulencia", "Dolor Abdominal",
           "Diarrea", "Estreñimiento", "Distensión", "Eructos"]
TODAY = datetime.now().strftime("%d/%m/%Y")
ASSETS_DIR = Path(__file__).parent.parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"
FIRMA_PATH = ASSETS_DIR / "firma.png"


def _load_image(path: Path, width_cm: float, height_cm: float):
    """Carga una imagen desde disco si existe; retorna RLImage o None."""
    if path.exists():
        try:
            return RLImage(str(path), width=width_cm*cm, height=height_cm*cm,
                           kind="proportional")
        except Exception:
            return None
    return None


def generate_pdf(data: dict,
                 logo_path: str | None = None,
                 firma_path: str | None = None) -> bytes:
    """
    Genera el PDF y retorna bytes.
    logo_path / firma_path: si se pasan explícitamente (ej. desde un tempfile)
    se usan en su lugar; si son None se intenta cargar desde assets/.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=1.5*cm, bottomMargin=2*cm,
    )
    W, _ = A4
    cw = W - 4*cm
    story = []

    # ── Colores ─────────────────────────────────────────────────────
    DARK = colors.HexColor("#1E3A5F")
    BLUE = colors.HexColor("#2563EB")
    GREEN = colors.HexColor("#10B981")
    GREY = colors.HexColor("#64748B")
    LGREY = colors.HexColor("#F5F7FA")
    RED = colors.HexColor("#DC2626")
    base = getSampleStyleSheet()

    def ps(n, **k):
        return ParagraphStyle(n, parent=base["Normal"], **k)

    sT = ps("T",  fontSize=14, textColor=DARK,
            fontName="Helvetica-Bold",  spaceAfter=3,  alignment=TA_CENTER)
    sSu = ps("Su", fontSize=9,  textColor=GREY,  fontName="Helvetica",
             spaceAfter=2,  alignment=TA_CENTER)
    sSH = ps("SH", fontSize=9,  textColor=BLUE,
             fontName="Helvetica-Bold",  spaceBefore=7, spaceAfter=3)
    sLb = ps("Lb", fontSize=8,  textColor=GREY,  fontName="Helvetica")
    sVl = ps("Vl", fontSize=9,  textColor=DARK,  fontName="Helvetica-Bold")
    sBo = ps("Bo", fontSize=9,  textColor=DARK,  fontName="Helvetica",
             leading=14, spaceAfter=4, alignment=TA_JUSTIFY)
    sIP = ps("IP", fontSize=10, textColor=RED,
             fontName="Helvetica-Bold",  spaceAfter=5,  alignment=TA_CENTER)
    sIN = ps("IN", fontSize=10, textColor=GREEN,
             fontName="Helvetica-Bold",  spaceAfter=5,  alignment=TA_CENTER)
    sAU = ps("AU", fontSize=9,  textColor=DARK,
             fontName="Helvetica",       leading=14)
    sCo = ps("Co", fontSize=8,  textColor=RED,
             fontName="Helvetica-BoldOblique", spaceAfter=4, alignment=TA_CENTER)
    sFt = ps("Ft", fontSize=7,  textColor=GREY,
             fontName="Helvetica",       alignment=TA_CENTER)
    sSig = ps("Sg", fontSize=9,  textColor=DARK,
              fontName="Helvetica-Bold",  alignment=TA_CENTER)
    sSub = ps("Sb", fontSize=8,  textColor=GREY,
              fontName="Helvetica",       alignment=TA_CENTER)

    fv = data.get("fields", {})

    def full(prefix):
        n = fv.get(f"{prefix}_nombre",   "").strip()
        a = fv.get(f"{prefix}_apellido", "").strip()
        dni = fv.get(f"{prefix}_dni", "").strip()
        return f"{n} {a}".strip() or "—"

    # ── Logo centrado + encabezado ───────────────────────────────────
    # Logo solo, centrado, más grande
    _logo_p = Path(logo_path) if logo_path else LOGO_PATH
    if _logo_p.exists():
        try:
            logo_centered = RLImage(str(_logo_p), width=8*cm, height=3*cm,
                                    kind="proportional")
            logo_tbl = Table([[logo_centered]], colWidths=[cw])
            logo_tbl.setStyle(TableStyle([
                ("ALIGN",        (0, 0), (0, 0), "CENTER"),
                ("VALIGN",       (0, 0), (0, 0), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (0, 0), 8),
            ]))
            story.append(logo_tbl)
        except Exception:
            pass

    # Título, subtítulo (tipo + sustrato) y fecha
    story.append(Paragraph("INFORME DE PRUEBA DE AIRE ESPIRADO", sT))
    story.append(Paragraph(
        f"{data.get('tipo_analisis', 'SIBO')} — Sustrato: {data.get('sustrato', '')}",
        sSu))
    story.append(Paragraph(f"Fecha: {fv.get('pac_fecha', TODAY)}", sSu))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.2, color=DARK))
    story.append(Spacer(1, 6))

    # ── Info block ───────────────────────────────────────────────────
    def ib(pairs):
        t = Table(
            [[Paragraph(l, sLb), Paragraph(str(v) if v else "—", sVl)]
             for l, v in pairs],
            colWidths=[3.5*cm, None],
        )
        t.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LGREY, colors.white]),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
            ("TOPPADDING",    (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        return t

    # ── Dos columnas: profesional | paciente (sin DNI/email/afiliado) ─
    pb = [Paragraph("PROFESIONAL MÉDICO", sSH), ib([
        ("Nombre",       full("prof")),
        ("Especialidad", fv.get("prof_esp", "")),
        ("Matrícula",    fv.get("prof_mat", "")),
        ("Institución",  fv.get("prof_inst", "")),
    ])]
    pcb = [Paragraph("DATOS DEL PACIENTE", sSH), ib([
        ("Nombre",      full("pac")),
        ("DNI",      fv.get("pac_dni", "")),
        ("Fecha Nac.",  fv.get("pac_fnac", "")),
        ("Edad / Sexo",
         f"{fv.get('pac_edad', '')} / {fv.get('pac_sexo', '')}"),
        ("Obra social", fv.get("pac_obra_social", "")),
    ])]
    story.append(Table(
        [[pb, pcb]], colWidths=[cw/2, cw/2],
        style=[("VALIGN", (0, 0), (-1, -1), "TOP"),
               ("LEFTPADDING", (0, 0), (-1, -1), 0),
               ("RIGHTPADDING", (0, 0), (-1, -1), 4)],
    ))
    story += [Spacer(1, 4), HRFlowable(width="100%",
                                       thickness=0.5, color=BLUE), Spacer(1, 6)]

    # ── Síntomas ─────────────────────────────────────────────────────
    sint_txt = ", ".join(data.get("sint_pre", [])) or "Ninguno"
    if data.get("sint_otros"):
        sint_txt += f"  |  Otros: {data['sint_otros']}"
    story += [Paragraph("SÍNTOMAS ANTERIORES A LA PRUEBA", sSH),
              Paragraph(sint_txt, sBo), Spacer(1, 4)]

    # ── Tabla PPM ────────────────────────────────────────────────────
    h2_vals = data.get("h2_vals",    [])
    ch4_vals = data.get("ch4_vals",   [])
    tiempos = data.get("tiempos",    [])
    time_lbls = data.get("time_labels", [])
    umbral = data.get("umbral",      20)

    auc_h2 = calcular_auc(h2_vals,  tiempos)
    auc_ch4 = calcular_auc(ch4_vals, tiempos)
    h2s = f"{auc_h2:.0f}" if auc_h2 is not None else "N/D"
    ch4s = f"{auc_ch4:.0f}" if auc_ch4 is not None else "N/D"

    def phc(txt, col=colors.white, bold=True):
        return Paragraph(txt, ps("_p", fontSize=8, textColor=col,
                                 fontName="Helvetica-Bold" if bold else "Helvetica",
                                 alignment=TA_CENTER))

    pr = [[phc("Tiempo"), phc("H2 (ppm)"), phc("CH4 (ppm)")]]
    for i, tl in enumerate(time_lbls):
        pr.append([
            phc(tl, DARK, False),
            phc(str(h2_vals[i]) if i < len(h2_vals) and h2_vals[i] is not None else "—",
                colors.HexColor("#2563EB"), False),
            phc(str(ch4_vals[i]) if i < len(ch4_vals) and ch4_vals[i] is not None else "—",
                colors.HexColor("#10B981"), False),
        ])
    wc = cw / 3
    pt = Table(pr, colWidths=[wc, wc, wc])
    pt.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  DARK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LGREY, colors.white]),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(Paragraph("VALORES PPM — H2 y CH4", sSH))
    story.append(KeepTogether([
        pt, Spacer(1, 4),
        Paragraph(
            f"<b>AUC H2:</b> {h2s} ppm·min &nbsp; ",
            # f"<b>AUC CH4:</b> {ch4s} ppm·min &nbsp;|&nbsp; Umbral: {umbral} ppm",
            ps("_au", fontSize=9, textColor=DARK, alignment=TA_CENTER),
        ),
    ]))
    story.append(Spacer(1, 8))

    # ── Gráfico ──────────────────────────────────────────────────────
    chart_bytes = data.get("chart_bytes")
    if chart_bytes:
        story += [
            Paragraph("CURVA DE EVOLUCIÓN PPM / TIEMPO", sSH),
            RLImage(io.BytesIO(chart_bytes), width=cw,
                    height=6*cm, kind="proportional"),
            Spacer(1, 8),
        ]

    # ── Diagnóstico del profesional ──────────────────────────────────
    story += [HRFlowable(width="100%", thickness=0.5, color=BLUE),
              Spacer(1, 6), Paragraph("DIAGNÓSTICO", sSH)]
    diagnostico = data.get("diagnostico", "").strip()
    story.append(
        Paragraph(diagnostico if diagnostico else "Sin diagnóstico registrado.", sBo))
    story += [Spacer(1, 8), HRFlowable(width="100%",
                                       thickness=0.5, color=BLUE), Spacer(1, 6)]

    # ── Efectos adversos ─────────────────────────────────────────────
    ef_raw = data.get("ef_vars", {})

    ef_found = [
        (time_lbls[i], ", ".join(
            s for s in EFECTOS if ef_raw.get(i, {}).get(s, False)))
        for i in range(len(time_lbls))
        if any(ef_raw.get(i, {}).get(s, False) for s in EFECTOS)
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
            ("BACKGROUND",    (0, 0), (-1, 0),  DARK),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LGREY, colors.white]),
            ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
            ("TOPPADDING",    (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ]))
        story.append(et)
    else:
        story.append(Paragraph("Sin efectos adversos registrados.", sBo))

    if data.get("ef_otros", "").strip():
        story.append(Paragraph(f"Otros: {data['ef_otros'].strip()}", sBo))

    # ── Medicación ───────────────────────────────────────────────────
    # story += [Spacer(1,6), Paragraph("MEDICACIÓN", sSH),
    #          Paragraph(data.get("medicacion","").strip() or "Sin registro.", sBo)]

    # ═══════════════════════════════════════════════════════════════
    # FIRMA — alineada al margen DERECHO
    # Layout: celda vacía a la izquierda | bloque de firma a la derecha
    # ═══════════════════════════════════════════════════════════════
    story.append(Spacer(1, 40))  # espacio generoso antes de la firma

    prof_nombre_completo = full("prof")
    prof_mat = fv.get("prof_mat", "")
    prof_esp = fv.get("prof_esp", "")

    LEFT_W = cw * 0.45   # espacio vacío izquierdo
    RIGHT_W = cw * 0.55   # bloque de firma a la derecha

    # Imagen de firma (arg explícito o desde assets/)
    _firma_p = Path(firma_path) if firma_path else FIRMA_PATH
    firma_img = None
    if _firma_p.exists():
        try:
            firma_img = RLImage(str(_firma_p), width=5*cm, height=2*cm,
                                kind="proportional")
        except Exception:
            pass

    # Construir la tabla de firma derecha
    firma_rows = []
    if firma_img:
        firma_rows.append(["", firma_img])
    # Línea horizontal sobre el nombre (solo en col derecha)
    # Nombre + matrícula
    firma_rows.append([
        "",
        Paragraph(f"<b>{prof_nombre_completo}</b>", sSig),
    ])
    firma_rows.append([
        "",
        Paragraph(f"{prof_esp}  —  Mat. {prof_mat}", sSub),
    ])

    sig_tbl = Table(firma_rows, colWidths=[LEFT_W, RIGHT_W])

    # Línea encima de la celda del nombre (primera fila sin imagen, o segunda si hay imagen)
    nombre_row_idx = 1 if firma_img else 0
    sig_tbl.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "BOTTOM"),
        ("ALIGN",        (1, 0), (1, -1),  "CENTER"),
        ("LINEABOVE",    (1, nombre_row_idx), (1, nombre_row_idx), 0.8, DARK),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(sig_tbl)

    # ── Pie de página ────────────────────────────────────────────────
    story += [
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=0.3, color=GREY),
        Paragraph(
            f"Informe generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')} "
            f"— SIBO Analyzer v8.0",
            sFt,
        ),
    ]

    doc.build(story)
    buf.seek(0)
    return buf.read()
