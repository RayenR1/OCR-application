# app/main.py
# github:@RayenR1 | linkedin:Rayen Jlassi
from fastapi import FastAPI
from app.kafka.consumer import KafkaConsumer
from app.kafka.producer import KafkaProducer
from app.ocr.extractor import TextExtractor
from app.kafka.topic_manager import KafkaTopicManager
from app.config import INPUT_TOPIC, OUTPUT_TOPIC
import threading
import logging

app = FastAPI(title="Text Extraction Service")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize dependencies
extractor = TextExtractor()
kafka_producer = KafkaProducer()

def consume_and_process():
    """Consume messages from output-layout and process with TextExtractor."""
    consumer = KafkaConsumer()
    for image, layout_data in consumer.consume_messages():
        try:
            logger.info(f"Processing image with layout data: {layout_data}")
            # Extract text using TextExtractor
            result = extractor.extract_text(image, layout_data)
            logger.info(f"Extract_text result type: {type(result)}, value: {result}")  # Debug log
            message_id = result["message_id"]
            text_data = result["text"]
            # Send extracted text to text_output topic
            kafka_producer.send_text(text_data, message_id)
            logger.info(f"Text data extracted and sent to text_output for message ID {message_id}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")

@app.on_event("startup")
async def startup_event():
    # Initialize Kafka topic manager and create topics
    topic_manager = KafkaTopicManager()
    topic_manager.create_topic(INPUT_TOPIC)
    topic_manager.create_topic(OUTPUT_TOPIC)
    
    # Start Kafka consumer in a background thread
    thread = threading.Thread(target=consume_and_process, daemon=True)
    thread.start()
    logger.info("Kafka consumer started")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)