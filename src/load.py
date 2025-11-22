import logging
from datetime import datetime
from database.config import get_session, init_db
from database.models import Location, Measurement

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AirQualityLoader:
    
    def __init__(self):
        # Créer la base si elle n'existe pas
        init_db()
    
    def load_data(self, locations_df, measurements_df):
        # Charger les données dans SQLite
        session = get_session()
        
        try:
            if locations_df.empty and measurements_df.empty:
                logger.warning("Aucune donnee a charger")
                return

            # Étape 1 : Charger les villes
            logger.info(f"Chargement de {len(locations_df)} locations...")
            
            location_map = {}  # Pour stocker les IDs des villes
            
            for _, row in locations_df.iterrows():
                city = row['city']
                country = row['country']
                
                # Vérifier si la ville existe déjà
                loc = session.query(Location).filter_by(city=city, country=country).first()
                
                if not loc:
                    # Créer une nouvelle ville
                    loc = Location(
                        city=city,
                        country=country,
                        latitude=row['latitude'],
                        longitude=row['longitude']
                    )
                    session.add(loc)
                    session.flush()  # Pour récupérer l'ID
                else:
                    # Mettre à jour les coordonnées si elles ont changé
                    loc.latitude = row['latitude']
                    loc.longitude = row['longitude']
                    loc.last_updated = datetime.utcnow()
                
                location_map[(city, country)] = loc.id
            
            # Étape 2 : Charger les mesures
            logger.info(f"Chargement de {len(measurements_df)} mesures...")
            
            new_count = 0
            for _, row in measurements_df.iterrows():
                loc_key = (row['city'], row['country'])
                
                if loc_key in location_map:
                    loc_id = location_map[loc_key]
                    
                    # Vérifier si la mesure existe déjà (même lieu, paramètre, date)
                    exists = session.query(Measurement).filter_by(
                        location_id=loc_id,
                        parameter=row['parameter'],
                        measurement_date=row['measurement_date']
                    ).first()
                    
                    if not exists:
                        # Ajouter la nouvelle mesure
                        measure = Measurement(
                            location_id=loc_id,
                            parameter=row['parameter'],
                            value=row['value'],
                            unit=row['unit'],
                            measurement_date=row['measurement_date']
                        )
                        session.add(measure)
                        new_count += 1
            
            # Sauvegarder tout d'un coup
            session.commit()
            logger.info(f"Succes : {new_count} nouvelles mesures ajoutees")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur lors du chargement: {e}")
            raise
        finally:
            session.close()
    
    def get_stats(self):
        # Récupérer les stats de la base
        session = get_session()
        try:
            loc_count = session.query(Location).count()
            mes_count = session.query(Measurement).count()
            last_mes = session.query(Measurement).order_by(Measurement.measurement_date.desc()).first()
            
            return {
                'locations': loc_count,
                'measurements': mes_count,
                'last_measurement': last_mes.measurement_date if last_mes else None
            }
        finally:
            session.close()
