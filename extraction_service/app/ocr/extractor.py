import cv2
import easyocr
import numpy as np
from PIL import Image
import os
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
import json
from app.config import CONFIDENCE_THRESHOLD, MAX_TOKENS
import logging

logger = logging.getLogger(__name__)

class TextExtractor:
    def __init__(self):
        
     # Initialize Qari-OCR model
        model_name = "NAMAA-Space/Qari-OCR-0.2.2.1-VL-2B-Instruct"
        model = Qwen2VLForConditionalGeneration.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto"
            )
        self.processor = AutoProcessor.from_pretrained(model_name)
        self.reader = easyocr.Reader(['ar', 'en'])
        logger.info("Initialized Qari-OCR and EasyOCR")

    def safe_crop(self, image, bbox):
        x_min, y_min, x_max, y_max = [int(x) for x in bbox]
        x_min = max(0, x_min - 10)
        y_min = max(0, y_min - 10)
        x_max = min(image.shape[1], x_max + 10)
        y_max = min(image.shape[0], y_max + 10)
        if x_max <= x_min or y_max <= y_min:
            return None
        return image[y_min:y_max, x_min:x_max]

    def extract_text_from_crop(self, crop):
        if crop is None:
            return []
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        easyocr_results = self.reader.readtext(thresh, detail=1, paragraph=False)
        texts = []
        for (bbox, text, prob) in easyocr_results:
            if prob < CONFIDENCE_THRESHOLD:
                continue
            (top_left, top_right, bottom_right, bottom_left) = bbox
            top_left = (int(top_left[0]), int(top_left[1]))
            bottom_right = (int(bottom_right[0]), int(bottom_right[1]))
            sub_crop = crop[max(0, top_left[1]-5):bottom_right[1]+5, max(0, top_left[0]-5):bottom_right[0]+5]
            if sub_crop.size == 0:
                continue
            crop_pil = Image.fromarray(cv2.cvtColor(sub_crop, cv2.COLOR_BGR2RGB))
            temp_img_path = "temp_crop.png"
            crop_pil.save(temp_img_path)
            prompt = "Extract the plain text from the provided image as if you were reading it naturally. Do not hallucinate."
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": f"file://{temp_img_path}"},
                        {"type": "text", "text": prompt},
                    ],
                }
            ]
            text_input = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            image_inputs, video_inputs = process_vision_info(messages)
            inputs = self.processor(
                text=[text_input], images=image_inputs, videos=video_inputs, padding=True, return_tensors="pt"
            )
            inputs = inputs.to("cuda" if torch.cuda.is_available() else "cpu")
            generated_ids = self.model.generate(**inputs, max_new_tokens=MAX_TOKENS)
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            qari_text = self.processor.batch_decode(
                generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )[0].strip()
            os.remove(temp_img_path)
            final_text = qari_text or text
            if final_text:
                texts.append({
                    "text": final_text,
                    "box": [top_left[0], top_left[1], bottom_right[0], bottom_right[1]]
                })
        return texts

    def extract_text(self, image, layout_data):
        image_height, image_width = image.shape[:2]
        lines = layout_data.get("lines", [])
        tables = layout_data.get("tables", {})

        # Identify table headers
        table_headers = {}
        for table_key, table_coords in tables.items():
            table_bbox = [float(x) for x in table_key.strip("()").split(",")]
            table_y_min = table_bbox[1]
            header_line = None
            min_y_diff = float("inf")
            for i, line in enumerate(lines):
                line_y_max = line["bounding_box"][3]
                if line_y_max <= table_y_min and table_y_min - line_y_max < min_y_diff:
                    min_y_diff = table_y_min - line_y_max
                    header_line = i
            if header_line is not None and min_y_diff < 50:
                table_headers[table_key] = header_line

        # Group lines by left and right side
        midpoint = image_width / 2
        left_lines = [i for i, line in enumerate(lines) if line["bounding_box"][0] < midpoint]
        right_lines = [i for i, line in enumerate(lines) if line["bounding_box"][0] >= midpoint]

        # Process lines
        line_texts = [[] for _ in lines]
        for i, line in enumerate(lines):
            if i in table_headers.values():
                continue
            bbox = line["bounding_box"]
            crop = self.safe_crop(image, bbox)
            texts = self.extract_text_from_crop(crop)
            for text in texts:
                text["box"][0] += bbox[0]
                text["box"][2] += bbox[0]
                text["box"][1] += bbox[1]
                text["box"][3] += bbox[1]
            line_texts[i] = texts

        # Process tables
        table_texts = {key: [] for key in tables}
        for table_key, table_coords in tables.items():
            table_bbox = [float(x) for x in table_key.strip("()").split(",")]
            crop = self.safe_crop(image, table_bbox)
            texts = self.extract_text_from_crop(crop)
            for text in texts:
                text["box"][0] += table_bbox[0]
                text["box"][2] += table_bbox[0]
                text["box"][1] += table_bbox[1]
                text["box"][3] += table_bbox[1]
            table_texts[table_key] = texts
            header_idx = table_headers.get(table_key)
            if header_idx is not None:
                header_bbox = lines[header_idx]["bounding_box"]
                crop = self.safe_crop(image, header_bbox)
                header_texts = self.extract_text_from_crop(crop)
                for text in header_texts:
                    text["box"][0] += header_bbox[0]
                    text["box"][2] += header_bbox[0]
                    text["box"][1] += header_bbox[1]
                    text["box"][3] += header_bbox[1]
                line_texts[header_idx] = header_texts

        # Format output
        formatted_text = []
        for line_idx in sorted(left_lines, key=lambda i: lines[i]["bounding_box"][1]):
            if line_idx in table_headers.values():
                continue
            texts = line_texts[line_idx]
            if not texts:
                continue
            texts.sort(key=lambda t: t["box"][0])
            line_text = " ".join(t["text"] for t in texts if t["text"].strip())
            if line_text:
                formatted_text.append(line_text)

        for line_idx in sorted(right_lines, key=lambda i: lines[i]["bounding_box"][1]):
            if line_idx in table_headers.values():
                continue
            texts = line_texts[line_idx]
            if not texts:
                continue
            texts.sort(key=lambda t: -t["box"][0])
            line_text = " ".join(t["text"] for t in texts if t["text"].strip())
            if line_text:
                formatted_text.append(line_text)

        for table_key, table_coords in tables.items():
            table_bbox = [float(x) for x in table_key.strip("()").split(",")]
            texts = table_texts[table_key]
            if not texts:
                continue
            col_names = []
            col_positions = []
            header_idx = table_headers.get(table_key)
            if header_idx is not None:
                header_texts = line_texts[header_idx]
                header_texts.sort(key=lambda t: t["box"][0])
                col_names = [t["text"] for t in header_texts if t["text"].strip()]
                col_positions = [(t["box"][0] + t["box"][2]) / 2 for t in header_texts]
            texts.sort(key=lambda t: t["box"][1])
            rows = []
            current_row = []
            current_y = None
            y_tolerance = 20
            for text in texts:
                y = text["box"][1]
                if current_y is None or abs(y - current_y) < y_tolerance:
                    current_row.append(text)
                    current_y = y if current_y is None else current_y
                else:
                    if current_row:
                        rows.append(current_row)
                    current_row = [text]
                    current_y = y
            if current_row:
                rows.append(current_row)
            aligned_rows = []
            for row in rows:
                row.sort(key=lambda t: t["box"][0])
                row_positions = [(t["box"][0] + t["box"][2]) / 2 for t in row]
                aligned_row = [""] * len(col_names)
                for text, pos in zip([t["text"] for t in row], row_positions):
                    if col_positions:
                        closest_col_idx = min(range(len(col_positions)), key=lambda i: abs(col_positions[i] - pos))
                        aligned_row[closest_col_idx] = text
                aligned_rows.append(aligned_row)
            max_widths = [max(len(col_names[i]) if i < len(col_names) else 0,
                             max((len(row[i]) if i < len(row) else 0) for row in aligned_rows))
                         for i in range(max(len(col_names), max(len(row) for row in aligned_rows)))]
            if col_names:
                header_row = " | ".join(col_names[i].ljust(max_widths[i]) if i < len(col_names) else "".ljust(max_widths[i])
                                       for i in range(len(max_widths)))
                formatted_text.append(header_row)
                formatted_text.append("-" * len(header_row))
            for row in aligned_rows:
                row_text = " | ".join(row[i].ljust(max_widths[i]) if i < len(row) else "".ljust(max_widths[i])
                                     for i in range(len(max_widths)))
                formatted_text.append(row_text)

        return "\n".join(formatted_text)