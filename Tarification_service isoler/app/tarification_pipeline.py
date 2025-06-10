#github:@YassineBenMaktouf | linkedin :Yassine Ben Maktouf

# app/ocr_pipeline.py

import cv2
import re
import easyocr
import csv
import os
import numpy as np
from PIL import Image
from transformers import VisionEncoderDecoderModel, TrOCRProcessor
from fuzzywuzzy import process as fuzzy_process
import json
import subprocess
import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA

MEDS_PATH = "Content/medicine_data_tn.csv"

# Helper to check Arabic text
def contains_arabic(text):
    return bool(re.search(r'[\u0600-\u06FF\u0750-\u077F]', text))

def process_image(image: np.ndarray, processor: TrOCRProcessor, model: VisionEncoderDecoderModel, output_dir="extracted"):
    # Resize
    print("Processing image...")
    scale_percent = 200
    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    dim = (width, height)
    image = cv2.resize(image, dim, interpolation=cv2.INTER_CUBIC)

    # Grayscale + threshold
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # OCR with EasyOCR
    reader = easyocr.Reader(['en', 'fr'], gpu=False)
    results = reader.readtext(thresh, detail=1, paragraph=False, text_threshold=0.3, low_text=0.2, link_threshold=0.3)

    # Prepare outputs
    txt_lines = []
    csv_lines = [("ligne", "texte", "bbox")]

    for idx, (bbox, text, prob) in enumerate(results):
        if contains_arabic(text):
            continue

        x_min = int(min(pt[0] for pt in bbox))
        y_min = int(min(pt[1] for pt in bbox))
        x_max = int(max(pt[0] for pt in bbox))
        y_max = int(max(pt[1] for pt in bbox))
        cropped = image[y_min:y_max, x_min:x_max]

        pil_img = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
        inputs = processor(images=pil_img, return_tensors="pt").pixel_values.to(model.device)
        generated_ids = model.generate(inputs)
        trocr_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        txt_lines.append(trocr_text)
        csv_lines.append((idx + 1, trocr_text, str(bbox)))

    # Save outputs
    os.makedirs(output_dir, exist_ok=True)

    txt_path = os.path.join(output_dir, "extraction_trocr.txt")
    csv_path = os.path.join(output_dir, "extraction_trocr.csv")

    with open(txt_path, "w", encoding="utf-8") as f_txt:
        for line in txt_lines:
            f_txt.write(line + "\n")

    with open(csv_path, "w", encoding="utf-8", newline='') as f_csv:
        writer = csv.writer(f_csv)
        writer.writerows(csv_lines)
    
    print("Image processing completed.")

    return {
        "lines": txt_lines,
        "txt_path": txt_path,
        "csv_path": csv_path
    }

