import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os
from sqlalchemy import text

# Ajout du chemin racine pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.config import get_engine, init_db
from database.load_demo import load_demo_data

# Initialiser automatiquement la base de données au premier lancement
init_db()

# Si la base est vide, charger les données de démo
try:
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM measurements"))
        count = result.fetchone()[0]
        if count == 0:
            load_demo_data()
except:
    pass  # Ignorer les erreurs silencieusement

# Configuration de la page
st.set_page_config(
    page_title="Air Quality Dashboard",
    page_icon="🌍",
    layout="wide"
)

# Fonction de chargement des données (mise en cache)
@st.cache_data(ttl=300)  # Cache pour 5 minutes
def load_data():
    """Charge les données depuis la base SQLite"""
    engine = get_engine()
    
    query = """
    SELECT 
        l.city, 
        l.country, 
        l.latitude, 
        l.longitude,
        m.parameter, 
        m.value, 
        m.unit, 
        m.measurement_date
    FROM measurements m
    JOIN locations l ON m.location_id = l.id
    ORDER BY m.measurement_date DESC
    """
    
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
            # Conversion explicite des dates
            df['measurement_date'] = pd.to_datetime(df['measurement_date'])
            return df
    except Exception as e:
        st.error(f"Erreur de connexion à la base de données: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_statistics():
    """Récupère les statistiques générales."""
    engine = get_engine()
    
    with engine.connect() as conn:
        # Nombre total de mesures
        result = conn.execute(text("SELECT COUNT(*) FROM measurements"))
        total_measurements = result.fetchone()[0]
        
        # Nombre de villes
        result = conn.execute(text("SELECT COUNT(DISTINCT city) FROM locations"))
        total_cities = result.fetchone()[0]
        
        # Nombre de pays
        result = conn.execute(text("SELECT COUNT(DISTINCT country) FROM locations"))
        total_countries = result.fetchone()[0]
        
        # Dernière mise à jour
        result = conn.execute(text("SELECT MAX(measurement_date) FROM measurements"))
        last_update = result.fetchone()[0]
        
        # Conversion string -> datetime si nécessaire (SQLite stocke les dates en string)
        if isinstance(last_update, str):
            try:
                last_update = datetime.strptime(last_update, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                try:
                    last_update = datetime.strptime(last_update, "%Y-%m-%d %H:%M:%S")
                except:
                    pass
    
    return {
        'total_measurements': total_measurements,
        'total_cities': total_cities,
        'total_countries': total_countries,
        'last_update': last_update
    }

def main():
    """Application principale du dashboard."""
    # En-tête
    st.title("🌍 Tableau de Bord - Qualité de l'Air")
    st.markdown("**Analyse en temps réel des données de pollution atmosphérique**")
    st.markdown("---")
    
    try:
        # Chargement des données
        with st.spinner('Chargement des données...'):
            df = load_data()
            stats = get_statistics()
        
        if df.empty:
            st.warning("⚠️ Aucune donnée disponible. Veuillez exécuter le pipeline ETL d'abord.")
            st.code("python src/pipeline.py", language="bash")
            return
        
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Mesures", f"{stats['total_measurements']:,}")
        
        with col2:
            st.metric("Villes", stats['total_cities'])
        
        with col3:
            st.metric("Pays", stats['total_countries'])
        
        with col4:
            if stats['last_update']:
                st.metric("Dernière MAJ", stats['last_update'].strftime("%d/%m/%Y"))
        
        st.markdown("---")
        
        # Filtres
        st.sidebar.header("Filtres")
        
        # Filtre par pays
        countries = sorted(df['country'].unique())
        selected_countries = st.sidebar.multiselect(
            "Pays",
            options=countries,
            default=countries[:3] if len(countries) > 3 else countries
        )
        
        # Filtre par paramètre
        parameters = sorted(df['parameter'].unique())
        selected_param = st.sidebar.selectbox(
            "Polluant",
            options=parameters,
            index=0
        )
        
        # Filtrer les données
        filtered_df = df[
            (df['country'].isin(selected_countries)) &
            (df['parameter'] == selected_param)
        ]
        
        if filtered_df.empty:
            st.warning("Aucune donnée pour les filtres sélectionnés.")
            return
        
        # GRAPHIQUE 1: Évolution temporelle
        st.subheader(f"📈 Évolution de {selected_param.upper()} dans le temps")
        
        fig_time = px.line(
            filtered_df,
            x='measurement_date',
            y='value',
            color='city',
            title=f"Concentration de {selected_param.upper()} par ville",
            labels={'value': f'{selected_param.upper()} ({filtered_df["unit"].iloc[0]})', 
                    'measurement_date': 'Date'}
        )
        fig_time.update_layout(height=400)
        st.plotly_chart(fig_time, width='stretch')
        
        # GRAPHIQUE 2: Comparaison par ville
        st.subheader(f"🏙️ Comparaison par ville - {selected_param.upper()}")
        
        city_avg = filtered_df.groupby('city')['value'].mean().sort_values(ascending=False).head(10)
        
        fig_bar = px.bar(
            x=city_avg.index,
            y=city_avg.values,
            title=f"Moyenne de {selected_param.upper()} par ville",
            labels={'x': 'Ville', 'y': f'{selected_param.upper()} moyen ({filtered_df["unit"].iloc[0]})'},
            color=city_avg.values,
            color_continuous_scale='RdYlGn_r'
        )
        fig_bar.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_bar, width='stretch')
        
        # GRAPHIQUE 3: Carte géographique
        st.subheader(f"🗺️ Carte de la pollution - {selected_param.upper()}")
        
        # Données agrégées par ville
        map_data = filtered_df.groupby(['city', 'country', 'latitude', 'longitude']).agg({
            'value': 'mean'
        }).reset_index()
        
        map_data = map_data.dropna(subset=['latitude', 'longitude'])
        
        if not map_data.empty:
            fig_map = px.scatter_geo(
                map_data,
                lat='latitude',
                lon='longitude',
                size='value',
                color='value',
                hover_name='city',
                hover_data={'country': True, 'value': ':.2f'},
                title=f"Concentration moyenne de {selected_param.upper()}",
                color_continuous_scale='RdYlGn_r',
                size_max=30
            )
            fig_map.update_geos(
                scope='europe',
                showcountries=True,
                countrycolor="lightgray"
            )
            fig_map.update_layout(height=750)  # Carte plus grande
            st.plotly_chart(fig_map, width='stretch')
        
        # Tableau de données
        st.subheader("📊 Données détaillées")
        
        # Top 10 villes les plus polluées
        top_cities = filtered_df.groupby('city').agg({
            'value': ['mean', 'max', 'min', 'count']
        }).round(2)
        top_cities.columns = ['Moyenne', 'Maximum', 'Minimum', 'Nb mesures']
        top_cities = top_cities.sort_values('Moyenne', ascending=False).head(10)
        
        st.dataframe(top_cities, width='stretch')
        
        # Explications sur les polluants
        with st.expander("🔬 Qu'est-ce que ces polluants ?"):
            st.markdown("""
            ### PM2.5 (Particules fines)
            Minuscules particules < 2.5 µm. **Sources** : Trafic routier, chauffage au bois, industrie.  
            **Risques** : Pénètrent profondément dans les poumons, problèmes respiratoires.
            
            ### PM10 (Particules)
            Particules < 10 µm. **Sources** : Poussières, chantiers, combustion.  
            **Risques** : Irritations respiratoires, allergies.
            
            ### NO₂ (Dioxyde d'azote)
            Gaz irritant. **Sources** : Voitures diesel, centrales thermiques.  
            **Risques** : Inflammation des voies respiratoires, aggrave l'asthme.
            
            ### O₃ (Ozone)
            Gaz formé par réaction chimique. **Sources** : Pollution + soleil.  
            **Risques** : Irritation des yeux, toux, essoufflement.
            
            ### SO₂ (Dioxyde de soufre)
            Gaz acide. **Sources** : Combustion charbon/pétrole, industrie.  
            **Risques** : Brûlures respiratoires, pluies acides.
            
            ### CO (Monoxyde de carbone)
            Gaz inodore toxique. **Sources** : Combustion incomplète (voitures, chauffage).  
            **Risques** : Réduit l'oxygène dans le sang, maux de tête, vertiges.
            """)
        
        # Source des données
        with st.expander("📡 Source des données"):
            st.markdown("""
            **API** : Open-Meteo Air Quality API (gratuit, temps réel)  
            **Mise à jour** : Données des dernières 48 heures  
            **Technologie** : Pipeline ETL automatisé avec Python + SQLite
            """)
    
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des données: {e}")
        st.info("Assurez-vous que la base de données est accessible et que le pipeline a été exécuté.")

if __name__ == "__main__":
    main()
