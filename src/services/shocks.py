# src/services/shocks.py
import math
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .simulador_base import (
    rv_bernoulli, rv_poisson_inverse, rv_normal_ar, rv_triangular_cresc_01, rv_uniform
)

@dataclass
class ShockState:
    E: int      # crisis (0/1)
    D: int      # denuncias (0..)
    P: float    # debate (0..1)
    R: float    # redes (0..1)
    phi: float  # contagio social (0..)
    alpha: float

def sample_daily_shocks(params: Dict[str, Any]) -> ShockState:
    E = rv_bernoulli(params["p_crisis"])
    D = rv_poisson_inverse(params["lam_denuncias"])
    P = rv_normal_ar(params["mu_debate"], params["sigma_debate"], 0.0, 1.0)
    R = rv_triangular_cresc_01()
    phi = rv_uniform(params["phi_min"], params["phi_max"])
    alpha = rv_uniform(params["alpha_min"], params["alpha_max"])
    return ShockState(E=E, D=D, P=P, R=R, phi=phi, alpha=alpha)

def apply_injected_shocks(sh: ShockState, injected: Optional[Dict[str, Any]]) -> ShockState:
    """
    injected ejemplo:
    {"E":1} o {"D_add":3} o {"P_set":0.2} o {"R_set":0.95}
    """
    if not injected:
        return sh

    E = injected.get("E", sh.E)
    D = sh.D + int(injected.get("D_add", 0))
    P = float(injected.get("P_set", sh.P))
    R = float(injected.get("R_set", sh.R))
    phi = float(injected.get("phi_set", sh.phi))
    alpha = float(injected.get("alpha_set", sh.alpha))

    # clamp simple
    P = max(0.0, min(1.0, P))
    R = max(0.0, min(1.0, R))
    return ShockState(E=E, D=D, P=P, R=R, phi=phi, alpha=alpha)
