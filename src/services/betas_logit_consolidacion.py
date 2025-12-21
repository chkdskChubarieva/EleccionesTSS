# src/services/betas_logit_consolidacion.py
import os
import sys
import json
import argparse
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from dotenv import load_dotenv
load_dotenv()
# ============================================================
# Compatibilidad de imports (funciona corriendo como script o -m)
# ============================================================
def _safe_import_services():
    """
    Si ejecutas como script: python src/services/betas_logit_consolidacion.py
    Python no siempre resuelve "src.*". Esto asegura que la raíz del proyecto
    quede en sys.path para que "src.services.*" funcione.
    """
    here = os.path.abspath(os.path.dirname(__file__))          # .../src/services
    src_dir = os.path.abspath(os.path.join(here, ".."))        # .../src
    root_dir = os.path.abspath(os.path.join(src_dir, ".."))    # .../ (raíz proyecto)
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    return root_dir

ROOT_DIR = _safe_import_services()

from src.services.normalize_sheets import normalize_df_sheets
from src.services.calibrador_betas_consolidacion import calibrar_betas_consolidacion

# Intentar importar fetch_responses_df, pero no hacerlo obligatorio (por fallback)
try:
    from src.services.sheets import fetch_responses_df
except Exception:
    fetch_responses_df = None


# =========================
# Config de voto / candidatos
# =========================
COL_VOTO = "Si las elecciones fueran mañana, ¿por quién votarías?"
CAND_A = "TUTO"
CAND_B = "PAZ"

VOTE_ALIASES = {
    "TUTO": [
        "TUTO", "Tuto", "Tuto Quiroga", "Jorge Quiroga",
        "Jorge Quiroga Ramírez", "Quiroga", "Tuto Quiroga Ramírez"
    ],
    "PAZ": [
        "PAZ", "Paz", "Rodrigo Paz",
        "Rodrigo Paz Pereira", "Paz Pereira"
    ]
}


# Salida: SIEMPRE a src/services/betas_sim.json
SERVICES_DIR = os.path.abspath(os.path.dirname(__file__))
OUT_PATH = os.path.join(SERVICES_DIR, "betas_sim.json")

# Excel local por defecto (si no hay Sheets)
DEFAULT_XLSX = os.path.join(ROOT_DIR, "Resultados Encuesta.xlsx")


def _canonical_vote(x) -> str:
    if not isinstance(x, str):
        return ""
    s = x.strip().lower()
    if "tuto" in s or "quiroga" in s:
        return CAND_A
    if "paz" in s:
        return CAND_B
    return ""


def load_df(source: str, xlsx_path: str | None) -> pd.DataFrame:
    """
    source:
      - "sheets": usa fetch_responses_df() si está disponible
      - "xlsx": lee el excel local
      - "auto": intenta sheets y si falla, cae a xlsx
    """
    if source not in {"auto", "sheets", "xlsx"}:
        raise ValueError("source debe ser: auto | sheets | xlsx")

    if source in {"auto", "sheets"}:
        if fetch_responses_df is None:
            if source == "sheets":
                raise RuntimeError("fetch_responses_df no está disponible (falló import).")
        else:
            try:
                df = fetch_responses_df()
                if isinstance(df, pd.DataFrame) and len(df) > 0:
                    print(f"[OK] Datos cargados desde Sheets: {df.shape}")
                    return df
                print("[WARN] Sheets devolvió DF vacío. Intentando fallback a XLSX...")
            except Exception as e:
                print(f"[WARN] No se pudo leer Sheets ({type(e).__name__}: {e}). Intentando XLSX...")

    # XLSX
    path = xlsx_path or DEFAULT_XLSX
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"No se encontró el Excel local en: {path}\n"
            f"-> Pasa --xlsx \"ruta\" o coloca Resultados Encuesta.xlsx en la raíz del proyecto."
        )

    df = pd.read_excel(path)
    print(f"[OK] Datos cargados desde XLSX: {path}  shape={df.shape}")
    return df


