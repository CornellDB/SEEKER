import numpy as np
from src.backend.profiles.base_profile import BaseProfile

class CorrProfile(BaseProfile):
    def name(self) -> str:
        return "corr"

    def score(self, df, new_col):
        corrs = df.corr(numeric_only=True)[new_col]
        return {col: 0.0 if np.isnan(v) else float(v)
                for col, v in corrs.items() if col != new_col}
