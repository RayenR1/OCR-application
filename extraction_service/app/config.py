KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
INPUT_TOPIC = "output-layout"  # Topic de sortie du layout_detection_service
OUTPUT_TOPIC = "text_output"   # Topic pour les résultats textuels
CONFIDENCE_THRESHOLD = 0.80    # Seuil de confiance pour EasyOCR
MAX_TOKENS = 2000              # Tokens maximum pour Qari-OCR