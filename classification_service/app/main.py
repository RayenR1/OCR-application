# app/main.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from app.models import ModelLoader, YOLOClassifier
from app.Kafka import KafkaConsumer, KafkaProducer, KafkaTopicManager
from app.mlflow import MLflowTracker
from app.config import MODEL_PATH, MLFLOW_TRACKING_URI
import cv2
import numpy as np
import asyncio
import threading
import mlflow
from mlflow.server import app as mlflow_app
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize components
model_loader = ModelLoader(MODEL_PATH)
model = model_loader.load_model()
classifier = YOLOClassifier(model)
kafka_consumer = KafkaConsumer()
kafka_producer = KafkaProducer()

kafka_topic_manager = KafkaTopicManager()

# Function to start the MLflow UI in a separate thread
def start_mlflow_ui():
    logger.info("Starting MLflow UI on port 5000...")
    try:
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow_app.run(host="0.0.0.0", port=5000, threaded=True)
    except Exception as e:
        logger.error(f"Failed to start MLflow UI: {str(e)}")
        raise

mlflow_tracker = MLflowTracker(max_retries=10, retry_delay=3)

# Create Kafka topics and start MLflow UI on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Creating Kafka topics...")
    kafka_topic_manager.create_topics()
    
    logger.info("Starting MLflow UI thread...")
    mlflow_thread = threading.Thread(target=start_mlflow_ui, daemon=True)
    mlflow_thread.start()
    
    logger.info("Starting Kafka consumer task...")
    asyncio.create_task(process_kafka_messages())

# Background task to process Kafka messages
async def process_kafka_messages():
    for image in kafka_consumer.consume():
        # Classify image
        classified_image, class_name, confidence = classifier.classify(image)
        
        # Send to appropriate Kafka topic
        kafka_producer.produce(classified_image, class_name)

# Endpoint for testing (upload an image)
@app.post("/classify")
async def classify_image(file: UploadFile = File(...)):
    # Read image
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image")

    # Classify image
    classified_image, class_name, confidence = classifier.classify(image)

    # Send to Kafka
    kafka_producer.produce(classified_image, class_name)

    return {"class_name": class_name, "confidence": confidence}

# Endpoint to update model
@app.post("/update-model")
async def update_model(model_path: str, version: str):
    mlflow_tracker.log_model(model_path, version)
    global classifier, model_loader
    model_loader.update_model(model_path)
    model = model_loader.load_model()
    classifier = YOLOClassifier(model)
    return {"message": f"Model updated to version {version}"}

# Endpoint to rollback model
@app.post("/rollback-model")
async def rollback_model(version: str):
    model_path = mlflow_tracker.rollback_model(version)
    global classifier, model_loader
    model_loader.update_model(model_path)
    model = model_loader.load_model()
    classifier = YOLOClassifier(model)
    return {"message": f"Model rolled back to version {version}"}