from fastapi import FastAPI
from app.kafka.consumer import KafkaConsumer
from app.kafka.topic_manager import KafkaTopicManager
from app.config import INPUT_TOPIC, OUTPUT_TOPIC
import asyncio
import logging
import uvicorn

app = FastAPI(title="Text Extraction Service")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    # Initialize Kafka topic manager and create topics
    topic_manager = KafkaTopicManager()
    topic_manager.create_topic(INPUT_TOPIC)
    topic_manager.create_topic(OUTPUT_TOPIC)
    
    # Start Kafka consumer in the background
    consumer = KafkaConsumer()
    asyncio.create_task(consumer.consume())

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)