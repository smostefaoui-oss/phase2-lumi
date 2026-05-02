import pandas as pd
import numpy as np

# =========================================
# 1. CHARGEMENT
# =========================================

df = pd.read_excel("DATAS.xlsx")

# =========================================
# 2. NETTOYAGE COLONNES
# =========================================

df.columns = df.columns.str.strip().str.lower()

df = df.rename(columns={
    "business-activite": "activite",
    "revenue": "revenu",
    "concurence": "concurrence",
    "agence gam existant": "agences_gam"
})

# =========================================
#  3. CONVERSION EN NUMÉRIQUE + CLEAN NaN
# =========================================

cols = ["population", "activite", "revenu", "concurrence", "agences_gam"]

for col in cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# supprimer lignes invalides
df = df.dropna(subset=cols)

# =========================================
# 4. POIDS AHP
# =========================================

weights = np.array([0.416, 0.262, 0.161, 0.099, 0.062])

# =========================================
#  5. MATRICE
# =========================================

criteria = df[cols].values

# =========================================
#  6. NORMALISATION
# =========================================

norm = criteria / np.sqrt((criteria**2).sum(axis=0))

# =========================================
#  7. PONDÉRATION
# =========================================

weighted = norm * weights

# =========================================
#  8. SOLUTION IDÉALE
# =========================================

ideal_positive = np.array([
    weighted[:,0].max(),
    weighted[:,1].max(),
    weighted[:,2].max(),
    weighted[:,3].min(),
    weighted[:,4].min()
])

ideal_negative = np.array([
    weighted[:,0].min(),
    weighted[:,1].min(),
    weighted[:,2].min(),
    weighted[:,3].max(),
    weighted[:,4].max()
])

# =========================================
#  9. DISTANCES
# =========================================

D_plus = np.sqrt(((weighted - ideal_positive)**2).sum(axis=1))
D_minus = np.sqrt(((weighted - ideal_negative)**2).sum(axis=1))

# =========================================
#  10. SCORE (SAFE VERSION)
# =========================================

df["score"] = np.where(
    (D_plus + D_minus) == 0,
    0,
    D_minus / (D_plus + D_minus)
)

# =========================================
#  11. BESOIN AGENCES
# =========================================

df["besoin_total"] = np.ceil(df["population"] / 15000)

df["nouvelles_agences"] = df["besoin_total"] - df["agences_gam"]
df["nouvelles_agences"] = df["nouvelles_agences"].clip(lower=0)

df["agences_recommandees"] = np.round(
    df["nouvelles_agences"] * df["score"]
)

# =========================================
# 12.  CORRECTION DU PROBLÈME qcut
# =========================================

df = df.dropna(subset=["score"])

# si tous les scores sont presque identiques → problème qcut
if df["score"].nunique() < 4:
    df["priorite"] = "Moyen (insuffisant pour découpe)"
else:
    df["priorite"] = pd.qcut(
        df["score"],
        q=4,
        labels=["Faible", "Moyenne", "Bonne", "Haute"],
        duplicates="drop"
    )

# =========================================
# 13. TRI FINAL
# =========================================

df = df.sort_values(by="score", ascending=False)

# =========================================
#  14. EXPORT
# =========================================

df.to_excel("resultats_GAM.xlsx", index=False)

# =========================================
#  15. BUSINESS LAYER 
# =========================================

#  estimation simple du chiffre d'affaires potentiel par wilaya
# (hypothèse business : revenu moyen impacté par score + activité)

df["ca_potentiel"] = df["revenu"] * (1 + df["score"])

#  ROI estimé (très important pour jury business)
df["roi_estime"] = (df["ca_potentiel"] - df["revenu"]) / df["revenu"]

#  décision stratégique automatique
def decision(row):
    if row["score"] > 0.65 and row["agences_recommandees"] > 0:
        return "INVESTIR (Zone prioritaire)"
    elif row["score"] > 0.5:
        return "🟡 SURVEILLER (potentiel moyen)"
    else:
        return "🔴 NE PAS PRIORISER"

df["decision_business"] = df.apply(decision, axis=1)

#  segmentation business simple
df["segment"] = pd.cut(
    df["score"],
    bins=[0, 0.4, 0.6, 1],
    labels=["Faible potentiel", "Moyen potentiel", "Fort potentiel"]
)

# ranking business final
df["business_rank"] = df["score"].rank(ascending=False)

df.to_excel("resultats_GAM.xlsx", index=False)
df.to_excel("resultats_GAM_business.xlsx", index=False)
