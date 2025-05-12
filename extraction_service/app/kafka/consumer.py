from confluent_kafka import Consumer
import cv2
import numpy as np
import json
from app.config import KAFKA_BOOTSTRAP_SERVERS, INPUT_TOPIC
from app.ocr.extractor import TextExtractor
from app.kafka.producer import KafkaProducer
import logging

logger = logging.getLogger(__name__)

class KafkaConsumer:
    def __init__(self):
        self.consumer = Consumer({
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
            'group.id': 'text-extraction-group',
            'auto.offset.reset': 'earliest'
        })
        self.consumer.subscribe([INPUT_TOPIC])
        self.extractor = TextExtractor()
        self.producer = KafkaProducer()
        logger.info(f"Subscribed to topic: {INPUT_TOPIC}")

    async def consume(self):
        while True:
            msg = self.consumer.poll(timeout=1.0)
            if msg is None:
                logger.debug("No message received from Kafka")
                continue
            if msg.error():
                logger.error(f"Consumer error: {msg.error()}")
                continue

            try:
                # Message format: {"image": bytes, "layout": json}
                data = json.loads(msg.value().decode('utf-8'))
                image_data = np.frombuffer(data['image'], np.uint8)
                image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
                layout_data = data['layout']

                if image is None:
                    logger.error("Failed to decode image")
                    continue

                # Extract text
                formatted_text = self.extractor.extract_text(image, layout_data)
                logger.info("Text extracted successfully")

                # Produce result
                self.producer.produce(formatted_text)
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")