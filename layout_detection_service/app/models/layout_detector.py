# app/models/layout_detector.py
# github:@RayenR1 | linkedin :Rayen Jlassi
import torch
import numpy as np
import cv2
from PIL import Image
import re
from paddleocr import PaddleOCR
import json
from craft_text_detector import (
    read_image,
    load_craftnet_model,
    load_refinenet_model,
    get_prediction,
    export_detected_regions
)
from app.config import (
    CRAFT_LONG_SIZE,
    MIN_BOX_WIDTH,
    MIN_BOX_HEIGHT,
    MIN_BOX_AREA,
    LINE_HEIGHT_TOLERANCE,
    MIN_LINE_WIDTH
)

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

def get_box_rect(box):
    """Convertit une boîte en rectangle (x, y, w, h)"""
    if isinstance(box, list):
        x_coords = [point[0] for point in box]
        y_coords = [point[1] for point in box]
    else:
        x_coords = box[:, 0]
        y_coords = box[:, 1]
    
    x = min(x_coords)
    y = min(y_coords)
    w = max(x_coords) - x
    h = max(y_coords) - y
    return x, y, w, h

def is_valid_box(box):
    """Vérifie si une boîte est assez grande"""
    _, _, w, h = get_box_rect(box)
    area = w * h
    return (w >= MIN_BOX_WIDTH and 
            h >= MIN_BOX_HEIGHT and 
            area >= MIN_BOX_AREA)

def boxes_overlap(box1, box2, threshold=0.5):
    """Vérifie si deux boîtes se chevauchent."""
    x1, y1, w1, h1 = get_box_rect(box1)
    x2, y2, w2, h2 = get_box_rect(box2)
    
    xi1 = max(x1, x2)
    yi1 = max(y1, y2)
    xi2 = min(x1 + w1, x2 + w2)
    yi2 = min(y1 + h1, y2 + h2)

    inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
    box1_area = w1 * h1
    box2_area = w2 * h2
    union_area = box1_area + box2_area - inter_area

    iou = inter_area / union_area if union_area > 0 else 0
    return iou > threshold

def extract_text_and_layout(image):
    modes = ["rgb", "contrast"]
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
                if len(text) < 2:
                    continue
                if not is_valid_box(box):
                    continue

                overlaps = False
                for existing in extracted_data:
                    if boxes_overlap(existing["box"], box):
                        overlaps = True
                        break

                if not overlaps:
                    extracted_data.append({"text": text, "box": box, "source": "paddle"})

    print(f"[INFO] Nombre total de boîtes détectées : {len(extracted_data)}")
    return extracted_data

def filter_field_names(extracted_data):
    filtered_data = []
    for item in extracted_data:
        text = item["text"]
        if is_likely_field_name(text):
            filtered_data.append(item)
    return filtered_data

def ultra_precise_adjustment(boxes, original_size, network_size, long_size):
    orig_h, orig_w = original_size
    net_h, net_w = network_size
    
    scale_x = orig_w / net_w
    scale_y = orig_h / net_h
    
    size_ratio = long_size / max(net_w, net_h)
    
    aspect_ratio_correction = np.sqrt((scale_x * scale_y) / (size_ratio**2))
    
    adjusted_boxes = []
    for box in boxes:
        box = np.array(box, dtype=np.float32)
        if box.shape != (4, 2):
            continue
            
        box[:, 0] = box[:, 0] * scale_x / aspect_ratio_correction
        box[:, 1] = box[:, 1] * scale_y / aspect_ratio_correction
        
        box[:, 0] *= 1.0015
        box[:, 1] *= 0.9985
        
        box[:, 0] = np.clip(box[:, 0], 0, orig_w - 1)
        box[:, 1] = np.clip(box[:, 1], 0, orig_h - 1)
        
        adjusted_boxes.append(box)
    
    return adjusted_boxes

def detect_text_with_craft(image, existing_boxes):
    orig_h, orig_w = image.shape[:2]
    
    craft_net = load_craftnet_model(cuda=False)
    refine_net = load_refinenet_model(cuda=False)
    
    prediction_result = get_prediction(
        image=image,
        craft_net=craft_net,
        refine_net=refine_net,
        text_threshold=0.7,
        link_threshold=0.45,
        low_text=0.4,
        cuda=False,
        long_size=CRAFT_LONG_SIZE,
        poly=False
    )
    
    score_map = prediction_result["heatmaps"]["text_score_heatmap"]
    net_h, net_w = score_map.shape[:2]
    
    raw_boxes = prediction_result["boxes"]
    valid_boxes = [b for b in raw_boxes if isinstance(b, np.ndarray) and b.shape == (4, 2)]
    
    craft_data = []
    
    if valid_boxes:
        final_boxes = ultra_precise_adjustment(
            valid_boxes,
            (orig_h, orig_w),
            (net_h, net_w),
            CRAFT_LONG_SIZE
        )
        
        for box in final_boxes:
            if not is_valid_box(box):
                continue
                
            overlaps = False
            for existing in existing_boxes:
                if boxes_overlap(existing["box"], box):
                    overlaps = True
                    break
            
            if not overlaps:
                box_points = box.tolist()
                craft_data.append({
                    "box": box_points,
                    "text": "",
                    "source": "craft"
                })
    
    return craft_data

