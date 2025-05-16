from pydantic_settings import BaseSettings
import logging

class Settings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    INPUT_TOPIC: str = "output-layout"
    OUTPUT_TOPIC: str = "output-ocr"
    LOG_LEVEL: str = "INFO"
    OCR_MIN_SIZE: int = 28
    KAFKA_CONSUMER_TIMEOUT: int = 600000
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

# Configuration du logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)