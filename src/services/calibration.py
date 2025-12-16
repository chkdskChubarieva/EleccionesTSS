# src/services/calibration.py
from dataclasses import dataclass
import numpy as np
import pandas as pd
from typing import Dict, Any

@dataclass
class CalibrationResult:
    init_dist: Dict[str, float]
    by_estrato: Dict[str, Dict[str, float]]
    by_ideologia: Dict[str, Dict[str, float]]
    normals: Dict[str, Dict[str, float]]  # {"debate": {"mu":..,"sigma":..}, ...}

def _dist(series: pd.Series) -> Dict[str, float]:
    vc = series.value_counts(dropna=False)
    total = float(vc.sum()) if len(vc) else 1.0
    return {k: float(v) / total for k, v in vc.items()}

def _safe_mu_sigma(x: pd.Series, default_mu=0.6, default_sigma=0.15):
    vals = pd.to_numeric(x, errors="coerce").dropna().astype(float)
    if len(vals) < 5:
        return default_mu, default_sigma
    mu = float(vals.mean())
    sigma = float(vals.std(ddof=0))
    sigma = max(1e-6, sigma)
    return mu, sigma

def calibrate(df: pd.DataFrame) -> CalibrationResult:
    # Distribuciones iniciales
    init_dist = _dist(df["estado_inicial"])

    by_estrato = {}
    for est, sub in df.groupby("estrato"):
        by_estrato[str(est)] = _dist(sub["estado_inicial"])

    by_ideologia = {}
    for ide, sub in df.groupby("ideologia"):
        by_ideologia[str(ide)] = _dist(sub["estado_inicial"])

    # Normales desde datos (si tienes columna específica para debate/percepción, aquí la enchufas)
    # Como mínimo: usamos seguridad (1..5) para derivar "rapidez respuesta" (alpha) y "resistencia"
    mu_seg, sig_seg = _safe_mu_sigma(df["seguridad_1a5"], default_mu=3.0, default_sigma=1.0)

    normals = {
        # Esto alimentará el motor como "parámetros por defecto" derivados del dataset
        "seguridad": {"mu": mu_seg, "sigma": sig_seg},
    }

    return CalibrationResult(
        init_dist=init_dist,
        by_estrato=by_estrato,
        by_ideologia=by_ideologia,
        normals=normals
    )
