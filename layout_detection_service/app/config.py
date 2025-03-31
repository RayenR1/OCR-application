# app/config.py
#github:@RayenR1 | linkedin :Rayen Jlassi
FILTERED_TOPICS = {
    "BS": "filtered-BS",
    "ordonnance": "filtered-ordonnances",
    "facture": "filtered-facture",
    "autre": "filtered-autre"
}

OUTPUT_TOPIC = "output-layout"

KAFKA_BOOTSTRAP_SERVERS = "kafka:9093"
MLFLOW_TRACKING_URI = "http://mlflow:5000"