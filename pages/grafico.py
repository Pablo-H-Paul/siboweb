"""
Pestaña 3 — Gráfico & AUC
"""

from logic.interpretacion import interpretar
from logic.auc import calcular_auc
import matplotlib.pyplot as plt
import io
import streamlit as st
import matplotlib
matplotlib.use("Agg")


H2_COLOR = "#2563EB"
CH4_COLOR = "#10B981"
UMBRAL_COLOR = "#F59E0B"


def _get_ppm_vals():
    n = st.session_state.get("n_mediciones", 7)
    iv = st.session_state.get("intervalo",    30)
    tiempos = [i * iv for i in range(n)]
    h2, ch4 = [], []
    for i in range(n):
        try:
            h2.append(float(st.session_state.get(f"h2_{i}", "")))
        except:
            h2.append(None)
        try:
            ch4.append(float(st.session_state.get(f"ch4_{i}", "")))
        except:
            ch4.append(None)
    return h2, ch4, tiempos


def _build_chart(h2_vals, ch4_vals, tiempos, umbral, tls) -> bytes:
    fig, ax = plt.subplots(figsize=(9, 4))
    fig.patch.set_facecolor("#F8FAFC")
    ax.set_facecolor("#F8FAFC")

    x = tiempos
    h2x = [x[i] for i, v in enumerate(h2_vals) if v is not None]
    h2y = [v for v in h2_vals if v is not None]
    ch4x = [x[i] for i, v in enumerate(ch4_vals) if v is not None]
    ch4y = [v for v in ch4_vals if v is not None]

    if h2x:
        ax.plot(h2x, h2y, "o-", color=H2_COLOR,
                lw=2.2, ms=7, label="H₂",  zorder=3)
        ax.fill_between(h2x, h2y, alpha=0.08, color=H2_COLOR)
    if ch4x:
        ax.plot(ch4x, ch4y, "s-", color=CH4_COLOR,
                lw=2.2, ms=7, label="CH₄", zorder=3)
        ax.fill_between(ch4x, ch4y, alpha=0.08, color=CH4_COLOR)

    ax.axhline(umbral, color=UMBRAL_COLOR, ls="--", lw=1.4,
               label=f"Umbral {umbral} ppm", alpha=0.9)

    ax.set_xticks(x)
    ax.set_xticklabels(tls, fontsize=8, rotation=20, ha="right")
    ax.set_xlabel("Tiempo (min)", fontsize=9)
    ax.set_ylabel("PPM",          fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(True, ls="--", alpha=0.4, color="#E2E8F0")
    for sp in ax.spines.values():
        sp.set_color("#E2E8F0")
    if h2x or ch4x:
        ax.legend(fontsize=9, edgecolor="#E2E8F0")

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def render():
    h2_vals, ch4_vals, tiempos = _get_ppm_vals()
    umbral = st.session_state.get("umbral", 20)
    n = st.session_state.get("n_mediciones", 7)
    iv = st.session_state.get("intervalo",    30)
    tls = [f"{t} min" for t in tiempos]

    auc_h2 = calcular_auc(h2_vals,  tiempos)
    # auc_ch4 = calcular_auc(ch4_vals, tiempos)
    h2s = f"{auc_h2:.0f}" if auc_h2 is not None else "—"
    # ch4s = f"{auc_ch4:.0f}" if auc_ch4 is not None else "—"

    # ── Métricas ─────────────────────────────────────────────────────
    mc1, mc3, mc4 = st.columns(3)
    mc1.metric("AUC H₂ (ppm·min)",  h2s)
    # mc2.metric("AUC CH₄ (ppm·min)", ch4s)
    mc3.metric("Umbral H₂",         f"{umbral} ppm")
    mc4.metric("Ref. H₂",           "1000–3000")

    # ── Interpretación automática ────────────────────────────────────
    if any(v is not None for v in h2_vals):  # ch4_vals
        tit, cpo, pos = interpretar(
            h2_vals,  # ch4_vals,
            st.session_state.get("tipo_analisis", "SIBO"),
            st.session_state.get("sustrato",      "Lactulosa"),
            tiempos, umbral,
        )
        if pos:
            st.error(f"**{tit}**")
        else:
            st.success(f"**{tit}**")

        with st.expander("Ver detalle de la interpretación"):
            for line in cpo.strip().split("\n"):
                line = line.strip()
                if line:
                    if "CONSULTE" in line.upper():
                        st.warning(line)
                    else:
                        st.write(line)

    # ── Gráfico ──────────────────────────────────────────────────────
    if any(v is not None for v in h2_vals):  # + ch4_vals
        chart_bytes = _build_chart(h2_vals,  tiempos, umbral, tls)  # ch4_vals,
        st.session_state["chart_bytes"] = chart_bytes   # para el PDF
        st.image(chart_bytes, use_container_width=True)
    else:
        st.info(
            "Ingresá valores PPM en la pestaña **Datos y valores** para ver el gráfico.")
        st.session_state["chart_bytes"] = None
