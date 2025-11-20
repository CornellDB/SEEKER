import random
from src.backend.profiles.base_profile import BaseProfile
class UninformativeProfile(BaseProfile):
    """
    Generates a specified number of random noise features under the 'uninfo' profile.
    """
    def __init__(self, count: int):
        self.count = count

    def name(self) -> str:
        return "uninfo"

    def score(self, df, new_col: str) -> dict[str, float]:
        # produce {"0": rand0, "1": rand1, ...}
        return {str(i): random.random() for i in range(self.count)}
