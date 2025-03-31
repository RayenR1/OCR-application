# app/mlflow/mlflow_client.py
#github:@RayenR1 | linkedin :Rayen Jlassi
from mlflow.tracking import MlflowClient
from app.config import MLFLOW_TRACKING_URI

class MLflowClient:
    def __init__(self):
        self.client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)
        self.experiment_name = "layout_detection"
        self.experiment_id = self._get_or_create_experiment()

    def _get_or_create_experiment(self):
        experiment = self.client.get_experiment_by_name(self.experiment_name)
        if experiment is None:
            experiment_id = self.client.create_experiment(self.experiment_name)
        else:
            experiment_id = experiment.experiment_id
        return experiment_id

    def log_layout_metrics(self, image_type, num_tables, num_typed_text, num_handwritten_text):
        """Enregistre les métriques de segmentation dans MLflow."""
        with self.client.start_run(experiment_id=self.experiment_id):
            self.client.log_param("image_type", image_type)
            self.client.log_metric("num_tables", num_tables)
            self.client.log_metric("num_typed_text", num_typed_text)
            self.client.log_metric("num_handwritten_text", num_handwritten_text)
            print(f"[INFO] Métriques enregistrées dans MLflow pour {image_type}")