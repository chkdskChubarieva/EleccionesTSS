# src/services/calibration.py
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class CalibrationResult:
    init_dist: Dict[str, float]
    by_estrato: Dict[str, Dict[str, float]]
    by_ideologia: Dict[str, Dict[str, float]]
    normals: Dict[str, Dict[str, float]]  # {"seguridad": {"mu":..,"sigma":..,"n":..,"min":..,"max":..}, ...}


# ----------------------------
# Helpers estadísticos robustos
# ----------------------------
def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _safe_mu_sigma(
    series: Optional[pd.Series],
    default_mu: float,
    default_sigma: float,
    clip: Optional[Tuple[float, float]] = None
) -> Tuple[float, float, int, float, float]:
    """
    Devuelve mu, sigma, n, min, max de una serie numérica.
    Si no hay datos, devuelve defaults.
    """
    if series is None:
        return float(default_mu), float(default_sigma), 0, float("nan"), float("nan")

    s = _to_numeric(series).dropna()
    if clip is not None:
        s = s.clip(clip[0], clip[1])

    n = int(len(s))
    if n == 0:
        return float(default_mu), float(default_sigma), 0, float("nan"), float("nan")

    mu = float(s.mean())
    sigma = float(s.std(ddof=1)) if n > 1 else float(default_sigma)
    smin = float(s.min())
    smax = float(s.max())

    # sigma mínimo para evitar "0" si todos respondieron igual
    if not np.isfinite(sigma) or sigma <= 1e-9:
        sigma = float(default_sigma)

    return mu, sigma, n, smin, smax


def _pick_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """
    Devuelve el primer nombre de columna existente en df de la lista candidates.
    """
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _dist(series: pd.Series) -> Dict[str, float]:
    vc = series.value_counts(dropna=False)
    total = float(vc.sum()) if len(vc) else 1.0
    out = {}
    for k, v in vc.items():
        out[str(k)] = float(v) / total
    return out


