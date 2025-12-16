def sensitivity_by_estrato(df):
    """
    Devuelve por estrato el factor con mayor “poder” (proxy):
    |mean(corrupcion)| vs |mean(economia)|
    """
    COL_ESTRATO = "Estrato socioeconómico"
    C_ECO = "Factores decisión: Economía (1-5)"
    C_COR = "Factores decisión: Corrupción/Justicia (1-5)"

    out = []
    if COL_ESTRATO not in df.columns:
        return out

    for est, sub in df.groupby(COL_ESTRATO):
        eco = sub.get(C_ECO, 0)
        cor = sub.get(C_COR, 0)

        eco_m = float(eco.astype(float).mean()) if len(sub) else 0
        cor_m = float(cor.astype(float).mean()) if len(sub) else 0

        if abs(cor_m) >= abs(eco_m):
            out.append({"estrato": str(est), "factor": "Corrupción/Justicia", "coef": cor_m})
        else:
            out.append({"estrato": str(est), "factor": "Economía", "coef": eco_m})

    return out
