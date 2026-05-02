import pandas as pd
import numpy as np

# =========================================
# 🟢 1. CHARGEMENT
# =========================================

df = pd.read_excel("tablecommune.xlsx")

# =========================================
# 🟢 2. NETTOYAGE COLONNES
# =========================================

df.columns = df.columns.str.strip().str.lower()

df = df.rename(columns={
    "WILAYA": "wilaya",    "business-activite": "activite",
    "revenue": "revenu",
    "concurence": "concurrence",
    "agence gam existant": "agences_gam",
    "commune": "commune"   # assure-toi que cette colonne existe
})

# =========================================
# 🟢 3. CONVERSION EN NUMÉRIQUE + CLEAN NaN
# =========================================

cols = ["population", "activite", "revenu", "concurrence", "agences_gam"]

for col in cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# 🔥 supprimer lignes invalides
df = df.dropna(subset=cols)

# =========================================
# 🟢 4. POIDS AHP
# =========================================

weights = np.array([0.416, 0.262, 0.161, 0.099, 0.062])

# =========================================
# 🟢 5. MATRICE
# =========================================

criteria = df[cols].values

# =========================================
# 🟢 6. NORMALISATION
# =========================================

norm = criteria / np.sqrt((criteria**2).sum(axis=0))

# =========================================
# 🟢 7. PONDÉRATION
# =========================================

weighted = norm * weights

# =========================================
# 🟢 8. SOLUTION IDÉALE
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
# 🟢 9. DISTANCES
# =========================================

D_plus = np.sqrt(((weighted - ideal_positive)**2).sum(axis=1))
D_minus = np.sqrt(((weighted - ideal_negative)**2).sum(axis=1))

# =========================================
# 🟢 10. SCORE (SAFE VERSION)
# =========================================

df["score"] = np.where(
    (D_plus + D_minus) == 0,
    0,
    D_minus / (D_plus + D_minus)
)

# =========================================
# 🟢 11. BESOIN AGENCES
# =========================================

df["besoin_total"] = np.ceil(df["population"] / 15000)

df["nouvelles_agences"] = df["besoin_total"] - df["agences_gam"]
df["nouvelles_agences"] = df["nouvelles_agences"].clip(lower=0)

df["agences_recommandees"] = np.round(
    df["nouvelles_agences"] * df["score"]
)

# =========================================
# 🟢 12. 🔥 CORRECTION DU PROBLÈME qcut
# =========================================

df = df.dropna(subset=["score"])

# si tous les scores sont presque identiques → problème qcut
if df["score"].nunique() < 4:
    df["priorite"] = "🟡 Moyen (insuffisant pour découpe)"
else:
    df["priorite"] = pd.qcut(
        df["score"],
        q=4,
        labels=["🔴 Faible", "🟠 Moyenne", "🟡 Bonne", "🟢 Haute"],
        duplicates="drop"
    )
# =========================================
# 13. SECTION IA : OPTIMISATION DU RÉSEAU  ← ICI, APRÈS le scoring
# =========================================
def optimisation_reseau(df,
                         seuil_concurrence=5,
                         seuil_gam=2):
    decisions = []
    raisons = []

    for _, row in df.iterrows():
        raison = []
        ouvrir = True

        # Règle 1 : Score trop faible
        if row["score"] < 0.3:
            ouvrir = False
            raison.append("Score TOPSIS trop faible")

        # Règle 2 : Trop de concurrents
        if row["concurrence"] > seuil_concurrence:
            ouvrir = False
            raison.append(f"Trop de concurrents ({int(row['concurrence'])})")

        # Règle 3 : Déjà bien couvert par GAM
        besoin = row["population"] / 15000
        if row["agences_gam"] >= besoin:
            ouvrir = False
            raison.append("Déjà suffisamment couvert par GAM")

        # Règle 4 : Bonus zone stratégique
        if row["concurrence"] <= 2 and row["score"] >= 0.6:
            raison.append("Zone stratégique : faible concurrence + fort potentiel")

        decisions.append("OUVRIR" if ouvrir else "REJETER")
        raisons.append(" | ".join(raison) if raison else "Conditions favorables")

    df["decision"] = decisions
    df["raison"] = raisons
    return df

# Appliquer l'optimisation
df = optimisation_reseau(df)

# =========================================
# =========================================
# 14. TRI FINAL
# =========================================
# Garder l'ordre original (wilayas groupées comme l'input)
df = df.sort_values(by=["wilaya", "score"], ascending=[True, False])

# =========================================
# 15. EXPORT  ← decision + raison inclus automatiquement
# =========================================
df.to_excel("resultats_GAM_communes.xlsx", index=False)
print("SUCCESS : fichier généré → resultats_GAM_communes.xlsx")
