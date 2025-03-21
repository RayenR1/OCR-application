# app/models/classifier.py
import cv2
import numpy as np

class YOLOClassifier:
    def __init__(self, model):
        self.model = model
        self.class_names = {
            0: "Bulltin soin",
            1: "autre",
            2: "facture",
            3: "ordonnances"
        }

    def classify(self, image):
        # Resize image to 224x224 (YOLOv11 input size)
        input_image = cv2.resize(image, (224, 224))

        # Perform classification
        results = self.model(input_image)
        probs = results[0].probs
        class_id = probs.top1
        confidence = probs.top1conf.item()

        # Get class name
        class_name = self.class_names.get(class_id, "Inconnu")

        # Overlay text on the original image
        text = f"{class_name} ({confidence:.2f})"
        cv2.putText(image, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        return image, class_name, confidence