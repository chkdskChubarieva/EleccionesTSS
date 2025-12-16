# src/services/agents.py
from dataclasses import dataclass
import random

@dataclass
class Agent:
    agent_id: int
    estado: str            # "A","B","Indeciso","Blanco","Nulo"
    estrato: str
    ideologia: str
    seguridad_1a5: float   # 1..5
    evento_det: str
    medios: str

    # derivados
    lealtad: float         # 0..1 (resistencia al cambio)
    suscept: float         # 0..1 (sensibilidad a contagio/shocks)

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def build_agent(row) -> Agent:
    seg = float(row["seguridad_1a5"])

    # Firmeza: 1..5 -> 0..1 (más alto = más leal)
    lealtad = clamp01((seg - 1.0) / 4.0)

    # Susceptibilidad: inversa de lealtad + ajuste si usa redes
    medios = str(row.get("medios", "")).lower()
    usa_redes = any(k in medios for k in ["tiktok", "facebook", "instagram", "red", "social"])
    base_sus = 1.0 - lealtad
    suscept = clamp01(base_sus + (0.15 if usa_redes else 0.0))

    return Agent(
        agent_id=int(row["agent_id"]),
        estado=str(row["estado_inicial"]),
        estrato=str(row["estrato"]),
        ideologia=str(row["ideologia"]),
        seguridad_1a5=seg,
        evento_det=str(row["evento_det"]),
        medios=str(row.get("medios", "")),
        lealtad=lealtad,
        suscept=suscept
    )
