from dataclasses import dataclass
from typing import Dict

@dataclass
class Agent:
    agent_id: int
    estado: str            # "A","B","Indeciso","Blanco","Nulo"
    estrato: str
    ideologia: str
    seguridad_1a5: float   
    
    # Guardamos cuánto le importan estos temas (normalizado 0.0 a 1.0)
    intereses: Dict[str, float] 
    
    lealtad: float         # Resistencia al cambio
    suscept: float         # Sensibilidad a redes/entorno

    evento_det: str
    medios: str

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def build_agent(row) -> Agent:
    seg = float(row.get("seguridad_1a5", 3))
    
    # Calculamos lealtad (Firmeza)
    lealtad = clamp01((seg - 1.0) / 4.0)

    # Calculamos susceptibilidad (Redes sociales aumentan exposición)
    medios = str(row.get("medios", "")).lower()
    usa_redes = any(k in medios for k in ["tiktok", "facebook", "instagram", "twitter", "x "])
    base_sus = 1.0 - lealtad
    suscept = clamp01(base_sus + (0.15 if usa_redes else 0.0))

    # Buscamos las columnas de la encuesta "Factores decisión..." y las normalizamos
    def get_interest(col_keyword):
        col_name = next((c for c in row.index if col_keyword in str(c)), None)
        if col_name:
            try:
                val = float(row[col_name]) # Valor 1 a 5
                return (val - 1) / 4.0     # Normalizar a 0..1
            except:
                return 0.5
        return 0.5 # Valor neutro si falta dato

    intereses = {
        "economia": get_interest("Economía"),
        "educacion": get_interest("Educación"),
        "corrupcion": get_interest("Corrupción"),
        "seguridad": get_interest("Seguridad"),
        "ambiente": get_interest("Medio ambiente"),
        "derechos": get_interest("Derechos"),
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