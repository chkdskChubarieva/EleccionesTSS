# src/services/abm_engine.py
import random
import math
from typing import List, Dict, Any, Optional
from collections import Counter

from src.services.agents import Agent, clamp01
from src.services.shocks import sample_daily_shocks, ElectoralShock


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))


class ABMSimulator:
    def __init__(
        self,
        agents: List[Agent],
        betas: Dict[str, float],
        params: Dict[str, Any],
        steps: int = 12,
        k_contacts: int = 8,
        contagio_umbral: float = 0.60,
        lealtad_estrato: Optional[Dict[str, float]] = None,
        injected_shocks: Optional[Dict[int, List[Dict]]] = None,
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

        # sliders / factores (si no llegan, quedan default)
        self.factor_lealtad = float(self.params.get("factor_lealtad", 1.0))
        self.factor_medios = float(self.params.get("factor_medios", 1.0))
        self.factor_memoria = float(self.params.get("factor_memoria", 0.8))

        self.trace_counts = []
        self.trace_debug = []

    def _global_shares(self) -> Dict[str, float]:
        c = Counter(a.estado for a in self.agents)
        n = float(len(self.agents)) if self.agents else 1.0
        return {k: c.get(k, 0) / n for k in ["A", "B", "Indeciso", "Blanco", "Nulo"]}

    def _effective_lealtad(self, a: Agent) -> float:
        mult = float(self.lealtad_estrato.get(str(a.estrato), 1.0))
        return clamp01(a.lealtad * self.factor_lealtad * mult)

    def _calculate_shock_impact(self, agent: Agent, shocks: List[ElectoralShock]) -> Dict[str, float]:
        bias_A = 0.0
        bias_B = 0.0

        for shock in shocks:
            relevancia = agent.intereses.get(shock.topic, 0.5)

            # ✅ factor_medios: más impacto de propaganda/escándalos
            impacto = shock.magnitude * relevancia * shock.polarity * self.factor_medios

            if shock.target == "A":
                bias_A += impacto
            elif shock.target == "B":
                bias_B += impacto
            elif shock.target == "SISTEMA":
                bias_A += impacto * 0.5
                bias_B += impacto * 0.5

        return {"bias_A": bias_A, "bias_B": bias_B}

    def _contacts(self, idx: int) -> List[Agent]:
        n = len(self.agents)
        if n <= 1:
            return []
        picks = set()
        while len(picks) < min(self.k_contacts, n - 1):
            j = self.rng.randrange(0, n)
            if j != idx:
                picks.add(j)
        return [self.agents[j] for j in picks]

    def run(self):
        w_macro = float(self.params.get("w_macro", 0.20))

        # ✅ memoria: suaviza el macro-clima (persistencia)
        h_prev = 0.5
        mem = clamp01(float(self.factor_memoria))  # 0..1

        for t in range(self.steps):
            shares = self._global_shares()
            sh_state = sample_daily_shocks(self.params, self.injected_shocks.get(t))

            beta0 = float(self.betas.get("beta0", 0.0))
            betaE = float(self.betas.get("betaE", 0.0))
            betaD = float(self.betas.get("betaD", 0.0))
            betaP = float(self.betas.get("betaP", 0.0))
            betaR = float(self.betas.get("betaR", 0.0))

            z_t = (
                beta0
                + betaE * float(sh_state.E)
                + betaD * float(sh_state.D)
                + betaP * float(sh_state.P)
                + betaR * float(sh_state.R)
                + float(sh_state.phi) * (shares["A"] - shares["B"])
            )
            h_raw = sigmoid(z_t)

            # ✅ h_t con memoria (más alto => más inercia)
            h_t = mem * h_prev + (1.0 - mem) * h_raw
            h_prev = h_t

            shares_before = dict(shares)
            n_agents = len(self.agents) if self.agents else 1
            contA_on = 0
            contB_on = 0
            transitions = Counter()

            new_states = []
            for i, a in enumerate(self.agents):
                contacts = self._contacts(i)
                if contacts:
                    fracA = sum(1 for c in contacts if c.estado == "A") / len(contacts)
                    fracB = sum(1 for c in contacts if c.estado == "B") / len(contacts)
                else:
                    fracA, fracB = shares["A"], shares["B"]

                if fracA > self.contagio_umbral:
                    contA_on += 1
                if fracB > self.contagio_umbral:
                    contB_on += 1

                impactos = self._calculate_shock_impact(a, sh_state.active_events)
                bias_A = impactos["bias_A"]
                bias_B = impactos["bias_B"]

                # ✅ lealtad por estrato aplicada
                lealtad_eff = self._effective_lealtad(a)

                base_prob = 0.05 * (1.0 - lealtad_eff)
                macro_push = w_macro * (h_t - 0.5)

                prob_move_A = base_prob + (0.1 * bias_A) + macro_push + (0.15 if fracA > self.contagio_umbral else 0)
                prob_move_B = base_prob + (0.1 * bias_B) - macro_push + (0.15 if fracB > self.contagio_umbral else 0)

                prob_move_A = clamp01(prob_move_A)
                prob_move_B = clamp01(prob_move_B)

                u = self.rng.random()
                current = a.estado
                next_st = current

                if current == "Indeciso":
                    score_A = prob_move_A * (1.0 + a.suscept)
                    score_B = prob_move_B * (1.0 + a.suscept)

                    if u < score_A:
                        next_st = "A"
                    elif u < score_A + score_B:
                        next_st = "B"

                elif current == "A":
                    fuerza_salida = 0.0
                    if bias_A < -0.2:
                        fuerza_salida += abs(bias_A) * 1.5
                    if bias_B > 0.5:
                        fuerza_salida += bias_B * 0.5
                    if fracB > 0.7:
                        fuerza_salida += 0.2

                    prob_leave = clamp01(fuerza_salida * (1.0 - lealtad_eff))
                    if u < prob_leave:
                        next_st = "B" if bias_B > 0.3 else "Indeciso"

                elif current == "B":
                    fuerza_salida = 0.0
                    if bias_B < -0.2:
                        fuerza_salida += abs(bias_B) * 1.5
                    if bias_A > 0.5:
                        fuerza_salida += bias_A * 0.5
                    if fracA > 0.7:
                        fuerza_salida += 0.2

                    prob_leave = clamp01(fuerza_salida * (1.0 - lealtad_eff))
                    if u < prob_leave:
                        next_st = "A" if bias_A > 0.3 else "Indeciso"

                else:
                    if bias_A > 0.6 and u < 0.1:
                        next_st = "A"
                    elif bias_B > 0.6 and u < 0.1:
                        next_st = "B"

                if next_st != current:
                    transitions[f"{current}->{next_st}"] += 1

                new_states.append(next_st)

            for a, ns in zip(self.agents, new_states):
                a.estado = ns

            shares_after = self._global_shares()
            self.trace_counts.append(shares_after)

            debug_info = {
                "t": t,
                "h_t": h_t,
                "z_t": z_t,
                "EDPR": {"E": sh_state.E, "D": sh_state.D, "P": sh_state.P, "R": sh_state.R, "phi": sh_state.phi},
                "events": [f"{ev.target}:{ev.topic} ({ev.polarity})" for ev in sh_state.active_events] if sh_state.active_events else [],
                "rules": {
                    "contagio_umbral": self.contagio_umbral,
                    "contagio_A_ratio": contA_on / n_agents,
                    "contagio_B_ratio": contB_on / n_agents,
                    "w_macro": w_macro,
                    "factor_lealtad": self.factor_lealtad,
                    "factor_medios": self.factor_medios,
                    "factor_memoria": self.factor_memoria,
                },
                "transitions": dict(transitions),
                "shares_before": shares_before,
                "shares_after": shares_after
            }
            self.trace_debug.append(debug_info)

        return self.trace_counts, self.trace_debug
