import json
import os
import sys

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from database.config import get_session, init_db
from database.models import Location, Measurement

def load_demo_data():
    """Charge des données de démonstration si la base est vide"""
    
    # Chemin vers le fichier de données de démo
    demo_file = os.path.join(os.path.dirname(__file__), '..', 'demo_data.json')
    
    if not os.path.exists(demo_file):
        print("Fichier demo_data.json introuvable")
        return False
    
    # Charger le JSON
    with open(demo_file, 'r') as f:
        data = json.load(f)
    
    session = get_session()
    
    try:
        # Charger les villes
        location_map = {}
        for loc_data in data['locations']:
            loc = Location(
                city=loc_data['city'],
                country=loc_data['country'],
                latitude=loc_data['latitude'],
                longitude=loc_data['longitude']
            )
            session.add(loc)
            session.flush()
            location_map[(loc.city, loc.country)] = loc.id
        
        # Charger les mesures
        for mes_data in data['measurements']:
            loc_key = (mes_data['city'], mes_data['country'])
            if loc_key in location_map:
                mes = Measurement(
                    location_id=location_map[loc_key],
                    parameter=mes_data['parameter'],
                    value=mes_data['value'],
                    unit=mes_data['unit'],
                    measurement_date=datetime.fromisoformat(mes_data['measurement_date'].replace('Z', '+00:00'))
                )
                session.add(mes)
        
        session.commit()
        print(f"Donnees de demo chargees : {len(data['locations'])} villes, {len(data['measurements'])} mesures")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"Erreur lors du chargement des donnees de demo: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    init_db()
    load_demo_data()
