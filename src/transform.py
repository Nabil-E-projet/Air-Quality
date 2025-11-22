import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AirQualityTransformer:
    
    def transform(self, raw_data):
        # Nettoyer et structurer les données brutes
        
        if not raw_data:
            logger.warning("Aucune donnee a transformer")
            return pd.DataFrame(), pd.DataFrame()
        
        # Convertir en DataFrame pour faciliter la manipulation
        df = pd.DataFrame(raw_data)
        
        logger.info(f"Debut transformation de {len(df)} lignes")
        
        # 1. Nettoyer les données
        df = df.dropna(subset=['value', 'date'])  # Supprimer les lignes avec valeurs manquantes
        df = df[df['value'] >= 0]  # Garder seulement les valeurs positives
        
        # 2. Convertir les dates en format datetime
        df['measurement_date'] = pd.to_datetime(df['date'])
        
        # 3. Séparer en deux tables : locations et measurements
        
        # Table des villes (sans doublon)
        locations_df = df[['city', 'country', 'latitude', 'longitude']].drop_duplicates()
        
        # Table des mesures
        measurements_df = df[['city', 'country', 'parameter', 'value', 'unit', 'measurement_date']].copy()
        
        logger.info(f"Transformation terminee: {len(locations_df)} villes, {len(measurements_df)} mesures")
        
        return locations_df, measurements_df
    
    def get_aggregated_stats(self, measurements_df):
        # Calculer quelques stats rapides (moyenne par ville/paramètre)
        if measurements_df.empty:
            return pd.DataFrame()
        
        stats = measurements_df.groupby(['city', 'parameter']).agg({
            'value': ['mean', 'min', 'max', 'count']
        }).round(2)
        
        return stats
