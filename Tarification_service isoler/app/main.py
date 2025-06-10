#github:@YassineBenMaktouf | linkedin :Yassine Ben Maktouf
from fastapi.middleware.cors import CORSMiddleware
# app/main.py

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from io import BytesIO
from PIL import Image
import numpy as np
import pandas as pd
import cv2
from app.config import processor, model
from app.tarification_pipeline import process_image, structure_with_llama, compute_tarification,estimate_future_reserve_simple, forecast_linear_trend, forecast_arima

app = FastAPI(title="Tarification")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:4201"], # Adjust to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.post("/extract/")
async def extract_text(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        return JSONResponse(status_code=400, content={"error": "Invalid image format"})

    contents = await file.read()
    image = Image.open(BytesIO(contents)).convert("RGB")
    image_np = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    results = process_image(image_np, processor, model)
    return {
        "extracted_lines": results["lines"],
        "text_file": results["txt_path"],
        "csv_file": results["csv_path"]
    }

@app.post("/Tarification")
async def full_ocr_pipeline(file: UploadFile = File(...)):
    print("Process started ...")
    
    print(f"Received file: {file.filename}, Content-Type: {file.content_type}, Size: {file.size}")

    if not file.content_type.startswith("image/"):
        return JSONResponse(status_code=400, content={"error": f"Invalid image format: {file.content_type}"})

    try:
        contents = await file.read()
        print(f"File contents read, size: {len(contents)} bytes")
        
        if len(contents) == 0:
            return JSONResponse(status_code=422, content={"error": "File contents are empty"})

        with open(f"debug_{file.filename}", "wb") as f:
            f.write(contents)
        print(f"Saved received file as debug_{file.filename}")

        try:
            image = Image.open(BytesIO(contents))
            print(f"Image opened successfully, mode: {image.mode}")
            image = image.convert("RGB")
        except Exception as img_error:
            print(f"Failed to open image: {str(img_error)}")
            return JSONResponse(status_code=422, content={"error": f"Failed to open image: {str(img_error)}"})

        print("Processing image...")
        image_np = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        ocr_result = process_image(image_np, processor, model)
        print("Image processing completed.")

        print("Reading CSV and extracting text...")
        try:
            df = pd.read_csv(ocr_result["csv_path"])
            print(f"CSV read successfully, columns: {df.columns}")
            full_text = "\n".join(df["texte"].dropna().astype(str))
            print(f"Extracted full_text (first 100 chars): {full_text[:100]}")
        except Exception as csv_error:
            print(f"Error reading CSV: {str(csv_error)}")
            return JSONResponse(status_code=422, content={"error": f"Failed to read CSV: {str(csv_error)}"})

        print("Structuring data ...")
        try:
            structured = structure_with_llama(full_text)
            print(f"Structured data: {structured}")
        except Exception as struct_error:
            print(f"Error in structure_with_llama: {str(struct_error)}")
            return JSONResponse(status_code=422, content={"error": f"Failed to structure data: {str(struct_error)}"})

        print("Computing tarification...")
        try:
            matched = compute_tarification(structured)
            print(f"Tarification summary: {matched['summary']}")
        except Exception as tarif_error:
            print(f"Error in compute_tarification: {str(tarif_error)}")
            return JSONResponse(status_code=422, content={"error": f"Failed to compute tarification: {str(tarif_error)}"})

        print("Reading resultats_tarifaires.json...")
        try:
            df_tarif = pd.read_json("extracted/resultats_tarifaires.json")
            print(f"resultats_tarifaires.json read successfully, shape: {df_tarif.shape}")
        except Exception as json_error:
            print(f"Error reading resultats_tarifaires.json: {str(json_error)}")
            return JSONResponse(status_code=422, content={"error": f"Failed to read resultats_tarifaires.json: {str(json_error)}"})

        date_facture_str = structured["date_facture"]

        print("Estimating reserves...")
        reserve_simple = estimate_future_reserve_simple(df_tarif)
        reserve_linear = forecast_linear_trend(df_tarif, date_facture_str)
        reserve_arima = forecast_arima(df_tarif, date_facture_str)

        print("Process finished.")

        return {
            "success": True,
            "structured_data": structured,
            "tarification_summary": matched["summary"],
            "reserve_estimation_simple": reserve_simple,
            "forecast_linear": reserve_linear,
            "forecast_arima": reserve_arima
        }
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return JSONResponse(status_code=422, content={"error": f"Failed to process image: {str(e)}"})