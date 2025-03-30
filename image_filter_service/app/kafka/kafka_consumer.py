# app/kafka/kafka_consumer.py
#github:@RayenR1 | linkedin :Rayen Jlassi
from confluent_kafka import Consumer
import cv2
import numpy as np
from app.config import KAFKA_BOOTSTRAP_SERVERS, CLASSIFIED_TOPICS
import logging

logger = logging.getLogger(__name__)
class KafkaConsumer:
    def __init__(self):
        self.consumer = Consumer({
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
            'group.id': 'image-filter-group',
            'auto.offset.reset': 'earliest'
        })
        # S'abonner à tous les topics classifiés
        self.topics = list(CLASSIFIED_TOPICS.values())
        logger.info(f"Subscribing to topics: {self.topics}")
        self.consumer.subscribe(self.topics)

        # Créer un dictionnaire pour mapper les topics à leurs classes
        self.topic_to_class = {topic: class_name for class_name, topic in CLASSIFIED_TOPICS.items()}

    def consume(self):
        while True:
            msg = self.consumer.poll(timeout=1.0)
            if msg is None:
                logger.debug("No message received from Kafka")
                continue
            if msg.error():
                logger.error(f"Consumer error: {msg.error()}")
                print(f"Consumer error: {msg.error()}")
                continue

            # Récupérer l'image et la classe à partir du topic
            image_data = msg.value()
            topic = msg.topic()
            class_name = self.topic_to_class.get(topic, "autre")  # Déterminer la classe
            logger.info(f"Received message from topic {topic} with class {class_name}")

            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is not None:
                logger.info(f"Successfully decoded image for class {class_name}")
                yield image, class_name
            else:
                logger.error(f"Failed to decode image from Kafka message in topic {topic}")
    def __del__(self):
        logger.info("Closing Kafka consumer")
        self.consumer.close()