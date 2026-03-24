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
from pathlib import Path

# Rutas de archivos persistentes (relativas al directorio del proyecto)
ASSETS_DIR = Path(__file__).parent.parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"
FIRMA_PATH = ASSETS_DIR / "firma.png"

ESPECIALIDADES = [
    "Gastroenterología", "Clínica Médica / Medicina Interna",
    "Medicina General / Familiar", "Nutrición y Dietética",
    "Pediatría", "Cirugía General", "Endocrinología",
    "Infectología", "Hepatología", "Oncología",
    "Reumatología", "Geriatría", "Otra",
]
SEXOS = ["Masculino", "Femenino", "Otro"]
SINTOMAS = ["Flatulencia", "Dolor Abdominal",
            "Diarrea", "Estreñimiento", "Distensión"]

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


# ── Helpers ─────────────────────────────────────────────────────────

def _ensure_assets():
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def _load_asset(path: Path):
    """Carga un archivo de /assets/ y retorna sus bytes, o None si no existe."""
    if path.exists():
        return path.read_bytes()
    return None


def _save_asset(path: Path, data: bytes):
    _ensure_assets()
    path.write_bytes(data)


def _init_state():
    defaults = {
        "prof_nombre": "", "prof_apellido": "", "prof_esp": "Gastroenterología",
        "prof_mat": "", "prof_inst": "", "prof_email": "", "prof_tel": "",
        "pac_nombre": "", "pac_apellido": "",
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


# ── Render ──────────────────────────────────────────────────────────

def render():
    _init_state()
    _ensure_assets()

    col1, col2 = st.columns(2, gap="medium")

    # ═══════════════════════════════════════════
    # COL 1 — Profesional + Paciente + Archivos
    # ═══════════════════════════════════════════
    with col1:

        # ── Profesional ──────────────────────────────────────────────
        with st.expander("**Profesional médico**", expanded=True):
            c1, c2 = st.columns(2)
            st.session_state["prof_nombre"] = c1.text_input(
                "Nombre",   value=st.session_state["prof_nombre"],   key="_pn")
            st.session_state["prof_apellido"] = c2.text_input(
                "Apellido", value=st.session_state["prof_apellido"], key="_pa")

            esp_idx = ESPECIALIDADES.index(st.session_state["prof_esp"]) \
                if st.session_state["prof_esp"] in ESPECIALIDADES else 0
            st.session_state["prof_esp"] = st.selectbox(
                "Especialidad", ESPECIALIDADES, index=esp_idx, key="_esp")

            c3, c4 = st.columns(2)
            st.session_state["prof_mat"] = c3.text_input(
                "Matrícula",   value=st.session_state["prof_mat"],  key="_pm")
            st.session_state["prof_inst"] = c4.text_input(
                "Institución", value=st.session_state["prof_inst"], key="_pi")

        # ── Paciente ─────────────────────────────────────────────────
        with st.expander("**Datos del paciente**", expanded=True):
            c1, c2 = st.columns(2)
            st.session_state["pac_nombre"] = c1.text_input(
                "Nombre",   value=st.session_state["pac_nombre"],   key="_pcn")
            st.session_state["pac_apellido"] = c2.text_input(
                "Apellido", value=st.session_state["pac_apellido"], key="_pca")

            c3, c4 = st.columns(2)
            fnac = c3.text_input("Fecha de nacimiento (DD/MM/AAAA)",
                                 value=st.session_state["pac_fnac"],
                                 key="_pfnac", placeholder="25/03/1985")
            if not _validate_date(fnac):
                c3.error("Formato inválido — DD/MM/AAAA")
            else:
                st.session_state["pac_fnac"] = fnac
                st.session_state["pac_edad"] = _calc_edad(fnac)

            sexo_idx = SEXOS.index(st.session_state["pac_sexo"]) \
                if st.session_state["pac_sexo"] in SEXOS else 0
            st.session_state["pac_sexo"] = c4.selectbox(
                "Sexo", SEXOS, index=sexo_idx, key="_psexo")

            c5, c6 = st.columns(2)
            c5.text_input("Edad (calculada)", value=st.session_state["pac_edad"],
                          key="_pedad", disabled=True)

            fecha_est = c6.text_input("Fecha del estudio (DD/MM/AAAA)",
                                      value=st.session_state["pac_fecha"],
                                      key="_pfecha", placeholder=TODAY)
            if not _validate_date(fecha_est):
                c6.error("Formato inválido — DD/MM/AAAA")
            else:
                st.session_state["pac_fecha"] = fecha_est

            st.session_state["pac_obra_social"] = st.text_input(
                "Obra Social / Prepaga",
                value=st.session_state["pac_obra_social"], key="_pos")

        # ── Logo de la institución ────────────────────────────────────
        # with st.expander("**Logo de la institución**", expanded=False):
        #    logo_bytes = _load_asset(LOGO_PATH)
        #    if logo_bytes:
        #        st.image(logo_bytes, width=200)
        #        st.caption(f"Logo cargado desde `assets/logo.png`")
        #    else:
        #        st.caption("No hay logo guardado. Subí uno a continuación.")

        #    st.markdown("**Reemplazar logo:**")
        #    logo_file = st.file_uploader(
        #        "Subir logo (JPG, PNG)", type=["jpg","jpeg","png","webp","bmp"],
        #        key="_logo_up", label_visibility="collapsed")
        #    if logo_file:
        #        data = logo_file.read()
        #        _save_asset(LOGO_PATH, data)
        #        st.success("Logo guardado en `assets/logo.png`. Se usará en todos los PDF.")
        #        st.rerun()

        # ── Firma digital ─────────────────────────────────────────────
        # with st.expander("**Firma digital del profesional**", expanded=False):
        #    firma_bytes = _load_asset(FIRMA_PATH)
        #    if firma_bytes:
        #        st.image(firma_bytes, width=220)
        #        st.caption(f"Firma cargada desde `assets/firma.png`")
        #    else:
        #        st.caption("No hay firma guardada. Subí una a continuación.")

        #    st.markdown("**Reemplazar firma:**")
        #    firma_file = st.file_uploader(
        #        "Subir firma (JPG, PNG)", type=["jpg","jpeg","png"],
        #        key="_firma_up", label_visibility="collapsed")
        #    if firma_file:
        #        data = firma_file.read()
        #        _save_asset(FIRMA_PATH, data)
        #        st.success("Firma guardada en `assets/firma.png`. Se usará en todos los PDF.")
        #        st.rerun()

    # ═══════════════════════════════════════════
    # COL 2 — Síntomas + Análisis + Mediciones + PPM
    # ═══════════════════════════════════════════
    with col2:

        # ── Síntomas ─────────────────────────────────────────────────
        with st.expander("**Síntomas anteriores a la prueba**", expanded=True):
            sc = st.columns(3)
            for i, s in enumerate(SINTOMAS):
                st.session_state[f"sint_{s}"] = sc[i % 3].checkbox(
                    s, value=st.session_state[f"sint_{s}"], key=f"_cb_{s}")
            st.session_state["sint_otros"] = st.text_input(
                "Otros síntomas",
                value=st.session_state["sint_otros"], key="_siotros")

        # ── Tipo de análisis ─────────────────────────────────────────
        with st.expander("**Tipo de análisis y sustrato**", expanded=True):
            tipo_idx = TIPOS.index(st.session_state["tipo_analisis"]) \
                if st.session_state["tipo_analisis"] in TIPOS else 0
            tipo = st.selectbox("Tipo de análisis", TIPOS,
                                index=tipo_idx, key="_tipo")
            st.session_state["tipo_analisis"] = tipo

            sust_opts = TIPO_SUSTRATO[tipo]
            cur_sust = st.session_state["sustrato"]
            sust_idx = sust_opts.index(
                cur_sust) if cur_sust in sust_opts else 0
            sustrato = st.selectbox("Sustrato", sust_opts,
                                    index=sust_idx, key="_sust")
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
                step=1, key="_n",
                help=f"Valor por defecto para este estudio: {n_def}")
            st.session_state["n_mediciones"] = n

            # Intervalo
            iv_opts = [10, 20, 30]
            iv_cur = st.session_state["intervalo"]
            iv_idx = iv_opts.index(iv_cur) if iv_cur in iv_opts else 2
            iv = st.radio(
                "Minutos entre tomas",
                iv_opts, index=iv_idx, horizontal=True, key="_iv",
                format_func=lambda x: f"{x} min",
                help=f"Valor por defecto para este estudio: {iv_def} min")
            st.session_state["intervalo"] = iv

            # Umbral H₂
            umb = st.slider(
                "Umbral positivo H₂ (ppm)",
                min_value=5, max_value=50,
                value=st.session_state["umbral"],
                step=1, key="_umb",
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
        with st.expander("**Valores PPM — H₂ y CH₄**", expanded=True):
            tiempos = [i * iv for i in range(n)]
            tls = [f"{t} min" for t in tiempos]

            hc = st.columns([2, 2, 2])
            hc[0].markdown("**Tiempo**")
            hc[1].markdown("**H₂ (ppm)**")
            hc[2].markdown("**CH₄ (ppm)**")
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
                    key=f"_h2_{i}", placeholder="ppm")
                st.session_state[f"ch4_{i}"] = rc[2].text_input(
                    f"ch4_{i}", value=st.session_state[f"ch4_{i}"],
                    label_visibility="collapsed",
                    key=f"_c4_{i}", placeholder="ppm")

        # ── Interpretación ───────────────────────────────────────────
        with st.expander("**Interpretación del profesional (opcional)**",
                         expanded=False):
            st.session_state["interpretacion"] = st.text_area(
                "Observaciones",
                value=st.session_state["interpretacion"],
                height=80, key="_interp",
                label_visibility="collapsed")
