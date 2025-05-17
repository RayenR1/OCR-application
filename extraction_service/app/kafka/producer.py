from confluent_kafka import Producer
from app.config import settings
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class KafkaProducer:
    def __init__(self):
        conf = {
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "client.id": "ocr-extraction-producer",
            "message.max.bytes": 10000000,  # 10MB (taille maximale des messages)
            "compression.type": "gzip"
        }
        self.producer = Producer(conf)

    def delivery_report(self, err, msg):
        """Callback pour vérifier la livraison des messages"""
        if err is not None:
            logger.error(f"Échec de livraison: {err}")
        else:
            logger.debug(f"Message livré à {msg.topic()} [partition {msg.partition()}]")

    def send_result(self, result: Dict[str, Any]):
        """
        Envoie le résultat OCR consolidé vers Kafka.
        Contient tout le texte extrait et les positions des boîtes dans un seul JSON.
        """
        try:
            # Sérialisation du résultat
            message_json = json.dumps(result, ensure_ascii=False).encode('utf-8')
            
            # Envoi vers le topic de sortie
            self.producer.produce(
                topic=settings.OUTPUT_TOPIC,
                key=result.get('message_id', '').encode('utf-8'),
                value=message_json,
                callback=self.delivery_report
            )
            
            # Forcer l'envoi immédiat
            self.producer.flush()
            
            logger.info(f"Résultat OCR envoyé pour le message {result.get('message_id')}")
        except Exception as e:
            logger.error(f"Échec de l'envoi: {str(e)}", exc_info=True)
            raise