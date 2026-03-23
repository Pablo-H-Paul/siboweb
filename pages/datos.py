"""
Pestaña 1 — Datos & Valores — v7.0
Cambios:
- Logo de institución (upload)
- Firma digital (upload)
- Sin DNI, email, nro afiliado del paciente
- Dolor Abdominal en lugar de Retortijones; sin Non GI
- Sustratos y defaults por tipo de estudio
"""

import streamlit as st
from datetime import datetime, date

ESPECIALIDADES = [
    "Gastroenterología","Clínica Médica / Medicina Interna",
    "Medicina General / Familiar","Nutrición y Dietética",
    "Pediatría","Cirugía General","Endocrinología",
    "Infectología","Hepatología","Oncología",
    "Reumatología","Geriatría","Otra",
]
SEXOS    = ["Masculino","Femenino","Otro"]
SINTOMAS = ["Flatulencia","Dolor Abdominal","Diarrea","Estreñimiento","Distensión"]

TIPO_SUSTRATO = {
    "SIBO":                       ["Lactulosa","Glucosa"],
    "Intolerancia a la Lactosa":  ["Lactosa"],
    "Intolerancia a la Fructosa": ["Fructosa"],
    "Intolerancia al Sorbitol":   ["Sorbitol"],
    "Deficiencia de Sucrasa":     ["Sacarosa"],
}
TIPOS = list(TIPO_SUSTRATO.keys())

# Defaults por tipo: (n_mediciones, intervalo_min)
TIPO_DEFAULTS = {
    "SIBO":                       (7, 30),   # 7 × 30 min = 0..180
    "Intolerancia a la Lactosa":  (6, 30),   # 6 × 30 min = 0..150
    "Intolerancia a la Fructosa": (6, 30),
    "Intolerancia al Sorbitol":   (6, 30),
    "Deficiencia de Sucrasa":     (6, 30),
}
# SIBO con glucosa usa 7 muestras cada 20 min
SIBO_GLUCOSA_DEFAULTS = (7, 20)

TODAY = datetime.now().strftime("%d/%m/%Y")


