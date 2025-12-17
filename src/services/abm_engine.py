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
        injected_shocks: Optional[Dict[int, List[Dict]]] = None,  # Ahora es lista de dicts
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
        self.trace_debug = []

    def _global_shares(self) -> Dict[str, float]:
        c = Counter(a.estado for a in self.agents)
        n = float(len(self.agents)) if self.agents else 1.0
        return {k: c.get(k, 0) / n for k in ["A", "B", "Indeciso", "Blanco", "Nulo"]}

    def _calculate_shock_impact(self, agent: Agent, shocks: List[ElectoralShock]) -> Dict[str, float]:
        """
        Calcula cómo afectan los eventos de la semana a ESTE agente específico,
        basado en sus intereses personales.
        Retorna: {"bias_A": float, "bias_B": float} (positivo = a favor, negativo = en contra)
        """
        bias_A = 0.0
        bias_B = 0.0

        for shock in shocks:
            # 1. ¿Cuánto le importa el tema al agente?
            relevancia = agent.intereses.get(shock.topic, 0.5)

            # 2. Fuerza del impacto = Magnitud del evento * Interés del agente
            impacto = shock.magnitude * relevancia * shock.polarity

            # 3. Asignar al target
            if shock.target == "A":
                bias_A += impacto
            elif shock.target == "B":
                bias_B += impacto
            elif shock.target == "SISTEMA":
                # Golpe a ambos (voto nulo/blanco o indeciso)
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
        for t in range(self.steps):
            shares = self._global_shares()

            # Obtener shocks del entorno + inyectados
            sh_state = sample_daily_shocks(self.params, self.injected_shocks.get(t))

            # Factor macro (h_t) que afecta a todos un poco (clima general)
            # Usamos el promedio de polaridad de eventos como proxy para h_t si hay eventos
            macro_trend = 0.0
            if sh_state.active_events:
                # Sumamos polaridad neta hacia A (si target B es neg, suma a A)
                for ev in sh_state.active_events:
                    if ev.target == "A":
                        macro_trend += ev.polarity * ev.magnitude
                    elif ev.target == "B":
                        macro_trend -= ev.polarity * ev.magnitude

            # h_t base + tendencia de eventos
            z_base = self.betas.get("beta0", 0.0) + sh_state.phi * (shares["A"] - shares["B"])
            h_t = sigmoid(z_base + macro_trend * 2.0)

            # --- RF 3.4: contadores (se reinician por semana t) ---
            shares_before = dict(shares)
            n_agents = len(self.agents) if self.agents else 1
            contA_on = 0
            contB_on = 0
            transitions = Counter()

            new_states = []
            for i, a in enumerate(self.agents):
                # === 1. Influencia Social (Contagio) ===
                contacts = self._contacts(i)
                if contacts:
                    fracA = sum(1 for c in contacts if c.estado == "A") / len(contacts)
                    fracB = sum(1 for c in contacts if c.estado == "B") / len(contacts)
                else:
                    fracA, fracB = shares["A"], shares["B"]

                # RF 3.4: contar si se activó umbral (esto NO cambia el modelo, solo registra)
                if fracA > self.contagio_umbral:
                    contA_on += 1
                if fracB > self.contagio_umbral:
                    contB_on += 1

                # === 2. Impacto de Shocks (Personalizado) ===
                impactos = self._calculate_shock_impact(a, sh_state.active_events)
                bias_A = impactos["bias_A"]  # Ej: +0.4 (Noticia buena A)
                bias_B = impactos["bias_B"]  # Ej: -0.8 (Escándalo B)

                # === 3. Probabilidades de Transición ===
                base_prob = 0.05 * (1.0 - a.lealtad)  # Los leales cambian menos

                # Probabilidad de moverse HACIA A o B
                prob_move_A = base_prob + (0.1 * bias_A) + (0.15 if fracA > self.contagio_umbral else 0)
                prob_move_B = base_prob + (0.1 * bias_B) + (0.15 if fracB > self.contagio_umbral else 0)

                prob_move_A = clamp01(prob_move_A)
                prob_move_B = clamp01(prob_move_B)

                # === 4. Lógica de Cambio de Estado ===
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
                        fuerza_salida += abs(bias_A) * 1.5  # Voto castigo
                    if bias_B > 0.5:
                        fuerza_salida += bias_B * 0.5       # Atracción rival
                    if fracB > 0.7:
                        fuerza_salida += 0.2                 # Presión social

                    prob_leave = clamp01(fuerza_salida * (1.0 - a.lealtad))

                    if u < prob_leave:
                        if bias_B > 0.3:
                            next_st = "B"
                        else:
                            next_st = "Indeciso"

                elif current == "B":
                    fuerza_salida = 0.0
                    if bias_B < -0.2:
                        fuerza_salida += abs(bias_B) * 1.5
                    if bias_A > 0.5:
                        fuerza_salida += bias_A * 0.5
                    if fracA > 0.7:
                        fuerza_salida += 0.2

                    prob_leave = clamp01(fuerza_salida * (1.0 - a.lealtad))

                    if u < prob_leave:
                        if bias_A > 0.3:
                            next_st = "A"
                        else:
                            next_st = "Indeciso"

                else:  # Blanco/Nulo
                    if bias_A > 0.6 and u < 0.1:
                        next_st = "A"
                    elif bias_B > 0.6 and u < 0.1:
                        next_st = "B"

                # RF 3.4: registrar flujo (transición) - NO cambia el modelo
                if next_st != current:
                    transitions[f"{current}->{next_st}"] += 1

                new_states.append(next_st)

            # Actualizar agentes
            for a, ns in zip(self.agents, new_states):
                a.estado = ns

            shares_after = self._global_shares()
            self.trace_counts.append(shares_after)

            # Guardar info para el gráfico de escenarios (RF 3.4)
            debug_info = {
                "t": t,
                "h_t": h_t,
                "events": [
                    f"{ev.target}:{ev.topic} ({ev.polarity})"
                    for ev in sh_state.active_events
                ] if sh_state.active_events else [],
                "rules": {
                    "contagio_umbral": self.contagio_umbral,
                    "contagio_A_ratio": contA_on / n_agents,
                    "contagio_B_ratio": contB_on / n_agents
                },
                "transitions": dict(transitions),
                "shares_before": shares_before,
                "shares_after": shares_after
            }
            self.trace_debug.append(debug_info)

        return self.trace_counts, self.trace_debug