def group_boxes_into_lines(boxes, image_width, tolerance=LINE_HEIGHT_TOLERANCE):
    if not boxes:
        return []
    
    box_rects = []
    for box in boxes:
        x, y, w, h = get_box_rect(box["box"])
        center_y = y + h/2
        box_rects.append((center_y, box))
    
    box_rects.sort(key=lambda x: x[0])
    
    lines = []
    current_line = []
    current_ref_y = box_rects[0][0]
    
    for center_y, box in box_rects:
        if abs(center_y - current_ref_y) <= tolerance:
            current_line.append(box)
        else:
            if current_line:
                left_boxes = []
                right_boxes = []
                for b in current_line:
                    box_center = (get_box_rect(b["box"])[0] + get_box_rect(b["box"])[2]/2)
                    if box_center < image_width/2:
                        left_boxes.append(b)
                    else:
                        right_boxes.append(b)
                
                if left_boxes:
                    lines.append(left_boxes)
                if right_boxes:
                    lines.append(right_boxes)
            
            current_line = [box]
            current_ref_y = center_y
    
    if current_line:
        left_boxes = []
        right_boxes = []
        for b in current_line:
            box_center = (get_box_rect(b["box"])[0] + get_box_rect(b["box"])[2]/2)
            if box_center < image_width/2:
                left_boxes.append(b)
            else:
                right_boxes.append(b)
        
        if left_boxes:
            lines.append(left_boxes)
        if right_boxes:
            lines.append(right_boxes)
    
    return lines

def is_inside_any_table(box, table_bboxes):
    if not table_bboxes:
        return False
    
    if isinstance(box, list):
        x_coords = [point[0] for point in box]
        y_coords = [point[1] for point in box]
        box_x1 = min(x_coords)
        box_y1 = min(y_coords)
        box_x2 = max(x_coords)
        box_y2 = max(y_coords)
    else:
        box_x1, box_y1 = box.min(axis=0)
        box_x2, box_y2 = box.max(axis=0)
    
    box_center_x = (box_x1 + box_x2) / 2
    box_center_y = (box_y1 + box_y2) / 2
    
    for tab_bbox in table_bboxes.keys():
        tab_x1, tab_y2, tab_x2, tab_y1 = tab_bbox
        
        if (tab_x1 <= box_center_x <= tab_x2 and 
            tab_y1 <= box_center_y <= tab_y2):
            return True
    
    return False

def save_combined_data(table_bbox, typed_text_data, line_data, image_type):
    serializable_table_bbox = {str(key): value for key, value in table_bbox.items()}
    
    combined_data = {
        "image_type": image_type,
        "tables": serializable_table_bbox,
        "typed_text": typed_text_data,
        "lines": line_data
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

    # Étape 2 : Extraction du texte tapé avec PaddleOCR
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    extracted_data = extract_text_and_layout(image_pil)
    typed_text_data = filter_field_names(extracted_data)

    # Étape 3 : Détection de texte supplémentaire avec CRAFT
    craft_data = detect_text_with_craft(img, typed_text_data)
    
    # Combiner les résultats
    combined_text_data = typed_text_data + craft_data

    # Étape 4 : Grouper les boîtes hors tableaux en lignes
    non_table_boxes = [box for box in combined_text_data if not is_inside_any_table(box["box"], table_bbox)]
    lines = group_boxes_into_lines(non_table_boxes, image_width)
    
    # Préparer les données de lignes pour la sortie
    line_data = []
    for line in lines:
        if not line:
            continue
        x_min = int(min(get_box_rect(box["box"])[0] for box in line))
        y_min = int(min(get_box_rect(box["box"])[1] for box in line))
        x_max = int(max(get_box_rect(box["box"])[0] + get_box_rect(box["box"])[2] for box in line))
        y_max = int(max(get_box_rect(box["box"])[1] + get_box_rect(box["box"])[3] for box in line))
        line_data.append({
            "boxes": [{"text": box["text"], "coordinates": box["box"]} for box in line],
            "bounding_box": [x_min, y_min, x_max, y_max]
        })

    # Étape 5 : Préparer les données combinées
    layout_data = save_combined_data(table_bbox, combined_text_data, line_data, image_type)
    return layout_data