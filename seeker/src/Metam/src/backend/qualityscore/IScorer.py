# profiles/scorers/base.py
from abc import ABC, abstractmethod
import pandas as pd
class IScorer(ABC):
    @abstractmethod
    def score(self, candidates: list[int]) -> list[tuple[int, float]]: ...
    @abstractmethod
    def observe_gain(
        self,
        src_id: int,
        gain: float,
        utility: float | None = None,
        cluster_ids: list[int] | None = None,
    ): ...
    @abstractmethod
    def reset(self): ...