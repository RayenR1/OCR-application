import base64
import cv2
import numpy as np
import easyocr
import os
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
        self.max_tokens = 2000
        self.min_image_size = 32  # Taille minimale pour le modèle Qwen
        self.initialized = False

    def initialize(self):
        if not self.initialized:
            try:
                logger.info("Initializing EasyOCR reader...")
                self.reader = easyocr.Reader(['ar', 'en'])
                
                logger.info("Loading Qwen model...")
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

    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        if not self.initialized:
            self.initialize()

        try:
            # Validation et décodage de l'image
            image = self._decode_image(message)
            if image is None:
                raise ValueError("Invalid image data")

            # Traitement des régions d'intérêt
            layout_data = message.get('layout_data', {})
            line_texts, table_texts = self._process_regions(image, layout_data)

            return {
                "message_id": message.get('message_id', str(uuid.uuid4())),
                "status": "success",
                "extracted_text": self._format_output(image.shape[1], layout_data, line_texts, table_texts),
                "metadata": {
                    "lines_processed": len(line_texts),
                    "tables_processed": len(table_texts)
                }
            }

        except Exception as e:
            logger.error(f"Processing failed: {str(e)}", exc_info=True)
            return {
                "message_id": message.get('message_id', str(uuid.uuid4())),
                "status": "error",
                "error": str(e)
            }

    def _decode_image(self, message: Dict[str, Any]) -> np.ndarray:
        """Décode l'image à partir du message"""
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
            
        return image

    def _process_regions(self, image: np.ndarray, layout_data: Dict[str, Any]) -> tuple:
        """Traite toutes les régions d'intérêt dans l'image"""
        lines = layout_data.get('lines', [])
        tables = layout_data.get('tables', {})
        
        # Traitement des lignes
        line_texts = []
        for line in lines:
            bbox = line.get('bounding_box', [])
            if len(bbox) != 4:
                line_texts.append([])
                continue
                
            crop = self._safe_crop(image, bbox)
            texts = self._extract_text(crop) if crop is not None else []
            line_texts.append(self._adjust_coordinates(texts, bbox))

        # Traitement des tables
        table_texts = {}
        for table_key, table_coords in tables.items():
            try:
                table_bbox = [float(x) for x in table_key.strip("()").split(",")]
                if len(table_bbox) != 4:
                    continue
                    
                crop = self._safe_crop(image, table_bbox)
                texts = self._extract_text(crop) if crop is not None else []
                table_texts[table_key] = self._adjust_coordinates(texts, table_bbox)
            except Exception as e:
                logger.error(f"Table processing error: {str(e)}")
                continue

        return line_texts, table_texts

    def _safe_crop(self, image: np.ndarray, bbox: List[float], padding: int = 5) -> np.ndarray:
        """Extrait une région de l'image avec vérification des limites"""
        try:
            x_min, y_min, x_max, y_max = [int(round(x)) for x in bbox]
            x_min = max(0, x_min - padding)
            y_min = max(0, y_min - padding)
            x_max = min(image.shape[1], x_max + padding)
            y_max = min(image.shape[0], y_max + padding)
            
            if x_max <= x_min or y_max <= y_min:
                return None
                
            crop = image[y_min:y_max, x_min:x_max]
            
            # Vérification de la taille minimale
            if crop.shape[0] < self.min_image_size or crop.shape[1] < self.min_image_size:
                scale = max(self.min_image_size/crop.shape[0], self.min_image_size/crop.shape[1])
                crop = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                
            return crop
            
        except Exception as e:
            logger.debug(f"Crop error: {str(e)}")
            return None

    def _extract_text(self, crop: np.ndarray) -> List[Dict[str, Any]]:
        """Extrait le texte d'une région d'image"""
        if crop is None or crop.size == 0:
            return []
            
        try:
            # Pré-traitement de l'image
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            
            # Détection avec EasyOCR
            easyocr_results = self.reader.readtext(thresh, detail=1, paragraph=False)
            texts = []
            
            for (bbox, text, prob) in easyocr_results:
                try:
                    (tl, tr, br, _) = bbox
                    x_min, y_min = map(int, tl)
                    x_max, y_max = map(int, br)
                    
                    # Extraction de la sous-région
                    sub_crop = crop[
                        max(0, y_min-2):min(crop.shape[0], y_max+2),
                        max(0, x_min-2):min(crop.shape[1], x_max+2)
                    ]
                    
                    if sub_crop.size == 0:
                        continue
                        
                    # Traitement avec Qwen2VL si la région est valide
                    if sub_crop.shape[0] >= 28 and sub_crop.shape[1] >= 28:
                        final_text = self._process_with_qwen(sub_crop) or text
                    else:
                        final_text = text
                    
                    if final_text.strip():
                        texts.append({
                            "text": final_text,
                            "box": [x_min, y_min, x_max, y_max],
                            "confidence": float(prob)
                        })
                        
                except Exception as e:
                    logger.debug(f"Text element skipped: {str(e)}")
                    continue
                    
            return texts
            
        except Exception as e:
            logger.error(f"Text extraction error: {str(e)}")
            return []

    def _process_with_qwen(self, image: np.ndarray) -> str:
        """Utilise Qwen2VL pour extraire le texte"""
        try:
            temp_path = "temp_crop.png"
            cv2.imwrite(temp_path, image)
            
            prompt = "Extract the text exactly as shown in the image without any modifications."
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": f"file://{temp_path}"},
                        {"type": "text", "text": prompt},
                    ],
                }
            ]
            
            inputs = self.processor(
                text=self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True),
                images=[image],
                return_tensors="pt"
            ).to(self.model.device)
            
            generated_ids = self.model.generate(**inputs, max_new_tokens=self.max_tokens)
            generated_text = self.processor.decode(
                generated_ids[0][inputs.input_ids.shape[1]:], 
                skip_special_tokens=True
            ).strip()
            
            os.remove(temp_path)
            return generated_text
            
        except Exception as e:
            logger.error(f"Qwen processing failed: {str(e)}")
            return ""

    def _adjust_coordinates(self, texts: List[Dict[str, Any]], bbox: List[float]) -> List[Dict[str, Any]]:
        """Ajuste les coordonnées par rapport à l'image originale"""
        return [{
            **text,
            "box": [
                text["box"][0] + bbox[0],
                text["box"][1] + bbox[1],
                text["box"][2] + bbox[0],
                text["box"][3] + bbox[1]
            ]
        } for text in texts]

    def _format_output(self, image_width: int, layout_data: Dict[str, Any], 
                      line_texts: List[List[Dict[str, Any]]], 
                      table_texts: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Formate le résultat final en texte structuré"""
        formatted = []
        midpoint = image_width / 2
        
        # Traitement des lignes (gauche et droite)
        for i, line in enumerate(layout_data.get('lines', [])):
            bbox = line.get('bounding_box', [])
            if not bbox or i >= len(line_texts):
                continue
                
            is_left_side = bbox[0] < midpoint
            texts = sorted(
                line_texts[i],
                key=lambda t: t["box"][0] if is_left_side else -t["box"][0]
            )
            
            line_text = " ".join(t["text"] for t in texts if t["text"].strip())
            if line_text:
                formatted.append(line_text)

        # Traitement des tables
        for table_key, texts in table_texts.items():
            if not texts:
                continue
                
            # Regroupement par ligne
            rows = []
            current_row = []
            current_y = None
            
            for text in sorted(texts, key=lambda t: t["box"][1]):
                y = text["box"][1]
                if current_y is None or abs(y - current_y) < 20:  # Tolérance verticale
                    current_row.append(text)
                    current_y = y if current_y is None else current_y
                else:
                    if current_row:
                        rows.append(sorted(current_row, key=lambda t: t["box"][0]))
                    current_row = [text]
                    current_y = y
                    
            if current_row:
                rows.append(sorted(current_row, key=lambda t: t["box"][0]))
            
            # Formatage des lignes
            for row in rows:
                row_text = " | ".join(t["text"] for t in row if t["text"].strip())
                if row_text:
                    formatted.append(row_text)

        return formatted