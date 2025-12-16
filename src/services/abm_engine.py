# src/services/abm_engine.py
import random
import math
from typing import List, Dict, Any, Optional
from collections import Counter

from src.services.agents import Agent
from src.services.shocks import sample_daily_shocks, apply_injected_shocks

def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

class ABMSimulator:
    def __init__(
        self,
        agents: List[Agent],
        betas: Dict[str, float],
        params: Dict[str, Any],
        steps: int = 60,
        k_contacts: int = 10,
        contagio_umbral: float = 0.60,
        lealtad_estrato: Optional[Dict[str, float]] = None,  # 0..1 por estrato
        injected_shocks: Optional[Dict[int, Dict[str, Any]]] = None,  # {t: {...}}
        seed: int = 42
    ):
        self.rng = random.Random(seed)
        self.agents = agents
        self.betas = betas
        self.params = params
        self.steps = steps
        self.k_contacts = k_contacts
        self.contagio_umbral = contagio_umbral
        self.lealtad_estrato = lealtad_estrato or {}
        self.injected_shocks = injected_shocks or {}

        self.trace_counts = []
        self.trace_debug = []  # para RF 3.4 luego (qué shocks/reglas se activaron)

    def _global_shares(self) -> Dict[str, float]:
        c = Counter(a.estado for a in self.agents)
        n = float(len(self.agents)) if self.agents else 1.0
        return {k: c.get(k, 0) / n for k in ["A","B","Indeciso","Blanco","Nulo"]}

    def _estrato_loyalty(self, a: Agent) -> float:
        # lealtad por estrato (si no existe, neutro)
        base = float(self.lealtad_estrato.get(a.estrato, 0.5))
        return clamp01(base)

    def _event_match_weight(self, a: Agent, sh) -> float:
        """
        Si el agente dijo que cambiaría por corrupción y hoy hay muchas denuncias,
        su suscept aumenta para ese shock.
        """
        ev = (a.evento_det or "").lower()
        w = 1.0
        if "corrup" in ev or "denunc" in ev or "esc" in ev:
            w += 0.20 * min(sh.D, 5)
        if "crisis" in ev or "econom" in ev or "precio" in ev:
            w += 0.40 * sh.E
        if "debate" in ev:
            w += 0.40 * abs(sh.P - 0.5) * 2
        if "red" in ev or "viral" in ev:
            w += 0.50 * sh.R
        return clamp01(w / 3.0 + 0.7)  # reescala suave a ~[0.7..1]

    def _contacts(self, idx: int) -> List[Agent]:
        # contactos aleatorios (puedes luego hacerlo por estrato/ideologia)
        n = len(self.agents)
        if n <= 1:
            return []
        picks = set()
        while len(picks) < min(self.k_contacts, n-1):
            j = self.rng.randrange(0, n)
            if j != idx:
                picks.add(j)
        return [self.agents[j] for j in picks]

    def run(self):
        for t in range(self.steps):
            shares = self._global_shares()
            sh = sample_daily_shocks(self.params)
            sh = apply_injected_shocks(sh, self.injected_shocks.get(t))

            # “impacto macro” estilo tu modelo: h_t inclina a A vs B
            beta0 = self.betas.get("beta0", 0.0)
            betaE = self.betas.get("betaE", 0.0)
            betaD = self.betas.get("betaD", 0.0)
            betaP = self.betas.get("betaP", 0.0)
            betaR = self.betas.get("betaR", 0.0)

            z = (
                beta0
                + betaE * (2 * sh.E - 1)
                + betaD * sh.D
                + betaP * (sh.P - 0.5)
                + betaR * (sh.R - 0.5)
                + sh.phi * (shares["A"] - shares["B"])
            )
            h_t = sigmoid(z)  # prob “macro” pro-A

            # actualización agente por agente
            new_states = []
            for i, a in enumerate(self.agents):
                contacts = self._contacts(i)
                if contacts:
                    fracA = sum(1 for c in contacts if c.estado == "A") / len(contacts)
                    fracB = sum(1 for c in contacts if c.estado == "B") / len(contacts)
                else:
                    fracA, fracB = shares["A"], shares["B"]

                # RF 2.3: Umbral de contagio
                contagio_activo_A = fracA >= self.contagio_umbral
                contagio_activo_B = fracB >= self.contagio_umbral

                # RF 2.3: Lealtad (firmeza + estrato)
                loyalty = clamp01(0.55 * a.lealtad + 0.45 * self._estrato_loyalty(a))
                resistencia = loyalty
                suscept = clamp01(a.suscept * (1.0 - 0.7 * resistencia))

                # RF 2.5: Impacto de shocks por “evento determinante”
                w_evento = self._event_match_weight(a, sh)
                suscept_eff = clamp01(suscept * w_evento)

                # Probabilidades base (manteniendo tu esencia de tasas pequeñas)
                # Las hacemos “micro” y moduladas por shocks (R, E, D, P) como tu modelo
                # Luego las frenamos por lealtad.
                p_to_A = 0.02 + 0.06 * sh.R + 0.10 * (h_t - 0.5)
                p_to_B = 0.02 + 0.06 * sh.R - 0.10 * (h_t - 0.5)
                p_to_A = clamp01(p_to_A * (0.6 + 0.8 * suscept_eff))
                p_to_B = clamp01(p_to_B * (0.6 + 0.8 * suscept_eff))

                # Contagio empuja fuerte si umbral se cumple
                if contagio_activo_A:
                    p_to_A = clamp01(p_to_A + 0.15 * sh.phi)
                if contagio_activo_B:
                    p_to_B = clamp01(p_to_B + 0.15 * sh.phi)

                # Lealtad frena cambios
                p_to_A *= (1.0 - 0.65 * resistencia)
                p_to_B *= (1.0 - 0.65 * resistencia)

                # Reglas por estado actual
                s = a.estado
                u = self.rng.random()

                if s == "Indeciso":
                    # decide A/B o se queda indeciso
                    if u < p_to_A:
                        ns = "A"
                    elif u < p_to_A + p_to_B:
                        ns = "B"
                    else:
                        ns = "Indeciso"

                elif s == "A":
                    # A puede volverse indeciso o pasarse a B si shock golpea
                    flip = clamp01(0.01 + 0.05 * sh.E + 0.02 * min(sh.D, 3))
                    flip *= (0.6 + suscept_eff)
                    flip *= (1.0 - 0.7 * resistencia)
                    if u < flip * 0.70:
                        ns = "Indeciso"
                    elif u < flip:
                        ns = "B"
                    else:
                        ns = "A"

                elif s == "B":
                    # B cambia por debate (como tu idea tau_BA depende de P)
                    flip = clamp01(0.01 + 0.06 * sh.P + 0.02 * min(sh.D, 3))
                    flip *= (0.6 + suscept_eff)
                    flip *= (1.0 - 0.7 * resistencia)
                    if u < flip * 0.70:
                        ns = "Indeciso"
                    elif u < flip:
                        ns = "A"
                    else:
                        ns = "B"

                else:
                    # Blanco/Nulo suelen ser más estables, pero podrían ir a indeciso si hay alta viralización
                    bump = clamp01(0.01 + 0.05 * sh.R)
                    bump *= (0.6 + suscept_eff) * (1.0 - 0.6 * resistencia)
                    ns = "Indeciso" if u < bump else s

                new_states.append(ns)

            # aplicar actualización
            for a, ns in zip(self.agents, new_states):
                a.estado = ns

            self.trace_counts.append(self._global_shares())
            self.trace_debug.append({
                "t": t,
                "shock": {"E": sh.E, "D": sh.D, "P": sh.P, "R": sh.R, "phi": sh.phi, "alpha": sh.alpha},
                "h_t": h_t
            })

        return self.trace_counts, self.trace_debug
