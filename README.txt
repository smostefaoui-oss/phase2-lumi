## Génération des fichiers
python3 neww.py

→ génère :

resultats_GAM.xlsx
resultats_GAM_business.xlsx
### Niveau commune

python3 codecommunes.py

→ génère :

* resultats_GAM_communes.xlsx

---

### Niveau wilaya

python3 codewilaya.py

→ génère :

* resultats_GAM_2.xlsx

---

## Dashboards

### Dashboard global

python3 -m streamlit run add.py

→ permet de visualiser :

* classement des wilayas
* carte d’attractivité
* recommandations d’agences
* analyse ROI
* couverture territoriale (%)
* décisions stratégiques

---

### Dashboard communes

python3 -m streamlit run dashboardCommune.py

→ permet de visualiser :

* indicateurs clés
* comparaisons wilaya /communes
* détection des incohérences
* table complete 
---

## Remarque

## Chaque script python génère automatiquement des fichiers Excel utilisés par 
les dashboards.



