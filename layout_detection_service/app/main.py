# app/main.py
# github:@RayenR1 | linkedin :Rayen Jlassi
from fastapi import FastAPI, File, UploadFile, HTTPException
from .kafka.consumer import KafkaConsumer
from .kafka.producer import KafkaProducer
from .models.layout_detector import detect_layout
from .mlflow.mlflow_client import MLflowClient
from .kafka.kafka_topic_manager import KafkaTopicManager
import cv2
import numpy as np
import threading

app = FastAPI()

# Initialisation des dépendances
kafka_producer = KafkaProducer()
mlflow_client = MLflowClient()
kafka_topic_manager = KafkaTopicManager()
kafka_topic_manager.create_all_topics()

# Fonction pour consommer les messages Kafka et traiter les layouts
def consume_and_process():
    consumer = KafkaConsumer()
    for image, image_type in consumer.consume_messages():
        try:
            print(f"[INFO] Traitement de l'image de type {image_type}")
            layout_data = detect_layout(image, image_type)
            
            # Enregistrer les métriques dans MLflow
            mlflow_client.log_layout_metrics(
                image_type,
                len(layout_data["tables"]),
                len(layout_data["typed_text"]),
                len(layout_data["lines"])
            )

            # Envoyer l'image et le layout au topic de sortie
            kafka_producer.send_layout(image, layout_data)
            print(f"[INFO] Layout détecté et envoyé pour l'image de type {image_type}")
        except Exception as e:
            print(f"[ERROR] Erreur lors du traitement de l'image de type {image_type} : {str(e)}")

# Lancer le consommateur Kafka dans un thread séparé
@app.on_event("startup")
async def startup_event():
    thread = threading.Thread(target=consume_and_process, daemon=True)
    thread.start()
    print("[INFO] Consommateur Kafka démarré")

# API de test pour soumettre une image manuellement
@app.post("/detect-layout")
async def detect_layout_endpoint(file: UploadFile = File(...), image_type: str = "BS"):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Impossible de lire l'image")

        layout_data = detect_layout(image, image_type)

        # Enregistrer les métriques dans MLflow
        mlflow_client.log_layout_metrics(
            image_type,
            len(layout_data["tables"]),
            len(layout_data["typed_text"]),
            len(layout_data["lines"])
        )

        return {"layout_data": layout_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la détection de layout : {str(e)}")

@app.get("/")
async def root():
    return {"message": "Layout Detection Service is running"}