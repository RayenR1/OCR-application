from confluent_kafka import Consumer, KafkaError
import json
import logging
import uuid
from typing import Callable, Dict, Any
from app.config import settings
from app.kafka.producer import KafkaProducer

logger = logging.getLogger(__name__)

class KafkaConsumer:
    def __init__(self):
        self.conf = {
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": "text-structuring-group",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "max.poll.interval.ms": 86400000
        }
        self.consumer = Consumer(self.conf)
        self.consumer.subscribe([settings.INPUT_TOPIC])

    async def consume_messages(self, processing_callback: Callable[[Dict[str, Any], KafkaProducer], Dict[str, Any]], producer: KafkaProducer = None):
        logger.info(f"Starting consumer for topic: {settings.INPUT_TOPIC}")
        
        try:
            while True:
                msg = self.consumer.poll(1.0)
                
                if msg is None:
                    continue
                    
                if msg.error():
                    self._handle_kafka_error(msg.error())
                    continue
                
                try:
                    message_value = self._decode_message(msg)
                    logger.info(f"Processing OCR output for message: {message_value.get('message_id')}")
                    
                    # Process the message exactly once
                    result = processing_callback(message_value, producer=producer)
                    
                    if result.get('status') == 'success':
                        self.consumer.commit(asynchronous=False)
                        logger.info(f"Successfully structured text for message {message_value.get('message_id')}")
                    else:
                        logger.error(f"Failed to structure text for message {message_value.get('message_id')}")
                        
                except Exception as e:
                    logger.error(f"Message processing failed: {str(e)}", exc_info=True)
                    continue
                    
        except KeyboardInterrupt:
            logger.info("Consumer stopped by user")
        except Exception as e:
            logger.error(f"Consumer fatal error: {str(e)}", exc_info=True)
        finally:
            self.close()

    def _decode_message(self, msg):
        try:
            message = json.loads(msg.value().decode('utf-8'))
            message.setdefault('message_id', str(uuid.uuid4()))
            return message
        except Exception as e:
            logger.error(f"Message decoding failed: {str(e)}")
            return {
                'data': msg.value(),
                'message_id': str(uuid.uuid4()),
                'error': f"Decoding error: {str(e)}"
            }

    def _handle_kafka_error(self, error):
        if error.code() == KafkaError.NO_ERROR:
            return
        elif error.code() == KafkaError._PARTITION_EOF:
            logger.debug("Reached end of partition")
        else:
            logger.error(f"Kafka error: {error.str()}")

    def close(self):
        try:
            self.consumer.close()
            logger.info("Consumer closed successfully")
        except Exception as e:
            logger.error(f"Error closing consumer: {str(e)}")