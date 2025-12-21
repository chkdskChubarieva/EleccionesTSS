# src/services/shocks.py
from dataclasses import dataclass
from typing import List, Dict, Any
from .simulador_base import (
    rv_bernoulli, rv_poisson_inverse, rv_normal_ar,
    rv_triangular_cresc_01, rv_uniform
)


@dataclass
class ElectoralShock:
    target: str      # "A", "B", "SISTEMA"
    topic: str       # CLAVES ALINEADAS A betas_sim.json
    polarity: float  # -1.0 a +1.0
    magnitude: float # 0.0 a 1.0

    def __post_init__(self):
        self.polarity = max(-1.0, min(1.0, self.polarity))
        self.magnitude = max(0.0, min(1.0, self.magnitude))


@dataclass
class ShockState:
    E: int
    D: int
    P: float
    R: float
    phi: float
    active_events: List[ElectoralShock]


def sample_daily_shocks(params: Dict[str, Any], injected_data: List[Dict] = None) -> ShockState:
    # Ruido de fondo (tu modelo original)
    E = rv_bernoulli(params.get("p_crisis", 0.3))
    D = rv_poisson_inverse(params.get("lam_denuncias", 1.0))
    P = rv_normal_ar(params.get("mu_debate", 0.6), params.get("sigma_debate", 0.15), 0.0, 1.0)
    R = rv_triangular_cresc_01()
    phi = rv_uniform(params.get("phi_min", 0.3), params.get("phi_max", 0.6))

    active_events = []

    # Shocks inyectados desde UI
    if injected_data:
        for item in injected_data:
            try:
                active_events.append(ElectoralShock(
                    target=item.get("target", "SISTEMA"),
                    topic=item.get("topic", "economia_empleo"),
                    polarity=float(item.get("polarity", -1.0)),
                    magnitude=float(item.get("magnitude", 0.5))
                ))
            except Exception as e:
                print(f"Error procesando shock: {e}")

    return ShockState(
        E=E, D=D, P=P, R=R,
        phi=phi,
        active_events=active_events
    )
