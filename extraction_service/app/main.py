from fastapi import FastAPI
import uvicorn
from app.kafka.consumer import KafkaConsumer
from app.ocr.extractor import OCRProcessor
from app.config import settings
import asyncio
import logging

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="OCR Extraction Service")

@app.on_event("startup")
async def startup_event():
    try:
        logger.info("Starting OCR service...")
        
        # Initialisation des composants
        ocr_processor = OCRProcessor()
        consumer = KafkaConsumer()
        
        # Démarrer le consommateur Kafka dans un tâche séparée
        asyncio.create_task(consumer.consume_messages(ocr_processor.process))
        
        logger.info("Service started successfully")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}", exc_info=True)
        raise

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ocr_extraction"}

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_config=None,
        access_log=False
    )