import base64
import cv2
import numpy as np
import easyocr
import torch
import logging
import uuid
from typing import Dict, Any, List
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from PIL import Image

logger = logging.getLogger(__name__)

class OCRProcessor:
    def __init__(self):
        self.reader = None
        self.model = None
        self.processor = None
        self.initialized = False

    def initialize(self):
        if not self.initialized:
            try:
                logger.info("Initializing OCR components...")
                self.reader = easyocr.Reader(['ar', 'en'])
                
                model_name = "NAMAA-Space/Qari-OCR-0.2.2.1-VL-2B-Instruct"
                self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                    model_name,
                    torch_dtype="auto",
                    device_map="auto"
                )
                self.processor = AutoProcessor.from_pretrained(model_name)
                
                self.initialized = True
                logger.info("OCR processor initialized successfully")
            except Exception as e:
                logger.error(f"Initialization failed: {str(e)}", exc_info=True)
                raise

    def process_entire_image(self, message: Dict[str, Any]) -> Dict[str, Any]:
        if not self.initialized:
            self.initialize()

        try:
            # Decode image
            if 'image' in message:
                image_bytes = base64.b64decode(message['image'])
            elif 'binary_data' in message:
                image_bytes = message['binary_data']
            else:
                raise ValueError("Message must contain 'image' or 'binary_data'")

            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("Failed to decode image")

            # Convert to PIL Image for Qwen2VL
            image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

            # Extract text and boxes with EasyOCR
            results = self.reader.readtext(image, detail=1, paragraph=False)
            
            # Prepare consolidated output
            extracted_data = []
            for (bbox, text, prob) in results:
                # Convert bbox to [x_min, y_min, x_max, y_max]
                x_min = min([point[0] for point in bbox])
                y_min = min([point[1] for point in bbox])
                x_max = max([point[0] for point in bbox])
                y_max = max([point[1] for point in bbox])
                
                extracted_data.append({
                    "text": text,
                    "confidence": float(prob),
                    "bbox": [x_min, y_min, x_max, y_max]
                })

            # Optional: Refine with Qwen2VL for the entire image
            prompt = "Extract all text from this document exactly as shown, preserving the original layout and structure."
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image_pil},
                        {"type": "text", "text": prompt},
                    ],
                }
            ]

            inputs = self.processor(
                text=self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True),
                images=[image_pil],
                return_tensors="pt"
            ).to(self.model.device)

            generated_ids = self.model.generate(**inputs, max_new_tokens=4000)
            full_text = self.processor.decode(
                generated_ids[0][inputs.input_ids.shape[1]:], 
                skip_special_tokens=True
            ).strip()

            # Combine results
            return {
                "message_id": message.get('message_id', str(uuid.uuid4())),
                "status": "success",
                "extracted_data": extracted_data,
                "full_text": full_text,
                "metadata": {
                    "processing_method": "full_image",
                    "image_dimensions": f"{image.shape[1]}x{image.shape[0]}"
                }
            }

        except Exception as e:
            logger.error(f"Processing failed: {str(e)}", exc_info=True)
            return {
                "message_id": message.get('message_id', str(uuid.uuid4())),
                "status": "error",
                "error": str(e)
            }