from confluent_kafka.admin import AdminClient, NewTopic
from app.config import KAFKA_BOOTSTRAP_SERVERS, INPUT_TOPIC, OUTPUT_TOPIC
import logging

logger = logging.getLogger(__name__)

class KafkaTopicManager:
    def __init__(self):
        self.admin_client = AdminClient({
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS
        })

    def create_topic(self, topic_name, num_partitions=1, replication_factor=1):
        existing_topics = self.list_topics()
        if topic_name in existing_topics:
            logger.info(f"Topic '{topic_name}' already exists")
            return

        new_topic = NewTopic(
            topic=topic_name,
            num_partitions=num_partitions,
            replication_factor=replication_factor
        )
        try:
            self.admin_client.create_topics([new_topic])
            logger.info(f"Topic '{topic_name}' created successfully")
        except Exception as e:
            logger.error(f"Error creating topic '{topic_name}': {str(e)}")
            raise

    def list_topics(self):
        try:
            cluster_metadata = self.admin_client.list_topics(timeout=10)
            return set(cluster_metadata.topics.keys())
        except Exception as e:
            logger.error(f"Error listing topics: {str(e)}")
            return set()

    def create_all_topics(self):
        for topic in [INPUT_TOPIC, OUTPUT_TOPIC]:
            self.create_topic(topic)