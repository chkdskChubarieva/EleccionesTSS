# src/services/sensitivity.py
import os
import json
import math

BASE_DIR = os.path.dirname(__file__)  # .../src/services
BETAS_PATH = os.path.join(BASE_DIR, "betas_sim.json")

FACTORES_MAP = {
    "economia_empleo": "Factores decisión: Economía (1-5)",
    "corrupcion_institucional": "Factores decisión: Corrupción/Justicia (1-5)",
    "educacion": "Factores decisión: Educación (1-5)",
    "seguridad_ciudadana": "Factores decisión: Seguridad ciudadana (1-5)",
    "derechos_sociales": "Factores decisión: Derechos sociales (1-5)",
    "medio_ambiente": "Factores decisión: Medio ambiente (1-5)"
}

def load_betas():
    with open(BETAS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _safe_float(x, default=0.0):
    try:
        fx = float(x)
        if math.isnan(fx):
            return default
        return fx
    except Exception:
        return default

def _safe_mean_numeric(series):
    vals = []
    for v in series:
        try:
            fv = float(v)
            if not math.isnan(fv):
                vals.append(fv)
        except Exception:
            continue
    return sum(vals) / len(vals) if vals else None

def sensitivity_by_estrato(
    df,
    factor_lealtad=1.0,
    factor_contagio=1.0,
    factor_ruido=1.0,
    factor_medios=1.0,
    factor_memoria=0.8,
    top_k=1
):
    """
    score = |beta_efectivo| * interes_promedio_normalizado * multiplicadores

    beta_efectivo:
      - si betas_sim.json tiene "global": usa betas["global"][factor]
      - si además tiene "delta_by_estrato" con dict por estrato: suma delta[estrato][factor]
      - si delta_by_estrato[estrato] no es dict (float, str, etc): ignora delta (0)
    """
    betas = load_betas()

    beta_global = betas.get("global", {})
    if not isinstance(beta_global, dict):
        beta_global = {}

    delta_by_estrato = betas.get("delta_by_estrato", {})
    if not isinstance(delta_by_estrato, dict):
        delta_by_estrato = {}

    # Detectar columna de estrato (flexible)
    COL_ESTRATO = None
    estrato_candidates = ["estrato", "Estrato socioeconómico", "estrato_socioeconomico"]
    for col in estrato_candidates:
        if col in df.columns:
            COL_ESTRATO = col
            break
    
    if COL_ESTRATO is None:
        print("⚠️ No se encontró columna de estrato en sensibilidad")
        return []

    print(f"🔍 Sensibilidad usando columna: {COL_ESTRATO}")
    results = []

    for estrato, sub in df.groupby(COL_ESTRATO):
        estrato_key = str(estrato)

        delta_est = delta_by_estrato.get(estrato_key, {})
        # ✅ Si delta_est no es dict, lo anulamos (evita el error que tienes)
        if not isinstance(delta_est, dict):
            delta_est = {}

        scores = {}

        for factor, col in FACTORES_MAP.items():
            if col not in sub.columns:
                continue

            mean_val = _safe_mean_numeric(sub[col])
            if mean_val is None:
                continue

            interes_norm = (mean_val - 1.0) / 4.0
            interes_norm = max(0.0, min(1.0, interes_norm))

            b_global = _safe_float(beta_global.get(factor, 0.0), 0.0)
            b_delta  = _safe_float(delta_est.get(factor, 0.0), 0.0)
            beta_eff = b_global + b_delta

            score = (
                abs(beta_eff)
                * interes_norm
                * _safe_float(factor_contagio, 1.0)
                * _safe_float(factor_medios, 1.0)
                * _safe_float(factor_memoria, 0.8)
                * (1.0 / max(_safe_float(factor_lealtad, 1.0), 0.1))
                * (1.0 / max(_safe_float(factor_ruido, 1.0), 0.1))
            )

            scores[factor] = score

        if not scores:
            continue

        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:max(1, int(top_k))]

        for rank, (factor, coef) in enumerate(top, start=1):
            results.append({
                "estrato": estrato_key,
                "factor": factor,
                "coef": round(float(coef), 6),
                "rank": rank
            })

    print(f"✅ Sensibilidad calculada: {len(results)} resultados")
    return results
