import cv2
import numpy as np
from typing import Tuple, Optional

def preprocess_image(image: np.ndarray) -> np.ndarray:
    """Preprocess image for better OCR results"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    return enhanced

def calculate_iou(box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
    """Calculate Intersection over Union for two bounding boxes"""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    
    return intersection / float(area1 + area2 - intersection)

def merge_boxes(boxes: list, iou_threshold: float = 0.5) -> list:
    """Merge overlapping bounding boxes"""
    if not boxes:
        return []
    
    boxes = sorted(boxes, key=lambda x: x[0])
    merged = [boxes[0]]
    
    for box in boxes[1:]:
        last = merged[-1]
        if calculate_iou(last, box) > iou_threshold:
            new_box = (
                min(last[0], box[0]),
                min(last[1], box[1]),
                max(last[2], box[2]),
                max(last[3], box[3])
            )
            merged[-1] = new_box
        else:
            merged.append(box)
    
    return merged