def build_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    df = df.copy()

    if COL_VOTO not in df.columns:
        raise KeyError(f"Falta la columna de voto: '{COL_VOTO}'")

    df[COL_VOTO] = df[COL_VOTO].apply(_canonical_vote)

    df_train = df[df[COL_VOTO].isin([CAND_A, CAND_B])].copy()
    if df_train.empty:
        uniques = df[COL_VOTO].dropna().astype(str).unique().tolist()[:30]
        raise ValueError(
            "No hay filas con voto A/B tras filtrar.\n"
            f"-> Revisa textos exactos de candidatos.\n"
            f"-> Ejemplo de valores vistos (primeros 30): {uniques}"
        )

    y = (df_train[COL_VOTO] == CAND_A).astype(int)

    def safe_num(col: str) -> pd.Series:
        if col not in df_train.columns:
            return pd.Series([np.nan] * len(df_train), index=df_train.index)
        return pd.to_numeric(df_train[col], errors="coerce")

    # ---------- Diferenciales Tuto - Paz (1-5) ----------
    traits = [
        "Experiencia en gestión (1-5)",
        "Honestidad/Transparencia (1-5)",
        "Capacidad de unir a la población (1-5)",
        "Conexión con los jóvenes (1-5)",
        "Liderazgo fuerte/Decisivo (1-5)",
        "Propuestas claras y realistas (1-5)",
        "Coherencia discurso/acciones (1-5)",
        "Empatía con sectores vulnerables (1-5)",
        "Competencia técnica/Académica (1-5)",
        "Cercanía con la realidad boliviana (1-5)",
    ]

    for t in traits:
        col_paz = f"Rodrigo Paz - {t}"
        col_tuto = f"Tuto Quiroga - {t}"
        key = (
            "delta_" + t.replace(" (1-5)", "")
            .replace("/", "_")
            .replace(" ", "_")
            .lower()
        )
        df_train[key] = safe_num(col_tuto) - safe_num(col_paz)

    # ---------- Temas (1-5) ----------
    temas_factores = [
        "Factores decisión: Economía (1-5)",
        "Factores decisión: Educación (1-5)",
        "Factores decisión: Corrupción/Justicia (1-5)",
        "Factores decisión: Servicios públicos (1-5)",
        "Factores decisión: Seguridad ciudadana (1-5)",
        "Factores decisión: Medio ambiente (1-5)",
        "Factores decisión: Derechos sociales (1-5)",
        "Factores decisión: Modelo de desarrollo (1-5)",
    ]
    temas_prioridad = [
        "Prioridad: Crisis económica y desempleo (1-5)",
        "Prioridad: Combustible/recursos energéticos (1-5)",
        "Prioridad: Transporte público (1-5)",
        "Prioridad: Corrupción/Desconfianza institucional (1-5)",
        "Prioridad: Seguridad ciudadana (1-5)",
        "Prioridad: Salud y educación pública (1-5)",
        "Prioridad: Medio ambiente/gestión de residuos (1-5)",
    ]
    for c in temas_factores + temas_prioridad:
        if c in df_train.columns:
            df_train[c] = safe_num(c)

    extra_num = [
        "Interés por la política nacional (slider)",
        "Frecuencia con la que conversas sobre política (slider)",
        "¿Qué tan seguro estás de tu elección? (1-5)",
        "Expectativa de futuro profesional",
        "Mercado laboral: oportunidades para jóvenes",
        "Mercado laboral: demanda de mi carrera",
        "Mercado laboral: accesibilidad a empleos formales",
        "Influencia del pasado del candidato (1-5)",
        "Conocimiento del historial de candidatos (1-5)",
        "Importancia del rol del vicepresidente (1-5)",
    ]
    for c in extra_num:
        if c in df_train.columns:
            df_train[c] = safe_num(c)

    # ---------- Features ----------
    num_cols = [c for c in df_train.columns if c.startswith("delta_")]
    num_cols += [c for c in temas_factores + temas_prioridad + extra_num if c in df_train.columns]

    cat_candidates = [
        "Edad", "Género", "Departamento", "Provincia / Localidad",
        "Situación educativa", "Estrato socioeconómico",
        "Estatus laboral", "Alineamiento ideológico personal",
        "Tiempo de conexión a internet por día",
        "Acceso a servicios básicos",
        "Medio de influencia (selección múltiple)",
        "¿Qué tipo de evento te haría cambiar de opinión respecto a los candidatos?",
    ]
    cat_cols = [c for c in cat_candidates if c in df_train.columns]

    X = df_train[num_cols + cat_cols].copy()
    return X, y


