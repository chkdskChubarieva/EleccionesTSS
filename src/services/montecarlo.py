# src/services/montecarlo.py
import math
import copy
import random
from typing import List, Dict, Any, Optional, Tuple
from statistics import mean, pstdev

from src.services.abm_engine import ABMSimulator
from src.services.agents import Agent

def ic95(vals: List[float]) -> Tuple[float, float, float]:
    m = mean(vals)
    sd = pstdev(vals) if len(vals) > 1 else 0.0
    n = len(vals)
    se = sd / math.sqrt(n) if n > 0 else 0.0
    lo = m - 1.96 * se
    hi = m + 1.96 * se
    return m, lo, hi

def run_montecarlo(
    base_agents: List[Agent],
    betas: Dict[str, float],
    params: Dict[str, Any],
    steps: int,
    n_replicas: int = 1000,
    contagio_umbral: float = 0.60,
    lealtad_estrato: Optional[Dict[str, float]] = None,
    injected_shocks: Optional[Dict[int, Dict[str, Any]]] = None,
    seed: int = 123
):
    if n_replicas < 1000:
        raise ValueError("RF 2.4 exige mínimo 1,000 réplicas.")

    finals_A = []
    finals_B = []
    traces_sample = []  # guardamos algunas réplicas para RF 3.4

    rng = random.Random(seed)

    for r in range(n_replicas):
        # clon profundo de agentes
        agents = copy.deepcopy(base_agents)

        sim = ABMSimulator(
            agents=agents,
            betas=betas,
            params=params,
            steps=steps,
            contagio_umbral=contagio_umbral,
            lealtad_estrato=lealtad_estrato,
            injected_shocks=injected_shocks,
            seed=rng.randrange(1, 10_000_000)
        )
        trace, debug = sim.run()
        fin = trace[-1] if trace else {"A":0,"B":0,"Indeciso":0,"Blanco":0,"Nulo":0}

        finals_A.append(fin["A"])
        finals_B.append(fin["B"])

        if r < 5:  # guardamos pocas para visualizar escenarios luego
            traces_sample.append({"replica": r+1, "trace": trace, "debug": debug})

    mA, loA, hiA = ic95(finals_A)
    mB, loB, hiB = ic95(finals_B)

    return {
        "A": {"mean": mA, "lo95": loA, "hi95": hiA},
        "B": {"mean": mB, "lo95": loB, "hi95": hiB},
        "samples": traces_sample
    }
