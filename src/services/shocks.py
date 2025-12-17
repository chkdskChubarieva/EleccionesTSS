# src/services/shocks.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from .simulador_base import (
    rv_bernoulli, rv_poisson_inverse, rv_normal_ar, rv_triangular_cresc_01, rv_uniform
)

@dataclass
class ElectoralShock:
    target: str      # "A" (Tuto), "B" (Paz), "SISTEMA" (Todos)
    topic: str       # "economia", "corrupcion", "seguridad", "debate", "redes"
    polarity: float  # -1.0 (Muy Negativo/Escándalo) a +1.0 (Muy Positivo/Logro)
    magnitude: float # 0.0 a 1.0 (Impacto mediático / Cobertura)

    def __post_init__(self):
        # Asegurar rangos lógicos
        self.polarity = max(-1.0, min(1.0, self.polarity))
        self.magnitude = max(0.0, min(1.0, self.magnitude))

@dataclass
class ShockState:
    # Ruido de fondo (Variables latentes del entorno)
    E: int      # Crisis latente
    D: int      # Nivel de denuncia basal
    P: float    # Desempeño debate basal
    R: float    # Viralidad basal
    phi: float  # Coeficiente contagio social
    
    # === Lista de Eventos Específicos de esa semana ===
    active_events: List[ElectoralShock] 

def sample_daily_shocks(params: Dict[str, Any], injected_data: List[Dict] = None) -> ShockState:
    """
    Genera el estado del entorno para una semana 't', combinando
    el ruido aleatorio (Monte Carlo) con los eventos inyectados por el usuario.
    """
    # 1. Generar ruido de fondo (Tu modelo original)
    E = rv_bernoulli(params.get("p_crisis", 0.3))
    D = rv_poisson_inverse(params.get("lam_denuncias", 1.0))
    P = rv_normal_ar(params.get("mu_debate", 0.6), params.get("sigma_debate", 0.15), 0.0, 1.0)
    R = rv_triangular_cresc_01()
    phi = rv_uniform(params.get("phi_min", 0.3), params.get("phi_max", 0.6))
    
    # 2. Procesar Shocks Inyectados (Desde el Dashboard)
    active_events = []
    if injected_data:
        for item in injected_data:
            # item ejemplo: {"target": "B", "topic": "corrupcion", "polarity": -1, "magnitude": 0.9}
            try:
                shock = ElectoralShock(
                    target=item.get("target", "SISTEMA"),
                    topic=item.get("topic", "general"),
                    polarity=float(item.get("polarity", -1.0)),
                    magnitude=float(item.get("magnitude", 0.5))
                )
                active_events.append(shock)
            except Exception as e:
                print(f"Error procesando shock: {e}")

    return ShockState(E=E, D=D, P=P, R=R, phi=phi, active_events=active_events)