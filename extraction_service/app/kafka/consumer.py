from confluent_kafka import Consumer, KafkaException
import json
import logging
import uuid
from typing import Callable, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

class KafkaConsumer:
    def __init__(self):
        self.conf = {
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": "ocr-extraction-group",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "max.poll.interval.ms": 6000000,  # 5 minutes
            "session.timeout.ms": 10240
        }
        self.consumer = Consumer(self.conf)
        self.consumer.subscribe([settings.INPUT_TOPIC])

    async def consume_messages(self, processing_callback: Callable[[Dict[str, Any]], Dict[str, Any]]):
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
                    logger.debug(f"Received message: {message_value.get('message_id')}")
                    
                    result = processing_callback(message_value)
                    
                    if result.get('status') == 'success':
                        self.consumer.commit(msg)
                        logger.info(f"Processed message {message_value.get('message_id')}")
                    else:
                        logger.error(f"Failed to process message {message_value.get('message_id')}: {result.get('error')}")
                        
                except Exception as e:
                    logger.error(f"Message processing failed: {str(e)}", exc_info=True)
                    continue
                    
        except KeyboardInterrupt:
            logger.info("Consumer stopped by user")
        except Exception as e:
            logger.error(f"Consumer error: {str(e)}", exc_info=True)
        finally:
            self.consumer.close()
            logger.info("Consumer closed")

    def _decode_message(self, msg):
        try:
            # Essayer de décoder en JSON d'abord
            message = json.loads(msg.value().decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            # Si échec, traiter comme message binaire
            message = {
                'binary_data': msg.value(),
                'layout_data': {},
                'message_id': str(uuid.uuid4())
            }
        
        # Assurer la présence des champs obligatoires
        if 'message_id' not in message:
            message['message_id'] = str(uuid.uuid4())
        if 'layout_data' not in message:
            message['layout_data'] = {}
            
        return message

    def _handle_kafka_error(self, error):
        """Gère les erreurs Kafka de manière robuste"""
        try:
            # Utilisez la constante correcte pour la fin de partition
            if error.code() == KafkaException._PARTITION_EOF:
                logger.debug("Reached end of partition")
            elif error.code() == KafkaError._PARTITION_EOF:  # Alternative
                logger.debug("Reached end of partition")
            else:
                logger.error(f"Kafka error: {error.str()}")
        except Exception as e:
            logger.error(f"Error handling Kafka error: {str(e)}")

    def close(self):
        self.consumer.close()