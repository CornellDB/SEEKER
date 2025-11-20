from abc import ABC, abstractmethod
import pandas as pd
class BaseProfile(ABC):
    """Interface for a profiling strategy on an augmented column."""

    @abstractmethod
    def name(self) -> str:
        """Return a short string to identify this profile (used as key)."""
        ...

    @abstractmethod
    def score(self, df: pd.DataFrame, new_col: str) -> dict[str, float]:
        """
        Given a merged DataFrame and the name of the new column,
        compute a dict mapping each existing column (or 'all') to a score.
        """
        ...