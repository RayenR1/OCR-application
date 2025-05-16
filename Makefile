PYTHON = c:/users/jlassi/miniconda3/envs/PIDS/python.exe

start_all:
	@echo "Starting classification service..."
	(cd classification_service && $(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8000) &
	@echo "Starting image filter service..."
	(cd image_filter_service && $(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8001) &
	@echo "Starting layout detection service..."
	(cd layout_detection_service && $(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8002) &
	@echo "Starting extraction service..."
	(cd extraction_service && $(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8003) &
