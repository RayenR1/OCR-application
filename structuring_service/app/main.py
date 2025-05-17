from fastapi import FastAPI
import uvicorn
from app.kafka.consumer import KafkaConsumer
from app.kafka.producer import KafkaProducer
from app.text_structurer.structurer import TextStructurer
import logging
from app.config import settings
from app.kafka.topic_manager import KafkaTopicManager

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Text Structuring Service")

producer = None

@app.on_event("startup")
async def startup_event():
    global producer
    try:
        logger.info("Starting text structuring service...")
        
        # Create topics
        topic_manager = KafkaTopicManager()
        topic_manager.create_topics()
        
        structurer = TextStructurer()
        structurer.initialize()
        
        producer = KafkaProducer()
        
        consumer = KafkaConsumer()
        
        await consumer.consume_messages(structurer.process_ocr_output, producer=producer)
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}", exc_info=True)
        raise

@app.on_event("shutdown")
async def shutdown_event():
    global producer
    try:
        if producer:
            producer.close()
            logger.info("Producer closed during shutdown")
    except Exception as e:
        logger.error(f"Shutdown failed: {str(e)}", exc_info=True)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8004,  # Different port from extraction_service
        log_level=settings.LOG_LEVEL.lower()
    )