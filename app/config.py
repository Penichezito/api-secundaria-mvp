import os
from pathlib import Path

class Config:
    """Configuração centralizada da aplicação"""

    # Diretórios
    BASE_DIR = Path(__file__).parent.parent
    UPLOAD_FOLDER = BASE_DIR / "uploads"

    # Banco de dados
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@db:5432/freela_facility_secondary"
    )

    # API Externa (Google Cloud Vision)
    GOOGLE_CLOUD_VISION_ENABLED = os.getenv("GOOGLE_CLOUD_VISION_ENABLED", "false").lower() == "true"
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    # Limites de Processamento 
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    MIN_TAG_CONFIDENCE = float(os.getenv("MIN_TAG_CONFIDENCE", "0.7")) # 70% de confiança
    MAX_TAGS_PER_FILE = int(os.getenv("MAX_TAGS_PER_FILE", "15")) # 15 tags no máximo por arquivo

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_ENV", "development") == "development"

    @classmethod
    def init_app(cls):
        """Inicializa diretórios necessários"""
        cls.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        
config = Config()