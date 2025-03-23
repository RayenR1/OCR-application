# app/main.py
import asyncio
import logging
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from app.kafka.kafka_consumer import KafkaConsumer
from app.kafka.kafka_producer import KafkaProducer
from app.kafka.kafka_topic_manager import KafkaTopicManager
from app.image_processing.image_filter import ImageFilter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Image Filter Service")

# Initialize Kafka consumer, producer, and topic manager
kafka_consumer = KafkaConsumer()
kafka_producer = KafkaProducer()
image_filter = ImageFilter()
kafka_topic_manager = KafkaTopicManager()

@app.post("/filter")
async def filter_image(file: UploadFile = File(...), class_name: str = "autre"):
    """ Endpoint pour tester le prétraitement d'une image """
    # Lire l'image
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image")

    # Générer closedEdges
    closed_edges = image_filter.edgesDet(image, minVal=200, maxVal=250)
    if closed_edges is None:
        raise HTTPException(status_code=500, detail="Failed to detect edges")

    # Prétraiter l'image
    filtered_image = image_filter.preprocess_image(image, closed_edges, class_name=class_name)
    if filtered_image is None:
        raise HTTPException(status_code=500, detail="Failed to preprocess image")

    # Envoyer l'image prétraitée à Kafka
    kafka_producer.produce(filtered_image, class_name)

    return {"message": f"Image filtered and sent to Kafka topic for class {class_name}"}

async def process_kafka_messages():
    """ Tâche en arrière-plan pour consommer et prétraiter les images depuis Kafka """
    for image, class_name in kafka_consumer.consume():
        # Générer closedEdges
        closed_edges = image_filter.edgesDet(image, minVal=200, maxVal=250)
        if closed_edges is None:
            logger.error(f"Failed to detect edges for image of class {class_name}")
            continue

        # Prétraiter l'image
        filtered_image = image_filter.preprocess_image(image, closed_edges, class_name=class_name)
        if filtered_image is None:
            logger.error(f"Failed to preprocess image for class {class_name}")
            continue
        
        # Envoyer l'image prétraitée à Kafka dans le topic correspondant
        kafka_producer.produce(filtered_image, class_name)
        logger.info(f"Image filtered and sent to Kafka topic for class {class_name}")

@app.on_event("startup")
async def startup_event():
    logger.info("Creating Kafka topics for filtered images...")
    kafka_topic_manager.create_all_topics()  # Créer uniquement les topics de sortie
    logger.info("Starting Kafka consumer task...")
    asyncio.create_task(process_kafka_messages())