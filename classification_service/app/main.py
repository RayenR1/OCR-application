#app/main.py
#github:@RayenR1 | linkedin :Rayen Jlassi
from fastapi import FastAPI, File, UploadFile, HTTPException
from app.models import ModelLoader, YOLOClassifier
from app.Kafka import KafkaConsumer, KafkaProducer, KafkaTopicManager
from app.mlflow import MLflowTracker
from app.config import MODEL_PATH, MLFLOW_TRACKING_URI
import cv2
import numpy as np
import asyncio
import mlflow
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize components with logging
logger.info(f"Loading model from {MODEL_PATH}")
model_loader = ModelLoader(MODEL_PATH)
model = model_loader.load_model()
logger.info("Model loaded successfully")
classifier = YOLOClassifier(model)

logger.info("Initializing Kafka components")
kafka_consumer = KafkaConsumer()
kafka_producer = KafkaProducer()
kafka_topic_manager = KafkaTopicManager()
mlflow_tracker = MLflowTracker(max_retries=10, retry_delay=3)

# Set MLflow tracking URI
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Creating Kafka topics...")
    try:
        kafka_topic_manager.create_topics()
    except Exception as e:
        logger.error(f"Failed to create Kafka topics: {str(e)}")
        raise
    
    logger.info("Starting Kafka consumer task...")
    asyncio.create_task(process_kafka_messages())
    logger.info("Startup event completed")

# Background task to process Kafka messages
async def process_kafka_messages():
    logger.info("Entering Kafka message processing loop")
    try:
        # Use the generator pattern from KafkaConsumer
        for image in kafka_consumer.consume():
            if image is None:
                logger.debug("Received None from Kafka, skipping...")
                await asyncio.sleep(0.1)  # Yield control
                continue
            logger.info("Consumed an image from Kafka")
            try:
                # Ensure image is a valid NumPy array
                if not isinstance(image, np.ndarray):
                    logger.error(f"Invalid image type received: {type(image)}")
                    continue
                classified_image, class_name, confidence = classifier.classify(image)
                kafka_producer.produce(classified_image, class_name)
                logger.info(f"Produced classification result to Kafka: {class_name}, {confidence}")
            except Exception as e:
                logger.error(f"Error processing image: {str(e)}")
            await asyncio.sleep(0.1)  # Yield control to event loop
    except Exception as e:
        logger.error(f"Error in Kafka consumer loop: {str(e)}")
        await asyncio.sleep(1)  # Wait before retrying if the loop breaks

# Endpoint for testing (upload an image)
@app.post("/classify")
async def classify_image(file: UploadFile = File(...)):
    logger.info("Received image upload request")
    # Read image
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        logger.error("Failed to decode uploaded image")
        raise HTTPException(status_code=400, detail="Invalid image")

    # Classify image
    logger.info("Classifying image")
    classified_image, class_name, confidence = classifier.classify(image)

    # Send to Kafka
    try:
        kafka_producer.produce(classified_image, class_name)
        logger.info(f"Sent classification to Kafka: {class_name}, {confidence}")
    except Exception as e:
        logger.error(f"Failed to produce to Kafka: {str(e)}")

    return {"class_name": class_name, "confidence": confidence}

# Endpoint to update model
@app.post("/update-model")
async def update_model(model_path: str, version: str):
    logger.info(f"Updating model to {model_path} version {version}")
    try:
        mlflow_tracker.log_model(model_path, version)
        global classifier, model_loader
        model_loader.update_model(model_path)
        model = model_loader.load_model()
        classifier = YOLOClassifier(model)
        logger.info("Model updated successfully")
        return {"message": f"Model updated to version {version}"}
    except Exception as e:
        logger.error(f"Failed to update model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to rollback model
@app.post("/rollback-model")
async def rollback_model(version: str):
    logger.info(f"Rolling back model to version {version}")
    try:
        model_path = mlflow_tracker.rollback_model(version)
        global classifier, model_loader
        model_loader.update_model(model_path)
        model = model_loader.load_model()
        classifier = YOLOClassifier(model)
        logger.info("Model rolled back successfully")
        return {"message": f"Model rolled back to version {version}"}
    except Exception as e:
        logger.error(f"Failed to rollback model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))