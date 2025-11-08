"""
This file contains the implementation of the threshold predicate algorithm for FPtile problem.
note that we use the federated setting, that is we use synopsis of datasets as the input.
About the CPtile problem, we directly use the dataset.

The algorithm is based on the paper's Algorithm 1 & 2
"""



from main_algo.execution.setups4threshold import construct_T_input_threshold, compute_R_prime_threshold
from main_algo.data_processing.histograms import Histogram


import numpy as np
from rtree import index
from typing import Optional, List, Tuple, Dict
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
import time


class ThresholdDynamicRangeTree:
    def __init__(self, d: int):
        """
        param d: dimension of the data
        For 1D data, we map each interval [a,b] to a point (a,b) in 2D space.
        """
        self.d = d
        # For 1D data, we use a 2D rtree to store 2D points.
        self.actual_dim = 2 if d == 1 else 2 * d
        self.idx = index.Index(
            properties=index.Property(dimension=self.actual_dim),
            interleaved=True
        )
        self.entry_counter = 0
        self.entry_registry = {}       # {entry_id: (weight, dataset_idx)}
        self.dataset_points = {}       # {dataset_idx: set(entry_ids)} stores the entry_ids of the hyperrectangles that belong to the dataset
        self.original_data = {}        # {dataset_idx: (Q_j, W_j)} stores the original data for re-insertion

    def insert_hyperrectangle(
            self, 
            Q: np.ndarray, 
            W: np.ndarray, 
            I: np.ndarray
    ) -> None:
        """
        Inserts the hyperrectangles into the dynamic range tree.
        param Q: hyperrectangle coordinates
        param W: weights
        param I: dataset indices
        """
        # Store the original data for re-insertion.
        for dataset_idx in np.unique(I):
            mask = (I == dataset_idx)
            self.original_data[dataset_idx] = (Q[mask], W[mask])
        
        # Batch insert into RTree to improve efficiency.
        for i, (q, w, idx) in enumerate(zip(Q, W, I)):
            entry_id = self.entry_counter + i
            # For 1D data, q is the point [a, b]. We insert it as a point
            # into the 2D rtree. rtree expects a bounding box, so a point
            # (a,b) is represented as a degenerate rectangle [a, b, a, b].
            if self.d == 1:
                a, b = q[0], q[1]
                coords = [a, b, a, b]  # [min_x, min_y, max_x, max_y]
            else:
                coords = q.tolist()
            self.idx.insert(entry_id, coords, (float(w), int(idx)))
        
        # Update the metadata.
        for i, (q, w, idx) in enumerate(zip(Q, W, I)):
            entry_id = self.entry_counter + i
            self.entry_registry[entry_id] = (w, idx)
            if idx not in self.dataset_points:
                self.dataset_points[idx] = set()
            self.dataset_points[idx].add(entry_id)
        self.entry_counter += len(Q)

    def report_first(
            self, 
            R_prime: tuple, 
            I_prime: Tuple[float, float]
    ) -> Tuple[Optional[int], Optional[int]]:
        """
        Reports the first hyperrectangle that intersects with the query hyperrectangle.
        param R_prime: query hyperrectangle
        param I_prime: query threshold interval
        return: the first hyperrectangle that intersects with the query hyperrectangle
        """
        matches = (
            (item.id, item.object[1])  # (entry_id, dataset_idx)
            for item in self.idx.intersection(R_prime, objects=True)
            if I_prime[0] <= item.object[0] <= I_prime[1]  # weight check
        )

        try:
            return next(matches)  # Returns the first match.
        except StopIteration:
            return None, None

    def delete_rectangles_by_dataset(
            self, 
            dataset_idx: int
    ) -> None:
        """
        Deletes the hyperrectangles that belong to the dataset.
        param dataset_idx: index of the dataset
        """
        if dataset_idx not in self.dataset_points:
            return
        
        # Delete each item individually since rtree's batch delete is not working as expected.
        delete_ids = list(self.dataset_points[dataset_idx])
        for entry_id in delete_ids:
            self.idx.delete(entry_id, self.idx.get_bounds(entry_id))
        
        # Clean up the metadata.
        for entry_id in delete_ids:
            del self.entry_registry[entry_id]
        self.dataset_points[dataset_idx].clear()

    def reinsert_dataset(
            self, 
            dataset_idx: int
    ) -> None:
        """
        Reinserts the hyperrectangles that belong to the dataset.
        param dataset_idx: index of the dataset
        """
        if dataset_idx not in self.original_data:
            return
        
        Q_j, W_j = self.original_data[dataset_idx]
        I_j = np.full(len(Q_j), dataset_idx)
        self.insert_hyperrectangle(Q_j, W_j, I_j)

    

