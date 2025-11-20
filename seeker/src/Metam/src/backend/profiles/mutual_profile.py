from sklearn.metrics import adjusted_mutual_info_score
from src.backend.profiles.base_profile import BaseProfile

class MutualInfoProfile(BaseProfile):
    def name(self) -> str:
        return "mutual"

    def score(self, df, new_col):
        res = {}
        for col in df.columns:
            if col == new_col:
                continue
            res[col] = float(adjusted_mutual_info_score(
                df[col].fillna(-1)[:100], df[new_col].fillna(-1)[:100]
            ))
        return res
