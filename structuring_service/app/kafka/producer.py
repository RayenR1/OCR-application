from confluent_kafka import Producer
from app.config import settings
import json
import logging
from typing import Dict, Any
import time
from functools import wraps
import random

logger = logging.getLogger(__name__)

def retry_on_failure(max_attempts=3, base_delay=1.0, max_jitter=0.2):
    """Decorator to retry a function on transient Kafka errors."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        logger.error(f"Failed after {max_attempts} attempts: {str(e)}", exc_info=True)
                        raise
                    delay = base_delay * (2 ** (attempts - 1)) + random.uniform(0, max_jitter)
                    logger.warning(f"Attempt {attempts} failed: {str(e)}. Retrying in {delay:.2f}s...")
                    time.sleep(delay)
        return wrapper
    return decorator

class KafkaProducer:
    def __init__(self):
        conf = {
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "client.id": "text-structuring-producer",
            "message.max.bytes": 10000000,  # 10MB
            "compression.type": "gzip",
            "linger.ms": 5,
            "retries": 3,
            "retry.backoff.ms": 100
        }
        self.producer = Producer(conf)

    def delivery_report(self, err, msg):
        """Callback pour vérifier la livraison des messages"""
        if err is not None:
            logger.error(f"Échec de livraison pour topic {msg.topic()} (message_id: {msg.key().decode('utf-8')}): {err}")
        else:
            logger.debug(f"Message livré à {msg.topic()} [partition {msg.partition()}] (message_id: {msg.key().decode('utf-8')})")

    @retry_on_failure(max_attempts=3, base_delay=1.0, max_jitter=0.2)
    def send_result(self, result: Dict[str, Any]):
        """
        Envoie le résultat structuré vers Kafka.
        Contient le texte structuré dans un JSON.
        """
        try:
            message_json = json.dumps(result, ensure_ascii=False).encode('utf-8')
            message_id = result.get('message_id', '')
            
            self.producer.produce(
                topic=settings.OUTPUT_TOPIC,
                key=message_id.encode('utf-8'),
                value=message_json,
                callback=self.delivery_report
            )
            
            self.producer.poll(0)
            
            logger.info(f"Résultat structuré envoyé pour le message {message_id} au topic {settings.OUTPUT_TOPIC}")
        except Exception as e:
            logger.error(f"Échec de l'envoi au topic {settings.OUTPUT_TOPIC} (message_id: {message_id}): {str(e)}", exc_info=True)
            raise

    def close(self):
        """Flush remaining messages and close the producer."""
        try:
            self.producer.flush(timeout=10.0)
            logger.info("Producer closed successfully")
        except Exception as e:
            logger.error(f"Error closing producer: {str(e)}", exc_info=True)