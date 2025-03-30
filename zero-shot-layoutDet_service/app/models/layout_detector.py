# app/models/layout_detector.py
#github:@RayenR1 | linkedin :Rayen Jlassi
import numpy as np
import cv2
from PIL import Image
import re
from paddleocr import PaddleOCR
import json

# Configuration OCR
OCR_ENGINE = PaddleOCR(
    use_angle_cls=True,
    lang="fr",
    use_gpu=False,
    det_db_thresh=0.4,
    det_db_box_thresh=0.5,
    det_db_unclip_ratio=2.0,
    rec_algorithm="SVTR_LCNet",
    max_text_length=100,
)

# -------- FONCTIONS DE DÉTECTION DE TABLEAUX --------
def adaptive_threshold(image, process_background=False, blocksize=15, c=-2):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if process_background:
        threshold = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blocksize, c
        )
    else:
        threshold = cv2.adaptiveThreshold(
            np.invert(gray),
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blocksize,
            c,
        )
    return image, threshold

def find_lines(threshold, regions=None, direction="horizontal", line_scale=15, iterations=0):
    lines = []
    if direction == "vertical":
        size = threshold.shape[0] // line_scale
        el = cv2.getStructuringElement(cv2.MORPH_RECT, (1, size))
    elif direction == "horizontal":
        size = threshold.shape[1] // line_scale
        el = cv2.getStructuringElement(cv2.MORPH_RECT, (size, 1))
    else:
        raise ValueError("Direction doit être 'vertical' ou 'horizontal'")

    if regions is not None:
        region_mask = np.zeros(threshold.shape)
        for region in regions:
            x, y, w, h = region
            region_mask[y:y + h, x:x + w] = 1
        threshold = np.multiply(threshold, region_mask)

    threshold = cv2.erode(threshold, el)
    threshold = cv2.dilate(threshold, el)
    dmask = cv2.dilate(threshold, el, iterations=iterations)

    try:
        _, contours, _ = cv2.findContours(
            threshold.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
    except ValueError:
        contours, _ = cv2.findContours(
            threshold.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        x1, x2 = x, x + w
        y1, y2 = y, y + h
        if direction == "vertical":
            lines.append(((x1 + x2) // 2, y2, (x1 + x2) // 2, y1))
        elif direction == "horizontal":
            lines.append((x1, (y1 + y2) // 2, x2, (y1 + y2) // 2))
    return dmask, lines

def find_contours(vertical, horizontal):
    mask = vertical + horizontal
    try:
        _, contours, _ = cv2.findContours(
            mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
    except ValueError:
        contours, _ = cv2.findContours(
            mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
    cont = []
    for c in contours:
        c_poly = cv2.approxPolyDP(c, 3, True)
        x, y, w, h = cv2.boundingRect(c_poly)
        cont.append((x, y, w, h))
    return cont, mask

def find_joints(contours, vertical, horizontal):
    joints = np.multiply(vertical, horizontal)
    tables = {}
    for c in contours:
        x, y, w, h = c
        roi = joints[y:y + h, x:x + w]
        try:
            _, jc, _ = cv2.findContours(
                roi.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
            )
        except ValueError:
            jc, _ = cv2.findContours(
                roi.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
            )
        if len(jc) <= 4:
            continue
        joint_coords = []
        for j in jc:
            jx, jy, jw, jh = cv2.boundingRect(j)
            c1, c2 = x + (2 * jx + jw) // 2, y + (2 * jy + jh) // 2
            joint_coords.append((c1, c2))
        tables[(x, y + h, x + w, y)] = joint_coords
    return tables

# -------- FONCTIONS D'EXTRACTION DES CHAMPS --------
def contains_arabic(text):
    return bool(re.search("[\u0600-\u06FF]", text))

def is_likely_handwritten(text, box, image):
    width = box[2][0] - box[0][0]
    height = box[2][1] - box[0][1]
    aspect_ratio = width / height if height > 0 else 0
    if aspect_ratio < 0.5 or aspect_ratio > 10 or len(text) < 3:
        return True
    return False

def is_likely_field_name(text):
    text = text.strip().upper()
    word_count = len(text.split())
    if word_count > 6:
        return False

    field_keywords = [
        "NOM", "PRENOM", "ADRESSE", "MATRICULE", "DATE", "MONTANT", "CODE",
        "VISA", "HONORAIRES", "DESIGNATION", "TOTAL", "OBSERVATIONS", "FRAIS",
        "NUMERO", "SIGNATURE", "RESERVE", "SORTIE", "ENTREE", "MATRICULE FISCAL"
    ]
    if any(keyword in text for keyword in field_keywords):
        return True

    non_field_patterns = [
        r"BULLETIN DE SOINS",
        r"RESERVE A L'ETABLISSEMENT HOSPITALIER",
        r"RESERVE A STAR",
        r"RESERVE AUX MEDECINS ET PRATICIENS",
        r"POUR LES CHIRURGIES OU DE TRAITEMENTS SPECIAUX",
        r"IL FAUT JOINDRE AU BULLETIN DE SOINS"
    ]
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in non_field_patterns):
        return False

    if len(text) > 50:
        return False

    return True

def preprocess_image(image, mode):
    image_np = np.array(image)
    if mode == "grayscale":
        return cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    elif mode == "rgb":
        return image_np
    elif mode == "binary":
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
        return cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, -2
        )
    elif mode == "contrast":
        img_lab = cv2.cvtColor(image_np, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(img_lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        img_lab = cv2.merge((l, a, b))
        return cv2.cvtColor(img_lab, cv2.COLOR_LAB2RGB)
    else:
        raise ValueError(f"Mode {mode} non supporté.")

def boxes_overlap(box1, box2, threshold=0.5):
    x1 = min(point[0] for point in box1)
    y1 = min(point[1] for point in box1)
    x2 = max(point[0] for point in box1)
    y2 = max(point[1] for point in box1)

    if len(box2) == 4 and isinstance(box2[0], list):
        x1_p = min(point[0] for point in box2)
        y1_p = min(point[1] for point in box2)
        x2_p = max(point[0] for point in box2)
        y2_p = max(point[1] for point in box2)
    else:
        x1_p, y1_p, x2_p, y2_p = box2

    xi1 = max(x1, x1_p)
    yi1 = max(y1, y1_p)
    xi2 = min(x2, x2_p)
    yi2 = min(y2, y2_p)

    inter_width = max(0, xi2 - xi1)
    inter_height = max(0, yi2 - yi1)
    inter_area = inter_width * inter_height

    box1_area = (x2 - x1) * (y2 - y1)
    box2_area = (x2_p - x1_p) * (y2_p - y1_p)
    union_area = box1_area + box2_area - inter_area

    iou = inter_area / union_area if union_area > 0 else 0
    return iou > threshold

def extract_text_and_layout(image):
    modes = ["grayscale", "rgb", "binary", "contrast"]
    extracted_data = []

    for mode in modes:
        print(f"[INFO] Application de l'OCR avec le mode {mode}")
        preprocessed_img = preprocess_image(image, mode)
        results = OCR_ENGINE.ocr(preprocessed_img, cls=True)

        if results is None:
            continue
        for line in results:
            if line is None:
                continue
            for word_info in line:
                if word_info is None:
                    continue
                text = word_info[1][0]
                confidence = word_info[1][1]
                box = word_info[0]

                text = text.replace("??", "é").replace("??", "à").strip()

                if confidence < 0.7:
                    continue
                if contains_arabic(text):
                    continue
                if is_likely_handwritten(text, box, preprocessed_img):
                    continue
                if len(text) < 2:
                    continue

                overlaps = False
                for existing in extracted_data:
                    if boxes_overlap(existing["box"], box):
                        overlaps = True
                        break

                if not overlaps:
                    extracted_data.append({"text": text, "box": box})

    print(f"[INFO] Nombre total de boîtes détectées : {len(extracted_data)}")
    return extracted_data

def filter_field_names(extracted_data):
    filtered_data = []
    for item in extracted_data:
        text = item["text"]
        if is_likely_field_name(text):
            filtered_data.append(item)
    return filtered_data

# -------- FONCTIONS POUR TEXTE MANUSCRIT --------
def thresholding(image):
    img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(img_gray, 80, 255, cv2.THRESH_BINARY_INV)
    return thresh

def detect_handwritten_text(image, thresh_img):
    kernel = np.ones((3, 85), np.uint8)
    dilated = cv2.dilate(thresh_img, kernel, iterations=1)
    (contours, _) = cv2.findContours(dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    sorted_contours_lines = sorted(contours, key=lambda ctr: cv2.boundingRect(ctr)[1])

    kernel2 = np.ones((3, 15), np.uint8)
    dilated2 = cv2.dilate(thresh_img, kernel2, iterations=1)
    words_list = []

    for line in sorted_contours_lines:
        x, y, w, h = cv2.boundingRect(line)
        roi_line = dilated2[y:y+h, x:x+w]
        (cnt, _) = cv2.findContours(roi_line.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        sorted_contour_words = sorted(cnt, key=lambda cntr: cv2.boundingRect(cntr)[0])

        for word in sorted_contour_words:
            if cv2.contourArea(word) < 50:
                continue
            x2, y2, w2, h2 = cv2.boundingRect(word)
            words_list.append([x+x2, y+y2, x+x2+w2, y+y2+h2])
    return words_list

# -------- FONCTIONS D'ANNOTATION ET SAUVEGARDE --------
def is_inside_table(box, table_bbox):
    box_center_x = (box[0][0] + box[2][0]) / 2
    box_center_y = (box[0][1] + box[2][1]) / 2
    for key in table_bbox.keys():
        x1, y2, x2, y1 = key
        if x1 <= box_center_x <= x2 and y1 <= box_center_y <= y2:
            return True
    return False

def save_combined_data(table_bbox, typed_text_data, handwritten_boxes, image_type):
    serializable_table_bbox = {str(key): value for key, value in table_bbox.items()}
    
    combined_data = {
        "image_type": image_type,
        "tables": serializable_table_bbox,
        "typed_text": typed_text_data,
        "handwritten_text": handwritten_boxes
    }
    return combined_data

def detect_layout(image, image_type):
    # Étape 1 : Préparation de l'image et détection des tableaux
    img, threshold = adaptive_threshold(image, process_background=False, blocksize=15, c=-2)
    vertical_mask, vertical_segments = find_lines(threshold, direction="vertical", line_scale=15, iterations=0)
    horizontal_mask, horizontal_segments = find_lines(threshold, direction="horizontal", line_scale=15, iterations=0)
    contours, mask = find_contours(vertical_mask, horizontal_mask)
    table_bbox = find_joints(contours, vertical_mask, horizontal_mask)

    # Filtrer les tableaux trop grands
    image_height, image_width = img.shape[:2]
    image_area = image_height * image_width
    threshold_area_ratio = 0.9
    filtered_table_bbox = {}
    for tab, joints in table_bbox.items():
        x1, y2, x2, y1 = tab
        table_area = (x2 - x1) * (y2 - y1)
        if table_area / image_area < threshold_area_ratio:
            filtered_table_bbox[tab] = joints
    table_bbox = filtered_table_bbox

    # Étape 2 : Extraction du texte tapé avec OCR
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    extracted_data = extract_text_and_layout(image_pil)
    typed_text_data = filter_field_names(extracted_data)

    # Étape 3 : Détection du texte manuscrit
    thresh_img = thresholding(img)
    handwritten_boxes = detect_handwritten_text(img, thresh_img)

    # Étape 4 : Filtrer les chevauchements entre texte tapé et manuscrit
    final_handwritten_boxes = []
    for h_box in handwritten_boxes:
        overlap = False
        for t_item in typed_text_data:
            t_box = t_item["box"]
            if boxes_overlap(t_box, h_box):
                overlap = True
                break
        if not overlap:
            final_handwritten_boxes.append(h_box)

    # Retourner les données combinées
    layout_data = save_combined_data(table_bbox, typed_text_data, final_handwritten_boxes, image_type)
    return layout_data