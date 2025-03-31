# app/utils/image_utils.py
#github:@RayenR1 | linkedin :Rayen Jlassi
import cv2
import numpy as np

def decode_image(image_bytes):
    """Désérialise les bytes d'une image en tableau NumPy."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return image if image is not None else None