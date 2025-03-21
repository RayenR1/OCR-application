# app/models/model_loader.py
from ultralytics import YOLO

class ModelLoader:
    def __init__(self, model_path):
        self.model_path = model_path
        self.model = None

    def load_model(self):
        try:
            self.model = YOLO(self.model_path)
            return self.model
        except Exception as e:
            raise Exception(f"Failed to load model from {self.model_path}: {str(e)}")

    def update_model(self, new_model_path):
        self.model_path = new_model_path
        self.model = None  # Reset model
        return self.load_model()