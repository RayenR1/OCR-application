from fastapi import FastAPI
import uvicorn
from app.kafka.consumer import KafkaConsumer
from app.ocr.extractor import OCRProcessor
import logging
from app.config import settings

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
        
        ocr_processor = OCRProcessor()
        ocr_processor.initialize()
        
        consumer = KafkaConsumer()
        
        # Utiliser process_entire_image pour traiter l'image entière
        await consumer.consume_messages(ocr_processor.process_entire_image)
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}", exc_info=True)
        raise

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_level=settings.LOG_LEVEL.lower()
    )