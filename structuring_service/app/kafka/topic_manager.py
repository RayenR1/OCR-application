from confluent_kafka.admin import AdminClient, NewTopic
from app.config import settings

class KafkaTopicManager:
    def __init__(self):
        self.admin_client = AdminClient({'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS})

    def create_topics(self):
        """Create Kafka topics if they don't already exist."""
        existing_topics = self.admin_client.list_topics(timeout=10).topics.keys()
        new_topics = []
        for topic in [settings.INPUT_TOPIC, settings.OUTPUT_TOPIC]:
            if topic not in existing_topics:
                new_topic = NewTopic(
                    topic=topic,
                    num_partitions=1,
                    replication_factor=1
                )
                new_topics.append(new_topic)

        if new_topics:
            futures = self.admin_client.create_topics(new_topics)
            for topic, future in futures.items():
                try:
                    future.result()
                    print(f"Topic {topic} created successfully")
                except Exception as e:
                    print(f"Failed to create topic {topic}: {str(e)}")
        else:
            print("All topics already exist")

    def __del__(self):
        self.admin_client = None