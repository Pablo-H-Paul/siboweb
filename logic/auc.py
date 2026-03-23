"""
Cálculo de AUC (área bajo la curva) por regla trapezoidal.
Lógica idéntica a la versión de escritorio.
"""


def calcular_auc(valores_ppm: list, tiempos: list) -> float | None:
    """
    Retorna el AUC en ppm·min usando la regla trapezoidal.
    Ignora valores None (intervalos no completados).
    """
    pts = [(t, v) for t, v in zip(tiempos, valores_ppm) if v is not None]
    if len(pts) < 2:
        return None
    return round(
        sum(
            0.5 * (pts[i][1] + pts[i + 1][1]) * (pts[i + 1][0] - pts[i][0])
            for i in range(len(pts) - 1)
        ),
        1,
    )
