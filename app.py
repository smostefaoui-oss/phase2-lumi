import streamlit as st
import pandas as pd
import numpy as np
import folium
import fiona
import unidecode
import re
from difflib import get_close_matches
from streamlit_folium import st_folium

# =========================================
# CONFIG
# =========================================
st.set_page_config(layout="wide")
st.title(" GAM Dashboard - Attractivité des Wilayas")

# =========================================
# CLEAN FUNCTION (IMPORTANT)
# =========================================
def clean(x):
    x = unidecode.unidecode(str(x)).upper().strip()
    x = re.sub(r"[^\w\s]", "", x)
    x = re.sub(r"\s+", " ", x)
    return x

# =========================================
#  LOAD DATA
# =========================================
df = pd.read_excel("resultats_GAM.xlsx")
df["wilaya_clean"] = df["wilaya"].apply(clean)

excel_wilayas = df["wilaya_clean"].tolist()

# =========================================
#  KPI
# =========================================
col1, col2, col3 = st.columns(3)

col1.metric("Top Wilaya", df.iloc[0]["wilaya"])
col2.metric("Score max", round(df["score"].max(), 3))
col3.metric("Total agences", int(df["agences_recommandees"].sum()))

# =========================================
#  RANKING
# =========================================
st.subheader(" Ranking national")

st.dataframe(
    df.sort_values("score", ascending=False)[
        ["wilaya", "score", "priorite", "agences_recommandees"]
    ]
)

# =========================================
#  COLOR FUNCTION
# =========================================
def get_color(priority):
    if priority == "Haute":
        return "#d73027"
    elif priority == "Bonne":
        return "#fc8d59"
    elif priority == "Moyenne":
        return "#fee08b"
    else:
        return "#1a9850"

# =========================================
#  MAP INIT
# =========================================
m = folium.Map(location=[28, 2], zoom_start=6)

# =========================================
#  SHAPEFILE LOOP (TON CODE AMÉLIORÉ + SAFE)
# =========================================
with fiona.open("gadm41_DZA.gpkg", layer="ADM_ADM_1") as src:

    for feature in src:
        name = clean(feature["properties"]["NAME_1"])

        # 🔥 fuzzy matching (robuste)
        match_name = get_close_matches(name, excel_wilayas, n=1, cutoff=0.6)

        if match_name:
            match = df[df["wilaya_clean"] == match_name[0]]

            if len(match) > 0:
                row = match.iloc[0]

                color = get_color(row["priorite"])

                tooltip = f"""
                <b>Wilaya:</b> {name}<br>
                <b>Match:</b> {match_name[0]}<br>
                <b>Score:</b> {row['score']:.3f}<br>
                <b>Priorité:</b> {row['priorite']}<br>
                <b>Agences:</b> {int(row['agences_recommandees'])}
                """
            else:
                color = "#cccccc"
                tooltip = f"{name} (no row)"
        else:
            color = "#cccccc"
            tooltip = f"{name} (no match)"

        folium.GeoJson(
            feature,
            style_function=lambda x, c=color: {
                "fillColor": c,
                "color": "black",
                "weight": 1,
                "fillOpacity": 0.75,
            },
            tooltip=folium.Tooltip(tooltip)
        ).add_to(m)

# =========================================
#  LEGEND
# =========================================
legend_html = """
<div style="
position: fixed;
bottom: 30px;
left: 30px;
background-color: white;
padding: 10px;
border:2px solid grey;
z-index:9999;
font-size:14px;
">
<b> Légende Priorité</b><br>
Haute<br>
 Bonne<br>
 Moyenne<br>
 Faible<br>
</div>
"""

m.get_root().html.add_child(folium.Element(legend_html))

# =========================================
# DISPLAY MAP
# =========================================
st.subheader(" Carte d’attractivité")

st_folium(m, width=1200, height=600)

# =========================================
#  RECOMMANDATIONS
# =========================================
st.subheader("Recommandations")

st.dataframe(
    df.sort_values("agences_recommandees", ascending=False)[
        ["wilaya", "agences_recommandees", "score", "priorite"]
    ]
)

# =========================================
#  SIMULATION
# =========================================
st.subheader(" Simulation")

extra = st.slider("Ajouter des agences fictives", 0, 20, 5)

df["new_agences"] = df["agences_gam"] + extra
df["coverage"] = df["population"] / df["new_agences"]

st.dataframe(
    df[["wilaya", "new_agences", "coverage"]].sort_values("coverage")
)
# =========================================
# BUSINESS INTELLIGENCE LAYER (ADD-ON)
# =========================================

st.subheader("Business Insights & Recommendations")

#  estimation CA potentiel par wilaya
df["ca_potentiel"] = df["score"] * df["population"] * 0.01

# ROI simplifié
df["roi_estime"] = (df["ca_potentiel"] - (df["agences_gam"] * 50000)) / (df["agences_gam"] * 50000 + 1)

# RECOMMANDATION EXACTE DU NOMBRE D'AGENCES (IMPORTANT WINNER PART)
# idée : besoin = population / capacité + ajustement par attractivité

CAPACITE_PAR_AGENCE = 15000

df["agences_optimales"] = np.ceil(
    (df["population"] / CAPACITE_PAR_AGENCE) * df["score"]
).astype(int)

# gap (manque ou surplus)
df["gap_agences"] = df["agences_optimales"] - df["agences_gam"]

#  décision automatique
def decision(row):
    if row["agences_optimales"] > row["agences_gam"]:
        return "🟢 INVESTIR - Ouvrir nouvelles agences"
    elif row["gap_agences"] < 0:
        return "🔵 SUR-DENSITÉ - Optimiser réseau"
    else:
        return "🟡 STABLE"

df["decision_business"] = df.apply(decision, axis=1)

