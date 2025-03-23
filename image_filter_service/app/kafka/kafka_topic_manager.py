# app/kafka/kafka_topic_manager.py
from confluent_kafka.admin import AdminClient, NewTopic
from app.config import KAFKA_BOOTSTRAP_SERVERS, FILTERED_TOPICS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaTopicManager:
    def __init__(self):
        """Initialise le client d'administration Kafka."""
        self.admin_client = AdminClient({
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS
        })

    def create_topic(self, topic_name, num_partitions=1, replication_factor=1):
        """
        Crée un topic Kafka s'il n'existe pas déjà.

        Args:
            topic_name (str): Nom du topic à créer.
            num_partitions (int): Nombre de partitions pour le topic (par défaut: 1).
            replication_factor (int): Facteur de réplication pour le topic (par défaut: 1).
        """
        existing_topics = self.list_topics()
        if topic_name in existing_topics:
            logger.info(f"Le topic '{topic_name}' existe déjà.")
            return

        new_topic = NewTopic(
            topic=topic_name,
            num_partitions=num_partitions,
            replication_factor=replication_factor
        )

        try:
            self.admin_client.create_topics([new_topic])
            logger.info(f"Topic '{topic_name}' créé avec succès.")
        except Exception as e:
            logger.error(f"Erreur lors de la création du topic '{topic_name}': {str(e)}")
            raise

    def list_topics(self):
        """
        Liste tous les topics Kafka existants.

        Returns:
            set: Ensemble des noms de topics existants.
        """
        try:
            cluster_metadata = self.admin_client.list_topics(timeout=10)
            topics = cluster_metadata.topics.keys()
            return set(topics)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des topics: {str(e)}")
            return set()

    def create_filtered_topics(self):
        """
        Crée tous les topics de sortie pour les images filtrées définis dans FILTERED_TOPICS.
        """
        for class_name, topic_name in FILTERED_TOPICS.items():
            try:
                self.create_topic(topic_name, num_partitions=1, replication_factor=1)
            except Exception as e:
                logger.error(f"Échec de la création du topic '{topic_name}' pour la classe '{class_name}': {str(e)}")

    def create_all_topics(self):
        """
        Crée tous les topics nécessaires (uniquement les topics de sortie filtrés).
        """
        self.create_filtered_topics()

    def __del__(self):
        """Ferme proprement le client d'administration Kafka."""
        pass