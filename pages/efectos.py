"""
Pestaña 2 — Efectos adversos & Medicación — v7.0
Síntomas actualizados: Dolor Abdominal en lugar de Retortijones, sin Non GI.
"""

import streamlit as st

EFECTOS = ["Flatulencia", "Dolor Abdominal",
           "Diarrea", "Estreñimiento", "Distensión"]


def _init_state():
    for i in range(15):
        for s in EFECTOS:
            st.session_state.setdefault(f"ef_{i}_{s}", False)
    st.session_state.setdefault("ef_otros",  "")
    # st.session_state.setdefault("medicacion", "")


def render():
    _init_state()

    n = st.session_state.get("n_mediciones", 7)
    iv = st.session_state.get("intervalo",    30)
    tiempos = [i * iv for i in range(n)]
    tls = [f"{t} min" for t in tiempos]

    st.markdown("#### Efectos adversos por intervalo")

    cols_h = st.columns([1.8] + [1] * len(EFECTOS))
    cols_h[0].markdown("**Tiempo**")
    for j, s in enumerate(EFECTOS):
        cols_h[j+1].markdown(f"**{s}**")

    st.divider()

    for i in range(n):
        row = st.columns([1.8] + [1] * len(EFECTOS))
        row[0].markdown(
            f"<div style='padding-top:4px;color:gray;font-size:13px'>{tls[i]}</div>",
            unsafe_allow_html=True)
        for j, s in enumerate(EFECTOS):
            st.session_state[f"ef_{i}_{s}"] = row[j+1].checkbox(
                s, value=st.session_state[f"ef_{i}_{s}"],
                key=f"_ef_{i}_{j}", label_visibility="collapsed")

    # st.divider()
    # col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        st.markdown("#### Otros efectos adversos")
        st.session_state["ef_otros"] = st.text_area(
            "Otros", value=st.session_state["ef_otros"],
            height=100, label_visibility="collapsed", key="_ef_otros")

    # Remover medicación - no es necesario
    # with col_b:
    #    st.markdown("#### Medicación del paciente")
    #    st.session_state["medicacion"] = st.text_area(
    #        "Medicación", value=st.session_state["medicacion"],
    #        height=100, label_visibility="collapsed", key="_med")
