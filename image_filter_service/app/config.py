# app/config.py
#github:@RayenR1 | linkedin :Rayen Jlassi
import os

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")  # changer ca a 9093 a la fin 

# Input topics (classified images from the previous service)
CLASSIFIED_TOPICS = {
    "BS": "Classified-BS",
    "ordonnance": "Classified-ordonnance",
    "facture": "Classified-facture"
}

# Output topics (filtered images)
FILTERED_TOPICS = {
    "BS": "filtered-BS",
    "ordonnance": "filtered-ordonnances",
    "facture": "filtered-facture",
    "autre": "filtered-autre"
}

# Image processing configuration
STANDARD_SIZES = {
    "BS": (800, 600),          # Taille pour BS
    "ordonnance": (640, 480),  # Taille pour ordonnance
    "facture": (720, 540),     # Taille pour facture
    "autre": (640, 480)        # Taille par défaut pour les cas non spécifiés
}