# ----------------------------
# Función principal
# ----------------------------
def calibrate(df: pd.DataFrame) -> CalibrationResult:
    """
    Crea:
    - init_dist: distribución inicial A/B/Indeciso/Blanco/Nulo
    - by_estrato: distribución por estrato
    - by_ideologia: distribución por ideología
    - normals: mu/sigma de variables cuantitativas relevantes (tarjeta de descriptivo)
    """
    if df is None or len(df) == 0:
        return CalibrationResult(init_dist={}, by_estrato={}, by_ideologia={}, normals={})

    # columnas normalizadas que ya usas en tu motor
    col_estado = _pick_col(df, ["estado_inicial", "estado", "voto", "choice"])
    col_estrato = _pick_col(df, ["estrato", "Estrato socioeconómico"])
    col_ideol = _pick_col(df, ["ideologia", "Alineamiento ideológico personal"])

    # --- Distribución inicial ---
    if col_estado is not None:
        init_dist = _dist(df[col_estado].fillna("Indeciso").astype(str))
    else:
        init_dist = {}

    # --- Distribución por estrato ---
    by_estrato: Dict[str, Dict[str, float]] = {}
    if col_estado is not None and col_estrato is not None:
        for est, sub in df.groupby(col_estrato):
            by_estrato[str(est)] = _dist(sub[col_estado].fillna("Indeciso").astype(str))

    # --- Distribución por ideología ---
    by_ideologia: Dict[str, Dict[str, float]] = {}
    if col_estado is not None and col_ideol is not None:
        for ide, sub in df.groupby(col_ideol):
            by_ideologia[str(ide)] = _dist(sub[col_estado].fillna("Indeciso").astype(str))

    # ----------------------------
    # Normales (tarjeta descriptivo)
    # ----------------------------

    # 1) Seguridad (1-5). En tu DF normalizado suele existir "seguridad_1a5".
    col_seg = _pick_col(df, ["seguridad_1a5", "¿Qué tan seguro estás de tu elección? (1-5)"])
    mu_seg, sig_seg, n_seg, min_seg, max_seg = _safe_mu_sigma(
        df[col_seg] if col_seg else None,
        default_mu=3.0,
        default_sigma=1.0,
        clip=(1.0, 5.0)
    )

    # 2) Interés por política (slider)
    col_interes = _pick_col(df, ["Interés por la política nacional (slider)"])
    mu_int, sig_int, n_int, min_int, max_int = _safe_mu_sigma(
        df[col_interes] if col_interes else None,
        default_mu=50.0,
        default_sigma=15.0,
        clip=None
    )

    # 3) Frecuencia de conversación (slider)
    col_freq = _pick_col(df, ["Frecuencia con la que conversas sobre política (slider)"])
    mu_freq, sig_freq, n_freq, min_freq, max_freq = _safe_mu_sigma(
        df[col_freq] if col_freq else None,
        default_mu=50.0,
        default_sigma=15.0,
        clip=None
    )

    # 4) Variables 1-5 de “conocimiento / influencia / importancia”
    col_past = _pick_col(df, ["Influencia del pasado del candidato (1-5)"])
    mu_past, sig_past, n_past, min_past, max_past = _safe_mu_sigma(
        df[col_past] if col_past else None,
        default_mu=3.0,
        default_sigma=1.0,
        clip=(1.0, 5.0)
    )

    col_hist = _pick_col(df, ["Conocimiento del historial de candidatos (1-5)"])
    mu_hist, sig_hist, n_hist, min_hist, max_hist = _safe_mu_sigma(
        df[col_hist] if col_hist else None,
        default_mu=3.0,
        default_sigma=1.0,
        clip=(1.0, 5.0)
    )

    col_vp = _pick_col(df, ["Importancia del rol del vicepresidente (1-5)"])
    mu_vp, sig_vp, n_vp, min_vp, max_vp = _safe_mu_sigma(
        df[col_vp] if col_vp else None,
        default_mu=3.0,
        default_sigma=1.0,
        clip=(1.0, 5.0)
    )

    # 5) (Opcional) Un “resumen” de prioridades: promedio global de factores decisión 1-5
    factores_cols = [
        c for c in df.columns
        if isinstance(c, str) and c.startswith("Factores decisión:")
    ]
    # Creamos un “índice” promedio de prioridades si existen esas columnas
    if factores_cols:
        factores_mean_row = df[factores_cols].apply(pd.to_numeric, errors="coerce").mean(axis=1)
        mu_fact, sig_fact, n_fact, min_fact, max_fact = _safe_mu_sigma(
            factores_mean_row,
            default_mu=3.0,
            default_sigma=0.7,
            clip=(1.0, 5.0)
        )
    else:
        mu_fact, sig_fact, n_fact, min_fact, max_fact = (3.0, 0.7, 0, float("nan"), float("nan"))

    normals: Dict[str, Dict[str, float]] = {
        "seguridad": {"mu": mu_seg, "sigma": sig_seg, "n": n_seg, "min": min_seg, "max": max_seg},

        # sliders (no asumimos escala fija, reportamos min/max reales)
        "interes_politico": {"mu": mu_int, "sigma": sig_int, "n": n_int, "min": min_int, "max": max_int},
        "frecuencia_conversacion": {"mu": mu_freq, "sigma": sig_freq, "n": n_freq, "min": min_freq, "max": max_freq},

        # 1-5
        "influencia_pasado": {"mu": mu_past, "sigma": sig_past, "n": n_past, "min": min_past, "max": max_past},
        "conocimiento_historial": {"mu": mu_hist, "sigma": sig_hist, "n": n_hist, "min": min_hist, "max": max_hist},
        "importancia_vicepresidente": {"mu": mu_vp, "sigma": sig_vp, "n": n_vp, "min": min_vp, "max": max_vp},

        # resumen
        "factores_decision_promedio": {"mu": mu_fact, "sigma": sig_fact, "n": n_fact, "min": min_fact, "max": max_fact},
    }

    return CalibrationResult(
        init_dist=init_dist,
        by_estrato=by_estrato,
        by_ideologia=by_ideologia,
        normals=normals
    )
