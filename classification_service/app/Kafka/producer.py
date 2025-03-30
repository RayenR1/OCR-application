# app/kafka/producer.py
#github:@RayenR1 | linkedin :Rayen Jlassi
from confluent_kafka import Producer
from app.config import KAFKA_BOOTSTRAP_SERVERS, CLASSIFIED_TOPICS
import cv2
import numpy as np

class KafkaProducer:
    def __init__(self):
        self.producer = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})

    def produce(self, image, class_name):
        # Encode image to bytes
        _, buffer = cv2.imencode('.jpg', image)
        image_data = buffer.tobytes()

        # Send to the appropriate topic
        topic = CLASSIFIED_TOPICS.get(class_name, "autre")
        self.producer.produce(topic, value=image_data)
        self.producer.flush()