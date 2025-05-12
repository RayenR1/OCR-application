import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

def preprocess_image(image):
    """
    Preprocess image for OCR (e.g., enhance contrast).
    """
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        enhanced = cv2.equalizeHist(gray)
        return enhanced
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        return image