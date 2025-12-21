# src/services/normalize_sheets.py
import pandas as pd

VOTO_MAP = {
    "Jorge Quiroga Ramírez (Derecha)": "A",
    "Tuto Quiroga": "A",
    "Jorge Quiroga": "A",

    "Rodrigo Paz Pereira (Izquierda)": "B",
    "Rodrigo Paz": "B",

    "Voto Blanco": "Blanco",
    "Voto Nulo": "Nulo",
    "Aún no lo decido": "Indeciso",
}

def _first_series(df: pd.DataFrame, candidates: list[str], default):
    for c in candidates:
        if c in df.columns:
            return df[c]
    return pd.Series([default] * len(df), index=df.index)

def _normalize_estrato_value(x: str) -> str:
    """
    Normaliza variantes de estrato para que SIEMPRE sea una de:
      - Bajo
      - Medio-Bajo
      - Medio
      - Medio-Alto
    """
    if x is None:
        return "Medio"

    s = str(x).strip().lower()
    s = s.replace("_", "-").replace("—", "-").replace("–", "-")
    s = s.replace(" ", "-")  # medio bajo -> medio-bajo

    # Mapas comunes por si la gente escribió distinto
    mapping = {
        "bajo": "Bajo",

        "medio-bajo": "Medio-Bajo",
        "mediobajo": "Medio-Bajo",

        "medio": "Medio",

        "medio-alto": "Medio-Alto",
        "medioalto": "Medio-Alto",
    }

    # si ya está en el mapping exacto
    if s in mapping:
        return mapping[s]

    # intentos por contiene
    if "bajo" in s and "medio" in s:
        return "Medio-Bajo"
    if "alto" in s and "medio" in s:
        return "Medio-Alto"
    if "bajo" in s:
        return "Bajo"
    if "medio" in s:
        return "Medio"

    # fallback
    return "Medio"

def normalize_df_sheets(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    # Estrato (normalizado a tus 4 categorías)
    estr = _first_series(
        df,
        ["Estrato socioeconómico", "estrato", "estrato_socioeconomico"],
        "Medio",
    ).fillna("Medio").astype(str)

    df["estrato"] = estr.apply(_normalize_estrato_value)

    # Ideología
    df["ideologia"] = _first_series(
        df,
        ["Alineamiento ideológico personal", "ideologia", "alineamiento_ideologico"],
        "Centro",
    ).fillna("Centro").astype(str)

    # Seguridad (1..5)
    seg = _first_series(
        df,
        ["¿Qué tan seguro estás de tu elección? (1-5)", "seguridad_voto", "seguridad_1a5"],
        3,
    )
    df["seguridad_1a5"] = pd.to_numeric(seg, errors="coerce").fillna(3).clip(1, 5)

    # Evento determinante
    df["evento_det"] = _first_series(
        df,
        [
            "¿Qué tipo de evento te haría cambiar de opinión respecto a los candidatos?",
            "evento_determinante",
            "evento_det",
        ],
        "Ninguno",
    ).fillna("Ninguno").astype(str)

    # Medios
    df["medios"] = _first_series(
        df,
        ["Medio de influencia (selección múltiple)", "medio_influencia", "medios"],
        "",
    ).fillna("").astype(str)

    # Voto inicial
    voto = _first_series(
        df,
        ["Si las elecciones fueran mañana, ¿por quién votarías?", "intencion_voto", "voto"],
        "Aún no lo decido",
    ).fillna("Aún no lo decido").astype(str)

    df["estado_inicial"] = voto.map(VOTO_MAP).fillna("Indeciso")

    # ID
    if "agent_id" not in df.columns:
        df["agent_id"] = range(1, len(df) + 1)

    return df
