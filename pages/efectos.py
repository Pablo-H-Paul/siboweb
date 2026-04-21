"""
Pestaña 2 — Efectos adversos & Medicación — v7.0
Síntomas actualizados: Dolor Abdominal en lugar de Retortijones, sin Non GI.
"""

import streamlit as st
from pathlib import Path

# Rutas de archivos persistentes (relativas al directorio del proyecto)
ASSETS_DIR = Path(__file__).parent.parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"
FIRMA_PATH = ASSETS_DIR / "firma.png"

EFECTOS = ["Flatulencia", "Dolor Abdominal",
           "Diarrea", "Estreñimiento", "Distensión", "Eructos"]


def _init_state():
    for i in range(15):
        for s in EFECTOS:
            st.session_state.setdefault(f"ef_{i}_{s}", False)
    st.session_state.setdefault("ef_otros",  "")
    st.session_state.setdefault("medicacion", "")

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


def firma_render():
    ####
    # ── Logo de la institución ────────────────────────────────────
    with st.expander("**Logo de la institución**", expanded=False):
        logo_bytes = _load_asset(LOGO_PATH)
        if logo_bytes:
            st.image(logo_bytes, width=200)
            st.caption(f"Logo cargado desde `assets/logo.png`")
        else:
            st.caption("No hay logo guardado. Subí uno a continuación.")

        st.markdown("**Reemplazar logo:**")
        logo_file = st.file_uploader(
            "Subir logo (JPG, PNG)", type=["jpg", "jpeg", "png", "webp", "bmp"],
            key="_logo_up", label_visibility="collapsed")
        if logo_file:
            data = logo_file.read()
            _save_asset(LOGO_PATH, data)
            st.success(
                "Logo guardado en `assets/logo.png`. Se usará en todos los PDF.")
            st.rerun()

    # ── Firma digital ─────────────────────────────────────────────
    with st.expander("**Firma digital del profesional**", expanded=False):
        firma_bytes = _load_asset(FIRMA_PATH)
        if firma_bytes:
            st.image(firma_bytes, width=220)
            st.caption(f"Firma cargada desde `assets/firma.png`")
        else:
            st.caption("No hay firma guardada. Subí una a continuación.")

        st.markdown("**Reemplazar firma:**")
        firma_file = st.file_uploader(
            "Subir firma (JPG, PNG)", type=["jpg", "jpeg", "png"],
            key="_firma_up", label_visibility="collapsed")
        if firma_file:
            data = firma_file.read()
            _save_asset(FIRMA_PATH, data)
            st.success(
                "Firma guardada en `assets/firma.png`. Se usará en todos los PDF.")
            st.rerun()

####


def render():
    _init_state()

    # v es un entero que se incrementa al limpiar desde app.py.
    # Al cambiar las keys de todos los widgets, Streamlit los recrea vacíos.
    v = st.session_state.get("_v", 0)

    n = st.session_state.get("n_mediciones", 7)
    iv = st.session_state.get("intervalo",    30)
    tiempos = [i * iv for i in range(n)]
    tls = [f"{t} min" for t in tiempos]

    st.markdown("#### Efectos adversos por intervalo")

    cols_h = st.columns([1.8] + [1] * len(EFECTOS), gap="small")
    cols_h[0].markdown("**Tiempo**")
    for j, s in enumerate(EFECTOS):
        cols_h[j+1].markdown(f"**{s}**")

    st.divider()

    for i in range(n):
        row = st.columns([1.8] + [1] * len(EFECTOS), gap="small")
        row[0].markdown(
            f"<div style='padding-top:4px;color:gray;font-size:13px'>{tls[i]}</div>",
            unsafe_allow_html=True)
        for j, s in enumerate(EFECTOS):
            # key usa versión para forzar limpieza visual; valor se guarda en ef_{i}_{s}
            val = row[j+1].checkbox(
                s,
                value=st.session_state.get(f"ef_{i}_{s}", False),
                key=f"_ef_{i}_{j}_{v}",
                label_visibility="collapsed")
            st.session_state[f"ef_{i}_{s}"] = val

    st.divider()
    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        st.markdown("#### Otros efectos adversos")
        st.session_state["ef_otros"] = st.text_area(
            "Otros", value=st.session_state["ef_otros"],
            height=100, label_visibility="collapsed", key=f"_ef_otros{v}")

    # with col_b:
    #    st.markdown("#### Medicación del paciente")
    #    st.session_state["medicacion"] = st.text_area(
    #        "Medicación", value=st.session_state["medicacion"],
    #        height=100, label_visibility="collapsed", key="_med")
