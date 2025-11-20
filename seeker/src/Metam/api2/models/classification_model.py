# api2/models/classification_model.py
import pandas as pd
from sklearn.linear_model import LogisticRegression

class SimpleClassifier:
    """
    Basic wrapper around LogisticRegression.
    - First tries to train on numeric columns.
    - If none exist, one‑hot encodes all columns.
    """
    def __init__(self):
        self.model = LogisticRegression(solver="liblinear")

    def _prepare(self, X: pd.DataFrame) -> pd.DataFrame:
        # select numeric first
        X_num = X.select_dtypes(include=["int64", "float64"])
        if X_num.shape[1] == 0:
            # fallback: one‑hot encode everything
            X_num = pd.get_dummies(X, drop_first=True)
        return X_num

    def fit(self, X: pd.DataFrame, y: pd.Series):
        X_proc = self._prepare(X)
        self.model.fit(X_proc, y)

    def predict(self, X: pd.DataFrame):
        X_proc = self._prepare(X)
        return self.model.predict(X_proc)
