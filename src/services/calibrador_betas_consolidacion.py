# src/services/calibrador_betas_consolidacion.py
import re
import numpy as np
import pandas as pd

def _get_feature_names_and_coefs(pipe, num_cols, cat_cols) -> tuple[pd.DataFrame, float]:
    """
    Devuelve df_coefs con coeficientes reescalados a 'por 1 unidad real'
    y el intercepto.
    """
    clf = pipe.named_steps["clf"]
    ct = pipe.named_steps["pre"]

    coef = clf.coef_.ravel()
    intercept = float(clf.intercept_[0])

    feats_out = ct.get_feature_names_out()

    # scaler de numéricas
    num_scaler = ct.named_transformers_["num"].named_steps["sc"]
    num_scales = dict(zip(num_cols, num_scaler.scale_))

    # onehot de categóricas
    oh = ct.named_transformers_["cat"].named_steps["oh"]
    cat_out = oh.get_feature_names_out(cat_cols)

    rows = []
    for j, fname in enumerate(feats_out):
        c_std = float(coef[j])

        is_cat = any(fname.endswith(x) or x in fname for x in cat_out)
        if is_cat:
            c_unit = c_std
        else:
            m = re.match(r"num__(.+)", fname)
            orig = m.group(1) if m else fname
            sd = num_scales.get(orig, 1.0)
            c_unit = 0.0 if (sd is None or sd == 0) else (c_std / sd)

        rows.append((fname, c_std, c_unit))

    df_coefs = pd.DataFrame(rows, columns=["feature_out", "coef_std", "coef_per_unit"])
    return df_coefs, intercept


def _group_mean(df_coefs: pd.DataFrame, patterns: list[str]) -> float:
    mask = np.zeros(len(df_coefs), dtype=bool)
    for pat in patterns:
        mask |= df_coefs["feature_out"].str.contains(pat, flags=re.IGNORECASE, regex=True)
    sub = df_coefs.loc[mask, "coef_per_unit"]
    return float(sub.mean()) if len(sub) else 0.0


def _normalize_globals(globals_dict: dict, target_max_abs: float) -> dict:
    if not globals_dict:
        return globals_dict
    max_abs = max(abs(v) for v in globals_dict.values()) if globals_dict else 0.0
    if max_abs == 0:
        return globals_dict
    scale = target_max_abs / max_abs
    return {k: float(v * scale) for k, v in globals_dict.items()}


def calibrar_betas_consolidacion(pipe, num_cols, cat_cols, df_raw, target_max_abs: float = 0.8):
    """
    Genera estructura betas_sim.json alineada a consolidación:
    {
      "beta0": ...,
      "global": { "economia_empleo":..., "corrupcion_institucional":..., ... },
      "delta_by_estrato": {...},
      "delta_by_ideologia": {...},
      "legacy": { "betaE":..., "betaD":..., "betaP":..., "betaR":... }
    }
    """
    df_coefs, intercept = _get_feature_names_and_coefs(pipe, num_cols, cat_cols)

    # ========= Mapeo de categorías temáticas (basado en tus headers reales) =========
    mapping = {
        "economia_empleo": [
            r"Factores decisión: Economía",
            r"Prioridad: Crisis económica",
            r"Prioridad: Combustible",
            r"Prioridad: Transporte",
            r"Mercado laboral:",
            r"Expectativa de futuro profesional",
        ],
        "corrupcion_institucional": [
            r"Factores decisión: Corrupción/Justicia",
            r"Prioridad: Corrupción/Desconfianza",
            r"delta_honestidad_transparencia",
            r"Influencia del pasado del candidato",
            r"Conocimiento del historial",
        ],
        "seguridad_ciudadana": [
            r"Factores decisión: Seguridad ciudadana",
            r"Prioridad: Seguridad ciudadana",
        ],
        "servicios_publicos": [
            r"Factores decisión: Servicios públicos",
            r"Prioridad: Salud y educación pública",
            r"Factores decisión: Educación",
            r"Acceso a servicios básicos",
        ],
        "medio_ambiente": [
            r"Factores decisión: Medio ambiente",
            r"Prioridad: Medio ambiente/gestión de residuos",
        ],
        "derechos_sociales": [
            r"Factores decisión: Derechos sociales",
        ],
        "modelo_desarrollo": [
            r"Factores decisión: Modelo de desarrollo",
        ],
        "liderazgo_competencia": [
            r"delta_experiencia_en_gestión",
            r"delta_competencia_técnica_académica",
            r"delta_liderazgo_fuerte_decisivo",
            r"delta_propuestas_claras_y_realistas",
            r"delta_coherencia_discurso_acciones",
            r"delta_capacidad_de_unir_a_la_población",
        ],
        "conexion_juventud": [
            r"delta_conexión_con_los_jóvenes",
            r"Situación educativa",
            r"Carrera",
        ],
        "ideologia": [
            r"Alineamiento ideológico personal",
        ],
        "medios_redes": [
            r"Tiempo de conexión a internet por día",
            r"Medio de influencia",
        ],
        "shock_evento": [
            r"¿Qué tipo de evento te haría cambiar de opinión",
        ],
        "politizacion": [
            r"Interés por la política nacional",
            r"Frecuencia con la que conversas sobre política",
        ]
    }

    globals_raw = {k: _group_mean(df_coefs, pats) for k, pats in mapping.items()}

    # Normalizar magnitudes globales
    globals_norm = _normalize_globals(globals_raw, target_max_abs=target_max_abs)

    # Escalar intercepto en la misma proporción (para consistencia)
    # Usamos el mismo scale que se aplicó al máximo absoluto:
    max_abs_raw = max(abs(v) for v in globals_raw.values()) if globals_raw else 0.0
    scale = (target_max_abs / max_abs_raw) if max_abs_raw else 1.0
    beta0 = float(intercept * scale)

    # ========= Segmentación: deltas por estrato/ideología (simple y defendible) =========
    # Nota: esto NO re-entrena por grupo (para no sobreajustar),
    # sino que da "sesgo" por grupo usando coeficientes de one-hot.

    def pick_onehot_coef(prefix: str) -> dict:
        out = {}
        # features_out del onehot suelen ser "cat__Columna_valor"
        for _, row in df_coefs.iterrows():
            fname = row["feature_out"]
            if fname.lower().startswith("cat__") and prefix.lower() in fname.lower():
                # ejemplo: cat__Estrato socioeconómico_Medio
                parts = fname.split(prefix + "_")
                if len(parts) == 2:
                    key = parts[1]
                    out[key] = float(row["coef_per_unit"] * scale)
        return out

    delta_by_estrato = pick_onehot_coef("Estrato socioeconómico")
    delta_by_ideologia = pick_onehot_coef("Alineamiento ideológico personal")

    # ========= Legacy (compatibilidad con E/D/P/R) =========
    # Mapeo simple: E->economia, D->corrupcion, P->shock_evento, R->medios_redes
    legacy = {
        "betaE": globals_norm.get("economia_empleo", 0.0),
        "betaD": globals_norm.get("corrupcion_institucional", 0.0),
        "betaP": globals_norm.get("shock_evento", 0.0),
        "betaR": globals_norm.get("medios_redes", 0.0),
    }

    return {
        "beta0": beta0,
        "global": globals_norm,
        "delta_by_estrato": delta_by_estrato,
        "delta_by_ideologia": delta_by_ideologia,
        "legacy": legacy
    }
