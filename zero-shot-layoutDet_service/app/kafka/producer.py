# app/kafka/producer.py
#github:@RayenR1 | linkedin :Rayen Jlassi
from confluent_kafka import Producer
from app.config import OUTPUT_TOPIC, KAFKA_BOOTSTRAP_SERVERS
import json
import cv2
import uuid

class KafkaProducer:
    def __init__(self):
        conf = {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "client.id": "layout_detection_producer",
        }
        self.producer = Producer(conf)

    def delivery_report(self, err, msg):
        if err is not None:
            print(f"[ERROR] Échec de l'envoi du message : {err}")
        else:
            print(f"[INFO] Message envoyé au topic {msg.topic()}")

    def send_layout(self, image, layout_data):
        message_id = str(uuid.uuid4())
        layout_data["message_id"] = message_id

        # Sérialiser l'image
        _, buffer = cv2.imencode(".jpg", image)
        image_bytes = buffer.tobytes()

        # Sérialiser le JSON
        layout_json = json.dumps(layout_data, ensure_ascii=False).encode("utf-8")

        # Envoyer l'image
        self.producer.produce(
            OUTPUT_TOPIC,
            key=f"image-{message_id}",
            value=image_bytes,
            callback=self.delivery_report,
        )

        # Envoyer le JSON
        self.producer.produce(
            OUTPUT_TOPIC,
            key=f"layout-{message_id}",
            value=layout_json,
            callback=self.delivery_report,
        )

        self.producer.flush()