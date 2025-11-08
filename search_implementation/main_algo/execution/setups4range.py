'''
This file contains the necessary setups for Ptile problem, especially for range predicate.
Note that from the paper, every dataset should have the same dimension, thus is applicable to the range tree.
'''
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import numpy as np
from typing import List, Tuple, Dict, Optional
from main_algo.data_processing.histograms import Histogram
from main_algo.execution.setups4threshold import weighted_random_sampling_from_histogram, generate_hyperrectangles_auto, compute_weights_for_hyperrectangles
from main_algo.execution.maximalpair4range import generate_pair_for_range_predicate_sweep_line, generate_candidate_pairs_brute_force, generate_pair_for_range_predicate_brute_force

INF=1e20 # simulate the infinite value


def compute_global_bounding_box(coresets: List[np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Computes the global bounding box (B_min, B_max) from a list of coresets.
    """
    # Reshape 1D arrays to 2D for consistent handling
    processed_coresets = []
    for cs in coresets:
        if cs.ndim == 1:
            processed_coresets.append(cs.reshape(-1, 1))
        else:
            processed_coresets.append(cs)
            
    merged_coreset = np.concatenate(processed_coresets)
    
    B_min = np.min(merged_coreset, axis=0)
    B_max = np.max(merged_coreset, axis=0)
    return B_min, B_max

def project_to_bounding_box(
    S_i: np.ndarray,
    B_min: np.ndarray,
    B_max: np.ndarray
) -> np.ndarray:
    """
    Generates projection points for each sampled point on each dimension's min/max bounds.
    Returns a collection of all projection points.
    For 1D case, returns boundary points as a (2, 1) 2D array.
    For nD case, returns projection points as an (n, d) 2D array.
    """
    S_i = np.asarray(S_i)
    if S_i.ndim == 1 or S_i.shape[1] == 1:
        # Return only boundary points, shape (2, 1)
        return np.vstack([B_min.flatten(), B_max.flatten()]).reshape(-1, 1)
    else:
        # nD case: return projection points
        d = S_i.shape[1]
        projection_points = []
        for dim in range(d):
            proj_min = S_i.copy()
            proj_min[:, dim] = B_min[dim]
            projection_points.append(proj_min)
            proj_max = S_i.copy()
            proj_max[:, dim] = B_max[dim]
            projection_points.append(proj_max)
        return np.concatenate(projection_points)



def  generate_combinatorial_rectangles(
        S_i: np.ndarray,
        projection_S_i: np.ndarray,
        d: int
) -> List[Dict[str, np.ndarray]]:
    """
    Generate combinatorial rectangles for range predicate Ptile problem
    Now with automatic optimization for high-dimensional data.
    """
    # For low-dimensional data, use the original version
    # Handle 1D arrays by reshaping them to 2D
    if S_i.ndim == 1:
        S_i = S_i.reshape(-1, 1)
    
    # projection_S_i is already 2D from project_to_bounding_box
    union_of_S_i = np.concatenate([S_i, projection_S_i])
    rectangles = generate_hyperrectangles_auto(union_of_S_i, d)
    
    return rectangles

def get_all_datasets(synopses: List[Tuple[np.uint32, Histogram]], d: int, epsilon: float, seed: int) -> List[np.ndarray]:
    """
    Get all datasets from synopses using epsilon-approximate sampling.
    """
    n_samples = int(1 / epsilon**2)
    
    # Check data dimension
    if d == 1:
        # 1D case: process each histogram independently
        all_datasets = []
        for hist_id, synopsis in synopses:
            S_i = weighted_random_sampling_from_histogram(synopsis, n_samples, seed=seed)
            all_datasets.append(S_i)
    else:
        # nD case: group histograms by dataset
        num_datasets = len(synopses) // d
        if len(synopses) % d != 0:
            raise ValueError(f"Number of synopses ({len(synopses)}) must be divisible by dimension ({d})")
        
        all_datasets = []
        for dataset_idx in range(num_datasets):
            # Sample for each dimension
            S_multi = []
            for dim in range(d):
                synopsis_idx = dataset_idx * d + dim
                hist_id, synopsis = synopses[synopsis_idx]
                S_dim = weighted_random_sampling_from_histogram(synopsis, n_samples, seed=seed)
                S_multi.append(S_dim)
            S_i = np.column_stack(S_multi)
            all_datasets.append(S_i)
    return all_datasets



def is_subset(rho, rho_hat):
    return np.all(rho['min_coords'] >= rho_hat['min_coords']) and np.all(rho['max_coords'] <= rho_hat['max_coords'])

def is_strict_subset(rho, rho_hat):
    return is_subset(rho, rho_hat) and (np.any(rho['min_coords'] > rho_hat['min_coords']) or np.any(rho['max_coords'] < rho_hat['max_coords']))

def is_strictly_interior_subset(rho_prime, rho_hat):
    """
    Checks if rho_prime is a strict subset of rho_hat without touching any boundaries.
    This corresponds to the ρ' ⊂⊂ ρ̂ condition in the paper.
    """
    return np.all(rho_prime['min_coords'] > rho_hat['min_coords']) and np.all(rho_prime['max_coords'] < rho_hat['max_coords'])


def compute_global_bounds_from_synopses(
    synopses: List[Tuple[np.uint32, Histogram]], 
    d: int,
    epsilon: float,
    seed: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute global bounding box from synopses for reuse across multiple queries.
    
    param synopses: List of (histogram_id, histogram) tuples
    param d: dimension of the data
    return: tuple of (B_min, B_max) global bounding box
    """
    all_datasets = get_all_datasets(synopses, d, epsilon, seed)
    B_min, B_max = compute_global_bounding_box(all_datasets)
    print(f"Computed global bounds: B_min={B_min}, B_max={B_max}")
    return B_min, B_max


def construct_T_input_range(
    synopses: List[Tuple[np.uint32, Histogram]], 
    epsilon: float,
    phi: float,
    d: int,
    use_sweep_line: bool = True,
    seed: int = 42
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Constructs input for the dynamic range tree T with epsilon-approximate sampling.
    For nD data, every d histograms form a dataset.
    Uses brute force maximal pair computation and global bounding box.
    
    param synopses: List of (histogram_id, histogram) tuples
    param epsilon: privacy parameter
    param phi: privacy parameter
    param d: dimension of the data
    param use_sweep_line: whether to use sweep line + R-tree method for maximal pairs
    param seed: random seed
    return:
        - Q: Union of all maximal pairs representations
        - W: Weights of all maximal pairs
        - I: Index of the dataset (not histogram)
    """
    import time
    Q_list, W_list, I_list = [], [], []
    
    
    all_datasets = get_all_datasets(synopses, d, epsilon, seed)
        
    # Compute global bounding box
    B_min, B_max = compute_global_bounding_box(all_datasets)
    print(f"Using global bounds: B_min={B_min}, B_max={B_max}")
        
    # Process each dataset with global bounding box
    for dataset_idx, S_i in enumerate(all_datasets):
        dataset_start_time = time.time()
        # Use global bounding box
        projection_S_i = project_to_bounding_box(S_i, B_min, B_max)
            
        R_i = generate_combinatorial_rectangles(S_i, projection_S_i, d)
        rect_start_time = time.time()
        rect_time = time.time() - rect_start_time
        pair_start_time = time.time()
        
        # Choose maximal pairs generation method
        if use_sweep_line:
            maximal_pairs = generate_pair_for_range_predicate_sweep_line(R_i, d)
            print(f"  Generated {len(maximal_pairs)} maximal pairs using sweep line method in {time.time() - pair_start_time:.2f}s")
        else:
            # Generate candidate pairs using brute force, then filter using DAG
            candidate_pairs = generate_candidate_pairs_brute_force(R_i)
            maximal_pairs = generate_pair_for_range_predicate_brute_force(R_i)
            print(f"  Generated {len(maximal_pairs)} maximal pairs using brute force + DAG method in {time.time() - pair_start_time:.2f}s")
        
        weights = compute_weights_for_hyperrectangles(S_i, [rho for rho, rho_hat in maximal_pairs])
        Qi, Wi, Ii = [], [], []
        for idx, (rho, rho_hat) in enumerate(maximal_pairs):
            q = np.concatenate([
                rho['min_coords'], rho_hat['min_coords'], 
                rho['max_coords'], rho_hat['max_coords']
            ])
            Qi.append(q)
            Wi.append(weights[idx])
            Ii.append(dataset_idx)
        if Qi:
            Q_list.append(np.array(Qi))
            W_list.append(np.array(Wi))
            I_list.append(np.array(Ii))
    
    if Q_list:
        Q = np.concatenate(Q_list, axis=0)
        W = np.concatenate(W_list, axis=0)
        I = np.concatenate(I_list, axis=0)
    else:
        Q = np.array([])
        W = np.array([])
        I = np.array([])
    print(f"Generated {len(Q)} total entries")
    return Q, W, I


def adjust_query_range_to_data_bounds(
    R_min: np.ndarray,
    R_max: np.ndarray,
    data_bounds: Tuple[np.ndarray, np.ndarray],
    d: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Adjust query range to fit within data bounds.
    
    param R_min: left-bottom corner of the query hyperrectangle
    param R_max: right-top corner of the query hyperrectangle
    param data_bounds: tuple of (data_min, data_max) from global bounding box
    param d: dimension of the data
    return: tuple of (adjusted_R_min, adjusted_R_max)
    """
    # Handle zero-dimensional arrays
    if R_min.ndim == 0:
        R_min = np.array([R_min])
    if R_max.ndim == 0:
        R_max = np.array([R_max])
        
    d_query = len(R_min)  # dimension of the input space
    data_min, data_max = data_bounds
    
    # Print global bounds info
    if d == 1:
        print(f"Adjusting query range with global bounds: Global bounds [{data_min[0]:.3f}, {data_max[0]:.3f}]")
    else:
        print(f"Adjusting query range with global bounds: Global bounds")
        print(f"  Min: [{', '.join([f'{x:.3f}' for x in data_min])}]")
        print(f"  Max: [{', '.join([f'{x:.3f}' for x in data_max])}]")
    
    # Clamp query range to fit within data bounds
    adjusted_R_min = R_min.copy().astype(np.float64)
    adjusted_R_max = R_max.copy().astype(np.float64)
    
    if d_query == 1:
        # For 1D, clamp query range to data range
        original_min, original_max = R_min[0], R_max[0]
        
        # Check if query range is completely outside data range
        if original_max < data_min[0]:
            raise ValueError(f"Please check your query range, invalid range: Query range [{original_min:.3f}, {original_max:.3f}] is completely below data range [{data_min[0]:.3f}, {data_max[0]:.3f}]")
        elif original_min > data_max[0]:
            raise ValueError(f"Please check your query range, invalid range: Query range [{original_min:.3f}, {original_max:.3f}] is completely above data range [{data_min[0]:.3f}, {data_max[0]:.3f}]")
        
        adjusted_R_min[0] = float(max(R_min[0], data_min[0]))
        adjusted_R_max[0] = float(min(R_max[0], data_max[0]))
        
        print(f"  Adjusted query range: [{adjusted_R_min[0]:.6f}, {adjusted_R_max[0]:.6f}]")
    else:
        # For higher dimensions, clamp each dimension
        original_min, original_max = R_min.copy(), R_max.copy()
        
        # Check if query range is completely outside data range in any dimension
        for i in range(d_query):
            if original_max[i] < data_min[i]:
                raise ValueError(f"Please check your query range, invalid range: Query range in dimension {i} is completely below data range")
            elif original_min[i] > data_max[i]:
                raise ValueError(f"Please check your query range, invalid range: Query range in dimension {i} is completely above data range")
        
        for i in range(d_query):
            adjusted_R_min[i] = float(max(R_min[i], data_min[i]))
            adjusted_R_max[i] = float(min(R_max[i], data_max[i]))
        
        # Check if adjustment was needed
        if not np.array_equal(adjusted_R_min, original_min) or not np.array_equal(adjusted_R_max, original_max):
            print(f"Adjusting query range:")
            print(f"  Original: [{', '.join([f'{x:.3f}' for x in original_min])}] x [{', '.join([f'{x:.3f}' for x in original_max])}]")
            print(f"  Adjusted: [{', '.join([f'{x:.3f}' for x in adjusted_R_min])}] x [{', '.join([f'{x:.3f}' for x in adjusted_R_max])}]")
        else:
            print(f"Query range is within data bounds, no adjustment needed: [{', '.join([f'{x:.3f}' for x in R_min])}] x [{', '.join([f'{x:.3f}' for x in R_max])}]")
    
    return adjusted_R_min, adjusted_R_max


def compute_R_prime_range(
        synopses: List[Tuple[np.uint32, Histogram]],
        R_min: np.ndarray, 
        R_max: np.ndarray,
        d: Optional[int] = None,
        epsilon: float = 0.1,
        seed: int = 42
) -> list:
    """
    For 1D case: map query interval [R_min, R_max] to a 4D query rectangle.
    The query rectangle finds all maximal pairs (rho, rho_hat) such that:
    - rho_min >= R_min and rho_max <= R_max (rho is contained in query)
    - rho_hat_min <= R_min and rho_hat_max >= R_max (rho_hat contains query)
    
    param R_min: left-bottom corner of the query hyperrectangle
    param R_max: right-top corner of the query hyperrectangle
    param synopses: list of synopses for computing global bounds
    param d: dimension of the data
    return: R' as a flat list of coordinates for rtree intersection
    """
    d_query = len(R_min) if R_min.ndim > 0 else 1  # dimension of the input space
    
    all_datasets = get_all_datasets(synopses, d, epsilon, seed)
        
    # Use global bounds from histograms
    global_B_min, global_B_max = compute_global_bounding_box(all_datasets)
    data_bounds = (global_B_min, global_B_max)
    
    # Adjust query range to fit within data bounds
    adjusted_R_min, adjusted_R_max = adjust_query_range_to_data_bounds(R_min, R_max, data_bounds, d)
    
    # For 1D case
    if d_query == 1:
        # For query R=[adjusted_R_min, adjusted_R_max], we search for maximal pairs (rho, rho_hat)
        # where rho is contained in R and rho_hat contains R
        # 
        # Conditions:
        # 1. rho_min >= adjusted_R_min (rho starts at or after query start)
        # 2. rho_max <= adjusted_R_max (rho ends at or before query end)  
        # 3. rho_hat_min <= adjusted_R_min (rho_hat starts at or before query start)
        # 4. rho_hat_max >= adjusted_R_max (rho_hat ends at or after query end)
        #
        # For rtree intersection, we need to provide bounds in the format:
        # (min_x, min_y, min_z, min_w, max_x, max_y, max_z, max_w)
        # where each point in the rtree is (rho_min, rho_hat_min, rho_max, rho_hat_max)
        
        coords = [
            float(adjusted_R_min[0]),    # min_x: rho_min >= adjusted_R_min
            float(-INF),                 # min_y: rho_hat_min <= adjusted_R_min
            float(-INF),                 # min_z: rho_max <= adjusted_R_max
            float(adjusted_R_max[0]),    # min_w: rho_hat_max >= adjusted_R_max
            float(INF),                  # max_x: no upper bound for rho_min
            float(adjusted_R_min[0]),    # max_y: rho_hat_min <= adjusted_R_min
            float(adjusted_R_max[0]),    # max_z: rho_max <= adjusted_R_max
            float(INF)                   # max_w: no upper bound for rho_hat_max
        ]
        return coords
   
    else:
        # For higher dimensions, maintain the same logic
        # For query R=[adjusted_R_min, adjusted_R_max], we search for maximal pairs (rho, rho_hat)
        # where rho is contained in R and rho_hat contains R
        # 
        # Conditions:
        # 1. rho_min >= adjusted_R_min (rho starts at or after query start)
        # 2. rho_max <= adjusted_R_max (rho ends at or before query end)  
        # 3. rho_hat_min <= adjusted_R_min (rho_hat starts at or before query start)
        # 4. rho_hat_max >= adjusted_R_max (rho_hat ends at or after query end)
        #
        # For rtree intersection, we need to provide bounds in the format:
        # (min_x1, min_x2, ..., min_y1, min_y2, ..., min_z1, min_z2, ..., min_w1, min_w2, ..., 
        #  max_x1, max_x2, ..., max_y1, max_y2, ..., max_z1, max_z2, ..., max_w1, max_w2, ...)
        # where each point in the rtree is (rho_min, rho_hat_min, rho_max, rho_hat_max)
        
        min_corner = np.concatenate([
            adjusted_R_min,              # rho_min >= adjusted_R_min
            np.full(d_query, -INF),      # rho_hat_min <= adjusted_R_min (no lower bound)
            np.full(d_query, -INF),      # rho_max <= adjusted_R_max (no lower bound)
            adjusted_R_max               # rho_hat_max >= adjusted_R_max
        ])

        max_corner = np.concatenate([
            np.full(d_query, INF),       # rho_min >= adjusted_R_min (no upper bound)
            adjusted_R_min,              # rho_hat_min <= adjusted_R_min
            adjusted_R_max,              # rho_max <= adjusted_R_max
            np.full(d_query, INF)        # rho_hat_max >= adjusted_R_max (no upper bound)
        ])
            
        return np.concatenate([min_corner, max_corner]).tolist()


def compute_R_prime_range_with_bounds(
        R_min: np.ndarray, 
        R_max: np.ndarray,
        data_bounds: Tuple[np.ndarray, np.ndarray],
        d: int
) -> list:
    """
    Compute R_prime using pre-computed data bounds to avoid recalculating global bounds.
    
    param R_min: left-bottom corner of the query hyperrectangle
    param R_max: right-top corner of the query hyperrectangle
    param data_bounds: tuple of (data_min, data_max) from global bounding box
    param d: dimension of the data
    return: R' as a flat list of coordinates for rtree intersection
    """
    d_query = len(R_min) if R_min.ndim > 0 else 1  # dimension of the input space
    
    # Adjust query range to fit within data bounds
    adjusted_R_min, adjusted_R_max = adjust_query_range_to_data_bounds(R_min, R_max, data_bounds, d)
    
    # For 1D case
    if d_query == 1:
        coords = [
            float(adjusted_R_min[0]),    # min_x: rho_min >= adjusted_R_min
            float(-INF),                 # min_y: rho_hat_min <= adjusted_R_min
            float(-INF),                 # min_z: rho_max <= adjusted_R_max
            float(adjusted_R_max[0]),    # min_w: rho_hat_max >= adjusted_R_max
            float(INF),                  # max_x: no upper bound for rho_min
            float(adjusted_R_min[0]),    # max_y: rho_hat_min <= adjusted_R_min
            float(adjusted_R_max[0]),    # max_z: rho_max <= adjusted_R_max
            float(INF)                   # max_w: no upper bound for rho_hat_max
        ]
        return coords
   
    else:
        # For higher dimensions, maintain the same logic
        min_corner = np.concatenate([
            adjusted_R_min,              # rho_min >= adjusted_R_min
            np.full(d_query, -INF),      # rho_hat_min <= adjusted_R_min (no lower bound)
            np.full(d_query, -INF),      # rho_max <= adjusted_R_max (no lower bound)
            adjusted_R_max               # rho_hat_max >= adjusted_R_max
        ])

        max_corner = np.concatenate([
            np.full(d_query, INF),       # rho_min >= adjusted_R_min (no upper bound)
            adjusted_R_min,              # rho_hat_min <= adjusted_R_min
            adjusted_R_max,              # rho_max <= adjusted_R_max
            np.full(d_query, INF)        # rho_hat_max >= adjusted_R_max (no upper bound)
        ])
            
        return np.concatenate([min_corner, max_corner]).tolist()


def construct_T_input_range_per_dataset(
    synopses: List[Tuple[np.uint32, Histogram]], 
    epsilon: float,
    phi: float,
    d: int,
    use_sweep_line: bool = True,
    seed: int = 42
) -> List[Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """
    Builds range tree input for each dataset separately, returning a list of (Q, W, I) tuples for each dataset.
    
    param synopses: List of (histogram_id, histogram) tuples
    param epsilon: privacy parameter
    param phi: privacy parameter
    param d: dimension of the data
    param use_sweep_line: whether to use sweep line + R-tree method for maximal pairs
    param seed: random seed
    return: List of (Q, W, I) tuples for each dataset
    """
    import time
    
    all_datasets = get_all_datasets(synopses, d, epsilon, seed)
    
    # Compute global bounding box
    B_min, B_max = compute_global_bounding_box(all_datasets)
    print(f"Using global bounds: B_min={B_min}, B_max={B_max}")
    
    dataset_results = []
    
    # Process each dataset separately
    for dataset_idx, S_i in enumerate(all_datasets):
        dataset_start_time = time.time()
        print(f"Processing dataset {dataset_idx}...")
        
        # Use global bounding box
        projection_S_i = project_to_bounding_box(S_i, B_min, B_max)
        
        R_i = generate_combinatorial_rectangles(S_i, projection_S_i, d)
        rect_start_time = time.time()
        rect_time = time.time() - rect_start_time
        pair_start_time = time.time()
        
        # Choose maximal pairs generation method
        if use_sweep_line:
            maximal_pairs = generate_pair_for_range_predicate_sweep_line(R_i, d)
            print(f"  Dataset {dataset_idx}: Generated {len(maximal_pairs)} maximal pairs (sweep line method) in {time.time() - pair_start_time:.2f}s")
        else:
            # Generate candidate pairs using brute force, then filter using DAG
            candidate_pairs = generate_candidate_pairs_brute_force(R_i)
            maximal_pairs = generate_pair_for_range_predicate_brute_force(R_i)
            print(f"  Dataset {dataset_idx}: Generated {len(maximal_pairs)} maximal pairs (brute force + DAG method) in {time.time() - pair_start_time:.2f}s")
        
        weights = compute_weights_for_hyperrectangles(S_i, [rho for rho, rho_hat in maximal_pairs])
        
        # Construct Q, W, I for the current dataset
        Qi, Wi, Ii = [], [], []
        for idx, (rho, rho_hat) in enumerate(maximal_pairs):
            q = np.concatenate([
                rho['min_coords'], rho_hat['min_coords'], 
                rho['max_coords'], rho_hat['max_coords']
            ])
            Qi.append(q)
            Wi.append(weights[idx])
            Ii.append(dataset_idx)  # Dataset index
        
        if Qi:
            Q_dataset = np.array(Qi)
            W_dataset = np.array(Wi)
            I_dataset = np.array(Ii)
            dataset_results.append((Q_dataset, W_dataset, I_dataset))
            print(f"  Dataset {dataset_idx}: Q shape={Q_dataset.shape}, W shape={W_dataset.shape}")
        else:
            # If no maximal pairs for dataset, create empty arrays
            dataset_results.append((np.array([]), np.array([]), np.array([])))
            print(f"  Dataset {dataset_idx}: No maximal pairs")
        
        print(f"  Dataset {dataset_idx} total time: {time.time() - dataset_start_time:.2f}s")
    
    print(f"Processed {len(dataset_results)} total datasets")
    return dataset_results