# =========================================
#  DECISION STRATEGIQUE (VISIBLE & SIMPLE)
# =========================================

st.subheader(" Strategic Decision (AI Recommendation)")

# =========================================
#  BUSINESS INTELLIGENCE LAYER (FIXED)
# =========================================

st.subheader(" Business Insights & Recommendations")

#  sécurité (évite colonnes vides)
df = df.dropna(subset=["score", "population", "agences_gam"])

# CA potentiel plus réaliste
# (modèle simple : population × score × facteur business)
df["ca_potentiel"] = (df["population"] * df["score"] * 0.02)

# ROI
df["investissement_estime"] = df["agences_gam"] * 50000

df["roi_estime"] = (
    df["ca_potentiel"] - df["investissement_estime"]
) / (df["investissement_estime"] + 1)

# 🏢 capacité par agence (business assumption)
CAPACITE = 15000

df["agences_optimales"] = np.ceil(
    (df["population"] / CAPACITE) * (0.5 + df["score"])
).astype(int)

# 🔥 gap stratégique
df["gap_agences"] = df["agences_optimales"] - df["agences_gam"]

def decision_business(row):
    if row["score"] >= df["score"].quantile(0.66):
        return "INVESTIR"
    elif row["score"] >= df["score"].quantile(0.33):
        return "🟡 SURVEILLER"
    else:
        return "🔴 IGNORER"

df["decision_business"] = df.apply(decision_business, axis=1)

# =========================================
#  DISPLAY CLEAN TABLE
# =========================================

st.dataframe(
    df[[
        "wilaya",
        "score",
        "population",
        "ca_potentiel",
        "agences_optimales",
        "gap_agences",
        "roi_estime",
        "decision_business"
    ]].sort_values("ca_potentiel", ascending=False)
)
# =========================================
#  BUSINESS MAP (NEW - DO NOT TOUCH MAIN MAP)
# =========================================

st.subheader(" Business Insights Map (Strategic Decisions)")

#  couleur selon décision business
def get_business_color(decision):
    if "INVESTIR" in str(decision):
        return "#2ecc71"   # vert
    elif "SURVEILLER" in str(decision):
        return "#f1c40f"   # jaune
    else:
        return "#e74c3c"   # rouge

m2 = folium.Map(location=[28, 2], zoom_start=6)

with fiona.open("gadm41_DZA.gpkg", layer="ADM_ADM_1") as src:

    for feature in src:
        name = clean(feature["properties"]["NAME_1"])

        match_name = get_close_matches(name, excel_wilayas, n=1, cutoff=0.6)

        if match_name:
            match = df[df["wilaya_clean"] == match_name[0]]

            if len(match) > 0:
                row = match.iloc[0]

                color = get_business_color(row["decision_business"])

                tooltip = f"""
                <b>Wilaya:</b> {name}<br>
                <b>Decision:</b> {row['decision_business']}<br>
                <b>Score:</b> {row['score']:.3f}<br>
                <b>Agences optimales:</b> {row['agences_optimales']}<br>
                <b>Gap:</b> {row['gap_agences']}
                """

            else:
                color = "#cccccc"
                tooltip = f"{name} (no data)"
        else:
            color = "#cccccc"
            tooltip = f"{name} (no match)"

        folium.GeoJson(
            feature,
            style_function=lambda x, c=color: {
                "fillColor": c,
                "color": "black",
                "weight": 1,
                "fillOpacity": 0.75,
            },
            tooltip=folium.Tooltip(tooltip)
        ).add_to(m2)

# 🧭 legend business
legend_html2 = """
<div style="
position: fixed;
bottom: 30px;
right: 30px;
background-color: white;
padding: 10px;
border:2px solid grey;
z-index:9999;
font-size:14px;
">
<b>💼 Business Legend</b><br>
 INVESTIR<br>
SURVEILLER<br>
 IGNORER<br>
</div>
"""

m2.get_root().html.add_child(folium.Element(legend_html2))

st_folium(m2, width=1200, height=600) 
# =========================================
# COUVERTURE (DASHBOARD ONLY - EN %)
# =========================================

CAPACITE = 15000  # 1 agence = 15 000 personnes

#  capacité totale avant optimisation
df["capacite_avant"] = df["agences_gam"] * CAPACITE

#  capacité totale après optimisation
df["agences_apres"] = df["agences_gam"] + df["agences_recommandees"]
df["capacite_apres"] = df["agences_apres"] * CAPACITE

#  couverture en POURCENTAGE
df["couverture_avant_pct"] = (df["capacite_avant"] / df["population"]) * 100
df["couverture_apres_pct"] = (df["capacite_apres"] / df["population"]) * 100

# 🔥 sécurité (éviter inf)
df["couverture_avant_pct"] = df["couverture_avant_pct"].replace([np.inf, -np.inf], np.nan)
df["couverture_apres_pct"] = df["couverture_apres_pct"].replace([np.inf, -np.inf], np.nan)

#  amélioration
df["amelioration_couverture_pct"] = (
    df["couverture_apres_pct"] - df["couverture_avant_pct"]
)

# =========================================
#  AFFICHAGE
# =========================================

st.subheader(" Couverture territoriale (%) Avant vs Après")

st.dataframe(
    df[[
        "wilaya",
        "population",
        "agences_gam",
        "agences_recommandees",
        "agences_apres",
        "couverture_avant_pct",
        "couverture_apres_pct",
        "amelioration_couverture_pct"
    ]].sort_values("couverture_apres_pct", ascending=False)
)

col1, col2 = st.columns(2)

col1.metric(
    "Couverture AVANT (%)",
    round(df["couverture_avant_pct"].mean(), 2)
)

col2.metric(
    " Couverture APRÈS (%)",
    round(df["couverture_apres_pct"].mean(), 2)
)