def construct_T_threshold(
        synopses: List[Histogram],
        epsilon: float,
        phi: float, # at least 1-phi probability that S_i is a epsilon+delta-sample of synopsis (random sampling from the synopsis)
        d: int,
        seed: int = 42
) -> ThresholdDynamicRangeTree:
    """
    construct the dynamic range tree T with epsilon-approximate sampling
    
    1. Perform epsilon-approximate sampling from synopses (n = 1/ε²)
    2. Construct the hyperrectangles Q,W,I
    3. Insert the hyperrectangles into the dynamic range tree
    4. Return the dynamic range tree
    
    param synopses: List of synopses (histograms)
    param epsilon: ε-approximation parameter (sampling size = 1/ε²)
    param phi: privacy parameter
    param d: dimension of data
    param seed: random seed for reproducibility
    return: ThresholdDynamicRangeTree
    """
    Q, W, I = construct_T_input_threshold(synopses, epsilon, phi, d, seed)

    T = ThresholdDynamicRangeTree(d)
    T.insert_hyperrectangle(Q, W, I)

    return T


def query_T_threshold(
    T: ThresholdDynamicRangeTree, R_prime: list, theta: Tuple[float, float], epsilon: float, delta: float
) -> List[int]:
    """
    Query the dynamic range tree T using an optimized, in-memory filtering approach.
    
    1. Fetches a candidate set of intersecting items from the rtree.
    2. Iteratively finds the first valid item, records its dataset, and removes
       all items from that same dataset from the candidate list before repeating.
    This simulates the "delete-reinsert" logic safely in memory.

    param T: The dynamic range tree.
    param R_prime: The logical query rectangle for the transformed space.
    param theta: The query threshold interval [a_θ, 1].
    param epsilon: The privacy parameter ε.
    param delta: The privacy parameter δ.
    return: A list of dataset indices that satisfy the query.
    """
    a_theta, _ = theta
    weight_interval = (a_theta - epsilon - delta, 1.0)

    # 1. Get a candidate set of all items that *intersect* with R_prime.
    candidate_items = list(T.idx.intersection(R_prime, objects=True))
    
    # This set will store the final dataset indices.
    J = set()

    # Continue as long as there are candidates to check.
    while candidate_items:
        found_match = False
        item_to_process = None
        
        # 2. Find the first valid item in the current candidate list.
        for item in candidate_items:
            # Apply our precise filtering logic
            if T.d == 1:
                query_min_x, _, _, query_max_y = R_prime
                item_x, item_y = item.bounds[0], item.bounds[1]
                is_spatially_contained = (item_x >= query_min_x and item_y <= query_max_y)
            else: # nD case
                query_min = np.array(R_prime[:T.d * 2])
                query_max = np.array(R_prime[T.d * 2:])
                item_coords = np.array(item.bounds[:T.d * 2])
                is_spatially_contained = np.all((item_coords >= query_min) & (item_coords <= query_max))

            weight, dataset_idx = item.object
            is_weight_ok = (weight_interval[0] <= weight <= weight_interval[1])

            if is_spatially_contained and is_weight_ok:
                item_to_process = item
                found_match = True
                print(f"Found match: ID={item.id}, Dataset={dataset_idx}, Weight={weight:.3f}")
                break
        
        # If no valid item was found in the list, we're done.
        if not found_match:
            break

        # 3. A valid item was found. Record its dataset.
        _, dataset_to_remove = item_to_process.object
        J.add(dataset_to_remove)

        # 4. Remove all items from this dataset from the candidate list for the next iteration.
        candidate_items = [
            item for item in candidate_items 
            if item.object[1] != dataset_to_remove
        ]
            
    return sorted(list(J))


# def query_T_threshold_with_removal(
#     T: ThresholdDynamicRangeTree,
#     R_prime: tuple,
#     theta: Tuple[float, float],
#     epsilon: float,
#     delta: float
# ) -> List[int]:
#     """
#     Query T by iteratively removing matched datasets.
#     Follows the original algorithm's "delete-reinsert" approach.
#     """
#     a_theta, _ = theta
#     I_prime = (a_theta - epsilon - delta, 1.0)
#     J = set()

#     while True:
#         # 1. Find the first matching entry
#         entry_id, dataset_idx = T.report_first(R_prime, I_prime)
#         if entry_id is None:
#             break  # No more matches

