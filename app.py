"""
SIBO Analyzer — Web v8.0
"""

import streamlit as st
from datetime import datetime

# Para limpiar la página
from streamlit_js_eval import streamlit_js_eval


# import auth
import pages.datos as pg_datos
import pages.efectos as pg_efectos
import pages.grafico as pg_grafico
from logic.pdf_gen import generate_pdf

EFECTOS = ["Flatulencia", "Dolor Abdominal",
           "Diarrea", "Estreñimiento", "Distensión"]
SINTOMAS = ["Flatulencia", "Dolor Abdominal",
            "Diarrea", "Estreñimiento", "Distensión"]
TODAY = datetime.now().strftime("%d/%m/%Y")

# BLOQUE LOGIN con Streamlit


# def login():
#    # Centrar un poco el formulario visualmente si lo deseas
#    _, col_form, _ = st.columns([1, 2, 1])
#
#    with col_form:
#        with st.form("login_form"):
#            # Agregamos los renglones en blanco antes del input
#            # Agregamos los espacios y el título principal
#            st.markdown("<br><br>", unsafe_allow_html=True)
#            st.title("⚕️ SIBO Analyzer")
#
#            user = st.text_input("Usuario")
#            pw = st.text_input("Contraseña", type="password")
#            submit = st.form_submit_button("Entrar")
#
#            if submit:
#                if user == st.secrets["credentials"]["admin_user"] and pw == st.secrets["credentials"]["admin_pass"]:
#                    st.session_state["role"] = "admin"
#                   st.rerun()
#                elif user == st.secrets["credentials"]["standard_user"] and pw == st.secrets["credentials"]["standard_pass"]:
#                    st.session_state["role"] = "user"
#                   st.rerun()
#                else:
#                    st.error("Credenciales fallidas")

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

# Estilos CSS personalizados
st.markdown("""
<style>
    /* Ajustes de espaciado */
    .block-container { 
        padding-top: 1rem; 
        padding-bottom: 1rem; 
    }
    
    /* Ocultar menú y footer */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* Contenedor para centrar título e icono */
    .header-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 20px;
        margin-bottom: 20px;
    }

    .header-icon {
        font-size: 50px;
        margin-bottom: 0px;
    }

    .header-title {
        font-size: 42px;
        font-weight: 700;
        margin-top: 0px;
    }
</style>
""", unsafe_allow_html=True)

# Renderizado del Título e Icono Centrados
st.markdown(
    """
    <div class="header-container">
        <div class="header-title">⚕ SIBO Analyzer | CIMeQ</div>
    </div>
    """,
    unsafe_allow_html=True
)


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
        "prof_nombre", "prof_apellido", "prof_esp", "prof_mat", "prof_inst",
        "prof_email", "prof_tel",
        "pac_nombre", "pac_apellido", "pac_fnac", "pac_edad",
        "pac_sexo", "pac_fecha", "pac_obra_social",
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
        "diagnostico":    ss.get("diagnostico", ""),
        "ef_vars":        ef_vars,
        "ef_otros":       ss.get("ef_otros", ""),
        "medicacion":     ss.get("medicacion", ""),
        "chart_bytes":    ss.get("chart_bytes"),
    }


# ── APP ──────────────────────────────────────────────────────────────
def show_app():

    # 1. Agregamos espacio al inicio de la app para que no pegue al borde superior
    st.markdown("<br><br>", unsafe_allow_html=True)

    hc1, hc2 = st.columns([5, 3])

    with hc2:
        st.markdown("<div style='margin-top:4px'>", unsafe_allow_html=True)
        bc1, bc2, bc3, bc4 = st.columns(4)

        # Generar PDF — logo y firma se cargan automáticamente desde assets/
        if bc1.button("📄 PDF", width='stretch', type="primary"):
            # 1. Ejecutar validación de campos obligatorios
            errores = pg_datos.validate_required_fields()

            if errores:
                # Si hay errores, mostramos una alerta y NO generamos nada
                mensaje_error = "No se puede generar el PDF. Faltan datos: " + \
                    ", ".join(errores)
                st.error(mensaje_error)
            else:
                try:
                    data = _build_pdf_data()
                    # Logo y firma: generate_pdf los carga desde assets/ por defecto
                    pdf_bytes = generate_pdf(data)
                    apellido = st.session_state.get(
                        "pac_apellido", "informe").replace(" ", "_")
                    filename = f"SIBO_{apellido}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                    st.session_state["_pdf_bytes"] = pdf_bytes
                    st.session_state["_pdf_filename"] = filename
                    st.toast("PDF generado. Hacé clic en Descargar.", icon="✅")
                except Exception as e:
                    st.error(f"Error al generar PDF: {e}")

        if st.session_state.get("_pdf_bytes"):
            bc2.download_button(
                label="⬇ Descargar",
                data=st.session_state["_pdf_bytes"],
                file_name=st.session_state.get("_pdf_filename", "informe.pdf"),
                mime="application/pdf",
                width='stretch',
            )

        # if bc3.button("Limpiar", width='stretch'):
        #    preserve = {"_pdf_bytes", "_pdf_filename"}
        #    for k in [k for k in st.session_state if k not in preserve]:
        #        del st.session_state[k]
        #    st.rerun()

        if bc3.button("Limpiar", width='stretch'):
            streamlit_js_eval(js_expressions="parent.window.location.reload()")

        if bc4.button("Salir", width='stretch'):
            # Eliminamos el rol para cerrar la sesión efectivamente
            del st.session_state["role"]
            st.rerun()

    tab1, tab2, tab3 = st.tabs([
        "  Datos y valores  ",
        "  Efectos  ",
        "  Gráfico y AUC  ",
    ])
    with tab1:
        pg_datos.render()
    with tab2:
        pg_efectos.render()
    with tab3:
        pg_grafico.render()


# ── ENTRY POINT ──────────────────────────────────────────────────────
# Reemplaza el bloque final por este:

# if "role" not in st.session_state:
#    login()
# else:
# Solo mostramos la app si el usuario pasó por el login()
show_app()
