# src/services/data_source.py
import pandas as pd
from typing import Optional

# Nombres (como en tu Google Sheets / BASE_HEADERS)
COL_VOTO = "Si las elecciones fueran mañana, ¿por quién votarías?"
COL_SEGURIDAD = "¿Qué tan seguro estás de tu elección? (1-5)"
COL_ESTRATO = "Estrato socioeconómico"
COL_IDEO = "Alineamiento ideológico personal"
COL_EVENTO = "¿Qué tipo de evento te haría cambiar de opinión respecto a los candidatos?"
COL_MEDIOS = "Medio de influencia (selección múltiple)"

# si tus opciones exactas difieren, aquí es donde se ajusta sin romper el motor
MAP_VOTO = {
    "Jorge Quiroga Ramírez (Derecha)": "A",
    "Rodrigo Paz Pereira (Izquierda)": "B",
    "Voto Blanco": "Blanco",
    "Voto Nulo": "Nulo",
    "Aún no lo decido": "Indeciso",
}

def load_from_excel(path: str, sheet_name: str = "Resultados Originales") -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet_name)
    return df

def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # voto -> estado
    if COL_VOTO in df.columns:
        df["estado_inicial"] = df[COL_VOTO].map(MAP_VOTO).fillna("Indeciso")
    else:
        df["estado_inicial"] = "Indeciso"

    # seguridad -> 1..5 (firmeza)
    if COL_SEGURIDAD in df.columns:
        df["seguridad_1a5"] = pd.to_numeric(df[COL_SEGURIDAD], errors="coerce").fillna(3).clip(1, 5)
    else:
        df["seguridad_1a5"] = 3

    # estrato
    df["estrato"] = df.get(COL_ESTRATO, "Medio").fillna("Medio").astype(str)

    # ideología
    df["ideologia"] = df.get(COL_IDEO, "Centro").fillna("Centro").astype(str)

    # evento determinante
    df["evento_det"] = df.get(COL_EVENTO, "Ninguno").fillna("Ninguno").astype(str)

    # medios
    df["medios"] = df.get(COL_MEDIOS, "").fillna("").astype(str)

    # id agente
    df["agent_id"] = range(1, len(df) + 1)

    return df
