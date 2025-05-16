# app/kafka/producer.py
# github:@RayenR1 | linkedin:Rayen Jlassi
from confluent_kafka import Producer
from app.config import OUTPUT_TOPIC, KAFKA_BOOTSTRAP_SERVERS
import json
import logging

class KafkaProducer:
    def __init__(self):
        conf = {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "client.id": "extraction_producer",
        }
        self.producer = Producer(conf)

    def delivery_report(self, err, msg):
        if err is not None:
            logging.error(f"Échec de l'envoi du message : {err}")
        else:
            logging.info(f"Message envoyé au topic {msg.topic()}")

    def send_text(self, text_data, message_id):
        """Send extracted text data to the text_output topic."""
        try:
            message = {
                "message_id": message_id,
                "text_data": text_data
            }
            message_json = json.dumps(message, ensure_ascii=False).encode("utf-8")
            self.producer.produce(
                OUTPUT_TOPIC,
                key=message_id.encode("utf-8"),
                value=message_json,
                callback=self.delivery_report,
            )
            self.producer.flush()
            logging.info(f"Sent text data with ID {message_id} to {OUTPUT_TOPIC}")
        except Exception as e:
            logging.error(f"Error sending text data: {str(e)}")
            raise