"""
Pestaña 1 — Datos & Valores — v8.0
Cambios:
- Logo y firma se cargan desde carpeta /assets/ del proyecto (persistentes)
- Opción de reemplazarlos via upload (guarda en /assets/)
- Intervalo, cantidad y umbral se actualizan automáticamente al cambiar estudio
- El usuario puede sobreescribir manualmente después del autoajuste
"""

import os
import io
import streamlit as st
from datetime import datetime, date


ESPECIALIDADES = [
    "Gastroenterología", "Clínica Médica / Medicina Interna",
    "Medicina General / Familiar", "Nutrición y Dietética",
    "Pediatría", "Cirugía General", "Endocrinología",
    "Infectología", "Hepatología", "Oncología",
    "Reumatología", "Geriatría", "Otra",
]
SEXOS = ["Masculino", "Femenino", "Otro"]
SINTOMAS = ["Flatulencia", "Dolor Abdominal",
            "Diarrea", "Estreñimiento", "Distensión", "Eructos"]

TIPO_SUSTRATO = {
    "SIBO":                       ["Lactulosa", "Glucosa"],
    "Intolerancia a la Lactosa":  ["Lactosa"],
    "Intolerancia a la Fructosa": ["Fructosa"],
    "Intolerancia al Sorbitol":   ["Sorbitol"],
    "Deficiencia de Sucrasa":     ["Sacarosa"],
}
TIPOS = list(TIPO_SUSTRATO.keys())

# Defaults clínicos por tipo: (n_mediciones, intervalo_min, umbral_h2)
TIPO_DEFAULTS = {
    "SIBO":                       (7, 30, 20),
    "Intolerancia a la Lactosa":  (6, 30, 20),
    "Intolerancia a la Fructosa": (6, 30, 20),
    "Intolerancia al Sorbitol":   (6, 30, 20),
    "Deficiencia de Sucrasa":     (6, 30, 20),
}
SIBO_GLUCOSA_DEFAULTS = (7, 20, 12)  # 7 muestras cada 20 min, umbral H2=12

TIPO_INFO = {
    "SIBO_Lactulosa": "7 muestras cada 30 min  (0 · 30 · 60 · 90 · 120 · 150 · 180 min)",
    "SIBO_Glucosa":   "7 muestras cada 20 min  |  Umbral H₂: 12 ppm  |  Umbral CH₄: 10 ppm",
    "Intolerancia a la Lactosa":  "25 g de lactosa  |  6 muestras cada 30 min",
    "Intolerancia a la Fructosa": "6 muestras cada 30 min",
    "Intolerancia al Sorbitol":   "6 muestras cada 30 min",
    "Deficiencia de Sucrasa":     "6 muestras cada 30 min",
}

TODAY = datetime.now().strftime("%d/%m/%Y")

