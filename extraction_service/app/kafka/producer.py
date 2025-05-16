from confluent_kafka import Producer
from app.config import settings
import json
import logging

logger = logging.getLogger(__name__)

class KafkaProducer:
    def __init__(self):
        conf = {
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "client.id": "ocr-extraction-producer",
            "message.max.bytes": 10000000,  # 10MB
            "compression.type": "gzip"
        }
        self.producer = Producer(conf)

    def delivery_report(self, err, msg):
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [partition {msg.partition()}]")

    def send_result(self, result: Dict[str, Any]):
        try:
            message_json = json.dumps(result, ensure_ascii=False).encode('utf-8')
            
            self.producer.produce(
                topic=settings.OUTPUT_TOPIC,
                key=result.get('message_id', '').encode('utf-8'),
                value=message_json,
                callback=self.delivery_report
            )
            
            self.producer.flush()
            logger.info(f"Sent OCR results for message {result.get('message_id')}")
        except Exception as e:
            logger.error(f"Failed to send results: {str(e)}", exc_info=True)
            raise