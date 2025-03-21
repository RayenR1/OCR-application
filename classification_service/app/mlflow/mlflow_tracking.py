# app/mlflow/mlflow_tracking.py
import mlflow
import mlflow.pytorch
from app.config import MLFLOW_TRACKING_URI, MODEL_NAME
import time
import requests
from requests.exceptions import ConnectionError

class MLflowTracker:
    def __init__(self, max_retries=5, retry_delay=2):
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        
        # Retry connecting to the MLflow server
        for attempt in range(max_retries):
            try:
                # Check if the MLflow server is up by making a simple request
                response = requests.get(f"{MLFLOW_TRACKING_URI}/health", timeout=5)
                if response.status_code == 200:
                    break
            except ConnectionError:
                if attempt == max_retries - 1:
                    raise Exception("Failed to connect to MLflow server after maximum retries")
                print(f"MLflow server not ready, retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)

        # Now set the experiment
        mlflow.set_experiment("YOLOv11-Classification")

    def log_model(self, model_path, version):
        with mlflow.start_run():
            mlflow.log_param("model_version", version)
            mlflow.log_artifact(model_path, artifact_path="weights")
            mlflow.set_tag("model_name", MODEL_NAME)
            return mlflow.active_run().info.run_id

    def load_model(self, version):
        client = mlflow.tracking.MlflowClient()
        runs = client.search_runs(
            experiment_ids=[client.get_experiment_by_name("YOLOv11-Classification").experiment_id],
            filter_string=f"params.model_version = '{version}'"
        )
        if not runs:
            raise Exception(f"No model found for version {version}")
        run_id = runs[0].info.run_id
        return f"runs:/{run_id}/weights/best.pt"

    def rollback_model(self, version):
        return self.load_model(version)