#         print(f"Found match: ID={entry_id}, Dataset={dataset_idx}")

#         # 2. Record the dataset index
#         J.add(dataset_idx)

#         # 3. Remove ALL entries from this dataset
#         T.delete_rectangles_by_dataset(dataset_idx)

#     # 4. Reinsert all removed datasets
#     for dataset_idx in J:
#         T.reinsert_dataset(dataset_idx)

#     return sorted(J)


# For the new parallel sampling function
from main_algo.execution.setups4range import compute_global_bounding_box, project_to_bounding_box
from main_algo.execution.setups4threshold import (
    generate_hyperrectangles_auto, compute_weights_for_hyperrectangles, weighted_random_sampling_from_histogram,
    compute_R_prime_threshold
)
from main_algo.execution.Ptilerange import RangeDynamicRangeTree # Used as threshold tree


def _process_sampling_and_hyperrectangles(dataset_idx: int, 
                                            dataset_synopses: List[Tuple[np.uint32, Histogram]], 
                                            d: int, epsilon: float, delta: float, seed: int) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Processes sampling and hyperrectangle generation for a single dataset (Threshold query specific, runnable in independent process)
    """
    # 1. Epsilon sampling
    n_samples = int(1 / epsilon**2)
    if d == 1:
        S_i = weighted_random_sampling_from_histogram(dataset_synopses[0][1], n_samples, seed=seed)
        all_datasets = [S_i]
    else:
        S_multi = []
        for synopsis in dataset_synopses:
            S_dim = weighted_random_sampling_from_histogram(synopsis[1], n_samples, seed=seed)
            S_multi.append(S_dim)
        S_i = np.column_stack(S_multi)
        all_datasets = [S_i]

    # 2. Compute global bounding box (even for a single dataset, for compatibility with generate_hyperrectangles_auto)
    B_min, B_max = compute_global_bounding_box(all_datasets)

    # 3. Construct hyperrectangles for this dataset
    # For Threshold queries, hyperrectangles are generated differently from Range queries
    # Range queries generate maximal pairs (rho, rho_hat)
    # Threshold queries generate rho (intervals/hyperrectangles) themselves
    projection_S_i = project_to_bounding_box(all_datasets[0], B_min, B_max)
    R_i = generate_hyperrectangles_auto(all_datasets[0], d)

    if len(R_i) == 0:
        return None, None, None

    weights = compute_weights_for_hyperrectangles(all_datasets[0], R_i)

    # Prepare R-tree input format
    Qi, Wi, Ii = [], [], []
    for idx, rho in enumerate(R_i):
        if d == 1:
            # For 1D data, map [a,b] to a 2D point (a,b)
            q = np.array([rho['min_coords'][0], rho['max_coords'][0]])
        else:
            # For nD data, map hyperrectangle to 2d point (min_coords, max_coords)
            q = np.concatenate([rho['min_coords'], rho['max_coords']])
        Qi.append(q)
        Wi.append(weights[idx])
        Ii.append(dataset_idx)  # Record original dataset index

    return np.array(Qi), np.array(Wi), np.array(Ii)


def query_threshold_with_parallel_sampling(
    synopses: List[Tuple[np.uint32, Histogram]],
    n_datasets: int,
    R_min: np.ndarray,
    R_max: np.ndarray,
    threshold: Optional[float],
    epsilon: float,
    delta: float,
    d: int,
    max_trials: int,
    seed: int,
    verbose: bool = True
) -> Dict:
    """
    Executes Threshold query using parallelized multiple epsilon sampling strategy.

    Args:
        synopses: List of synopses (histograms) for all datasets.
        n_datasets: Total number of datasets.
        R_min: Minimum coordinates of the query rectangle.
        R_max: Maximum coordinates of the query rectangle.
        threshold: Threshold value.
        epsilon: Epsilon approximation parameter.
        delta: Delta parameter.
        d: Data dimension.
        max_trials: Maximum number of sampling trials.
        seed: Random seed.
        verbose: Whether to print detailed information.

    Returns:
        Result dictionary containing intersecting datasets and statistics.
    """
    # Assuming QueryConfig is available or threshold is passed directly
    from config import QueryConfig # Import QueryConfig locally or ensure it's imported globally if needed
    threshold = threshold or QueryConfig.DEFAULT_THRESHOLD
    theta = (threshold, 1.0)

    if verbose:
        print(f"\n{'='*80}")
        print(f"  Starting Parallelized Multiple Sampling Threshold Query")
        print(f"{'='*80}")
        print(f"  Query Range: {R_min} x {R_max}")
        print(f"  Threshold: {threshold}")
        print(f"  Max Trials: {max_trials}")
        print(f"{'='*80}\n")

    start_time = time.time()

    intersecting_datasets = set()
    dataset_first_hit = {}
    active_datasets = set(range(n_datasets))
    trials_completed = 0

    with ProcessPoolExecutor(max_workers=min(mp.cpu_count(), n_datasets)) as executor:
        while active_datasets and trials_completed < max_trials:
            trials_completed += 1
            if verbose:
                print(f"\n--- Threshold Query Trial {trials_completed}/{max_trials} ---")
                print(f"  Active datasets: {sorted(list(active_datasets))}")

            all_hyperrectangles = []
            all_weights = []
            all_dataset_indices = []

            futures = {
                executor.submit(_process_sampling_and_hyperrectangles, 
                                dataset_idx, 
                                synopses[dataset_idx * d:(dataset_idx + 1) * d], 
                                d, epsilon, delta, 
                                seed + trials_completed + dataset_idx):
                dataset_idx for dataset_idx in active_datasets
            }

            for future in as_completed(futures):
                dataset_idx = futures[future]
                try:
                    Q_i, W_i, I_i = future.result()
                    if Q_i is not None and len(Q_i) > 0:
                        all_hyperrectangles.append(Q_i)
                        all_weights.append(W_i)
                        all_dataset_indices.append(I_i)
                except Exception as exc:
                    print(f'Dataset {dataset_idx} sampling or hyperrectangle generation failed: {exc}')

            if not all_hyperrectangles:
                if verbose:
                    print("  No hyperrectangles generated in this trial. Continuing to next trial.")
                continue

            # Aggregate all hyperrectangles from active datasets into one set for the current trial
            Q_trial = np.concatenate(all_hyperrectangles)
            W_trial = np.concatenate(all_weights)
            I_trial = np.concatenate(all_dataset_indices)

            # Construct a single RangeDynamicRangeTree for this trial (Threshold tree uses RangeDynamicRangeTree)
            if verbose:
                print(f"  Building Threshold Tree for Trial {trials_completed} with {len(Q_trial)} hyperrectangles...")
            # For Threshold queries, the R-tree stores 2D points (a,b) for 1D data, or 2d points for nD data.
            # So the dimension for RangeDynamicRangeTree needs to be 2 if self.d == 1, or 2 * self.d if self.d > 1.
            tree_dim = 2 if d == 1 else 2 * d
            trial_tree = RangeDynamicRangeTree(d, rtree_dim=tree_dim)
            trial_tree.insert_maximal_rectangle(Q_trial, W_trial, I_trial)

            # Compute R_prime for the query
            R_prime = compute_R_prime_threshold(R_min, R_max)

            # Query the single Threshold Tree
            if verbose:
                print(f"  Querying Threshold Tree for Trial {trials_completed}...")
            current_trial_intersecting_datasets = query_T_threshold(
                trial_tree, R_prime, theta, epsilon, delta
            )

            newly_intersecting = set()
            for ds_idx in current_trial_intersecting_datasets:
                if ds_idx in active_datasets:
                    newly_intersecting.add(ds_idx)
                    if ds_idx not in dataset_first_hit:
                        dataset_first_hit[ds_idx] = trials_completed
                        intersecting_datasets.add(ds_idx)

            if verbose:
                print(f"  Trial {trials_completed} intersecting datasets: {sorted(list(newly_intersecting))}")

            active_datasets -= newly_intersecting # Remove newly found datasets from active set

            if verbose and not active_datasets:
                print("  All datasets found to be satisfying threshold or no active datasets left. Early stopping.")

    elapsed = time.time() - start_time

    result_summary = {
        'intersecting_datasets': sorted(list(intersecting_datasets)),
        'n_intersecting': len(intersecting_datasets),
        'n_total_datasets': n_datasets,
        'total_trials': trials_completed,
        'max_trials': max_trials,
        'dataset_first_hit': dataset_first_hit,
        'epsilon': epsilon,
        'samples_per_trial': int(1 / epsilon**2),
        'query_range': (R_min.tolist(), R_max.tolist()),
        'threshold': threshold,
        'elapsed_time': elapsed,
        'avg_time_per_trial': elapsed / (n_datasets * trials_completed) if (n_datasets * trials_completed) > 0 else 0,
        'parallel_query': True
    }
    return result_summary