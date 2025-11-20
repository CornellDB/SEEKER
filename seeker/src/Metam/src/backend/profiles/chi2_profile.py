# profiles/chi2_profile.py

import pandas as pd
from scipy.stats import chi2_contingency
from src.backend.profiles.base_profile import BaseProfile

class Chi2Profile(BaseProfile):
    def name(self) -> str:
        return "chi2"

    def score(self, df: pd.DataFrame, new_col: str) -> dict[str, float]:
        res: dict[str, float] = {}
        for col in df.columns:
            if col == new_col:
                continue
            try:
                # use only first 4 rows for cross‑tab
                cross_tab = pd.crosstab(df[col][:4], df[new_col][:4])
                chi2, p, _, _ = chi2_contingency(cross_tab)
            except Exception:
                res[col] = 0.0
                continue

            if p < 0.1:
                # mirror original debug prints
                print(cross_tab)
                print(chi2, p)
                print(df[[col, new_col]][:10])
                res[col] = float(chi2)
            else:
                res[col] = 0.0

        return res
