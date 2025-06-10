#github:@YassineBenMaktouf | linkedin :Yassine Ben Maktouf

# app/config.py
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

PORT = 8001  # Port for the server
HOST = "127.0.0.1"

# Load pre-trained TrOCR model and processor
processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-printed')
model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-printed')