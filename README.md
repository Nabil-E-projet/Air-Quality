# Air Quality Pipeline

Pipeline ETL pour analyser la qualité de l'air en Europe avec visualisation interactive.

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

```bash
# Récupérer les données
python src/pipeline.py

# Lancer le dashboard
python -m streamlit run dashboard/app.py
```

## Fonctionnalités

Le projet récupère les données de pollution atmosphérique pour plusieurs villes européennes via l'API Open-Meteo, les nettoie et les structure dans une base SQLite, puis les affiche dans un dashboard interactif.

**Extraction** : Appels HTTP à l'API Open-Meteo pour récupérer les mesures horaires  
**Transformation** : Nettoyage des données avec Pandas (suppression des valeurs aberrantes, gestion des doublons)  
**Chargement** : Stockage dans SQLite avec SQLAlchemy ORM  
**Visualisation** : Dashboard Streamlit avec graphiques Plotly (évolution temporelle, cartes géographiques)

## Compétences techniques mises en œuvre

- Conception et implémentation d'un pipeline ETL complet
- Intégration d'APIs REST (requêtes HTTP, parsing JSON)
- Manipulation de données avec Pandas (nettoyage, agrégations, transformations)
- Modélisation de base de données relationnelle avec SQLAlchemy
- Visualisation de données avec Plotly (graphiques interactifs, cartes)
- Développement d'interfaces web avec Streamlit

## Stack

Python 3.9+, Pandas, NumPy, SQLAlchemy, Streamlit, Plotly, SQLite

## Structure du projet

```
src/             Code du pipeline ETL
database/        Configuration et modèles de la base
dashboard/       Application Streamlit
data/           Base de données (générée automatiquement)
```

## Données

Polluants mesurés : PM2.5, PM10, NO₂, O₃, SO₂, CO  
Villes surveillées : Paris, Lyon, Marseille, Berlin, Munich, Madrid, Barcelona, Rome, Milan, Brussels, Amsterdam, Zurich
