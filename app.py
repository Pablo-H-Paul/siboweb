"""
SIBO Analyzer — Web v7.0
Punto de entrada principal.

Para correr localmente:
    streamlit run app.py

Variables de entorno (.env):
    SUPABASE_URL=https://xxxx.supabase.co
    SUPABASE_ANON_KEY=eyJ...
"""

import io
import os
import tempfile
import streamlit as st
from datetime import datetime

import auth
import pages.datos as pg_datos
import pages.efectos as pg_efectos
import pages.grafico as pg_grafico
from logic.pdf_gen import generate_pdf

EFECTOS = ["Flatulencia", "Dolor Abdominal",
           "Diarrea", "Estreñimiento", "Distensión"]
SINTOMAS = ["Flatulencia", "Dolor Abdominal",
            "Diarrea", "Estreñimiento", "Distensión"]
TODAY = datetime.now().strftime("%d/%m/%Y")

st.set_page_config(
    page_title="SIBO Analyzer",
    page_icon="⚕",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.block-container { padding-top: 0.8rem; padding-bottom: 1rem; }
#MainMenu { visibility: hidden; }
footer     { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── LOGIN ────────────────────────────────────────────────────────────
def show_login():
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("##")
        with st.container(border=True):
            st.markdown("""
            <div style="background:#1E3A5F;border-radius:8px;padding:16px 20px;
                        margin-bottom:1rem;text-align:center">
                <h2 style="color:white;font-size:1.2rem;margin:0">SIBO Analyzer</h2>
                <p style="color:#94A3B8;font-size:0.8rem;margin:4px 0 0">
                    Sistema de análisis de hidrógeno espirado</p>
            </div>""", unsafe_allow_html=True)

            email = st.text_input("Correo electrónico",
                                  placeholder="medico@institucion.com")
            password = st.text_input("Contraseña", type="password")

            if st.button("Ingresar", use_container_width=True, type="primary"):
                if not email or not password:
                    st.error("Ingresá tu correo y contraseña.")
                else:
                    with st.spinner("Verificando..."):
                        user = auth.login(email, password)
                    if user:
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas.")

            st.markdown(
                "<p style='text-align:center;font-size:0.75rem;color:gray;margin-top:1rem'>"
                "SIBO Analyzer · v7.0 · Uso exclusivo profesional</p>",
                unsafe_allow_html=True)


# ── PDF DATA ─────────────────────────────────────────────────────────
def _build_pdf_data():
    ss = st.session_state
    n = ss.get("n_mediciones", 7)
    iv = ss.get("intervalo",    30)

    tiempos = [i * iv for i in range(n)]
    time_lbls = [f"{t} min" for t in tiempos]

    h2_vals, ch4_vals = [], []
    for i in range(n):
        try:
            h2_vals.append(float(ss.get(f"h2_{i}", "")))
        except:
            h2_vals.append(None)
        try:
            ch4_vals.append(float(ss.get(f"ch4_{i}", "")))
        except:
            ch4_vals.append(None)

    sint_pre = [s for s in SINTOMAS if ss.get(f"sint_{s}", False)]
    ef_vars = {i: {s: ss.get(f"ef_{i}_{s}", False)
                   for s in EFECTOS} for i in range(n)}

    fields = {k: ss.get(k, "") for k in [
        "prof_nombre", "prof_apellido", "prof_esp", "prof_mat", "prof_inst", "prof_email", "prof_tel",
        "pac_nombre", "pac_apellido", "pac_fnac", "pac_edad", "pac_sexo", "pac_fecha", "pac_obra_social",
    ]}

    return {
        "fields":         fields,
        "tipo_analisis":  ss.get("tipo_analisis", "SIBO"),
        "sustrato":       ss.get("sustrato", "Lactulosa"),
        "sint_pre":       sint_pre,
        "sint_otros":     ss.get("sint_otros", ""),
        "h2_vals":        h2_vals,
        "ch4_vals":       ch4_vals,
        "tiempos":        tiempos,
        "time_labels":    time_lbls,
        "umbral":         ss.get("umbral", 20),
        "interpretacion": ss.get("interpretacion", ""),
        "ef_vars":        ef_vars,
        "ef_otros":       ss.get("ef_otros", ""),
        "medicacion":     ss.get("medicacion", ""),
        "chart_bytes":    ss.get("chart_bytes"),
    }


def _bytes_to_tempfile(data: bytes, suffix: str) -> str:
    """Escribe bytes a un archivo temporal y retorna la ruta."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    return path


# ── APP ──────────────────────────────────────────────────────────────
def show_app():
    user = auth.get_user()
    email = user.email if user else ""

    # Header
    hc1, hc2 = st.columns([5, 3])
    with hc1:
        st.markdown(f"""
        <div style="background:#1E3A5F;color:white;padding:10px 16px;
                    border-radius:8px;margin-bottom:0.8rem;display:flex;
                    align-items:center;justify-content:space-between">
            <div>
                <span style="font-size:1rem;font-weight:500">⚕ SIBO Analyzer</span>
                <span style="font-size:0.8rem;color:#94A3B8;margin-left:12px">
                    {email}</span>
            </div>
        </div>""", unsafe_allow_html=True)

    with hc2:
        st.markdown("<div style='margin-top:4px'>", unsafe_allow_html=True)
        bc1, bc2, bc3, bc4 = st.columns(4)

        # Generar PDF
        if bc1.button("📄 PDF", use_container_width=True, type="primary"):
            try:
                data = _build_pdf_data()

                # Logo → tempfile
                logo_path = None
                logo_bytes = st.session_state.get("logo_bytes")
                if logo_bytes:
                    logo_path = _bytes_to_tempfile(logo_bytes, ".png")

                # Firma → tempfile
                firma_path = None
                firma_bytes = st.session_state.get("firma_bytes")
                if firma_bytes:
                    firma_path = _bytes_to_tempfile(firma_bytes, ".png")

                pdf_bytes = generate_pdf(
                    data, logo_path=logo_path, firma_path=firma_path)

                # Limpiar archivos temporales
                for p in [logo_path, firma_path]:
                    if p and os.path.exists(p):
                        os.unlink(p)

                apellido = st.session_state.get(
                    "pac_apellido", "informe").replace(" ", "_")
                filename = f"SIBO_{apellido}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                st.session_state["_pdf_bytes"] = pdf_bytes
                st.session_state["_pdf_filename"] = filename
                st.success("PDF listo para descargar")
            except Exception as e:
                st.error(f"Error: {e}")

        # Descargar
        if st.session_state.get("_pdf_bytes"):
            bc2.download_button(
                label="⬇ Descargar",
                data=st.session_state["_pdf_bytes"],
                file_name=st.session_state.get("_pdf_filename", "informe.pdf"),
                mime="application/pdf",
                use_container_width=True,
            )

        if bc3.button("Limpiar", use_container_width=True):
            preserve = {"_pdf_bytes", "_pdf_filename"}
            for k in [k for k in st.session_state if k not in preserve]:
                del st.session_state[k]
            st.rerun()

        if bc4.button("Salir", use_container_width=True):
            auth.logout()
            st.rerun()

    # Pestañas
    tab1, tab2, tab3 = st.tabs([
        "  Datos y valores  ",
        "  Efectos y medicación  ",
        "  Gráfico y AUC  ",
    ])
    with tab1:
        pg_datos.render()
    with tab2:
        pg_efectos.render()
    with tab3:
        pg_grafico.render()


# ── ENTRY POINT ──────────────────────────────────────────────────────
# if auth.is_authenticated():
show_app()
# else:
#    show_login()
