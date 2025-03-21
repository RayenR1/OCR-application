# app/kafka/topic_manager.py
from confluent_kafka.admin import AdminClient, NewTopic
from app.config import KAFKA_BOOTSTRAP_SERVERS, ALL_TOPICS

class KafkaTopicManager:
    def __init__(self):
        self.admin_client = AdminClient({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})

    def create_topics(self):
        """Create Kafka topics if they don't already exist."""
        # Get the list of existing topics
        existing_topics = self.admin_client.list_topics(timeout=10).topics.keys()

        # Define topic configurations
        new_topics = []
        for topic in ALL_TOPICS:
            if topic not in existing_topics:
                # Create a NewTopic object for each topic
                new_topic = NewTopic(
                    topic=topic,
                    num_partitions=1,  # Number of partitions
                    replication_factor=1  # Replication factor
                )
                new_topics.append(new_topic)

        if new_topics:
            # Create the topics
            futures = self.admin_client.create_topics(new_topics)
            for topic, future in futures.items():
                try:
                    future.result()  # Wait for the topic creation to complete
                    print(f"Topic {topic} created successfully")
                except Exception as e:
                    print(f"Failed to create topic {topic}: {str(e)}")
        else:
            print("All topics already exist")

    def __del__(self):
        """Clean up the AdminClient when the object is destroyed."""
        self.admin_client = None