_OS_TOP = ["OSDE", "PARTICULAR", "SWISS MEDICAL"]
_OS_REST = sorted([o for o in [
    "A.P.M / OSAPM", "ACCORD SALUD", "ACTIVA SALUD", "AMFFA", "ANDAR", "APRES",
    "APSOT / FFST", "ASMEPRIV", "ASSISTRAVEL", "ASOCIART ART", "AVALIAN", "BCO. PCIA. (AMEBPBA)",
    "BANCARIOS (OS.SSB)", "BERKLEY ART", "BRISTOL / STA. CECILIA", "C.A.S.A", "C.M.PUEYRREDON",
    "CAJA DE ABOGADOS", "CEMIC", "CIMA", "COBERMED", "COBERTEC / OS MOSAISTAS", "COLEGIO DE ESCRIBANOS",
    "COLONIA SUIZA ART", "COMEDICA (Plan especial OSSEG)", "COMEI", "CORPORACIÓN ASISTENCIAL",
    "DASMI - UNIV. DE LUJÁN", "DOM CENTRO DE REUMATOLOGÍA", "DOSUBA", "EMERGENCIAS", "EMPLEADOS DE FARMACIA",
    "ENSALUD (DELTA-KRONO-QUANTUM-OSOETSYL-OSPICAL-OSPIHMP-OSPIM MOLINEROS-OSIAD-FOSDIC-OSPINENDOCTER)",
    "EXPERTA ART", "FEDERADA SALUD", "FEDERACION PATRONAL ART", "FEMEDICA", "FRESENIUS", "GALENO",
    "HEALTH MEDICAL / OSSIMRA", "HOPE", "HOSPITAL ALEMÁN", "HOSPITAL BRITÁNICO", "HOSPITAL SIRIO LIBANES",
    "INST. SEGUROS DE JUJUY", "IOMA", "IOSFA", "JARDINEROS O.S.", "LA HOLANDO ART", "LA PEQUEÑA FAMILIA",
    "LA SEGUNDA ART", "LUIS PASTEUR", "LUZ Y FUERZA", "MEDICAL CORPORATIVE TRADE",
    "MEDICAL'S - MEDIN - Pro.Sa - PROMED - GENESEN - SEMESA", "MEDICENTER", "MEDICUS", "MEDIFE", "MEDITAR",
    "M&C SALUD / OS OSPACA", "MUTUAL DEL CLERO", "O.S.P.U.N.C.P.B.A.", "OBSBA", "OMINT", "OMIT ART", "OPDEA",
    "OSAM - PERGAMINO", "OSAP - ACEROS PARANÁ", "OSDEM", "OSDEPYM", "OSDIPP", "OSDOP",
    "OSETRA (O. S. EMPLEADFOS DEL TABACO )", "OSFATUN", "OSFE", "OSMECON EE", "OSMECON LdZ", "OSMITA", "OSOCNA",
    "OSPA – (O. S. PERSONAL AERONÁUTICO)", "OSPE - OSPE APROSS Y OSPE PMO", "OSPEDYC", "OSPESGYPE", "OSPETAX",
    "OSPESA", "OSPETELCO", "OSPIDA", "OSPIA", "OSPIL", "OSPIT - Textiles", "OSPIT - TABACALEROS",
    "OSPOCE / AMCI / INTEGRAL", "OSPREM", "OSSEG", "OSTECF", "PASTELEROS", "PERSONAL MUNICIPALIDAD DE LA MATANZA",
    "PODER JUDICIAL", "PREMEDIC", "PRESTADORES DE SALUD - SALUD DEL NUEVO ROSARIO", "PREVENCIÓN SALUD",
    "PREVENCION ART", "PRIVAMED", "PROME (PROTECCIÓN MÉDICA ESCOLAR)", "PROSAL SALUD", "PROVINCIA ART",
    "QUÍMICOS DE CAMPANA Y ZÁRATE", "RAS", "RED TOTAL - CONSULT RENT - MGN SALUD", "RED PRESTACIONAL - DOSUBA",
    "ROISA (IPROSS, OSMISS, OSYC, DOCTORED)", "SADAIC", "SAIS - GESTIÓN SALUD (OSDOP)", "SAMI MATANZA",
    "SANCOR SALUD / STAFF MÉDICO", "SANIDAD", "SEGUROS (OSSEG)", "SEMPRE LA PAMPA", "SGM ART",
    "SIGMA – OSLARA", "SMAI", "SALUD PLENA (AMTCIA-MOA-OSPICA-OSPM MARÍTIMOS-VESALIO SALUD)", "SWISS MEDICAL",
    "TIEMPO MÉDICO", "TV SALUD", "UAI SALUD", "UNION PERSONAL / ACCORD SALUD", "VIA MÉDICA (OS FUTBOLISTAS)",
    "O. S. DE PETROLEROS", "O. S. DEL SERVICIO PENITENCIARIO FEDERAL", "O. S. FERROVIARIA",
    "O. S. PATRONES DE CABOTAJE"
] if o not in _OS_TOP])
OBRAS_SOCIALES = _OS_TOP + _OS_REST


