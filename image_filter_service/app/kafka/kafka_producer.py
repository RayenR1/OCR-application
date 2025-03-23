# app/kafka/kafka_producer.py
from confluent_kafka import Producer
import cv2
from app.config import KAFKA_BOOTSTRAP_SERVERS, FILTERED_TOPICS

class KafkaProducer:
    def __init__(self):
        self.producer = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})

    def produce(self, image, class_name):
        topic = FILTERED_TOPICS.get(class_name, "filtered-autre")
        _, encoded_image = cv2.imencode('.jpg', image)
        self.producer.produce(topic, value=encoded_image.tobytes())
        self.producer.flush()