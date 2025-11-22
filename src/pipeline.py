import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime
from extract import AirQualityExtractor
from transform import AirQualityTransformer
from load import AirQualityLoader

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ETLPipeline:
    
    def __init__(self):
        self.extractor = AirQualityExtractor()
        self.transformer = AirQualityTransformer()
        self.loader = AirQualityLoader()
    
    def run(self, countries=['FR', 'DE', 'ES', 'IT', 'BE'], limit=100):
        # Lancer le pipeline complet : Extract → Transform → Load
        
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info("DEMARRAGE DU PIPELINE ETL")
        logger.info("=" * 60)
        
        try:
            # ETAPE 1 : Extraction
            logger.info("\n[1/3] EXTRACTION des donnees depuis l'API...")
            raw_data = self.extractor.extract_latest_measurements(countries=countries, limit=limit)
            
            if not raw_data:
                logger.error("Aucune donnee extraite. Arret du pipeline.")
                return False
            
            logger.info(f"Extraction reussie: {len(raw_data)} enregistrements")
            
            # ETAPE 2 : Transformation
            logger.info("\n[2/3] TRANSFORMATION et nettoyage des donnees...")
            locations_df, measurements_df = self.transformer.transform(raw_data)
            
            if locations_df.empty or measurements_df.empty:
                logger.error("Aucune donnee apres transformation. Arret du pipeline.")
                return False
            
            logger.info(f"Transformation reussie:")
            logger.info(f"  - {len(locations_df)} localisations uniques")
            logger.info(f"  - {len(measurements_df)} mesures valides")
            
            # Stats rapides
            stats = self.transformer.get_aggregated_stats(measurements_df)
            logger.info(f"  - {len(stats)} combinaisons ville/parametre")
            
            # ETAPE 3 : Chargement
            logger.info("\n[3/3] CHARGEMENT dans SQLite...")
            self.loader.load_data(locations_df, measurements_df)
            
            logger.info("Chargement reussi")
            
            # Stats finales de la base
            db_stats = self.loader.get_stats()
            logger.info("\n" + "=" * 60)
            logger.info("PIPELINE TERMINE AVEC SUCCES")
            logger.info("=" * 60)
            logger.info(f"Temps d'execution: {datetime.now() - start_time}")
            logger.info(f"\nStatistiques de la base de donnees:")
            logger.info(f"  - Total localisations: {db_stats['locations']}")
            logger.info(f"  - Total mesures: {db_stats['measurements']}")
            logger.info(f"  - Derniere mesure: {db_stats['last_measurement']}")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"\nERREUR CRITIQUE dans le pipeline: {e}")
            return False

def main():
    # Point d'entrée du script
    pipeline = ETLPipeline()
    
    # Pays européens à surveiller
    countries = ['FR', 'DE', 'ES', 'IT', 'BE', 'NL', 'CH']
    
    # Lancer le pipeline
    success = pipeline.run(countries=countries, limit=50)
    
    if success:
        logger.info("\n✓ Pipeline execute avec succes!")
        return 0
    else:
        logger.error("\n❌ Le pipeline a echoue.")
        return 1

if __name__ == "__main__":
    exit(main())
