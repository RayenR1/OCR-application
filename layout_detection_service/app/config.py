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

# Paramètres CRAFT
CRAFT_LONG_SIZE = 1280

# Paramètres de filtrage des boîtes
MIN_BOX_WIDTH = 15
MIN_BOX_HEIGHT = 10
MIN_BOX_AREA = 150
LINE_HEIGHT_TOLERANCE = 15
MIN_LINE_WIDTH = 50