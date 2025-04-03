# Image Filter Service

## Overview
This project is a FastAPI-based microservice designed for image preprocessing. It consumes images from a Kafka topic (`Input-Images`), applies a series of preprocessing steps, and sends the processed images to specific Kafka topics (`filtered-BS`, `filtered-ordonnances`, `filtered-facture`, etc.) for further processing (e.g., classification in another service).

## Preprocessing Pipeline
The image preprocessing steps include:
1. **Framing the image**: Correct perspective using OpenCV to avoid matrix out-of-bounds issues.
2. **Background removal**: Remove the background using OpenCV.
3. **Image enhancement**: Improve image quality (contrast and sharpness).
4. **Resizing**: Standardize the image size using OpenCV.
5. **Grayscale conversion**: Convert the image to grayscale.

## Project Structure
```
Image-Filter-Service/
│-- app/
│   │-- main.py           # FastAPI application entry point
│   │-- routes/
│   │   │-- preprocess.py  # API route for image preprocessing
│   │-- services/
│   │   │-- filter.py      # Image processing logic
│   │-- utils/
│   │   │-- kafka.py       # Kafka integration utilities
│-- config/
│   │-- settings.py       # Configuration settings
│-- Dockerfile           # Docker configuration
│-- docker-compose.yml   # Docker Compose setup
│-- requirements.txt     # Python dependencies
│-- README.md            # Project documentation
```

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/RayenR1/ImageFilterService.git
   cd ImageFilterService
   ```
2. Set up a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```
3. Start the service using Docker Compose:
   ```bash
   docker-compose up --build
   ```

## Authors
- **Rayen Jlassi** - Main Developer 

## License
© 2025 EyeQ - Esprit School of Engineering - Doxaria
