# app/kafka/producer.py
# github:@RayenR1 | linkedin :Rayen Jlassi
from confluent_kafka import Producer
from app.config import OUTPUT_TOPIC, KAFKA_BOOTSTRAP_SERVERS
import json
import cv2
import uuid
import base64
import logging

class KafkaProducer:
       def __init__(self):
           conf = {
               "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
               "client.id": "layout_detection_producer",
           }
           self.producer = Producer(conf)

       def delivery_report(self, err, msg):
           if err is not None:
               logging.error(f"Échec de l'envoi du message : {err}")
           else:
               logging.info(f"Message envoyé au topic {msg.topic()}")

       def send_layout(self, image, layout_data):
           """
           Envoie l'image et les données de layout (image_type, tables, typed_text, lines)
           au topic de sortie dans un seul message JSON.
           """
           try:
               message_id = str(uuid.uuid4())
               layout_data["message_id"] = message_id

               # Sérialiser l'image en base64
               _, buffer = cv2.imencode(".jpg", image)
               image_bytes = buffer.tobytes()
               image_base64 = base64.b64encode(image_bytes).decode('utf-8')

               # Créer le message JSON
               message = {
                   "image": image_base64,
                   "layout_data": layout_data
               }
               message_json = json.dumps(message, ensure_ascii=False).encode("utf-8")

               # Envoyer le message
               self.producer.produce(
                   OUTPUT_TOPIC,
                   key=message_id.encode("utf-8"),
                   value=message_json,
                   callback=self.delivery_report,
               )
               self.producer.flush()
               logging.info(f"Sent message with ID {message_id} to {OUTPUT_TOPIC}")
           except Exception as e:
               logging.error(f"Error sending layout: {str(e)}")
               raise