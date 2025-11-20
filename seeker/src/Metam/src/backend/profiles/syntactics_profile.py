from difflib import SequenceMatcher
from src.backend.profiles.base_profile import BaseProfile

class SyntacticProfile(BaseProfile):
    def __init__(self, orig_name: str):
        self.orig_name = orig_name

    def name(self) -> str:
        return "sim"

    def score(self, df, new_col):
        return {col: SequenceMatcher(None, col, self.orig_name).ratio()
                for col in df.columns if col != new_col}
