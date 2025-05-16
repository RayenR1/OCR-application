# app/kafka/consumer.py
# github:@RayenR1 | linkedin:Rayen Jlassi
from confluent_kafka import Consumer
import logging
import json
import base64
import cv2
import numpy as np

class KafkaConsumer:
    def __init__(self):
        self.consumer = Consumer({
            'bootstrap.servers': 'localhost:9092',
            'group.id': 'extraction_group',
            'auto.offset.reset': 'earliest'
        })
        self.consumer.subscribe(['output-layout'])
        logging.info("Subscribed to topic: output-layout")

    def consume_messages(self):
        while True:
            msg = self.consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                logging.error(f"Kafka error: {msg.error()}")
                continue
            try:
                # Decode JSON message
                message_json = msg.value().decode('utf-8')
                message = json.loads(message_json)
                logging.info(f"Raw message: {message}")
                # Extract image and layout data with fallback
                image_base64 = message.get('image', '')
                layout_data = message.get('layout_data', {})
                if not image_base64:
                    logging.warning("No image data found in message")
                    continue
                # Convert base64 image to NumPy array
                image_bytes = base64.b64decode(image_base64)
                nparr = np.frombuffer(image_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if image is None:
                    logging.error("Failed to decode image from base64")
                    continue
                logging.info(f"Decoded image shape: {image.shape}")
                message_id = layout_data.get('message_id', 'unknown')
                logging.info(f"Received message ID {message_id} with layout_data: {layout_data}")
                logging.info(f"layout_data type: {type(layout_data)}")
                # Add detailed logging for layout_data contents
                logging.debug(f"layout_data keys: {list(layout_data.keys())}")
                logging.debug(f"layout_data lines: {layout_data.get('lines', [])}")
                logging.debug(f"layout_data tables: {layout_data.get('tables', {})}")
                yield image, layout_data
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON message: {str(e)}")
                continue
            except Exception as e:
                logging.error(f"Error processing message: {str(e)}")
                continue