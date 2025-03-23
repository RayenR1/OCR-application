# app/config.py
from dotenv import load_dotenv
import os

load_dotenv()

# Kafka settings
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9093") ### changer ca a 9093 a la fin
INPUT_TOPIC = "Input-Images"
CLASSIFIED_TOPICS = {
    "Bulltin soin": "Classified-BS",
    "ordonnances": "Classified-ordonnance",
    "facture": "Classified-facture",
    "autre": "autre"
}

# List of all topics to create
ALL_TOPICS = [INPUT_TOPIC] + list(CLASSIFIED_TOPICS.values())

# MLflow settings
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
MODEL_NAME = "YOLOv11-Classifier"

# Model path
MODEL_PATH = "weights/best.pt"