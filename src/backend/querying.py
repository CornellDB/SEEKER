# File: metam/runner.py
import copy
import math
import random
from src.backend.group_querying import group_helper
from src.backend.qualityscore import profile_weights
from src.backend.others.logger import get_logger
from src.backend.qualityscore.GainProp import ClusterBalanceScorer
from src.backend.qualityscore.ProfileWeighting import ProfileWeightScorer
class MetamRunner:
    def __init__(self, tau, model, candidates, local_config, metric,
                 initial_df, new_col_lst, weights,
                 clusters, assignment, event_queue=None):
        self.local_config = local_config
        self.tau = tau
        self.model = model
        self.candidates = candidates
        self.theta = self.local_config.THETA
        self.metric = metric
        self.initial_df = initial_df
        self.new_col_lst = new_col_lst
        self.weights = weights
        self.class_attr = local_config.PRED_COL
        self.clusters = clusters
        self.assignment = assignment
        self.uninfo = local_config.UNINFO
        self.epsilon = local_config.EPSILON
        self.stopping = local_config.STOPPING_CRITERIA
        self.event_queue = event_queue

        # Thompson sampling counts
        self.likelihood_num = [1 for _ in clusters]
        self.likelihood_den = [1 for _ in clusters]
        # Cluster sizes
        self.cluster_size = self._compute_cluster_sizes()

        self.base_df = copy.deepcopy(initial_df)
        self.orig_metric = self.model.train_pred_eval(self.base_df, self.class_attr)
        self.total_queries = 0
        self.iteration = 0
        self.grp_size = local_config.GRP_SIZE
        self.grp_queried_cand = {}
        self.overall_queried = {}
        self.logger = get_logger(__name__)
        # self.scorer = ClusterBalanceScorer(self.new_col_lst, decay=0.8)
        self.scorer = local_config.QUALITYSCORER(self.new_col_lst, **local_config.SCORER_KWARGS)
    def _compute_cluster_sizes(self):
        size = {}
        for jc, cid in self.assignment.items():
            size[cid] = size.get(cid, 0) + 1
        return size

    def run(self):
        while self.metric < self.theta and self.total_queries <= self.stopping:
            self.logger.info(f"=== Outer iteration {self.iteration}: metric={self.metric}")
            if self.event_queue is not None:
                self.event_queue.put({
                    "type": "update",
                    "iteration": self.iteration,
                    "score": self.metric
                })
            # reset per‐iteration bests
            old_metric     = self.metric
            curr_max       = old_metric
            best_seq_df    = self.initial_df
            curr_max_grp   = old_metric
            best_grp_df    = self.base_df
            if self.event_queue is not None:
                self.event_queue.put({
                    "type": "augmentation",
                    "augmentation": "ITER " + str(self.initial_df.columns.tolist()),
                    "score": f"MET- {self.metric:.4f}",
                    "Color": "red"
                })
            i = 0
            queries_used = 0
            inner_queried_seq = {}   # candidate_id → gain
            inner_queried_grp = {}   # group-rep → gain

            # Version1’s inner loop: up to τ interleaved trials, or until no further seq gain
            while i < self.tau or curr_max <= old_metric:
                # —— one sequential trial ——
                seq = self._sequential_phase(inner_queried_seq)
                queries_used += seq['queries']
                if seq['metric'] > curr_max:
                    curr_max    = seq['metric']
                    best_seq_df = seq['df']

                if seq['queries'] == 0:
                    break
                # —— one group trial ——
                grp = self._group_phase(inner_queried_grp)
                queries_used += grp['queries']
                if grp['metric'] > curr_max_grp:
                    curr_max_grp = grp['metric']
                    best_grp_df  = grp['df']
                i += 1

            # pick the better of all seq vs. all group trials
            if curr_max_grp > curr_max:
                chosen_metric = curr_max_grp
                chosen_df     = best_grp_df
            else:
                chosen_metric = curr_max
                chosen_df     = best_seq_df

            if self.iteration == 0 and self.tau > 1:
                self._homogeneity_check()
            if chosen_metric <= old_metric:
                self.iteration += 1
                continue

            # apply the chosen augmentation
            self.initial_df   = chosen_df
            self.metric       = chosen_metric
            self.total_queries += queries_used
            # update weights from only the seq gains as in v1
            # self.weights = profile_weights.get_weights(
            #     self.new_col_lst,
            #     inner_queried_seq,
            #     self.weights
            # )

            self.iteration += 1


        # 完成后推送 complete

        if self.event_queue is not None:
            self.event_queue.put({"type": "complete"})

        return self.initial_df

    def _sequential_phase(self, inner_queried_seq):
        """
        Perform exactly one sequential (single-column) trial.
        Update inner_queried_seq and self.overall_queried.
        Return dict with keys: df, metric, queries, queried.
        """
        old_metric = self.metric
        curr_max   = old_metric
        max_df     = self.initial_df

        # pick next untried candidate
        ranked = self.scorer.score(self.candidates)  # 返回 [(candidate_id, score), ...]
        candidate_id = None
        for cid, _ in ranked:
            if cid not in inner_queried_seq:
                candidate_id = cid
                break
        if candidate_id is None:
            return {'df': max_df, 'metric': curr_max, 'queries': 0, 'queried': {}}

        # evaluate this join column
        merged = copy.deepcopy(self.initial_df)
        col = self.new_col_lst[candidate_id]
        merged[col.column] = col.merged_df[col.column]
        tmp_metric = max(self.model.train_pred_eval(merged, self.class_attr), old_metric)
        gain = tmp_metric - old_metric

        # record gains
        inner_queried_seq[candidate_id] = gain
        self.overall_queried[candidate_id] = gain

        self.logger.info(f"SEQ {tmp_metric} (gain={gain})")

        if self.event_queue is not None:
            self.event_queue.put({
                "type": "augmentation",
                "augmentation": "SEQ- "+str(merged.columns.tolist()),
                "score": f"MET- {tmp_metric:.4f} GAIN- {gain:.4f}",
                "Color": "black"
            })
        # 构造本次视为同簇的所有列 ID 列表
        cluster_id = self.assignment[self.new_col_lst[candidate_id]]
        cluster_ids = [jc.loc for jc in self.clusters[cluster_id]]

        # 通知 scorer 更新 balance
        self.scorer.observe_gain(
            src_id=candidate_id,
            gain=gain,
            utility=tmp_metric,
            cluster_ids=cluster_ids
        )
        if tmp_metric > curr_max:
            curr_max = tmp_metric
            max_df   = merged

        return {
            'df':      max_df,
            'metric':  curr_max,
            'queries': 1,
            'queried': {candidate_id: gain}
        }

    def _group_phase(self, inner_queried_grp):
        """
        Perform exactly one group (multi-column) trial via Thompson-sampling.
        Update inner_queried_grp and self.grp_queried_cand.
        Return dict with keys: df, metric, queries, queried.
        """
        old_metric = self.orig_metric
        curr_max_grp = old_metric
        max_df       = self.base_df

        # if we've exhausted all group signatures at this size, double it
        if len(self.grp_queried_cand) == len(self.new_col_lst):
            self.grp_size *= 2

        try:
            jc_list, rep = self.local_config.GRP_QUERY(
                self.new_col_lst,
                self.clusters,
                self.grp_size,
                self.likelihood_num,
                self.likelihood_den,
                self.grp_queried_cand
            )
        except RuntimeError as e:
            # couldn't find a new group within max_attempts → just return old state
            self.logger.warning(f"Group query skipped: {e}")
            return {
                'df': self.base_df,
                'metric': old_metric,
                'queries': 0,
                'queried': {}
            }

        merged = copy.deepcopy(self.base_df)
        for jc in jc_list:
            merged[jc.column] = jc.merged_df[jc.column]

        tmp_metric = max(self.model.train_pred_eval(merged, self.class_attr), old_metric)
        gain = tmp_metric - old_metric

        # record gains
        self.grp_queried_cand[rep] = gain
        inner_queried_grp[rep]    = gain

        # update Thompson counts
        for jc in jc_list:
            cid = self.assignment[jc]
            if tmp_metric > old_metric:
                self.likelihood_num[cid] += 1
            self.likelihood_den[cid] += 1

        self.logger.info(f"GRP {tmp_metric} (gain={gain})")

        if self.event_queue is not None:
            # 用逗号分隔所有列名
            cols = [jc.column for jc in jc_list]
            self.event_queue.put({
                "type": "augmentation",
                "augmentation": "GRP- "+str(merged.columns.tolist()),
                "score": f"MET- {tmp_metric:.4f} GAIN- {gain:.4f}",
                "Color": "black"
            })

        if tmp_metric > curr_max_grp:
            curr_max_grp = tmp_metric
            max_df       = merged

        return {
            'df':      max_df,
            'metric':  curr_max_grp,
            'queries': 1,
            'queried': {rep: gain}
        }

    def _homogeneity_check(self):
        """
        On first outer iteration only: sample each cluster to detect
        heterogeneity and, if found, add all their members back to candidates.
        """
        for cid, cluster in enumerate(self.clusters):
            size = len(cluster)
            k = math.ceil(math.log(size, 2))
            if k <= 1:
                continue

            samples = random.choices(cluster, k=k)
            gains = []
            for jc in samples:
                merged = copy.deepcopy(self.initial_df)
                merged[jc.column] = jc.merged_df[jc.column]
                tmp_metric = max(self.model.train_pred_eval(merged, self.class_attr), self.metric)
                gains.append(tmp_metric)
                self.total_queries += 1

            mean_gain = sum(gains) / len(gains)
            irregular = sum(1 for g in gains
                            if g > mean_gain * (1 + self.epsilon)
                            or g < mean_gain / (1 + self.epsilon))
            if irregular > len(gains) / 2:
                for jc in cluster:
                    self.candidates.append(jc.loc)
