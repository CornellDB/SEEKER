import copy
import pandas as pd
import numpy as np

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from src.backend.models.BaseModel import BaseModel

class SimpleRegression(BaseModel):
    def __init__(self, utility_metrics= "r2"):
        super().__init__("LinearRegression", utility_metrics = utility_metrics)
        self.model = LinearRegression()

    def train_pred_eval(self,
                        data: pd.DataFrame,
                        target_col: str,
                        test_size: float = 0.3,
                        random_state: int = 0) -> float:

        X_tr, X_te, y_tr, y_te = self._preprocess(
            data, target_col, test_size, random_state, is_classifier=False
        )

        self.model.fit(X_tr, y_tr)
        preds = self.model.predict(X_te)

        if self.utility_metrics == "mse":
            return mean_squared_error(y_te, preds)
        elif self.utility_metrics == "r2":
            return r2_score(y_te, preds)
        else:
            raise ValueError("Regression metric must be 'mse' or 'r2'")

if __name__ == '__main__':
    path = '/home/cc/open_data_usa/'
    # 基准数据
    base_df = pd.read_csv(path + 'base_school.csv')
    oracle = SimpleRegression()

    # 在原始数据上评估
    orig_metrics = oracle.train_classifier(base_df, 'target')  # 把 'target' 换为你的连续目标变量名
    print("原始数据回归指标：", orig_metrics)

    # 加入新特征后再评估
    new_df = pd.read_csv(path + '2010_Gen_Ed_Survey_Data.csv')
    merged = pd.merge(base_df, new_df,
                      left_on='DBN', right_on='dbn', how='left')
    merged_metrics = oracle.train_classifier(merged, 'target')
    print("合并后回归指标：", merged_metrics)

    # 对比 R2
    print(f"R² 改进：{merged_metrics['R2'] - orig_metrics['R2']:.4f}")