def _init_state():
    defaults = {
        "prof_nombre":"","prof_apellido":"","prof_esp":"Gastroenterología",
        "prof_mat":"","prof_inst":"","prof_email":"","prof_tel":"",
        "pac_nombre":"","pac_apellido":"",
        "pac_fnac":"","pac_edad":"","pac_sexo":"Femenino",
        "pac_fecha":TODAY,"pac_obra_social":"",
        "tipo_analisis":"SIBO","sustrato":"Lactulosa",
        "n_mediciones":7,"intervalo":30,"umbral":20,
        **{f"h2_{i}":"" for i in range(15)},
        **{f"ch4_{i}":"" for i in range(15)},
        **{f"sint_{s}":False for s in SINTOMAS},
        "sint_otros":"",
        "interpretacion":"",
        "logo_bytes":None,"firma_bytes":None,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def _validate_date(s):
    if not s: return True
    try:
        datetime.strptime(s.strip(), "%d/%m/%Y"); return True
    except ValueError: return False


def _calc_edad(fnac_str):
    try:
        fnac = datetime.strptime(fnac_str.strip(), "%d/%m/%Y").date()
        hoy  = date.today()
        return str(hoy.year - fnac.year - ((hoy.month,hoy.day)<(fnac.month,fnac.day)))
    except ValueError: return ""


def _apply_tipo_defaults(tipo, sustrato):
    """Actualiza n_mediciones e intervalo según tipo y sustrato."""
    if tipo == "SIBO" and sustrato == "Glucosa":
        n, iv = SIBO_GLUCOSA_DEFAULTS
    else:
        n, iv = TIPO_DEFAULTS.get(tipo, (7, 30))
    st.session_state["n_mediciones"] = n
    st.session_state["intervalo"]    = iv


def render():
    _init_state()

    col1, col2 = st.columns(2, gap="medium")

    # ═══════════════════════════════════════════
    # COL 1 — Profesional + Paciente + Archivos
    # ═══════════════════════════════════════════
    with col1:

        # ── Profesional ──────────────────────
        with st.expander("**Profesional médico**", expanded=True):
            c1, c2 = st.columns(2)
            st.session_state["prof_nombre"]   = c1.text_input("Nombre",   value=st.session_state["prof_nombre"],   key="_pn")
            st.session_state["prof_apellido"] = c2.text_input("Apellido", value=st.session_state["prof_apellido"], key="_pa")

            esp_idx = ESPECIALIDADES.index(st.session_state["prof_esp"]) if st.session_state["prof_esp"] in ESPECIALIDADES else 0
            st.session_state["prof_esp"] = st.selectbox("Especialidad", ESPECIALIDADES, index=esp_idx, key="_esp")

            c3, c4 = st.columns(2)
            st.session_state["prof_mat"]  = c3.text_input("Matrícula",   value=st.session_state["prof_mat"],  key="_pm")
            st.session_state["prof_inst"] = c4.text_input("Institución", value=st.session_state["prof_inst"], key="_pi")

        # ── Paciente (sin DNI, email, nro afiliado) ──
        with st.expander("**Datos del paciente**", expanded=True):
            c1, c2 = st.columns(2)
            st.session_state["pac_nombre"]   = c1.text_input("Nombre",   value=st.session_state["pac_nombre"],   key="_pcn")
            st.session_state["pac_apellido"] = c2.text_input("Apellido", value=st.session_state["pac_apellido"], key="_pca")

            c3, c4 = st.columns(2)
            fnac = c3.text_input("Fecha de nacimiento (DD/MM/AAAA)",
                                  value=st.session_state["pac_fnac"], key="_pfnac", placeholder="25/03/1985")
            if not _validate_date(fnac):
                c3.error("Formato inválido — DD/MM/AAAA")
            else:
                st.session_state["pac_fnac"] = fnac
                st.session_state["pac_edad"] = _calc_edad(fnac)

            sexo_idx = SEXOS.index(st.session_state["pac_sexo"]) if st.session_state["pac_sexo"] in SEXOS else 0
            st.session_state["pac_sexo"] = c4.selectbox("Sexo", SEXOS, index=sexo_idx, key="_psexo")

            c5, c6 = st.columns(2)
            c5.text_input("Edad (calculada)", value=st.session_state["pac_edad"], key="_pedad", disabled=True)

            fecha_est = c6.text_input("Fecha del estudio (DD/MM/AAAA)",
                                       value=st.session_state["pac_fecha"], key="_pfecha", placeholder=TODAY)
            if not _validate_date(fecha_est):
                c6.error("Formato inválido — DD/MM/AAAA")
            else:
                st.session_state["pac_fecha"] = fecha_est

            st.session_state["pac_obra_social"] = st.text_input(
                "Obra Social / Prepaga", value=st.session_state["pac_obra_social"], key="_pos")

        # ── Logo e institución ────────────────
        with st.expander("**Logo de la institución**", expanded=False):
            st.caption("Archivo JPG, PNG o similar. Aparecerá en el encabezado del PDF.")
            logo_file = st.file_uploader("Subir logo", type=["jpg","jpeg","png","gif","bmp","webp"],
                                          key="_logo_up", label_visibility="collapsed")
            if logo_file:
                st.session_state["logo_bytes"] = logo_file.read()
                st.image(st.session_state["logo_bytes"], width=180)
            elif st.session_state.get("logo_bytes"):
                st.image(st.session_state["logo_bytes"], width=180)
                if st.button("Quitar logo", key="_rm_logo"):
                    st.session_state["logo_bytes"] = None
                    st.rerun()

        # ── Firma digital ─────────────────────
        with st.expander("**Firma digital del profesional**", expanded=False):
            st.caption("Archivo JPG o PNG con la firma manuscrita escaneada.")
            firma_file = st.file_uploader("Subir firma", type=["jpg","jpeg","png"],
                                           key="_firma_up", label_visibility="collapsed")
            if firma_file:
                st.session_state["firma_bytes"] = firma_file.read()
                st.image(st.session_state["firma_bytes"], width=200)
            elif st.session_state.get("firma_bytes"):
                st.image(st.session_state["firma_bytes"], width=200)
                if st.button("Quitar firma", key="_rm_firma"):
                    st.session_state["firma_bytes"] = None
                    st.rerun()

    # ═══════════════════════════════════════════
    # COL 2 — Síntomas + Análisis + PPM
    # ═══════════════════════════════════════════
    with col2:

        # ── Síntomas ─────────────────────────
        with st.expander("**Síntomas anteriores a la prueba**", expanded=True):
            sc = st.columns(3)
            for i, s in enumerate(SINTOMAS):
                st.session_state[f"sint_{s}"] = sc[i % 3].checkbox(
                    s, value=st.session_state[f"sint_{s}"], key=f"_cb_{s}")
            st.session_state["sint_otros"] = st.text_input(
                "Otros síntomas", value=st.session_state["sint_otros"], key="_siotros")

        # ── Tipo de análisis ─────────────────
        with st.expander("**Tipo de análisis y sustrato**", expanded=True):
            tipo_idx = TIPOS.index(st.session_state["tipo_analisis"]) \
                       if st.session_state["tipo_analisis"] in TIPOS else 0
            tipo_prev = st.session_state["tipo_analisis"]

            tipo = st.selectbox("Tipo de análisis", TIPOS, index=tipo_idx, key="_tipo")
            st.session_state["tipo_analisis"] = tipo

            sust_opts = TIPO_SUSTRATO[tipo]
            sust_idx  = sust_opts.index(st.session_state["sustrato"]) \
                        if st.session_state["sustrato"] in sust_opts else 0
            sustrato = st.selectbox("Sustrato", sust_opts, index=sust_idx, key="_sust")
            st.session_state["sustrato"] = sustrato

            # Actualizar defaults si cambió tipo o sustrato
            if tipo != tipo_prev or sustrato != st.session_state.get("_prev_sust"):
                _apply_tipo_defaults(tipo, sustrato)
            st.session_state["_prev_sust"] = sustrato

            # Info contextual
            if tipo == "SIBO" and sustrato == "Lactulosa":
                st.info("7 muestras cada 30 min (0, 30, 60, 90, 120, 150, 180 min)")
            elif tipo == "SIBO" and sustrato == "Glucosa":
                st.info("7 muestras cada 20 min")
            elif tipo in ["Intolerancia a la Lactosa","Intolerancia a la Fructosa",
                           "Intolerancia al Sorbitol","Deficiencia de Sucrasa"]:
                st.info("6 muestras cada 30 min")

        # ── Configuración de mediciones ──────
        with st.expander("**Configuración de mediciones**", expanded=True):
            n = st.slider("Cantidad de mediciones", min_value=3, max_value=15,
                          value=st.session_state["n_mediciones"], step=1, key="_n")
            st.session_state["n_mediciones"] = n

            iv_opts = [10, 20, 30]
            iv_cur  = st.session_state["intervalo"]
            iv_idx  = iv_opts.index(iv_cur) if iv_cur in iv_opts else 2
            iv = st.radio("Minutos entre tomas", iv_opts, index=iv_idx,
                          horizontal=True, key="_iv", format_func=lambda x: f"{x} min")
            st.session_state["intervalo"] = iv

            umb = st.slider("Umbral positivo H₂ (ppm)", min_value=5, max_value=50,
                            value=st.session_state["umbral"], step=1, key="_umb")
            st.session_state["umbral"] = umb

        # ── Valores PPM ──────────────────────
        with st.expander("**Valores PPM — H₂ y CH₄**", expanded=True):
            tiempos = [i * iv for i in range(n)]
            tls     = [f"{t} min" for t in tiempos]

            hc = st.columns([2,2,2])
            hc[0].markdown("**Tiempo**")
            hc[1].markdown("**H₂ (ppm)**")
            hc[2].markdown("**CH₄ (ppm)**")
            st.divider()

            for i in range(n):
                rc = st.columns([2,2,2])
                rc[0].markdown(
                    f"<div style='padding-top:6px;color:gray;font-size:13px'>{tls[i]}</div>",
                    unsafe_allow_html=True)
                st.session_state[f"h2_{i}"]  = rc[1].text_input(
                    f"h2_{i}", value=st.session_state[f"h2_{i}"],
                    label_visibility="collapsed", key=f"_h2_{i}", placeholder="ppm")
                st.session_state[f"ch4_{i}"] = rc[2].text_input(
                    f"ch4_{i}", value=st.session_state[f"ch4_{i}"],
                    label_visibility="collapsed", key=f"_c4_{i}", placeholder="ppm")

        # ── Interpretación ───────────────────
        with st.expander("**Interpretación del profesional (opcional)**", expanded=False):
            st.session_state["interpretacion"] = st.text_area(
                "Observaciones", value=st.session_state["interpretacion"],
                height=80, key="_interp", label_visibility="collapsed")
