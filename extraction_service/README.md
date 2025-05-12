Text Extraction Service
This service extracts text from images using the Qari-OCR model, consuming messages from the layout_detection_service output topic (layout_output) and producing results to the text_output topic.
Prerequisites

Docker and Docker Compose
Kafka and Zookeeper (configured via EyeQ/docker-compose.yml)
Python 3.10+

Setup

Build and run the service:docker-compose -f ../docker-compose.yml up --build


Ensure the layout_output topic is producing messages with the format:{
    "image": "<image_bytes>",
    "layout": {"lines": [...], "tables": {...}}
}



Configuration

KAFKA_BOOTSTRAP_SERVERS: Kafka broker address (default: kafka:9093)
INPUT_TOPIC: Input topic (default: layout_output)
OUTPUT_TOPIC: Output topic (default: text_output)
CONFIDENCE_THRESHOLD: EasyOCR confidence threshold (default: 0.80)
MAX_TOKENS: Maximum tokens for Qari-OCR (default: 2000)

Output
The service produces messages to the text_output topic in the format:
{
    "text": "<formatted_text>"
}

Monitoring

Check logs: docker logs text_extraction_service
Use Kafdrop (http://localhost:9000) to inspect topics.

