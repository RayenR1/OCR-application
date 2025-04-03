# YOLO Classification Service

This project implements a FastAPI service for classifying images using a YOLOv11 model, integrated with Kafka for asynchronous processing and MLflow for model versioning.

## Folder Structure
```
YOLO-Classification-Service/
│-- app/
│   │-- main.py        # FastAPI application entry point
│   │-- config.py      # Configuration settings
│   │-- models/        # Model loading and classification logic
│   │-- kafka/         # Kafka consumer and producer
│   │-- mlflow/        # MLflow model versioning
│-- data/             # Optional folder for test images
│-- Model_Reports/    # Model reports (confusion matrix, etc.)
│-- weights/          # Stores YOLOv11 model weights
│-- notebooks/        # Jupyter notebooks for training YOLOv11 classification
│-- requirements.txt  # Python dependencies
│-- Dockerfile        # Docker configuration
```

## Setup
1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Local Testing
Run the FastAPI server:
```bash
c:\users\jlassi\miniconda3\envs\PIDS\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Start the MLflow UI:
```bash
mlflow ui --port 5000
```

Test classification with `curl`:
```bash
curl -X POST -F "file=@C:\Users\jlassi\Desktop\data\BS\BSComar\realComar2.jpg" http://localhost:8000/classify
```


## Authors
- **Rayen Jlassi** - Main Developer 

## License
© 2025 EyeQ - Esprit School of Engineering - Doxaria