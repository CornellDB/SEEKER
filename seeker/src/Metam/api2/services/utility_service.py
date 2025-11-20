# api2/services/utility_service.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics      import accuracy_score, recall_score, f1_score, mean_squared_error

from api2.models.classification_model import SimpleClassifier
from api2.models.regression_model     import SimpleRegressor
from api2.services.storage_service import StorageService
from src.backend.models.simpleclassification import ClassificationModel
from src.backend.models.simpleregression import SimpleRegression



def calculate_utility(
    job_id: str,
    task: str,
    attribute: str,
    metric:  str
) -> float:
    """
    - task: "classification" or "regression"
    - attribute: the column to predict
    - metric: e.g. "accuracy", "recall", "f1" or "mse"/"r2"
    """
    csv_path = StorageService.dataset_path(job_id)
    df = pd.read_csv(csv_path)
    # turn list-of-dicts into DataFrame if needed (this might already be done upstream)
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)

    # dispatch to the right model
    if task == "classification":
        model = ClassificationModel(metric)
    elif task == "regression":
        model = SimpleRegression(metric)
    else:
        raise ValueError(f"Unknown task: {task!r}")

    # call into our unified interface
    return model.train_pred_eval(
        data=df,
        target_col=attribute,
    )
