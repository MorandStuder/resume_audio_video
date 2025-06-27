import os
from pydantic import BaseSettings
from dotenv import load_dotenv

# Charger les variables d'environnement depuis un fichier .env s'il existe
load_dotenv()

class Settings(BaseSettings):
    """Configuration de l'application."""
    
    # Informations de base
    APP_NAME: str = "Eleven Strategy LinkedIn App"
    API_PREFIX: str = "/api"
    
    # Chemins de stockage
    DATA_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data"))
    ARTICLES_FILE: str = os.path.join(DATA_DIR, "articles.json")
    
    # Configuration OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Configuration LinkedIn
    LINKEDIN_CLIENT_ID: str = os.getenv("LINKEDIN_CLIENT_ID", "")
    LINKEDIN_CLIENT_SECRET: str = os.getenv("LINKEDIN_CLIENT_SECRET", "")
    LINKEDIN_ACCESS_TOKEN: str = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
    
    # Configuration CORS
    CORS_ORIGINS: list = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"

# Instance de configuration globale
settings = Settings()

# Créer le répertoire de données s'il n'existe pas
os.makedirs(settings.DATA_DIR, exist_ok=True)
