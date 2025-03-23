# Image Filter Service

## Overview
This project is a FastAPI-based microservice designed for image preprocessing. It consumes images from a Kafka topic (`Input-Images`), applies a series of preprocessing steps, and sends the processed images to specific Kafka topics (`filtered-BS`, `filtered-ordonnances`, `filtered-facture`, etc.) for further processing (e.g., classification in another service).

The preprocessing pipeline includes:
1. **Framing the image**: Correct perspective using OpenCV to avoid matrix out-of-bounds issues.
2. **Background removal**: Remove the background using OpenCV.
3. **Image enhancement**: Improve image quality (contrast and sharpness).
4. **Resizing**: Standardize the image size using OpenCV.
5. **Grayscale conversion**: Convert the image to grayscale.

## Project Structure