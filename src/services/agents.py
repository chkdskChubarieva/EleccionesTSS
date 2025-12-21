# src/services/agents.py
from dataclasses import dataclass
from typing import Dict

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


@dataclass
class Agent:
    agent_id: int
    estado: str            # "A","B","Indeciso","Blanco","Nulo"
    estrato: str
    ideologia: str
    seguridad_1a5: float   

    # Importancia por tema (0.0 a 1.0) — CLAVES ALINEADAS A betas_sim.json
    intereses: Dict[str, float] 

    lealtad: float
    suscept: float

    evento_det: str
    medios: str


def build_agent(row) -> Agent:
    seg = float(row.get("seguridad_1a5", 3))

    # Lealtad (firmeza de voto)
    lealtad = clamp01((seg - 1.0) / 4.0)

    # Susceptibilidad a redes
    medios = str(row.get("medios", "")).lower()
    usa_redes = any(k in medios for k in ["tiktok", "facebook", "instagram", "twitter", "x"])
    base_sus = 1.0 - lealtad
    suscept = clamp01(base_sus + (0.15 if usa_redes else 0.0))

    # Extraer intereses desde encuesta (1-5 → 0-1)
    def get_interest(col_keyword):
        col_name = next((c for c in row.index if col_keyword in str(c)), None)
        if col_name:
            try:
                val = float(row[col_name])
                return (val - 1.0) / 4.0
            except Exception:
                return 0.5
        return 0.5

    # 🔑 TOPICS ALINEADOS A betas_sim.json
    intereses = {
        "economia_empleo": get_interest("Economía"),
        "educacion": get_interest("Educación"),
        "corrupcion_institucional": get_interest("Corrupción"),
        "seguridad_ciudadana": get_interest("Seguridad"),
        "medio_ambiente": get_interest("Medio ambiente"),
        "derechos_sociales": get_interest("Derechos"),
        "salud": get_interest("Salud")
    }

    return Agent(
        agent_id=int(row.get("agent_id", 0)),
        estado=str(row.get("estado_inicial", "Indeciso")),
        estrato=str(row.get("estrato", "Medio")),
        ideologia=str(row.get("ideologia", "Centro")),
        seguridad_1a5=seg,
        intereses=intereses,
        lealtad=lealtad,
        suscept=suscept,
        evento_det=str(row.get("evento_det", "")),
        medios=medios
    )
