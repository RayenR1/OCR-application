from confluent_kafka import Producer
from app.config import KAFKA_BOOTSTRAP_SERVERS, OUTPUT_TOPIC
import json
import logging

logger = logging.getLogger(__name__)

class KafkaProducer:
    def __init__(self):
        self.producer = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})

    def produce(self, formatted_text):
        try:
            self.producer.produce(
                OUTPUT_TOPIC,
                value=json.dumps({"text": formatted_text}).encode('utf-8'),
                callback=self.delivery_report
            )
            self.producer.flush()
            logger.info(f"Produced text to topic {OUTPUT_TOPIC}")
        except Exception as e:
            logger.error(f"Failed to produce message: {str(e)}")
            raise

    @staticmethod
    def delivery_report(err, msg):
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()}")