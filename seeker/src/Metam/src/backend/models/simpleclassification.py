from sklearn.linear_model import LinearRegression, LogisticRegression
from src.backend.models.BaseModel import BaseModel
from sklearn.metrics import (
    mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score
)
from sklearn.model_selection import train_test_split
import copy
import pandas as pd


class ClassificationModel(BaseModel):
    def __init__(self, utility_metrics = "accuracy"):
        super().__init__("LogisticRegression", utility_metrics = utility_metrics)
        self.model = LogisticRegression(solver='liblinear')

    def train_pred_eval(self,
                        data: pd.DataFrame,
                        target_col: str,
                        test_size: float = 0.3,
                        random_state: int = 0,) -> float:

        X_tr, X_te, y_tr, y_te = self._preprocess(
            data, target_col, test_size, random_state, is_classifier=True
        )

        self.model.fit(X_tr, y_tr)
        preds = self.model.predict(X_te)

        if self.utility_metrics == "accuracy":
            return accuracy_score(y_te, preds)
        elif self.utility_metrics == "precision":
            return precision_score(y_te, preds, average="macro")
        elif self.utility_metrics == "recall":
            return recall_score(y_te, preds, average="macro")
        elif self.utility_metrics in ("f1", "f-score"):
            return f1_score(y_te, preds, average="macro")
        else:
            raise ValueError(
                "Classification metric must be 'accuracy', 'precision', 'recall', or 'f1'"
            )

if __name__ == "__main__":
    # —— Regression example ——
    # df_reg = pd.read_csv('path/to/base_school.csv')
    # reg = RegressionModel()
    # r2 = reg.train_pred_eval(df_reg, 'target', random_state=1, metric='r2')
    # mse = reg.train_pred_eval(df_reg, 'target', random_state=1, metric='mse')
    # print(f"R²: {r2:.4f}, MSE: {mse:.4f}")

    # —— Classification example with Iris dataset ——
    from sklearn.datasets import load_iris
    iris = load_iris(as_frame=True)
    df_iris = iris.frame
    clf = ClassificationModel()
    acc = clf.train_pred_eval(
        df_iris, 'target', random_state=42, metric='accuracy'
    )
    f1_macro = clf.train_pred_eval(
        df_iris, 'target', random_state=42, metric='f1', average='macro'
    )
    print(f"Iris accuracy: {acc:.4f}, F1 (macro): {f1_macro:.4f}")