def _init_state():
    defaults = {
        "prof_nombre": "Julián Gastón", "prof_apellido": "Ahualli", "prof_esp": "Gastroenterología",
        "prof_mat": "MN: 128.019 - MP: 229.654", "prof_inst": "CIMEQ", "prof_email": "", "prof_tel": "",
        "pac_nombre": "", "pac_apellido": "", "pac_dni": "",
        "pac_fnac": "", "pac_edad": "", "pac_sexo": "Femenino",
        "pac_fecha": TODAY, "pac_obra_social": "",
        "tipo_analisis": "SIBO", "sustrato": "Lactulosa",
        "n_mediciones": 7, "intervalo": 30, "umbral": 20,
        "_prev_tipo": "", "_prev_sust": "",
        **{f"h2_{i}": "" for i in range(15)},
        **{f"ch4_{i}": "" for i in range(15)},
        **{f"sint_{s}": False for s in SINTOMAS},
        "sint_otros": "",
        "interpretacion": "",
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def _validate_date(s):
    if not s:
        return True
    try:
        datetime.strptime(s.strip(), "%d/%m/%Y")
        return True
    except ValueError:
        return False


def _calc_edad(fnac_str):
    try:
        fnac = datetime.strptime(fnac_str.strip(), "%d/%m/%Y").date()
        hoy = date.today()
        return str(hoy.year - fnac.year - ((hoy.month, hoy.day) < (fnac.month, fnac.day)))
    except ValueError:
        return ""


def _get_defaults(tipo, sustrato):
    if tipo == "SIBO" and sustrato == "Glucosa":
        return SIBO_GLUCOSA_DEFAULTS
    return TIPO_DEFAULTS.get(tipo, (7, 30, 20))


def _apply_defaults(tipo, sustrato):
    n, iv, umb = _get_defaults(tipo, sustrato)
    st.session_state["n_mediciones"] = n
    st.session_state["intervalo"] = iv
    st.session_state["umbral"] = umb


def _tipo_changed(tipo, sustrato):
    return (tipo != st.session_state.get("_prev_tipo", "") or
            sustrato != st.session_state.get("_prev_sust", ""))


# ── Validación pública (usada por app.py antes de generar PDF) ───────

_PAC_REQUIRED = [
    ("pac_nombre",      "Nombre del paciente"),
    ("pac_apellido",    "Apellido del paciente"),
    ("pac_dni",         "DNI del paciente"),
    ("pac_fnac",        "Fecha de nacimiento"),
    ("pac_sexo",        "Sexo"),
    ("pac_obra_social", "Obra Social / Prepaga"),
]


def validate_required_fields() -> list:
    """Retorna lista de errores. Lista vacía = todo OK."""
    ss = st.session_state
    errors = []
    for key, label in _PAC_REQUIRED:
        if not ss.get(key, "").strip():
            errors.append(label)
    n = ss.get("n_mediciones", 7)
    h2_ok = all(ss.get(f"h2_{i}",  "").strip() for i in range(n))
    ch4_ok = all(ss.get(f"ch4_{i}", "").strip() for i in range(n))
    if not h2_ok and not ch4_ok:
        errors.append("Valores PPM (al menos H2 o CH4 completo)")
    return errors


def _show_patient_validation():
    missing = [label for key, label in _PAC_REQUIRED
               if not st.session_state.get(key, "").strip()]
    if missing:
        st.warning(
            "⚠ **Datos del paciente incompletos:** "
            + ", ".join(missing)
            + ". Estos campos son obligatorios para generar el PDF."
        )


# ── Render ──────────────────────────────────────────────────────────

def render():

    _init_state()

    # v es un entero que se incrementa al limpiar desde app.py.
    # Al cambiar las keys de todos los widgets, Streamlit los recrea vacíos.
    v = st.session_state.get("_v", 0)

    col1, col2 = st.columns(2, gap="medium")

    # ═══════════════════════════════════════════
    # COL 1 — Profesional + Paciente + Archivos
    # ═══════════════════════════════════════════
    with col1:

        # ── Profesional ──────────────────────────────────────────────
        with st.expander("**Profesional médico**", expanded=True):
            c1, c2 = st.columns(2)
            st.session_state["prof_nombre"] = c1.text_input(
                "Nombre",   value=st.session_state["prof_nombre"],   key=f"_pn{v}", placeholder="Julián Gastón")
            st.session_state["prof_apellido"] = c2.text_input(
                "Apellido", value=st.session_state["prof_apellido"], key=f"_pa{v}", placeholder="Ahualli")

            esp_idx = ESPECIALIDADES.index(st.session_state["prof_esp"]) \
                if st.session_state["prof_esp"] in ESPECIALIDADES else 0
            st.session_state["prof_esp"] = st.selectbox(
                "Especialidad", ESPECIALIDADES, index=esp_idx, key=f"_esp{v}")

            c3, c4 = st.columns(2)
            st.session_state["prof_mat"] = c3.text_input(
                "Matrícula",   value=st.session_state["prof_mat"],  key=f"_pm{v}", placeholder="MN: 128.019 - MP: 229.654")
            st.session_state["prof_inst"] = c4.text_input(
                "Institución", value=st.session_state["prof_inst"], key=f"_pi{v}", placeholder="CIMEQ")

        # ── Paciente ─────────────────────────────────────────────────

        # ── Validación de campos obligatorios del paciente ───────────────
        _show_patient_validation()

        with st.expander("**Datos del paciente**", expanded=True):
            c1, c2 = st.columns(2)
            st.session_state["pac_nombre"] = c1.text_input(
                "Nombre",   value=st.session_state["pac_nombre"],   key=f"_pcn{v}")

            st.session_state["pac_apellido"] = c2.text_input(
                "Apellido", value=st.session_state["pac_apellido"], key=f"_pca{v}")

            c3, c4 = st.columns(2)
            st.session_state["pac_dni"] = c3.text_input(
                "DNI", value=st.session_state["pac_dni"], key=f"_pcdni{v}")

            # Fecha de nacimiento — ingreso manual DD/MM/AAAA
            fnac = c4.text_input(
                "Fecha de nacimiento (DD/MM/AAAA)",
                value=st.session_state["pac_fnac"],
                key=f"_pfnac{v}", placeholder="25/03/1985")
            if not _validate_date(fnac):
                c4.error("Formato inválido — DD/MM/AAAA")
            else:
                st.session_state["pac_fnac"] = fnac
                st.session_state["pac_edad"] = _calc_edad(fnac)

            c5, c6 = st.columns(2)
            sexo_idx = SEXOS.index(st.session_state["pac_sexo"]) \
                if st.session_state["pac_sexo"] in SEXOS else 0
            st.session_state["pac_sexo"] = c5.selectbox(
                "Sexo", SEXOS, index=sexo_idx, key=f"_psexo{v}")

            fecha_est = c6.text_input(
                "Fecha del estudio (DD/MM/AAAA)",
                value=st.session_state["pac_fecha"],
                key=f"_pfecha{v}", placeholder=TODAY)
            if not _validate_date(fecha_est):
                c6.error("Formato inválido — DD/MM/AAAA")
            else:
                st.session_state["pac_fecha"] = fecha_est

            # Obra Social — buscador predictivo
            st.markdown("**Obra Social / Prepaga**")

            os_search = st.text_input(
                "Buscar obra social",
                value=st.session_state.get("_os_search_txt", ""),
                key=f"_os_search_txt{v}",
                placeholder="Escribí para buscar o agregar...",
                label_visibility="collapsed",
            )

            term = os_search.strip()

            if term:
                filtered = [o for o in OBRAS_SOCIALES if term.lower()
                            in o.lower()]

                if filtered:
                    show = filtered[:8]
                    options = show[:]

                    # Si el término no existe, damos opción de agregar
                    if term and term not in OBRAS_SOCIALES and not any(o.lower() == term.lower() for o in OBRAS_SOCIALES):
                        options = [f'➕ Agregar "{term}"'] + show[:7]

                    cur = st.session_state.get("pac_obra_social", "")
                    cur_idx = options.index(cur) if cur in options else 0

                    choice = st.radio(
                        "Seleccioná",
                        options,
                        index=cur_idx,
                        key=f"_os_radio_{term}{v}",
                        label_visibility="collapsed",
                    )

                    if choice:
                        if choice.startswith("➕ Agregar"):
                            if term not in OBRAS_SOCIALES:
                                OBRAS_SOCIALES.append(term)
                                rest = sorted(
                                    [o for o in OBRAS_SOCIALES if o not in _OS_TOP])
                                OBRAS_SOCIALES[:] = _OS_TOP + rest
                            st.session_state["pac_obra_social"] = term
                        else:
                            st.session_state["pac_obra_social"] = choice

            else:
                st.caption("Sin coincidencias.")
                if term:
                    if st.button(f'➕ Agregar "{term}"', key=f"_os_add{v}"):
                        OBRAS_SOCIALES.append(term)
                        rest = sorted(
                            [o for o in OBRAS_SOCIALES if o not in _OS_TOP])
                        OBRAS_SOCIALES[:] = _OS_TOP + rest
                        st.session_state["pac_obra_social"] = term
                        st.rerun()

            # Mostrar selección actual
            cur_os = st.session_state.get("pac_obra_social", "")
            if cur_os:
                st.caption(f"✔ Seleccionada: **{cur_os}**")

    # ═══════════════════════════════════════════
    # COL 2 — Síntomas + Análisis + Mediciones + PPM
    # ═══════════════════════════════════════════
    with col2:

        # ── Síntomas ─────────────────────────────────────────────────
        with st.expander("**Síntomas anteriores a la prueba**", expanded=True):
            sc = st.columns(3)
            for i, s in enumerate(SINTOMAS):
                st.session_state[f"sint_{s}"] = sc[i % 3].checkbox(
                    s, value=st.session_state[f"sint_{s}"], key=f"_cb_{s}{v}")
            st.session_state["sint_otros"] = st.text_input(
                "Otros síntomas",
                value=st.session_state["sint_otros"],
                key=f"sint_otros{v}")

        # ── Tipo de análisis ─────────────────────────────────────────
        with st.expander("**Tipo de análisis y sustrato**", expanded=True):
            tipo_idx = TIPOS.index(st.session_state["tipo_analisis"]) \
                if st.session_state["tipo_analisis"] in TIPOS else 0
            tipo = st.selectbox("Tipo de análisis", TIPOS,
                                index=tipo_idx, key=f"_tipo{v}")
            st.session_state["tipo_analisis"] = tipo

            sust_opts = TIPO_SUSTRATO[tipo]
            cur_sust = st.session_state["sustrato"]
            sust_idx = sust_opts.index(
                cur_sust) if cur_sust in sust_opts else 0
            sustrato = st.selectbox("Sustrato", sust_opts,
                                    index=sust_idx, key=f"_sust{v}")
            st.session_state["sustrato"] = sustrato

            # Autoajuste cuando cambia tipo o sustrato
            if _tipo_changed(tipo, sustrato):
                _apply_defaults(tipo, sustrato)
                st.session_state["_prev_tipo"] = tipo
                st.session_state["_prev_sust"] = sustrato

            # Info contextual del protocolo
            info_key = f"{tipo}_{sustrato}" if tipo == "SIBO" else tipo
            info_txt = TIPO_INFO.get(info_key, "")
            if info_txt:
                st.info(info_txt)

        # ── Configuración de mediciones ───────────────────────────────
        with st.expander("**Configuración de mediciones**", expanded=True):
            n_def, iv_def, umb_def = _get_defaults(tipo, sustrato)

            # Cantidad de mediciones
            n = st.slider(
                "Cantidad de mediciones",
                min_value=3, max_value=15,
                value=st.session_state["n_mediciones"],
                step=1, key=f"_n{v}",
                help=f"Valor por defecto para este estudio: {n_def}")
            st.session_state["n_mediciones"] = n

            # Intervalo
            iv_opts = [10, 20, 30]
            iv_cur = st.session_state["intervalo"]
            iv_idx = iv_opts.index(iv_cur) if iv_cur in iv_opts else 2
            iv = st.radio(
                "Minutos entre tomas",
                iv_opts, index=iv_idx, horizontal=True, key=f"_iv{v}",
                format_func=lambda x: f"{x} min",
                help=f"Valor por defecto para este estudio: {iv_def} min")
            st.session_state["intervalo"] = iv

            # Umbral H₂
            umb = st.slider(
                "Umbral positivo H₂ (ppm)",
                min_value=5, max_value=50,
                value=st.session_state["umbral"],
                step=1, key=f"_umb{v}",
                help=f"Valor por defecto para este estudio: {umb_def} ppm")
            st.session_state["umbral"] = umb

            # Indicador de si los valores fueron modificados manualmente
            cur = (n, iv, umb)
            dft = (n_def, iv_def, umb_def)
            if cur != dft:
                st.caption(
                    f"⚠ Valores modificados manualmente. "
                    f"Defecto para este estudio: {n_def} muestras · "
                    f"{iv_def} min · umbral {umb_def} ppm")

        # ── Valores PPM ──────────────────────────────────────────────
        with st.expander("**Valores PPM — H2 y CH4**", expanded=True):
            tiempos = [i * iv for i in range(n)]
            tls = [f"{t} min" for t in tiempos]

            hc = st.columns([2, 2, 2])
            hc[0].markdown("**Tiempo**")
            hc[1].markdown("**H2 (ppm)**")
            hc[2].markdown("**CH4 (ppm)**")
            st.divider()

            for i in range(n):
                rc = st.columns([2, 2, 2])
                rc[0].markdown(
                    f"<div style='padding-top:6px;color:gray;font-size:13px'>"
                    f"{tls[i]}</div>",
                    unsafe_allow_html=True)
                st.session_state[f"h2_{i}"] = rc[1].text_input(
                    f"h2_{i}", value=st.session_state[f"h2_{i}"],
                    label_visibility="collapsed",
                    key=f"_h2_{i}_{v}", placeholder="ppm")
                st.session_state[f"ch4_{i}"] = rc[2].text_input(
                    f"ch4_{i}", value=st.session_state[f"ch4_{i}"],
                    label_visibility="collapsed",
                    key=f"_c4_{i}_{v}", placeholder="ppm")
