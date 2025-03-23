# app/kafka/kafka_consumer.py
from confluent_kafka import Consumer
import cv2
import numpy as np
from app.config import KAFKA_BOOTSTRAP_SERVERS, CLASSIFIED_TOPICS

class KafkaConsumer:
    def __init__(self):
        self.consumer = Consumer({
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
            'group.id': 'image-filter-group',
            'auto.offset.reset': 'earliest'
        })
        # S'abonner à tous les topics classifiés
        self.topics = list(CLASSIFIED_TOPICS.values())
        self.consumer.subscribe(self.topics)

        # Créer un dictionnaire pour mapper les topics à leurs classes
        self.topic_to_class = {topic: class_name for class_name, topic in CLASSIFIED_TOPICS.items()}

    def consume(self):
        while True:
            msg = self.consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue

            # Récupérer l'image et la classe à partir du topic
            image_data = msg.value()
            topic = msg.topic()
            class_name = self.topic_to_class.get(topic, "autre")  # Déterminer la classe

            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is not None:
                yield image, class_name

    def __del__(self):
        self.consumer.close()