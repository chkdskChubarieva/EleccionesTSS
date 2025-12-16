
import math
import random
from typing import Callable, List, Tuple, Dict

SQRT2 = math.sqrt(2.0)
TWOPI = 2.0 * math.pi

def comb(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    k = min(k, n - k)
    num = 1
    den = 1
    for i in range(1, k + 1):
        num *= n - (k - i)
        den *= i
    return num // den

def phi_norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / SQRT2))


# Bernoulli(p)
def rv_bernoulli(p: float) -> int:
    """Bernoulli(p), retorna 1 con prob p, si no 0."""
    r = random.random()
    return 1 if r < p else 0

# Poisson(λ) Transformada inversa
def rv_poisson_inverse(lam: float) -> int:
    f0 = math.exp(-lam)
    acc = f0
    r = random.random()
    if r <= acc:
        return 0
    k = 0
    fk = f0
    while acc < r:
        k += 1
        fk = fk * lam / k
        acc += fk
    return k

def rv_poisson_knuth(lam: float) -> int:
    L = math.exp(-lam)
    k = 0
    p = 1.0
    while True:
        k += 1
        p *= random.random()
        if p <= L:
            return k - 1

# Normal(mu, sigma) Aceptación–Rechazo con propuesta Uniforme en [a,b]
def rv_normal_ar(mu: float, sigma: float, a: float = -math.inf, b: float = math.inf) -> float:
   
    if not math.isfinite(a) or not math.isfinite(b):
        a = mu - 6.0 * sigma
        b = mu + 6.0 * sigma
        
    fmax = 1.0 / (sigma * math.sqrt(2.0 * math.pi))
    while True:
        r1 = random.random()
        r2 = random.random()
        x = a + (b - a) * r1
      
        fx = (1.0 / (sigma * math.sqrt(2.0 * math.pi))) * math.exp(-0.5 * ((x - mu) / sigma) ** 2)
        if r2 <= (fx / fmax):
            return x


def rv_normal_boxmuller(mu: float, sigma: float) -> float:
    """Normal(mu,sigma) por Box–Muller (retorna 1 muestra)."""
    u1 = random.random()  # (0,1)
    u2 = random.random()
    z = math.sqrt(-2.0 * math.log(u1)) * math.cos(TWOPI * u2)  # N(0,1)
    return mu + sigma * z

# Triangular creciente en [0,1] f(x)=2x Transformada Inversa
def rv_triangular_cresc_01() -> float:
    u = random.random()
    return math.sqrt(u)

# Uniforme(a,b)
def rv_uniform(a: float, b: float) -> float:
    """Uniforme(a,b) directo desde U(0,1)."""
    u = random.random()
    return a + (b - a) * u

# pi_A(t+1) = (1-α)pi_A(t) + α h_t

def h_impact(
    E_t: int, D_t: int, P_t: float, R_t: float,
    phi: float, sA_t: float,
    beta0: float, betaE: float, betaD: float, betaP: float, betaR: float,
    gD: Callable[[int], float] = lambda d: min(d, 3)
) -> float:
    """
    Función de impacto h_t
    """
    z = (beta0
         + betaE * (2 * E_t - 1)
         + betaD * gD(D_t)
         + betaP * (P_t - 0.5)
         + betaR * (R_t - 0.5)
         + phi * (sA_t - 0.5))
    return 1.0 / (1.0 + math.exp(-z))

class SimuladorElectoral:
    """
    pi_A(t+1) = (1 - alpha) * pi_A(t) + alpha * h(E_t, D_t, P_t, R_t; phi, sA(t))
    pi_B(t) = 1 - pi_A(t)
    """
    def __init__(
        self,
        piA0: float,
        # parámetros variable aleatoria
        p_crisis: float = 0.40,          # Bernoulli para E_t (evento crisis)
        lam_denuncias: float = 1.0,      # Poisson para D_t
        mu_debate: float = 0.6,          # Normal para P_t
        sigma_debate: float = 0.15,
        alpha_min: float = 0.2,          # α Uniforme(alpha_min, alpha_max)
        alpha_max: float = 0.4,
        phi_min: float = 0.3,            # φ Uniforme(phi_min, phi_max)
        phi_max: float = 0.6,
        usar_box_muller: bool = False,
        truncar_debate_01: bool = True,  # Recortar P_t a [0,1]
        # betas de h(.)
        beta0: float = 0.0,
        betaE: float = 0.5,
        betaD: float = 0.25,
        betaP: float = 0.8,
        betaR: float = 0.8,
    ):
        self.piA = piA0
        self.p_crisis = p_crisis
        self.lam_denuncias = lam_denuncias
        self.mu_debate = mu_debate
        self.sigma_debate = sigma_debate
        self.alpha_min = alpha_min
        self.alpha_max = alpha_max
        self.phi_min = phi_min
        self.phi_max = phi_max
        self.usar_box_muller = usar_box_muller
        self.truncar_debate_01 = truncar_debate_01
        # betas
        self.beta0 = beta0
        self.betaE = betaE
        self.betaD = betaD
        self.betaP = betaP
        self.betaR = betaR

    def _generar_shocks(self) -> Tuple[int, int, float, float, float, float]:
        E_t = rv_bernoulli(self.p_crisis)
        D_t = rv_poisson_inverse(self.lam_denuncias)
        if self.usar_box_muller:
            P_t = rv_normal_boxmuller(self.mu_debate, self.sigma_debate)
        else:
            P_t = rv_normal_ar(self.mu_debate, self.sigma_debate, a=0.0, b=1.0)
        if self.truncar_debate_01:
            P_t = min(1.0, max(0.0, P_t))
        R_t = rv_triangular_cresc_01()
     
        phi = rv_uniform(self.phi_min, self.phi_max)
        alpha = rv_uniform(self.alpha_min, self.alpha_max)
        return E_t, D_t, P_t, R_t, phi, alpha

    def step(self, sA_t: float = None) -> Dict[str, float]:
        """
        Ejecuta un paso de tiempo. (Iteración)
        """
        if sA_t is None:
            sA_t = self.piA
        E_t, D_t, P_t, R_t, phi, alpha = self._generar_shocks()
        h_t = h_impact(
            E_t, D_t, P_t, R_t, phi, sA_t,
            self.beta0, self.betaE, self.betaD, self.betaP, self.betaR
        )
        piA_next = (1.0 - alpha) * self.piA + alpha * h_t
        self.piA = piA_next
        return {
            "E_t": E_t, "D_t": D_t, "P_t": P_t, "R_t": R_t,
            "phi": phi, "alpha": alpha,
            "h_t": h_t, "piA_next": piA_next, "piB_next": 1.0 - piA_next
        }

    def run(self, T: int, sA_rule: Callable[[float, int], float] = None) -> List[Dict[str, float]]:
      
        trace = []
        for t in range(T):
            sA_t = self.piA if sA_rule is None else sA_rule(self.piA, t)
            info = self.step(sA_t=sA_t)
            info["t"] = t + 1
            trace.append(info)
        return trace


if __name__ == "__main__":
    random.seed(42) 

    sim = SimuladorElectoral(
        piA0=0.48,
        p_crisis=0.40,
        lam_denuncias=1.0,
        mu_debate=0.6,
        sigma_debate=0.15,
        alpha_min=0.2, alpha_max=0.4,
        phi_min=0.3, phi_max=0.6,
        usar_box_muller=False,
        truncar_debate_01=True,
        beta0=0.0, betaE=0.5, betaD=0.25, betaP=0.8, betaR=0.8
    )

    trace = sim.run(T=12)
    print("Último estado:")
    print(trace[-1])

