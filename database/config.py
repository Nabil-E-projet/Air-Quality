import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Classe de base pour tous nos modèles de tables
Base = declarative_base()

def get_db_path():
    # On stocke la base de données dans un dossier 'data' à la racine du projet
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(root_dir, 'data')
    
    # Créer le dossier s'il n'existe pas
    os.makedirs(data_dir, exist_ok=True)
    
    return os.path.join(data_dir, 'air_quality.db')

def get_engine():
    # Créer le moteur SQLite (pas besoin de serveur, juste un fichier)
    db_path = get_db_path()
    return create_engine(f'sqlite:///{db_path}', echo=False)

def init_db():
    # Initialiser la base : créer les tables si elles n'existent pas
    engine = get_engine()
    
    # On importe les modèles pour que SQLAlchemy les connaisse
    from database.models import Location, Measurement
    
    # Créer toutes les tables définies dans nos modèles
    # checkfirst=True évite les erreurs si les tables existent déjà
    try:
        Base.metadata.create_all(engine, checkfirst=True)
        print(f"Base de donnees initialisee : {get_db_path()}")
    except Exception as e:
        # Si erreur (ex: table existe déjà), on ignore silencieusement
        pass

def get_session():
    # Ouvrir une nouvelle connexion à la base
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
