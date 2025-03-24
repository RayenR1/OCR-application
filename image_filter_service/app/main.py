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
logger.info("Initializing Kafka components")
kafka_consumer = KafkaConsumer()
kafka_producer = KafkaProducer()
image_filter = ImageFilter()
kafka_topic_manager = KafkaTopicManager()

@app.post("/filter")
async def filter_image(file: UploadFile = File(...), class_name: str = "autre"):
    """Endpoint to test image preprocessing"""
    logger.info("Received image filter request")
    # Read the image
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        logger.error("Failed to decode uploaded image")
        raise HTTPException(status_code=400, detail="Invalid image")

    # Generate closedEdges
    closed_edges = image_filter.edgesDet(image, minVal=200, maxVal=250)
    if closed_edges is None:
        logger.error("Failed to detect edges")
        raise HTTPException(status_code=500, detail="Failed to detect edges")

    # Preprocess the image
    filtered_image = image_filter.preprocess_image(image, closed_edges, class_name=class_name)
    if filtered_image is None:
        logger.error(f"Failed to preprocess image for class {class_name}")
        raise HTTPException(status_code=500, detail="Failed to preprocess image")

    # Send the preprocessed image to Kafka
    try:
        kafka_producer.produce(filtered_image, class_name)
        logger.info(f"Image filtered and sent to Kafka topic for class {class_name}")
    except Exception as e:
        logger.error(f"Failed to send to Kafka: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Kafka produce error: {str(e)}")

    return {"message": f"Image filtered and sent to Kafka topic for class {class_name}"}

async def process_kafka_messages():
    """Background task to consume and preprocess images from Kafka"""
    logger.info("Entering Kafka message processing loop")
    try:
        for image, class_name in kafka_consumer.consume():
            if image is None:
                logger.debug(f"Received None image for class {class_name}, skipping...")
                await asyncio.sleep(0.1)
                continue
            logger.info(f"Consumed an image from Kafka for class {class_name}")
            try:
                # Generate closedEdges
                closed_edges = image_filter.edgesDet(image, minVal=200, maxVal=250)
                if closed_edges is None:
                    logger.error(f"Failed to detect edges for image of class {class_name}")
                    continue

                # Preprocess the image
                filtered_image = image_filter.preprocess_image(image, closed_edges, class_name=class_name)
                if filtered_image is None:
                    logger.error(f"Failed to preprocess image for class {class_name}")
                    continue

                # Send the preprocessed image to Kafka
                kafka_producer.produce(filtered_image, class_name)
                logger.info(f"Image filtered and sent to Kafka topic for class {class_name}")
            except Exception as e:
                logger.error(f"Error processing image for class {class_name}: {str(e)}")
            await asyncio.sleep(0.1)  # Yield control to event loop
    except Exception as e:
        logger.error(f"Error in Kafka consumer loop: {str(e)}")
        await asyncio.sleep(1)  # Wait before retrying if the loop breaks

@app.on_event("startup")
async def startup_event():
    logger.info("Creating Kafka topics for filtered images...")
    try:
        kafka_topic_manager.create_all_topics()  # Create output topics only
    except Exception as e:
        logger.error(f"Failed to create Kafka topics: {str(e)}")
        raise
    logger.info("Starting Kafka consumer task...")
    asyncio.create_task(process_kafka_messages())
    logger.info("Startup event completed")