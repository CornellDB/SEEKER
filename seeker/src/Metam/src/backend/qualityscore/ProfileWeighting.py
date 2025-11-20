from typing import Dict, List, Tuple
import operator
from collections import defaultdict
from sklearn.linear_model import LinearRegression
from src.backend.qualityscore.IScorer import IScorer
from src.backend.qualityscore.profile_weights import get_features

class ProfileWeightScorer(IScorer):
    """
    基于 profile 权重的打分策略：
    * score() 对未测列使用 profile_features × 权重求和；
      对已测列，加上其真实 utility。
    * observe_gain() 在每次真实查询后保存 gain，并
      使用线性回归更新 profile 权重。

    默认在初始化时将所有 profile feature 的权重设为 1，
    并且 real_gain、utility 为空。
    """
    def __init__(
        self,
        new_col_lst: List,
        decay: float = 1.0
    ):
        self.new_col_lst = new_col_lst
        # 初始化权重为 1
        self.weights: Dict[Tuple[str, str], float] = {}
        prof_list = list(new_col_lst[0].profile_values.keys())
        for prof in prof_list:
            for key in new_col_lst[0].profile_values[prof]:
                self.weights[(prof, key)] = 1.0
        # 保存已测列的 gain 和 utility
        self.real_gain: Dict[int, float] = {}
        self.utility: Dict[int, float] = {}
        # 画像特征顺序列表，用于展开向量
        self._prof_list = prof_list

    def score(self, candidates: List[int]) -> List[Tuple[int, float]]:
        scores: Dict[int, float] = {}
        for cid in candidates:
            # 已测列优先：score = utility
            if cid in self.real_gain:
                scores[cid] = self.utility.get(cid, self.real_gain[cid])
                continue
            # 未测列：profile_features × weights
            jc = self.new_col_lst[cid]
            feats = get_features(jc.profile_values, self._prof_list)
            total = 0.0
            ptr = 0
            for prof in self._prof_list:
                sub = jc.profile_values[prof]
                for key in sorted(sub, key=lambda k: int(k) if k.isdigit() else k):
                    w = self.weights.get((prof, key), 0.0)
                    total += abs(sub[key] * w)
                    ptr += 1
            scores[cid] = total
        # 按分数降序返回
        return sorted(scores.items(), key=operator.itemgetter(1), reverse=True)

    def observe_gain(
        self,
        src_id: int,
        gain: float,
        utility: float | None = None,
        cluster_ids: List[int] | None = None,
    ):
        # 记录真实 gain
        self.real_gain[src_id] = gain
        # 如果提供了 tmp_metric，则记录 utility
        if utility is not None:
            self.utility[src_id] = utility
        # 构建回归训练集
        X: List[List[float]] = []
        Y: List[float] = []
        for cid, g in self.real_gain.items():
            jc = self.new_col_lst[cid]
            feats = get_features(jc.profile_values, self._prof_list)
            X.append(feats)
            Y.append(g)
        if not X  or len(X[0]) == 0:
            return
        # 回归更新所有权重
        model = LinearRegression().fit(X, Y)
        coefs = model.coef_
        ptr = 0
        for prof in self._prof_list:
            sub = self.new_col_lst[0].profile_values[prof]
            for key in sorted(sub, key=lambda k: int(k) if k.isdigit() else k):
                self.weights[(prof, key)] = coefs[ptr]
                ptr += 1

    def reset(self):
        # 无状态需要重置时可实现此处。
        pass
