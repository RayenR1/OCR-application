# app/kafka/consumer.py
#github:@RayenR1 | linkedin :Rayen Jlassi
from confluent_kafka import Consumer, KafkaException
import cv2
import numpy as np
from app.config import FILTERED_TOPICS, KAFKA_BOOTSTRAP_SERVERS

class KafkaConsumer:
    def __init__(self, group_id="layout_detection_group"):
        conf = {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
        }
        self.consumer = Consumer(conf)
        self.topics = list(FILTERED_TOPICS.values())
        self.consumer.subscribe(self.topics)

    def consume_messages(self):
        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    raise KafkaException(msg.error())

                topic = msg.topic()
                image_type = next(
                    key for key, value in FILTERED_TOPICS.items() if value == topic
                )

                image_bytes = msg.value()
                nparr = np.frombuffer(image_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if image is None:
                    print(f"[ERROR] Impossible de décoder l'image du topic {topic}")
                    continue

                yield image, image_type

        except KeyboardInterrupt:
            print("[INFO] Arrêt du consommateur Kafka")
        finally:
            self.consumer.close()