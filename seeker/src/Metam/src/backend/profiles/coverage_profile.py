from src.backend.profiles.base_profile import BaseProfile

class CoverageProfile(BaseProfile):
    def name(self) -> str:
        return "coverage"

    def score(self, df, new_col):
        # return fraction of non-null in new column
        total = len(df)
        non_null = df[new_col].notna().sum()
        return {"all": float(non_null) / float(total) if total > 0 else 0.0}