def structure_with_llama(full_text: str, prompt_file="extracted/prompt_llama3.txt", json_output_path="extracted/donnees_structurees.json"):
    print("Structuring data ...")
    # Generate prompt
    prompt = f"""
Tu es un expert en extraction automatique de données de factures médicales.

🧾 Ta mission est de structurer ce texte brut issu d'une facture de pharmacie en un JSON strict, conforme aux règles suivantes :

1. Si une donnée n'est pas trouvée (par exemple prix_unitaire ou prix_total), mets `null` SANS ajouter de commentaire ou texte supplémentaire.
2. Ne jamais écrire des opérations mathématiques dans les valeurs (exemple interdit : "4.235 + 0.240"), effectue les calculs toi-même et écris directement le résultat numérique.
3. Toutes les valeurs doivent être soit :
    - un nombre pur (ex: 12.34)
    - une chaîne de caractères correcte (ex: "Paracétamol")
    - ou `null`
4. Les champs obligatoires sont :
    - nom_pharmacien (string)
    - code_cnam (string)
    - telephone (string)
    - adresse_pharmacie (string)
    - date_facture (string au format DD/MM/YYYY)
    - medicaments (liste d'objets avec les champs suivants) :
        - nom (string)
        - quantite (nombre entier ou null)
        - prix_unitaire (nombre flottant ou null)
        - prix_total (nombre flottant ou null)
5. **Important** : Ignore les textes parasites et déduis au mieux un nombre entier, sinon mets `null`.
6. Le JSON doit être renvoyé entre balises ```json ... ``` proprement.

Voici le texte brut à analyser :

{full_text}
"""

    # Write prompt
    os.makedirs("extracted", exist_ok=True)
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(prompt)

    # Call LLaMA via Ollama subprocess
    result = subprocess.run(
        [r"C:\Users\jlassi\AppData\Local\Programs\Ollama\ollama.exe", "run", "llama3"], #<- to be changed "ollama"
        stdin=open(prompt_file, "r", encoding="utf-8"),
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    if result.returncode != 0:
        raise RuntimeError(f"Ollama execution failed: {result.stderr}")

    match = re.search(r"```(?:json)?\s*({.*?})\s*```", result.stdout, re.DOTALL)
    if not match:
        raise ValueError("No valid JSON block found in LLaMA output")

    structured_data = json.loads(match.group(1))

    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(structured_data, f, indent=4, ensure_ascii=False)

    print("Data structuring completed.")
    return structured_data


def compute_tarification(structured_json: dict, output_dir="extracted"):
    print("Computing tarification ...")
    df_meds = pd.read_csv(MEDS_PATH)
    df_meds.columns = df_meds.columns.str.strip().str.lower()
    df_meds = df_meds.rename(columns={"nom médicament": "name", "prix": "price", "montant assuré": "remboursement"})

    resultats = []

    for med in structured_json["medicaments"]:
        nom_facture = med["nom"].strip().lower()
        quantite = med["quantite"] if med["quantite"] is not None else 1
        prix_unitaire = med["prix_unitaire"]
        prix_total = med["prix_total"]

        result = fuzzy_process.extractOne(nom_facture, df_meds["name"])
        match_nom, score = result[0], result[1] if result else (None, 0)

        if score >= 90:
            ligne_base = df_meds[df_meds["name"] == match_nom].iloc[0]
            remboursement = float(str(ligne_base["remboursement"]).replace(",", "."))
            montant_rembourse = remboursement * quantite

            prix_base = float(str(ligne_base["price"]).replace(",", "."))

            resultat = {
                "medicament_facture": nom_facture,
                "match_base": match_nom,
                "score_match": score,
                "quantite": quantite,
                "prix_unitaire_facture": prix_unitaire,
                "prix_total_facture": prix_total,
                "prix_base": prix_base,
                "remboursement_unitaire": remboursement,
                "remboursement_total": montant_rembourse
            }
        else:
            resultat = {
                "medicament_facture": nom_facture,
                "match_base": None,
                "score_match": score,
                "quantite": quantite,
                "prix_unitaire_facture": prix_unitaire,
                "prix_total_facture": prix_total,
                "prix_base": None,
                "remboursement_unitaire": 0,
                "remboursement_total": 0
            }

        resultats.append(resultat)

    df_tarif = pd.DataFrame(resultats)
    df_tarif["prix_total_facture"] = pd.to_numeric(df_tarif["prix_total_facture"], errors="coerce")
    df_tarif["remboursement_total"] = pd.to_numeric(df_tarif["remboursement_total"], errors="coerce")

    total_facture = df_tarif["prix_total_facture"].sum()
    total_rembourse = df_tarif["remboursement_total"].sum()
    pourcentage_rembourse = round((total_rembourse / total_facture) * 100, 2) if total_facture > 0 else 0.0

    resume = {
        "Total Facturé (DT)": f"{total_facture:,.2f}",
        "Total Remboursé (DT)": f"{total_rembourse:,.2f}",
        "Taux de Remboursement (%)": f"{pourcentage_rembourse:.2f} %"
    }

    # Save outputs
    df_tarif.to_csv(os.path.join(output_dir, "detail_medicaments.csv"), index=False)
    df_tarif.to_json(os.path.join(output_dir, "resultats_tarifaires.json"), orient="records", force_ascii=False, indent=2)
    with open(os.path.join(output_dir, "resume_remboursement.json"), "w", encoding="utf-8") as f:
        json.dump(resume, f, ensure_ascii=False, indent=2)

    print("Tarification computation completed.")
    return {
        "details": resultats,
        "summary": resume
    }

def estimate_future_reserve_simple(df_tarif, nombre_demandes_futures=500, facteur_prudence=1.1):
    print("Estimating future reserve ...")
    remboursement_moyen = df_tarif["remboursement_total"].replace(0, pd.NA).dropna().mean()
    reserve_estimee = remboursement_moyen * nombre_demandes_futures
    reserve_avec_marge = reserve_estimee * facteur_prudence

    print("Future reserve estimation completed.")

    return {
        "remboursement_moyen": remboursement_moyen,
        "reserve_estimee": reserve_estimee,
        "reserve_avec_marge": reserve_avec_marge
    }

def forecast_linear_trend(df_tarif, data_facture_date_str):
    print("Forecasting linear trend ...")
    df_tarif = df_tarif.copy()
    df_tarif["date"] = pd.to_datetime(data_facture_date_str, dayfirst=True)
    df_monthly = df_tarif.groupby(df_tarif["date"].dt.to_period("M")).agg({
        "remboursement_total": "sum"
    }).reset_index()
    df_monthly["date"] = df_monthly["date"].dt.to_timestamp()
    df_monthly = df_monthly.sort_values("date")

    df_monthly["mois_num"] = np.arange(len(df_monthly))
    X = df_monthly[["mois_num"]]
    y = df_monthly["remboursement_total"]

    model = LinearRegression()
    model.fit(X, y)

    future_months = np.arange(len(df_monthly), len(df_monthly) + 12)
    future_dates = pd.date_range(start=df_monthly["date"].max() + pd.offsets.MonthBegin(1), periods=12, freq='MS')
    predictions = model.predict(future_months.reshape(-1, 1))

    reserve_estimee = predictions.sum()
    reserve_avec_marge = reserve_estimee * 1.1

    # Save graph
    plt.figure(figsize=(12, 6))
    plt.plot(df_monthly["date"], y, label="Remboursement observé", marker='o')
    plt.plot(future_dates, predictions, label="Prévision (12 mois)", linestyle="--", marker='x')
    plt.fill_between(future_dates, predictions, predictions * 1.1, alpha=0.2, label="Marge (10%)", color="orange")
    plt.legend()
    plt.title("Prévision Remboursements - Linéaire")
    plt.xlabel("Date")
    plt.ylabel("Montant remboursé (TD)")
    plt.grid(True)
    plt.tight_layout()

    os.makedirs("extracted", exist_ok=True)
    plt.savefig("extracted/forecast_linear.png")
    plt.close()

    print("Linear trend forecasting completed.")

    return {
        "reserve_estimee": reserve_estimee,
        "reserve_avec_marge": reserve_avec_marge
    }

def forecast_arima(df_tarif, data_facture_date_str):
    print("Forecasting with ARIMA ...")
    df = df_tarif.copy()
    df["date"] = pd.to_datetime(data_facture_date_str, dayfirst=True)
    df_monthly = df.groupby(df["date"].dt.to_period("M")).agg({
        "remboursement_total": "sum"
    }).reset_index()
    df_monthly["date"] = df_monthly["date"].dt.to_timestamp()

    df_arima = df_monthly.rename(columns={"date": "ds", "remboursement_total": "y"}).set_index("ds")

    model = ARIMA(df_arima["y"], order=(1, 1, 1))
    model_fit = model.fit()
    forecast = model_fit.forecast(steps=12)

    reserve_estimee = forecast.sum()
    reserve_avec_marge = reserve_estimee * 1.1

    # Save plot
    future_dates = pd.date_range(df_arima.index[-1] + pd.offsets.MonthBegin(), periods=12, freq='MS')
    plt.figure(figsize=(10, 6))
    plt.plot(df_arima.index, df_arima["y"], label="Historique")
    plt.plot(future_dates, forecast, label="Prévisions ARIMA", color='red')
    plt.title("Prévision des remboursements mensuels (ARIMA)")
    plt.xlabel("Date")
    plt.ylabel("Montant remboursé (TD)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    os.makedirs("extracted", exist_ok=True)
    plt.savefig("extracted/forecast_arima.png")
    plt.close()

    print("ARIMA forecasting completed.")

    return {
        "reserve_estimee": reserve_estimee,
        "reserve_avec_marge": reserve_avec_marge
    }
