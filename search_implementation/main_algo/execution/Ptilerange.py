"""
This file contains the implementation of the range predicate algorithm for FPtile problem.
note that we use the federated setting, that is we use synopsis of datasets as the input.
About the CPtile problem, we directly use the dataset.

difference is that we need to compute the maximal rectangles and only consider this if it fits
in the range predicate.

The algorithm is based on the paper's Algorithm 3 & 4
"""



from main_algo.execution.setups4range import construct_T_input_range, compute_R_prime_range, compute_R_prime_range_with_bounds, compute_global_bounds_from_synopses
from main_algo.data_processing.histograms import Histogram
from main_algo.execution.setups4range import construct_T_input_range_per_dataset

import numpy as np
from rtree import index
from typing import Optional, List, Tuple, Dict


class RangeDynamicRangeTree:
    def __init__(self, d: int, rtree_dim: Optional[int] = None):
        self.d = d
        # For 1D data, we use a 4D rtree to store maximal pairs (rho, rho_hat)
        # For threshold queries, 1D data is mapped to 2D points, so rtree_dim will be 2
        self.actual_dim = rtree_dim if rtree_dim is not None else (4 if d == 1 else 4 * d)
        self.idx = index.Index(
            properties=index.Property(dimension=self.actual_dim),
            interleaved=True
        )
        self.entry_counter = 0
        self.entry_registry = {}       # {entry_id: (weight, dataset_idx)}
        self.dataset_points = {}       # {dataset_idx: set(entry_ids)}
        self.original_data = {}        # {dataset_idx: (Q_j, W_j)}

    def insert_maximal_rectangle(
            self,
            Q: np.ndarray,
            W: np.ndarray,
            I: np.ndarray,
    ) -> None:
        """
        Insert maximal rectangles into the range tree.
        Q: (N, 4d) array, each row is (rho_min, rho_hat_min, rho_max, rho_hat_max)
        W: (N,) array, weights
        I: (N,) array, dataset indices
        """
        # Store for re-insertion
        for dataset_idx in np.unique(I):
            mask = (I == dataset_idx)
            self.original_data[dataset_idx] = (Q[mask], W[mask])

        # Insert all items into RTree
        for i, (q, w, idx) in enumerate(zip(Q, W, I)):
            entry_id = self.entry_counter + i
            # For 1D data, q is a 4D point [rho_min, rho_hat_min, rho_max, rho_hat_max]
            # For nD data, q is a 4d-dimensional point
            coords = q.tolist()
            self.idx.insert(entry_id, coords, (float(w), int(idx)))
        
        # Update the metadata
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
        Report the first maximal rectangle that intersects with the query hyperrectangle
        and whose weight is in I_prime.
        """

        matches = (
            (item.id, item.object[1])  # (entry_id, dataset_idx)
            for item in self.idx.intersection(R_prime, objects=True)
            if I_prime[0] <= item.object[0] <= I_prime[1]
        )
        try:
            return next(matches)
        except StopIteration:
            return None, None

    def delete_rectangles_by_dataset(self, dataset_idx: int) -> None:
        if dataset_idx not in self.dataset_points:
            return
        delete_ids = list(self.dataset_points[dataset_idx])
        bounds = [self.idx.get_bounds(id) for id in delete_ids]
        self.idx.delete(zip(delete_ids, bounds))
        for entry_id in delete_ids:
            del self.entry_registry[entry_id]
        self.dataset_points[dataset_idx].clear()


    def reinsert_dataset(self, dataset_idx: int) -> None:
        if dataset_idx not in self.original_data:
            return
        Q_j, W_j = self.original_data[dataset_idx]
        I_j = np.full(len(Q_j), dataset_idx)
        self.insert_maximal_rectangle(Q_j, W_j, I_j)


class MultipleRangeTrees:
    """
    Manages multiple range trees, with each dataset having its own independent range tree.
    """
    def __init__(self, d: int):
        self.d = d
        self.trees = {}  # {dataset_idx: RangeDynamicRangeTree}
        self.dataset_count = 0
    
    def add_dataset_tree(self, dataset_idx: int, Q: np.ndarray, W: np.ndarray, I: np.ndarray):
        """
        Adds a range tree for the specified dataset.
        
        Args:
            dataset_idx: Dataset index.
            Q: Maximal pair representation.
            W: Weights.
            I: Dataset index array.
        """
        if len(Q) == 0:
            print(f"Dataset {dataset_idx}: No maximal pairs, skipping.")
            return
        
        tree = RangeDynamicRangeTree(self.d)
        tree.insert_maximal_rectangle(Q, W, I)
        self.trees[dataset_idx] = tree
        self.dataset_count += 1
        print(f"Created range tree for dataset {dataset_idx} with {len(Q)} maximal pairs.")
    
    def get_tree(self, dataset_idx: int) -> Optional[RangeDynamicRangeTree]:
        """
        Retrieves the range tree for the specified dataset.
        """
        return self.trees.get(dataset_idx)

    def query_all_trees(self, R_min: np.ndarray, R_max: np.ndarray, 
                       theta: Tuple[float, float], epsilon: float, delta: float,
                       synopses) -> List[int]:
        """
        Queries all range trees and returns the indices of datasets that satisfy the conditions.
        
        Args:
            R_min: Minimum coordinates of the query rectangle.
            R_max: Maximum coordinates of the query rectangle.
            theta: Query range interval [a_theta, b_theta].
            epsilon: Privacy parameter ε.
            delta: Privacy parameter δ.
            synopses: Synopses used for computing global bounds.
        
        Returns:
            List of dataset indices that satisfy the conditions.
        """
        from main_algo.execution.setups4range import compute_R_prime_range
        
        try:
            # Compute the query rectangle.
            R_query = compute_R_prime_range(synopses, R_min, R_max, d=self.d)
        except ValueError as e:
            print(f"Query error: {e}")
            return []
        
        a_theta, b_theta = theta
        weight_interval = (a_theta - epsilon - delta, b_theta + epsilon + delta)
        
        print(f"Querying all range trees, weight interval: [{weight_interval[0]:.3f}, {weight_interval[1]:.3f}]")
        
        J = set()  # Indices of datasets that satisfy the conditions.
        
        for dataset_idx, tree in self.trees.items():
            print(f"Querying range tree for dataset {dataset_idx}...")
            
            # Get all candidates for this dataset.
            candidate_items = list(tree.idx.intersection(R_query, objects=True))
            
            if not candidate_items:
                print(f"  Dataset {dataset_idx}: No geometrically intersecting candidates.")
                continue
            
            # Extract weights.
            weights = [item.object[0] for item in candidate_items]
            max_weight = max(weights)
            
            print(f"  Dataset {dataset_idx}: Found {len(candidate_items)} candidates, max_weight={max_weight:.3f}")
            
            # Check if max weight is within the query interval.
            if weight_interval[0] <= max_weight <= weight_interval[1]:
                J.add(dataset_idx)
                print(f"  Dataset {dataset_idx}: Satisfies conditions, adding to results.")
            else:
                print(f"  Dataset {dataset_idx}: Does not satisfy conditions.")
        
        result = sorted(list(J))
        print(f"Query completed, returning {len(result)} satisfying datasets: {result}")
        return result
    
    def get_tree_count(self) -> int:
        """Returns the number of range trees."""
        return len(self.trees)
    
    def get_total_entries(self) -> int:
        """Returns the total number of entries across all range trees."""
        total = 0
        for tree in self.trees.values():
            total += tree.entry_counter
        return total
    
    def print_statistics(self):
        """Prints statistics."""
        print(f"\n=== Multiple Range Trees Statistics ===")
        print(f"Number of datasets: {self.dataset_count}")
        print(f"Number of range trees: {self.get_tree_count()}")
        print(f"Total entries: {self.get_total_entries()}")
        
        for dataset_idx, tree in self.trees.items():
            print(f"  Dataset {dataset_idx}: {tree.entry_counter} entries")


def construct_T_range(
    synopses,  
    epsilon: float,
    phi: float,
    d: int,
    use_sweep_line: bool = True
) -> RangeDynamicRangeTree:
    """
    Construct the range tree with optional sweep line optimization.
    
    param synopses: synopses data
    param epsilon: privacy parameter
    param phi: privacy parameter
    param d: dimension of the data
    param use_sweep_line: whether to use sweep line + R-tree method for maximal pairs
    return: RangeDynamicRangeTree
    """
    Q, W, I = construct_T_input_range(synopses, epsilon, phi, d, use_sweep_line)
    T = RangeDynamicRangeTree(d)
    T.insert_maximal_rectangle(Q, W, I)
    return T

def query_T_range(
    T: RangeDynamicRangeTree,
    R_min: np.ndarray,
    R_max: np.ndarray,
    theta: Tuple[float, float],
    epsilon: float,
    delta: float,
    synopses: List[Tuple[np.uint32, Histogram]],
) -> List[int]:
    """
    Query the range tree using max weight approach for range queries.

    1. Automatically detects data bounds and adjusts query range if needed.
    2. Fetches all candidate items that satisfy the geometric query.
    3. Groups these candidates by the dataset they belong to.
    4. For each dataset, it finds the maximum weight among all maximal pairs.
    5. A dataset is included in the final result only if this max weight
       falls within the query interval [a_θ - ε - δ, b_θ + ε + δ].

    param T: The dynamic range tree.
    param R_min: The query rectangle minimum coordinates.
    param R_max: The query rectangle maximum coordinates.
    param theta: The query range interval [a_theta, b_theta].
    param epsilon: The privacy parameter ε.
    param delta: The privacy parameter δ.
    param synopses: list of synopses for computing global bounds
    return: A list of dataset indices that satisfy the query.
    """
   
    try:
        # Compute the query rectangle with automatic range adjustment
        R_query = compute_R_prime_range(synopses, R_min, R_max, d=T.d)
    except ValueError as e:
        print(f"Query error: {e}")
        return []  # Return empty result for invalid query ranges
    
    a_theta, b_theta = theta
    # Correctly implement I' = [a_θ - ε - δ, b_θ + ε + δ] from Algorithm 4
    weight_interval = (a_theta - epsilon - delta, b_theta + epsilon + delta)

    # 1. Fetch all candidates that satisfy the geometric constraints.
    candidate_items = list(T.idx.intersection(R_query, objects=True))
    print(f"Found {len(candidate_items)} candidate items from geometric intersection")

    # 2. Group candidates by dataset index.
    dataset_candidates = {}
    for item in candidate_items:
        weight, dataset_idx = item.object
        if dataset_idx not in dataset_candidates:
            dataset_candidates[dataset_idx] = []
        dataset_candidates[dataset_idx].append(weight)
    

    # 3. For each dataset, find the maximum weight.
    J = set()
    for dataset_idx, weights in dataset_candidates.items():
        if not weights:
            continue

        max_weight = max(weights)
        print(f"Dataset {dataset_idx}: max_weight={max_weight}, interval=[{weight_interval[0]:.2f}, {weight_interval[1]:.2f}]")

        # 4. Check if the max weight is within the query interval.
        if weight_interval[0] <= max_weight <= weight_interval[1]:
            J.add(dataset_idx)

    return sorted(list(J))


def query_T_range_with_bounds(
    T: RangeDynamicRangeTree,
    R_min: np.ndarray,
    R_max: np.ndarray,
    theta: Tuple[float, float],
    epsilon: float,
    delta: float,
    data_bounds: Tuple[np.ndarray, np.ndarray],
) -> List[int]:
    """
    Query the range tree using pre-computed data bounds to avoid recalculating global bounds.
    
    This function is more efficient when multiple queries are performed on the same dataset,
    as it avoids recalculating the global bounding box for each query.

    param T: The dynamic range tree.
    param R_min: The query rectangle minimum coordinates.
    param R_max: The query rectangle maximum coordinates.
    param theta: The query range interval [a_theta, b_theta].
    param epsilon: The privacy parameter ε.
    param delta: The privacy parameter δ.
    param data_bounds: tuple of (data_min, data_max) from global bounding box
    return: A list of dataset indices that satisfy the query.
    """
   
    try:
        # Compute the query rectangle using pre-computed data bounds
        R_query = compute_R_prime_range_with_bounds(R_min, R_max, data_bounds, T.d)
    except ValueError as e:
        print(f"查询错误: {e}")
        return []  # Return empty result for invalid query ranges
    
    a_theta, b_theta = theta
    # Correctly implement I' = [a_θ - ε - δ, b_θ + ε + δ] from Algorithm 4
    weight_interval = (a_theta - epsilon - delta, b_theta + epsilon + delta)

    # 1. Fetch all candidates that satisfy the geometric constraints.
    candidate_items = list(T.idx.intersection(R_query, objects=True))
    print(f"Found {len(candidate_items)} candidate items from geometric intersection")

    # 2. Group candidates by dataset index.
    dataset_candidates = {}
    for item in candidate_items:
        weight, dataset_idx = item.object
        if dataset_idx not in dataset_candidates:
            dataset_candidates[dataset_idx] = []
        dataset_candidates[dataset_idx].append(weight)
    

    # 3. For each dataset, find the maximum weight.
    J = set()
    for dataset_idx, weights in dataset_candidates.items():
        if not weights:
            continue

        max_weight = max(weights)
        print(f"Dataset {dataset_idx}: max_weight={max_weight}, interval=[{weight_interval[0]:.2f}, {weight_interval[1]:.2f}]")

        # 4. Check if the max weight is within the query interval.
        if weight_interval[0] <= max_weight <= weight_interval[1]:
            J.add(dataset_idx)

    return sorted(list(J))


def construct_multiple_T_range(
    synopses,  
    epsilon: float,
    phi: float,
    d: int,
    use_sweep_line: bool = True,
    seed: int = 42
) -> MultipleRangeTrees:
    """
    Constructs range trees for each dataset separately.
    
    param synopses: Synopses data.
    param epsilon: Privacy parameter.
    param phi: Privacy parameter.
    param d: Dimension of the data.
    param use_sweep_line: Whether to use sweep line + R-tree method for maximal pairs.
    param seed: Random seed.
    return: MultipleRangeTrees object.
    """

    
    print("Starting to construct range trees for each dataset separately...")
    
    # Get (Q, W, I) for each dataset.
    dataset_results = construct_T_input_range_per_dataset(synopses, epsilon, phi, d, use_sweep_line, seed)
    
    # Create multiple range tree manager.
    multiple_trees = MultipleRangeTrees(d)
    
    # Create independent range trees for each dataset.
    for dataset_idx, (Q, W, I) in enumerate(dataset_results):
        multiple_trees.add_dataset_tree(dataset_idx, Q, W, I)
    
    # Print statistics.
    multiple_trees.print_statistics()
    
    return multiple_trees


def query_multiple_T_range(
    multiple_trees: MultipleRangeTrees,
    R_min: np.ndarray,
    R_max: np.ndarray,
    theta: Tuple[float, float],
    epsilon: float,
    delta: float,
    synopses: List[Tuple[np.uint32, Histogram]],
) -> List[int]:
    """
    Queries multiple range trees.
    
    param multiple_trees: MultipleRangeTrees object.
    param R_min: Minimum coordinates of the query rectangle.
    param R_max: Maximum coordinates of the query rectangle.
    param theta: Query range interval [a_theta, b_theta].
    param epsilon: Privacy parameter ε.
    param delta: Privacy parameter δ.
    param synopses: Synopses used for computing global bounds.
    return: List of dataset indices that satisfy the conditions.
    """
    return multiple_trees.query_all_trees(R_min, R_max, theta, epsilon, delta, synopses)