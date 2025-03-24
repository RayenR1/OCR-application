# app/kafka/consumer.py
from confluent_kafka import Consumer, KafkaError
from app.config import KAFKA_BOOTSTRAP_SERVERS, INPUT_TOPIC
import cv2
import numpy as np

class KafkaConsumer:
    def __init__(self):
        self.consumer = Consumer({
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
            'group.id': 'yolo-classifier-group',
            'auto.offset.reset': 'earliest'
        })
        self.consumer.subscribe([INPUT_TOPIC])

    def consume(self, timeout=1.0):
        while True:
            msg = self.consumer.poll(timeout_ms=int(timeout * 1000))
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(msg.error())
                    break

            # Decode image from message
            image_data = np.frombuffer(msg.value(), dtype=np.uint8)
            image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
            if image is not None:
                yield image
            else:
                print("Failed to decode image from Kafka message")