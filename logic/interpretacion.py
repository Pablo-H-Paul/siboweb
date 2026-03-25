"""
Lógica de interpretación clínica — v7.0
Reglas exactas por tipo de estudio.
"""

from logic.auc import calcular_auc

CONSULTE = (
    "SI SU ESTUDIO FUE POSITIVO, CONSULTE A SU MÉDICO ANTES DE REALIZAR "
    "UN NUEVO ESTUDIO DE AIRE ESPIRADO."
)


def interpretar(
    h2_vals: list,
    ch4_vals: list,
    tipo: str,
    sustrato: str,
    tiempos: list,
    umbral: int = 20,
) -> tuple:
    def safe(lst):
        return [v for v in lst if v is not None]

    h2 = safe(h2_vals)
    ch4 = safe(ch4_vals)

    auc_h2 = calcular_auc(h2_vals, tiempos)
    auc_ch4 = calcular_auc(ch4_vals, tiempos)

    basal_h2 = h2[0] if h2 else 0
    basal_ch4 = ch4[0] if ch4 else 0

    h2_90 = [v for v, t in zip(h2_vals, tiempos) if v is not None and t <= 90]
    rise_h2 = (max(h2_90) - basal_h2) if h2_90 else 0
    rise_ch4 = (max(ch4) - basal_ch4) if ch4 else 0
    peak_ch4 = max(ch4) if ch4 else 0

    h2s = f"{auc_h2:.0f}" if auc_h2 is not None else "N/D"
    ch4s = f"{auc_ch4:.0f}" if auc_ch4 is not None else "N/D"

    t_low = tipo.lower()
    s_low = sustrato.lower()

    # FRUCTOSA / SORBITOL — 6 det. cada 30 min
    if "fructosa" in t_low or "sorbitol" in t_low:
        nombre = "FRUCTOSA" if "fructosa" in t_low else "SORBITOL"
        pos = (rise_h2 >= 20) or (peak_ch4 >= 12)
        tit = f"LA CURVA OBTENIDA ES {'POSITIVA' if pos else 'NEGATIVA'} PARA INTOLERANCIA A LA {nombre}"
        cpo = (
            "Se considera positivo el aumento de 20 ppm sobre la basal de "
            "hidrógeno o 12 ppm sobre la basal de metano.\n"
            f"AUC H2: {h2s} ppm·min. Valor de referencia 1000-3000 ppm·min.\n"
            # f"AUC CH4: {ch4s} ppm·min. Valor de referencia hasta 1000 ppm·min.\n"
        )
        if pos:
            cpo += f"\n{CONSULTE}"
        return tit, cpo, pos

    # LACTOSA — 25 g, 6 muestras cada 30 min
    if "lactosa" in t_low:
        pos = (rise_h2 >= 20) or (peak_ch4 >= 12)
        tit = f"LA CURVA OBTENIDA ES {'POSITIVA' if pos else 'NEGATIVA'} PARA INTOLERANCIA A LA LACTOSA"
        cpo = (
            "Se considera positivo el aumento de 20 ppm sobre la basal de "
            "hidrógeno o 12 ppm sobre la basal de metano.\n"
            f"AUC H2: {h2s} ppm·min. Valor de referencia 1000-3000 ppm·min.\n"
            # f"AUC CH4: {ch4s} ppm·min. Valor de referencia hasta 1000 ppm·min.\n"
        )
        if pos:
            cpo += f"\n{CONSULTE}"
        return tit, cpo, pos

    # SUCRASA / DEFICIENCIA
    if "sucrasa" in t_low or "sacarosa" in s_low:
        pos = (rise_h2 >= 20) or (peak_ch4 >= 12)
        tit = f"LA CURVA OBTENIDA ES {'POSITIVA' if pos else 'NEGATIVA'} PARA DEFICIENCIA DE SUCRASA"
        cpo = (
            "Se considera positivo el aumento de 20 ppm sobre la basal de "
            "hidrógeno o 12 ppm sobre la basal de metano.\n"
            f"AUC H2: {h2s} ppm·min.\nAUC CH4: {ch4s} ppm·min.\n"
        )
        if pos:
            cpo += f"\n{CONSULTE}"
        return tit, cpo, pos

    # SIBO GLUCOSA — 7 muestras cada 20 min, umbral H2=12, CH4=10
    if "glucosa" in s_low:
        pos = (max(h2_90) >= 12) or (peak_ch4 >= 10)
        cpo = (
            "Se considera positivo el aumento de 12 ppm de H2 y/o 10 ppm sobre "
            "la basal de metano.\n"
            f"AUC H2: {h2s} ppm·min. Valor de referencia 1000-3000 ppm·min.\n"
            # f"AUC CH4: {ch4s} ppm·min. Valor de referencia hasta 1000 ppm·min.\n"
        )
        if pos:
            cpo += f"\n{CONSULTE}"
        return "SIBO CON GLUCOSA", cpo, pos

    # SIBO LACTULOSA — 7 muestras cada 30 min
    h2_pos = rise_h2 >= umbral
    ch4_pos = peak_ch4 >= 10
    auc_h2_val = auc_h2 if auc_h2 is not None else 0

    cpo = ""
    cpo_auc = ""

    if h2_pos and ch4_pos:
        cpo = (
            f"LA CURVA OBTENIDA ES POSITIVA PARA SOBRECRECIMIENTO BACTERIANO PARA FLORA MIXTA METANOGÉNICA E HIDROGENOGÉNICA"
        )
    if not h2_pos and not ch4_pos:
        cpo = (
            f"LA CURVA OBTENIDA ES NEGATIVA PARA SOBRECRECIMIENTO BACTERIANO. H2"
        )

    if ch4_pos and not h2_pos:
        cpo = (
            f"LA CURVA OBTENIDA ES COMPATIBLE CON IMO (Sobrecrecimiento Metanogénico Intestinal)"
        )

    if h2_pos and not ch4_pos:
        cpo = (
            f"LA CURVA OBTENIDA ES POSITIVA PARA SOBRECRECIMIENTO BACTERIANO PARA FLORA HIDROGENOGÉNICA (SIBO)"
        )

    if auc_h2_val > 3000:
        cpo_auc = (
            f"\n AUC H2: {h2s} ppm·min. Valor de referencia 1000-3000 ppm·min.LA CURVA OBTENIDA ES COMPATIBLE CON PERFIL FERMENTATIVO AUMENTADO"
        )
    elif (auc_h2_val < 1000) and not (ch4_pos and not h2_pos):
        cpo_auc = (
            "LA CURVA OBTENIDA ES NEGATIVA PARA SOBRECRECIMIENTO BACTERIANO."
        )

    else:
        cpo_auc = (
            f"\n AUC H2: {h2s} ppm·min. Valor de referencia 1000-3000 ppm·min.\n")

    cpo = cpo + "\n" + cpo_auc

    return (
        f"Se considera positivo el aumento de {umbral} ppm sobre la basal de "
        "hidrógeno durante los primeros 90 min o un valor mayor o igual a "
        "10 ppm de metano durante el estudio.\n"

        f"\n{CONSULTE}\n",
        cpo,
        False)