def train_and_export(source: str = "auto", xlsx: str | None = None, target_max_abs: float = 0.8) -> str:
    print(">>> INICIANDO CALIBRACIÓN DE BETAS (LOGIT) <<<")

    df = load_df(source=source, xlsx_path=xlsx)
    df = normalize_df_sheets(df)

    X, y = build_features(df)

    # Separar tipos
    num_cols = [c for c in X.columns if X[c].dtype != "object"]
    cat_cols = [c for c in X.columns if X[c].dtype == "object"]

    # Pipelines
    num_pipe = Pipeline(steps=[
        ("imp", SimpleImputer(strategy="median")),
        ("sc", StandardScaler())
    ])
    cat_pipe = Pipeline(steps=[
        ("imp", SimpleImputer(strategy="most_frequent")),
        ("oh", OneHotEncoder(handle_unknown="ignore"))
    ])

    pre = ColumnTransformer(
        transformers=[
            ("num", num_pipe, num_cols),
            ("cat", cat_pipe, cat_cols)
        ],
        remainder="drop"
    )

    clf = LogisticRegression(
        solver="saga",
        penalty="elasticnet",
        l1_ratio=0.3,
        C=1.0,
        max_iter=5000,
        class_weight="balanced"
    )

    pipe = Pipeline(steps=[("pre", pre), ("clf", clf)])
    pipe.fit(X, y)

    # Diagnóstico simple
    y_pred = pipe.predict(X)
    acc = float(accuracy_score(y, y_pred))
    cm = confusion_matrix(y, y_pred).tolist()

    betas_sim = calibrar_betas_consolidacion(
        pipe=pipe,
        num_cols=num_cols,
        cat_cols=cat_cols,
        df_raw=df,
        target_max_abs=target_max_abs
    )

    betas_sim["diagnostics"] = {
        "n_train": int(len(y)),
        "accuracy_train": acc,
        "confusion_matrix_train": cm,
        "source_used": source,
        "xlsx_used": xlsx or DEFAULT_XLSX
    }

    # Guardar SIEMPRE en src/services/betas_sim.json
    os.makedirs(SERVICES_DIR, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(betas_sim, f, ensure_ascii=False, indent=2)

    print(f"[OK] betas_sim.json actualizado en: {OUT_PATH}")
    print(f"[INFO] accuracy_train={acc:.3f}  n={len(y)}")

    return OUT_PATH


def main():
    parser = argparse.ArgumentParser(description="Calibración de betas (regresión logística) -> betas_sim.json")
    parser.add_argument("--source", choices=["auto", "sheets", "xlsx"], default="auto",
                        help="Origen de datos. auto intenta sheets y cae a xlsx.")
    parser.add_argument("--xlsx", default=None, help="Ruta al Excel local (Resultados Encuesta.xlsx).")
    parser.add_argument("--target_max_abs", type=float, default=0.8,
                        help="Normaliza magnitudes de betas globales al max abs indicado (ej: 0.8).")
    args = parser.parse_args()

    train_and_export(source=args.source, xlsx=args.xlsx, target_max_abs=args.target_max_abs)


if __name__ == "__main__":
    main()
