import logging
import json
from typing import Dict, Any, List
from ollama import Client
import uuid
from app.kafka.producer import KafkaProducer  # Explicit import

logger = logging.getLogger(__name__)

class TextStructurer:
    def __init__(self):
        self.client = None
        self.initialized = False

    def initialize(self):
        if not self.initialized:
            try:
                logger.info("Initializing Ollama client...")
                self.client = Client(host='http://localhost:11434')
                logger.info("Ollama client initialized successfully")
                self.initialized = True
            except Exception as e:
                logger.error(f"Initialization failed: {str(e)}", exc_info=True)
                raise

    def process_ocr_output(self, message: Dict[str, Any], producer: KafkaProducer = None) -> Dict[str, Any]:
        if not self.initialized:
            self.initialize()

        try:
            message_id = message.get('message_id', str(uuid.uuid4()))
            if message.get('status') != 'success':
                raise ValueError("Input message status is not 'success'")

            text_regions = message.get('text_regions', [])
            original_extracted_text = message.get('extracted_text', '')
            image_dimensions = message.get('metadata', {}).get('image_dimensions', 'unknown')

            # Filter high-confidence regions (confidence > 0.5)
            valid_regions = [
                region for region in text_regions
                if region.get('confidence', 0) >= 0.5 and region.get('text', '').strip()
            ]

            # Sort regions by y_min (top-to-bottom), then x_min (left-to-right)
            sorted_regions = sorted(
                valid_regions,
                key=lambda r: (r['bbox'][1], r['bbox'][0])
            )

            # Prepare input for Ollama
            regions_text = [
                {
                    "text": region['text'],
                    "bbox": region['bbox'],
                    "confidence": region['confidence']
                }
                for region in sorted_regions
            ]

            prompt = f"""
You are tasked with structuring text from a medical care form (Bulletin de soins) based on OCR output. The input is a list of text regions with bounding box coordinates and confidence scores. Your goal is to produce a single structured JSON object with field-value pairs for the form fields. Use the spatial information (bbox) to group related text (e.g., labels and values) and order fields logically (top-to-bottom, left-to-right). Ignore low-confidence or noisy text. If a field's value is missing, use "N/A".

Input:
```json
{json.dumps(regions_text, ensure_ascii=False, indent=2)}
```

Original extracted text (for context, but prioritize regions):
```
{original_extracted_text[:500]}...
```

Expected output format:
```json
{{
  "Bulletin de soins": "value",
  "Numéro CNAM": "value",
  "Matricule de l'adhérent": "value",
  "Date d'entrée": "value",
  "Date de sortie": "value",
  "Montant des frais": "value",
  "Matricule Fiscal": "value",
  "Code prestataire": "value",
  "Code rubrique frais engagés": "value",
  "Date de naissance": "value",
  "Signature de l'Adhérent": "value"
}}
```

Rules:
- Match text to known fields based on content and proximity.
- Use bounding box coordinates to pair labels with nearby values.
- If a value is missing or unclear, use "N/A".
- Ensure the output is concise and accurate.
- Handle both Arabic and French text.
- Return a single JSON object, no additional responses.

Provide the structured JSON output.
"""

            # Call Ollama API (single call)
            response = self.client.generate(
                model='llama3',
                prompt=prompt,
                options={'temperature': 0.2, 'max_tokens': 1000}
            )
            structured_text = json.loads(response['response'])

            result = {
                "message_id": message_id,
                "status": "success",
                "structured_text": structured_text,
                "metadata": {
                    "processing_method": "ollama_structuring",
                    "original_dimensions": image_dimensions
                }
            }

            # Check message size
            message_json = json.dumps(result, ensure_ascii=False).encode('utf-8')
            message_size = len(message_json)
            max_size = 10_000_000  # 10MB
            if message_size > 0.9 * max_size:
                logger.warning(f"Message size ({message_size} bytes) is close to Kafka limit ({max_size} bytes) for message_id: {message_id}")

            # Send result to Kafka exactly once
            if producer:
                producer.send_result(result)

            return result

        except Exception as e:
            logger.error(f"Processing failed: {str(e)}", exc_info=True)
            result = {
                "message_id": message_id,
                "status": "error",
                "error": str(e)
            }
            if producer:
                producer.send_result(result)
            return result