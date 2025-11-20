# profiles/scorers/cluster_balance.py
import math, operator
from collections import defaultdict
from typing import Dict, List, Tuple
from src.backend.qualityscore.IScorer import IScorer
from src.backend.qualityscore.profile_weights import get_features   # 仅用来把 profile 拉平成向量

class ClusterBalanceScorer(IScorer):
    """
    * 不使用 profile‑weight，等价于所有 profile 权重恒为 1。
    * 仅维护 balance：当同簇出现真实 gain 时，
      balance[tgt] += (1‑d) * gain  （d 为 profile 向量距离）。
    * score = balance + (已测列时再加 tmp_metric)。
    """

    # ---------- 初始化 ----------
    def __init__(self, new_col_lst: List, decay: float = 1.0):
        self._decay = decay

        # —— 固定向量 ——  profile → 一维向量
        self._vecs  = [
            get_features(jc.profile_values, list(jc.profile_values.keys()))
            for jc in new_col_lst
        ]
        self._dist_cache: Dict[Tuple[int, int], float] = {}

        # —— 运行期可变量 ——
        self._balance   = defaultdict(float)   # cid → balance
        self._tmp_metric: Dict[int, float] = {}  # 已测列的 utility
        self._real_gain: Dict[int, float] = {}   # 已测列的 gain

    # ---------- 内部工具 ----------
    def _dist(self, i: int, j: int) -> float:
        """归一化欧几里得距离 ∈ [0,1]，带缓存。"""
        key = (i, j) if i < j else (j, i)
        if key in self._dist_cache:
            return self._dist_cache[key]

        v1, v2 = self._vecs[i], self._vecs[j]
        d_raw  = math.dist(v1, v2)
        d_max  = math.dist([0]*len(v1), [1]*len(v1)) or 1
        d_norm = min(d_raw / d_max, 1.0)
        self._dist_cache[key] = d_norm
        return d_norm

    # ---------- IScorer 接口 ----------
    def score(self, candidates: List[int]) -> List[Tuple[int, float]]:
        """返回 [(cid, score)], score 越大越先测。"""
        scores = {}
        for cid in candidates:
            base = self._balance[cid]
            scores[cid] = (
                base + self._tmp_metric.get(cid, 0.0)  # 已测列再加 tmp_metric
            )
        return sorted(scores.items(), key=operator.itemgetter(1), reverse=True)

    def observe_gain(
        self,
        src_id: int,
        gain: float,
        utility: float | None = None,
        cluster_ids: List[int] | None = None,
    ):
        """
        src_id      : 刚被真实查询的列 ID
        gain        : tmp_metric - old_metric
        utility     : tmp_metric (可选；若传入即可在 score 中使用)
        cluster_ids : 这次视为与 src_id 同簇的所有列 ID（含 src_id）
        """
        self._real_gain[src_id] = gain
        if utility is not None:
            self._tmp_metric[src_id] = utility

        members = cluster_ids or [src_id]
        for tgt_id in members:
            d = 0.0 if tgt_id == src_id else self._dist(src_id, tgt_id)
            self._balance[tgt_id] += (1 - d) * gain * self._decay

    def reset(self):
        """
        若想跨外层迭代逐渐“淡忘”旧信息，可在此处执行：
        for k in self._balance: self._balance[k] *= rho   (0<rho≤1)
        目前保留空实现即可。
        """
        pass
