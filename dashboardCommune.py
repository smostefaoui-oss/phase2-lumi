import streamlit as st
import pandas as pd
import plotly.express as px

# =========================================
# CONFIG
# =========================================
st.set_page_config(page_title="GAM Dashboard", layout="wide")

st.title("🏆 GAM Assurance - Dashboard Stratégique")

# =========================================
# LOAD DATA
# =========================================

@st.cache_data
def load_data():
    wilaya = pd.read_excel("resultats_GAM_2.xlsx")
    commune = pd.read_excel("resultats_GAM_communes.xlsx")
    return wilaya, commune

df_wilaya, df_commune = load_data()

# =========================================
# SIDEBAR FILTRES
# =========================================

st.sidebar.header("🔎 Filtres")

selected_wilaya = st.sidebar.selectbox(
    "Choisir une wilaya",
    ["Toutes"] + sorted(df_commune["wilaya"].unique().tolist())
)

# filtre
if selected_wilaya != "Toutes":
    df_commune_filtered = df_commune[df_commune["wilaya"] == selected_wilaya]
    df_wilaya_filtered = df_wilaya[df_wilaya["wilaya"] == selected_wilaya]
else:
    df_commune_filtered = df_commune
    df_wilaya_filtered = df_wilaya

# =========================================
# KPIs
# =========================================

st.subheader("📊 Indicateurs clés")

col1, col2, col3 = st.columns(3)

total_agences_wilaya = df_wilaya_filtered["agences_recommandees"].sum()
total_agences_commune = df_commune_filtered["agences_recommandees"].sum()

col1.metric("🏢 Agences (Wilaya)", int(total_agences_wilaya))
col2.metric("🏘️ Agences (Communes)", int(total_agences_commune))
col3.metric("⚖️ Écart", int(total_agences_commune - total_agences_wilaya))

# =========================================
# COMPARAISON WILAYA vs COMMUNE
# =========================================

st.subheader("⚖️ Comparaison Wilaya vs Communes")

comparison = df_commune.groupby("wilaya")["agences_recommandees"].sum().reset_index()
comparison = comparison.merge(
    df_wilaya[["wilaya", "agences_recommandees"]],
    on="wilaya",
    suffixes=("_communes", "_wilaya")
)

comparison["ecart"] = comparison["agences_recommandees_communes"] - comparison["agences_recommandees_wilaya"]

fig = px.bar(
    comparison,
    x="wilaya",
    y=["agences_recommandees_communes", "agences_recommandees_wilaya"],
    barmode="group",
    title="Comparaison des agences recommandées"
)

st.plotly_chart(fig, use_container_width=True)

# =========================================
# DETECTION SUR-ESTIMATION
# =========================================

st.subheader("🚨 Détection des incohérences")

comparison["status"] = comparison["ecart"].apply(
    lambda x: "🔴 Sur-estimation" if x > 0 else "🟢 Cohérent"
)

st.dataframe(comparison)

# =========================================
# TOP WILAYAS
# =========================================

st.subheader("🏆 Top Wilayas")

top_wilayas = df_wilaya.sort_values(by="score", ascending=False).head(10)

fig2 = px.bar(
    top_wilayas,
    x="wilaya",
    y="score",
    title="Top 10 Wilayas (Score TOPSIS)"
)

st.plotly_chart(fig2, use_container_width=True)

# =========================================
# DETAILS COMMUNES


# =========================================
# TABLE DETAILLEE
# =========================================

st.subheader("📋 Table complète")

st.dataframe(df_commune_filtered)

# =========================================
# INSIGHTS AUTOMATIQUES
# =========================================

st.subheader("🧠 Insights automatiques")

sur_estimation = comparison[comparison["ecart"] > 0]

if len(sur_estimation) > 0:
    st.warning(f"{len(sur_estimation)} wilayas ont une sur-estimation au niveau des communes.")
else:
    st.success("Pas de problème de cohérence détecté.")




