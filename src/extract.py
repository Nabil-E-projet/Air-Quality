import requests
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AirQualityExtractor:
    
    def __init__(self):
        # URL de l'API gratuite Open-Meteo
        self.base_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        self.session = requests.Session()
    
    # Liste des villes qu'on va surveiller
    CITIES = {
        'Paris': {'lat': 48.8566, 'lon': 2.3522, 'country': 'FR'},
        'Lyon': {'lat': 45.7640, 'lon': 4.8357, 'country': 'FR'},
        'Marseille': {'lat': 43.2965, 'lon': 5.3698, 'country': 'FR'},
        'Berlin': {'lat': 52.5200, 'lon': 13.4050, 'country': 'DE'},
        'Munich': {'lat': 48.1351, 'lon': 11.5820, 'country': 'DE'},
        'Madrid': {'lat': 40.4168, 'lon': -3.7038, 'country': 'ES'},
        'Barcelona': {'lat': 41.3851, 'lon': 2.1734, 'country': 'ES'},
        'Rome': {'lat': 41.9028, 'lon': 12.4964, 'country': 'IT'},
        'Milan': {'lat': 45.4642, 'lon': 9.1900, 'country': 'IT'},
        'Brussels': {'lat': 50.8503, 'lon': 4.3517, 'country': 'BE'},
        'Amsterdam': {'lat': 52.3676, 'lon': 4.9041, 'country': 'NL'},
        'Zurich': {'lat': 47.3769, 'lon': 8.5417, 'country': 'CH'},
    }
    
    def extract_latest_measurements(self, countries=['FR', 'DE', 'ES', 'IT'], limit=100):
        # On récupère les données des dernières 24 heures pour chaque ville
        all_measurements = []
        
        # Dates pour les dernières 24h
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=24)
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # Filtrer uniquement les villes des pays qu'on veut
        selected_cities = {
            city: coords for city, coords in self.CITIES.items()
            if coords['country'] in countries
        }
        
        # Pour chaque ville, appeler l'API
        for city_name, coords in selected_cities.items():
            try:
                logger.info(f"Extraction des donnees pour {city_name}...")
                
                # Paramètres de la requête
                params = {
                    'latitude': coords['lat'],
                    'longitude': coords['lon'],
                    'hourly': 'pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone',
                    'start_date': start_str,
                    'end_date': end_str,
                    'timezone': 'auto'
                }
                
                # Appel HTTP GET
                response = self.session.get(self.base_url, params=params, timeout=10)
                response.raise_for_status()  # Erreur si status != 200
                
                data = response.json()
                
                # Parser les données reçues
                measurements = self._parse_measurements(data, city_name, coords['country'])
                all_measurements.extend(measurements)
                
                logger.info(f"{len(measurements)} mesures extraites pour {city_name}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Erreur lors de l'extraction pour {city_name}: {e}")
                continue
        
        logger.info(f"Total de {len(all_measurements)} mesures extraites")
        return all_measurements
    
    def _parse_measurements(self, data, city, country):
        # Transformer le JSON de l'API en liste de dicts exploitables
        measurements = []
        
        if 'hourly' not in data:
            logger.warning(f"Pas de donnees horaires pour {city}")
            return measurements
        
        hourly = data['hourly']
        times = hourly.get('time', [])
        
        if not times:
            logger.warning(f"Pas de timestamps pour {city}")
            return measurements
        
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        # Correspondance entre les noms de l'API et nos noms
        parameters = {
            'pm2_5': {'name': 'pm25', 'unit': 'µg/m³'},
            'pm10': {'name': 'pm10', 'unit': 'µg/m³'},
            'carbon_monoxide': {'name': 'co', 'unit': 'µg/m³'},
            'nitrogen_dioxide': {'name': 'no2', 'unit': 'µg/m³'},
            'sulphur_dioxide': {'name': 'so2', 'unit': 'µg/m³'},
            'ozone': {'name': 'o3', 'unit': 'µg/m³'}
        }
        
        # Pour chaque heure dans les données
        for i, measurement_time in enumerate(times):
            # Pour chaque type de polluant
            for api_param, info in parameters.items():
                if api_param in hourly:
                    values = hourly[api_param]
                    if i < len(values) and values[i] is not None:
                        # Créer un enregistrement
                        measurement = {
                            'city': city,
                            'country': country,
                            'latitude': latitude,
                            'longitude': longitude,
                            'parameter': info['name'],
                            'value': values[i],
                            'unit': info['unit'],
                            'date': measurement_time
                        }
                        measurements.append(measurement)
        
        return measurements
