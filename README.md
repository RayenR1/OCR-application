# 🚀 EyeQ - Plateforme Avancée de Traitement de Documents Médicaux
![EyeQ Logo](./Capture_d_écran_2025-02-01_162905-removebg-preview.png)

## 📌 Table des Matières
- [Présentation](#-présentation)
- [Fonctionnalités](#-fonctionnalités)
- [Architecture Technique](#-architecture-technique)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [Performance](#-performance)
- [Contributeur](#-contributeur)
- [Licence](#-licence)

## 🌟 Présentation
EyeQ est une plateforme avancée de traitement intelligent des documents médicaux, développée dans un contexte académique à l'Esprit School of Engineering. Elle combine des techniques de vision par ordinateur et d'apprentissage profond pour automatiser l'analyse et la classification des images médicales.

### Technologies clés
- YOLOv11, PaddleOCR, Kafka, MLflow, FastAPI, OpenCV

## 🛠 Fonctionnalités
### 🔍 Classification Intelligente
- Détection précise de 4 classes de documents médicaux
- Modèle YOLOv11 optimisé
- API REST performante

### ✨ Amélioration d'Images
- Correction automatique des images
- Amélioration de qualité
- Détection et correction des défauts

### 📑 Détection de mise en page et OCR avancé
- Extraction et structuration des informations textuelles
- Gestion des modèles et suivi des expériences avec MLflow

## 🏗 Architecture Technique
L'architecture d'EyeQ repose sur une approche modulaire, où chaque microservice a un rôle bien défini et communique avec les autres via Kafka.

```plaintext
EyeQ/
├── yolo_classification/
├── image_enhancement/
├── layout_analysis/
└── docker-compose.yml
```

### Technologies utilisées
- **Deep Learning** : YOLOv11, PaddleOCR, RCNN, U-Net
- **Vision par ordinateur** : OpenCV, PIL, PyTorch
- **Big Data Streaming** : Apache Kafka
- **Suivi de modèle** : MLflow
- **Containerisation** : Docker, Docker Compose
- **Framework Web** : FastAPI

## ⚙ Installation
### Prérequis
- Python 3.8+
- Docker & Docker Compose
- Apache Kafka & Zookeeper

### Déploiement avec Docker Compose
```bash
git clone https://github.com/RayenR1/EyeQ.git
cd EyeQ
docker-compose up -d --build
```

## 🖥 Utilisation
Exemple d'appel API en Python :
```python
import requests
response = requests.post("http://localhost:8000/analyze", files={'file': open('doc.jpg','rb')})
print(response.json())
```

## 📊 Performance
| Métrique               | Valeur  |
|------------------------|---------|
| Précision YOLOv11     | x.x%   |
| Latence Moyenne       | x.xs    |

## 👨💻 Contributeur
Développé par **Rayen Jlassi**  
🔗 [GitHub @RayenR1](https://github.com/RayenR1)  
🔗 [LinkedIn](https://www.linkedin.com/in/rayen-jlassi-5867612bb/)  

## 📜 Licence
© 2025 EyeQ - Esprit School of Engineering

