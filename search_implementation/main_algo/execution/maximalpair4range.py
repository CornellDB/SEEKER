"""
This file contains specific functions for finding maximal pairs for range predicate.
including: 
 - 1D interval tree
 - 2D sweep line
 - nD rtree
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import numpy as np
from numba import njit, prange
from typing import List, Tuple, Dict, Optional
from main_algo.data_processing.histograms import Histogram
from main_algo.execution.setups4threshold import weighted_random_sampling_from_histogram, generate_hyperrectangles_auto, compute_weights_for_hyperrectangles
from rtree import index
import numba


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

def generate_candidate_pairs_brute_force(R_i: List[Dict[str, np.ndarray]]) -> List[Tuple]:
    """
    Generate candidate pairs using brute force method.
    - R_i: list of rectangles
    """
    if not R_i:
        return []
    
    candidate_pairs = []
    
    # For each potential pair (rho, rho_hat)
    for i, rho in enumerate(R_i):
        for j, rho_hat in enumerate(R_i):
            if i == j:
                continue
                
            # Check if rho is a subset of rho_hat
            if is_subset(rho, rho_hat):
                candidate_pairs.append((i, j))
    
    print(f"Brute force found {len(candidate_pairs)} candidate pairs")
    
    return candidate_pairs

def generate_pair_for_range_predicate_brute_force(R_i: List[Dict[str, np.ndarray]]) -> List[Tuple]:
    """
    Generate maximal pairs using brute force method with direct maximality checking.
    - R_i: list of rectangles
    """
    if not R_i:
        return []
    
    maximal_pairs = []
    
    # For each potential pair (rho, rho_hat)
    for i, rho in enumerate(R_i):
        for j, rho_hat in enumerate(R_i):
            if i == j:
                continue
                
            # Check if rho is a subset of rho_hat
            if not is_subset(rho, rho_hat):
                continue
            
            # Check maximality directly
            is_maximal = True
            
            # Find all rectangles that are strict supersets of rho
            strict_supersets = []
            for k, rho_prime in enumerate(R_i):
                if k != i and k != j and is_strict_subset(rho, rho_prime):
                    strict_supersets.append(k)
            
            # Check if any of these strict supersets are strictly interior subsets of rho_hat
            for k in strict_supersets:
                if is_strictly_interior_subset(R_i[k], rho_hat):
                    is_maximal = False
                    break
            
            if is_maximal:
                maximal_pairs.append((rho, rho_hat))
    
    print(f"Brute force found {len(maximal_pairs)} maximal pairs")
    
    return maximal_pairs


def generate_pair_for_range_predicate_sweep_line(
    R_i: List[Dict[str, np.ndarray]], 
    d: int
) -> List[Tuple]:
    """
    Generate maximal pairs using optimized methods.
    - For 1D: sweep line method with Numba optimization
    - For 2D: sweep line with Numba optimization
    - For 3D: sweep line with Numba optimization (NEW!)
    - For d>=4: R-tree based method
    
    param R_i: list of rectangles
    param d: dimension of the data
    return: list of maximal pairs
    """
    if not R_i:
        return []
    
    # For 1D case, use sweep line method
    if d == 1:
        return generate_pair_for_range_predicate_1d_auto_optimized(R_i)
    
    # For 2D case, use sweep line with Numba optimization
    elif d == 2:
        return generate_pair_for_range_predicate_2d_auto_optimized(R_i)
    
    # For 3D case, use sweep line with Numba optimization
    elif d == 3:
        return generate_pair_for_range_predicate_3d_auto_optimized(R_i)
    
    # For higher dimensions (d>=4), use R-tree based method
    else:
        return generate_pair_for_range_predicate_nd_optimized(R_i, d)



# -----------------------------2D-----------------------------
def generate_pair_for_range_predicate_2d_auto_optimized(R_i: List[Dict[str, np.ndarray]]) -> List[Tuple]:
    """
    Optimized 2D sweep line implementation with fixes for Numba compatibility
    """
    if not R_i:
        return []
    
    # Convert input to numpy arrays for better performance
    n = len(R_i)
    min_coords = np.array([r['min_coords'] for r in R_i], dtype=np.float32)
    max_coords = np.array([r['max_coords'] for r in R_i], dtype=np.float32)
    
    # Generate events (x coordinate, event type, rectangle index)
    events = []
    for i in range(n):
        events.append((min_coords[i, 0], 0, i))  # 0 for left event
        events.append((max_coords[i, 0], 1, i))  # 1 for right event
    
    # Sort events by x coordinate
    events.sort()
    
    # Process events with optimized implementation
    candidate_pairs = _process_2d_events_fixed(events, min_coords, max_coords)
    
    print(f"Optimized 2D sweep line found {len(candidate_pairs)} candidate pairs")
    
    # Filter to get maximal pairs using optimized method
    maximal_pairs = _filter_maximal_pairs_2d(candidate_pairs, min_coords, max_coords)
    
    return maximal_pairs

@njit
def _process_2d_events_fixed(events, min_coords, max_coords):
    """
    Fixed version that avoids lambda capture issue
    """
    n = len(min_coords)
    active = []  # List of active rectangle indices
    active_y_mins = []  # Separate list for y_min values
    candidate_pairs = []
    
    for event in events:
        coord, event_type, rect_idx = event
        x_min, y_min = min_coords[rect_idx]
        x_max, y_max = max_coords[rect_idx]
        
        if event_type == 0:  # Left event (start of rectangle)
            # Check containment with all active rectangles
            for active_idx in active:
                a_x_min, a_y_min = min_coords[active_idx]
                a_x_max, a_y_max = max_coords[active_idx]
                
                # Check if active rectangle contains current rectangle
                if (a_x_min <= x_min and a_x_max >= x_max and
                    a_y_min <= y_min and a_y_max >= y_max):
                    candidate_pairs.append((rect_idx, active_idx))
                
                # Check if current rectangle contains active rectangle
                if (x_min <= a_x_min and x_max >= a_x_max and
                    y_min <= a_y_min and y_max >= a_y_max):
                    candidate_pairs.append((active_idx, rect_idx))
            
            # Add current rectangle to active list
            # Maintain active list sorted by y_min using insertion sort
            insert_pos = 0
            for i in range(len(active_y_mins)):
                if y_min >= active_y_mins[i]:
                    insert_pos = i + 1
                else:
                    break
            
            active.insert(insert_pos, rect_idx)
            active_y_mins.insert(insert_pos, y_min)
            
        else:  # Right event (end of rectangle)
            # Remove current rectangle from active list
            for i in range(len(active)):
                if active[i] == rect_idx:
                    active.pop(i)
                    active_y_mins.pop(i)
                    break
    
    return candidate_pairs


# 优化4: 并行化图形计算
@njit
def _compute_strict_superset_graph_2d(min_coords, max_coords):
    """
    Compute strict superset relationships between rectangles
    """
    n = len(min_coords)
    graph = np.zeros((n, n), dtype=np.bool_)
    
    for i in range(n):
        for j in range(n):
            if i != j:
                # Check if j is a strict superset of i
                cond1 = (min_coords[j, 0] <= min_coords[i, 0]) and (max_coords[j, 0] >= max_coords[i, 0])
                cond2 = (min_coords[j, 1] <= min_coords[i, 1]) and (max_coords[j, 1] >= max_coords[i, 1])
                cond3 = (min_coords[j, 0] < min_coords[i, 0]) or (max_coords[j, 0] > max_coords[i, 0]) or \
                        (min_coords[j, 1] < min_coords[i, 1]) or (max_coords[j, 1] > max_coords[i, 1])
                graph[i, j] = cond1 and cond2 and cond3
                
    return graph

@njit
def _compute_strict_interior_subset_graph_2d(min_coords, max_coords):
    """
    Compute strict interior subset relationships between rectangles
    """
    n = len(min_coords)
    graph = np.zeros((n, n), dtype=np.bool_)
    
    for i in range(n):
        for j in range(n):
            if i != j:
                # Check if i is a strict interior subset of j
                cond1 = (min_coords[i, 0] > min_coords[j, 0]) and (max_coords[i, 0] < max_coords[j, 0])
                cond2 = (min_coords[i, 1] > min_coords[j, 1]) and (max_coords[i, 1] < max_coords[j, 1])
                graph[i, j] = cond1 and cond2
                
    return graph

def _filter_maximal_pairs_truly_parallel_2d(candidate_pairs, strict_superset_graph, strict_interior_subset_graph):
    """
    2D truly parallel verification of maximal pair conditions - Correct version
    Uses Numba parallelization and optimized memory access.
    """
    if len(candidate_pairs) == 0:
        return []
    
    # Convert to numpy array
    candidate_pairs = np.array(candidate_pairs)
    
    # Use Numba for parallel optimization.
    @njit(parallel=True)
    def check_maximality_parallel_numba_2d(pairs, ss_graph, is_graph):
        maximal = np.ones(len(pairs), dtype=np.bool_)
        n = len(ss_graph)
        
        # Use Numba's parallel loop.
        for i in numba.prange(len(pairs)):
            a, b = pairs[i]  # a = rho_idx, b = rho_hat_idx
            
            # Find all strict supersets of rho (excluding itself).
            supersets = ss_graph[a]
            
            # Find all strict interior subsets of rho_hat.
            subsets = is_graph[:, b]
            
            # Check for intersection.
            conflict = False
            for j in range(n):
                # Exclude rho_hat (b) from supersets.
                if j == b:
                    continue
                if supersets[j] and subsets[j]:
                    conflict = True
                    break
                    
            maximal[i] = not conflict
        
        return maximal
    
    print("    Checking maximality (numba parallel)...")
    maximal_mask = check_maximality_parallel_numba_2d(candidate_pairs, strict_superset_graph, strict_interior_subset_graph)
    final_pairs = candidate_pairs[maximal_mask]
    
    return final_pairs

@njit
def _filter_maximal_serial_2d(candidate_pairs, ss_graph, is_graph):
    """
    Serial implementation for filtering maximal pairs
    """
    n = ss_graph.shape[0]
    maximal = np.ones(len(candidate_pairs), dtype=np.bool_)
    
    for idx in range(len(candidate_pairs)):
        a, b = candidate_pairs[idx]
        
        # Find all strict supersets of a
        supersets = ss_graph[a]
        
        # Find all strict interior subsets of b
        subsets = is_graph[:, b]
        
        # Check for conflicts (skip b without mutating the graph)
        conflict = False
        for j in range(n):
            if j == b:
                continue
            if supersets[j] and subsets[j]:
                conflict = True
                break
                
        maximal[idx] = not conflict
    
    return candidate_pairs[maximal]

def _filter_maximal_pairs_2d(candidate_pairs, min_coords, max_coords):
    """
    Optimized maximal pairs filtering for 2D case
    """
    if not candidate_pairs:
        return []
    
    # Convert to numpy array
    candidate_pairs = np.array(candidate_pairs)
    
    # Precompute containment relationships
    strict_superset_graph = _compute_strict_superset_graph_2d(min_coords, max_coords)
    strict_interior_subset_graph = _compute_strict_interior_subset_graph_2d(min_coords, max_coords)
    
    # Filter based on candidate count
    if len(candidate_pairs) >= 500000: 
        maximal_pairs = _filter_maximal_pairs_truly_parallel_2d(candidate_pairs, strict_superset_graph, strict_interior_subset_graph)
    else:  
        maximal_pairs = _filter_maximal_serial_2d(
            candidate_pairs, strict_superset_graph, strict_interior_subset_graph)
    
    # Convert back to original format
    result = [
        (
            {'min_coords': min_coords[a], 'max_coords': max_coords[a]},
            {'min_coords': min_coords[b], 'max_coords': max_coords[b]}
        )
        for a, b in maximal_pairs
    ]
    
    print(f"Filtered to {len(result)} maximal pairs")
    return result

# -----------------------------3D-----------------------------
def generate_pair_for_range_predicate_3d_auto_optimized(R_i: List[Dict[str, np.ndarray]]) -> List[Tuple]:
    """
    Optimized 3D sweep line implementation with Numba JIT compilation
    
    Similar to 2D version but extended to 3 dimensions.
    Uses x-axis as primary sweep dimension, checks full 3D containment.
    """
    if not R_i:
        return []
    
    # Convert input to numpy arrays for better performance
    n = len(R_i)
    min_coords = np.array([r['min_coords'] for r in R_i], dtype=np.float32)
    max_coords = np.array([r['max_coords'] for r in R_i], dtype=np.float32)
    
    # Generate events (x coordinate, event type, rectangle index)
    events = []
    for i in range(n):
        events.append((min_coords[i, 0], 0, i))  # 0 for left event
        events.append((max_coords[i, 0], 1, i))  # 1 for right event
    
    # Sort events by x coordinate
    events.sort()
    
    # Process events with Numba-optimized implementation
    candidate_pairs = _process_3d_events_numba(events, min_coords, max_coords)
    
    print(f"Optimized 3D sweep line found {len(candidate_pairs)} candidate pairs")
    
    # Filter to get maximal pairs using optimized method
    maximal_pairs = _filter_maximal_pairs_3d(candidate_pairs, min_coords, max_coords)
    
    return maximal_pairs


@njit
def _process_3d_events_numba(events, min_coords, max_coords):
    """
    3D sweep line core with Numba JIT compilation
    
    Extends 2D logic to 3 dimensions:
    - Sweep along x-axis
    - Check full 3D containment (x, y, z)
    - Maintain active rectangles list
    """
    active = []  # List of active rectangle indices
    candidate_pairs = []
    
    for event in events:
        coord, event_type, rect_idx = event
        x_min, y_min, z_min = min_coords[rect_idx]
        x_max, y_max, z_max = max_coords[rect_idx]
        
        if event_type == 0:  # Left event (start of rectangle)
            # Check containment with all active rectangles
            for active_idx in active:
                a_x_min, a_y_min, a_z_min = min_coords[active_idx]
                a_x_max, a_y_max, a_z_max = max_coords[active_idx]
                
                # Check if active rectangle contains current rectangle (all 3 dimensions)
                if (a_x_min <= x_min and a_x_max >= x_max and
                    a_y_min <= y_min and a_y_max >= y_max and
                    a_z_min <= z_min and a_z_max >= z_max):
                    candidate_pairs.append((rect_idx, active_idx))
                
                # Check if current rectangle contains active rectangle (all 3 dimensions)
                if (x_min <= a_x_min and x_max >= a_x_max and
                    y_min <= a_y_min and y_max >= a_y_max and
                    z_min <= a_z_min and z_max >= a_z_max):
                    candidate_pairs.append((active_idx, rect_idx))
            
            # Add current rectangle to active list
            active.append(rect_idx)
            
        else:  # Right event (end of rectangle)
            # Remove current rectangle from active list
            for i in range(len(active)):
                if active[i] == rect_idx:
                    active.pop(i)
                    break
    
    return candidate_pairs


@njit
def _compute_strict_superset_graph_3d(min_coords, max_coords):
    """
    Compute strict superset relationships between 3D rectangles
    
    rect_j is a strict superset of rect_i if:
    - rect_j contains rect_i in all 3 dimensions
    - rect_j is strictly larger in at least one dimension
    """
    n = len(min_coords)
    graph = np.zeros((n, n), dtype=np.bool_)
    
    for i in range(n):
        for j in range(n):
            if i != j:
                # Check if j contains i in all dimensions
                cond1 = (min_coords[j, 0] <= min_coords[i, 0]) and (max_coords[j, 0] >= max_coords[i, 0])
                cond2 = (min_coords[j, 1] <= min_coords[i, 1]) and (max_coords[j, 1] >= max_coords[i, 1])
                cond3 = (min_coords[j, 2] <= min_coords[i, 2]) and (max_coords[j, 2] >= max_coords[i, 2])
                
                # Check if j is strictly larger in at least one dimension
                cond4 = (min_coords[j, 0] < min_coords[i, 0]) or (max_coords[j, 0] > max_coords[i, 0]) or \
                        (min_coords[j, 1] < min_coords[i, 1]) or (max_coords[j, 1] > max_coords[i, 1]) or \
                        (min_coords[j, 2] < min_coords[i, 2]) or (max_coords[j, 2] > max_coords[i, 2])
                
                graph[i, j] = cond1 and cond2 and cond3 and cond4
                
    return graph


@njit
def _compute_strict_interior_subset_graph_3d(min_coords, max_coords):
    """
    Compute strict interior subset relationships between 3D rectangles
    
    rect_i is a strict interior subset of rect_j if:
    - rect_i is strictly inside rect_j in ALL 3 dimensions
    - rect_i doesn't touch any boundary of rect_j
    """
    n = len(min_coords)
    graph = np.zeros((n, n), dtype=np.bool_)
    
    for i in range(n):
        for j in range(n):
            if i != j:
                # Check if i is strictly inside j in all dimensions
                cond1 = (min_coords[i, 0] > min_coords[j, 0]) and (max_coords[i, 0] < max_coords[j, 0])
                cond2 = (min_coords[i, 1] > min_coords[j, 1]) and (max_coords[i, 1] < max_coords[j, 1])
                cond3 = (min_coords[i, 2] > min_coords[j, 2]) and (max_coords[i, 2] < max_coords[j, 2])
                
                graph[i, j] = cond1 and cond2 and cond3
                
    return graph


def _filter_maximal_pairs_3d(candidate_pairs, min_coords, max_coords):
    """
    Filter candidate pairs to get only maximal pairs for 3D rectangles
    
    Uses precomputed containment graphs for efficient filtering.
    Similar to 2D filtering but for 3D rectangles.
    """
    if len(candidate_pairs) == 0:
        return []
    
    # Convert to numpy array
    candidate_pairs = np.array(candidate_pairs)
    
    # Precompute 3D containment relationship graphs
    ss_graph = _compute_strict_superset_graph_3d(min_coords, max_coords)
    is_graph = _compute_strict_interior_subset_graph_3d(min_coords, max_coords)
    
    # Use optimized filtering
    maximal_pairs = _filter_maximal_serial_3d(candidate_pairs, ss_graph, is_graph)
    
    # Convert back to original format
    result = [
        (
            {'min_coords': min_coords[a], 'max_coords': max_coords[a]},
            {'min_coords': min_coords[b], 'max_coords': max_coords[b]}
        )
        for a, b in maximal_pairs
    ]
    
    print(f"Filtered to {len(result)} maximal pairs")
    return result


@njit
def _filter_maximal_serial_3d(candidate_pairs, ss_graph, is_graph):
    """
    Serial filtering of maximal pairs for 3D
    
    For each candidate pair (rho, rho_hat):
    - Check if there exists rho' where rho ⊂ rho' ⊂⊂ rho_hat
    - If not, it's a maximal pair
    """
    n = ss_graph.shape[0]
    maximal = np.ones(len(candidate_pairs), dtype=np.bool_)
    
    for idx in range(len(candidate_pairs)):
        a, b = candidate_pairs[idx]  # a = rho_idx, b = rho_hat_idx
        
        # Get strict supersets of rho (a)
        supersets = ss_graph[a]
        
        # Get strict interior subsets of rho_hat (b)
        subsets = is_graph[:, b]
        
        # Check for conflict (skip b without mutating)
        conflict = False
        for k in range(n):
            if k == b:
                continue
            if supersets[k] and subsets[k]:
                conflict = True
                break
        
        maximal[idx] = not conflict
    
    return candidate_pairs[maximal]


# -----------------------------1D-----------------------------

def filter_maximal_pairs(
    candidate_pairs: List[Tuple], 
    R_i: List[Dict[str, np.ndarray]]
) -> List[Tuple]:
    """
    Filter candidate pairs to get only maximal pairs.
    A pair (rho, rho_hat) is maximal if there's no rectangle rho_prime
    such that rho ⊂ rho_prime ⊂ rho_hat.
    
    Current strategy: Use DAG method for all dimensions.
    """
    """ Low-dimensional optimization: O(m) DAG-based method, uses pre-built containment graphs for faster filtering. """
    from collections import defaultdict
    
    # Pre-build containment graphs.
    n = len(R_i)
    strict_superset_graph = defaultdict(set)  # rho_idx -> {indices of all strict supersets}
    strict_interior_subset_graph = defaultdict(set)  # rho_idx -> {indices of all strict interior subsets}
    
    # Build strict superset and strict interior subset graphs.
    for i in range(n):
        for j in range(n):
            if i != j:
                # Check if i is a strict superset of j.
                if is_strict_subset(R_i[j], R_i[i]):
                    strict_superset_graph[j].add(i)
                # Check if i is a strict interior subset of j.
                if is_strictly_interior_subset(R_i[i], R_i[j]):
                    strict_interior_subset_graph[j].add(i)
    
    # print(f"DAG: Built strict superset graph with {len(strict_superset_graph)} entries")
    
    # Check if each candidate pair is maximal - accelerated using graph structure.
    maximal_pairs = []
    filtered_count = 0
    
    for rho_idx, rho_hat_idx in candidate_pairs:
        is_maximal = True
        
        # Find all strict supersets of rho.
        strict_supersets = strict_superset_graph[rho_idx]
        
        # Check if there exists rho_prime that is a strict interior subset of rho_hat.
        # Use set intersection operation, O(min(len(strict_supersets), len(strict_interior_subset_graph[rho_hat_idx]))).
        interior_subsets = strict_interior_subset_graph[rho_hat_idx]
        if rho_hat_idx in strict_supersets:
            strict_supersets = strict_supersets - {rho_hat_idx}  # Exclude itself.
        
        # Check if the intersection is empty.
        if strict_supersets & interior_subsets:
            is_maximal = False
            filtered_count += 1
        
        if is_maximal:
            maximal_pairs.append((R_i[rho_idx], R_i[rho_hat_idx]))
    
    # print(f"DAG: Filtered out {filtered_count} non-maximal pairs, kept {len(maximal_pairs)} maximal pairs")
    
    return maximal_pairs



def _compute_containment_relationships_1d(R_i):
    """
    Shared function to compute containment relationships for 1D rectangles.
    This avoids duplicate computation between different filtering methods.
    """
    R_min = np.array([r['min_coords'][0] for r in R_i], dtype=np.float32)
    R_max = np.array([r['max_coords'][0] for r in R_i], dtype=np.float32)
    n = len(R_i)
    
    @njit
    def compute_relationships(R_min, R_max):
        n = len(R_min)
        ss_graph = np.zeros((n, n), dtype=np.bool_)
        is_graph = np.zeros((n, n), dtype=np.bool_)
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    # Vectorized condition checking
                    cond1 = (R_min[i] <= R_min[j]) & (R_max[i] >= R_max[j])
                    cond2 = (R_min[i] < R_min[j]) | (R_max[i] > R_max[j])
                    ss_graph[j, i] = cond1 & cond2
                    
                    # is_graph[i, j] = True if rectangle i is a strict interior subset of rectangle j
                    is_graph[i, j] = (R_min[i] > R_min[j]) & (R_max[i] < R_max[j])
        return ss_graph, is_graph
    
    return compute_relationships(R_min, R_max)





def ultra_fast_maximal_pairs_filter(candidate_pairs, R_i):
    """
    Ultra-fast filtering method: only filters, does not regenerate candidate pairs.
    This is a truly optimized version that avoids repeated sweep line computations.
    """
    if len(candidate_pairs) == 0:
        return []
    
    # Convert to numpy array for performance.
    candidate_pairs = np.array(candidate_pairs)
    
    # Use shared containment relationship computation function.
    print("  Computing containment relationships...")
    strict_superset_graph, strict_interior_subset_graph = _compute_containment_relationships_1d(R_i)
    
    # Check maximality for each candidate pair (optimized version).
    @njit
    def check_maximality_optimized(pairs, ss_graph, is_graph):
        maximal = np.ones(len(pairs), dtype=np.bool_)
        n = len(ss_graph)
        
        for i in range(len(pairs)):
            a, b = pairs[i]  # a = rho_idx, b = rho_hat_idx
            
            # Find all strict supersets of rho (excluding itself).
            supersets = ss_graph[a]
            
            # Find all strict interior subsets of rho_hat.
            subsets = is_graph[:, b]
            
            # Optimization: directly check intersection, avoid array copying.
            conflict = False
            for j in range(n):
                # Exclude rho_hat (b) from supersets.
                if j == b:
                    continue
                if supersets[j] and subsets[j]:
                    conflict = True
                    break
                    
            maximal[i] = not conflict
        
        return maximal
    
    print("  Checking maximality (optimized)...")
    maximal_mask = check_maximality_optimized(candidate_pairs, strict_superset_graph, strict_interior_subset_graph)
    final_pairs = candidate_pairs[maximal_mask]
    
    # Convert back to original format for output.
    result = [(R_i[int(a)], R_i[int(b)]) for a, b in final_pairs]
    print(f"  Ultra-fast filter found {len(result)} maximal pairs")
    
    return result


def _optimized_sweep_line_1d(R_i):
    """
    Optimized 1D sweep line implementation, accelerated with Numba.
    """
    # Convert to numpy arrays.
    R_min = np.array([r['min_coords'][0] for r in R_i], dtype=np.float32)
    R_max = np.array([r['max_coords'][0] for r in R_i], dtype=np.float32)
    n = len(R_i)
    
    # Create event array.
    events = []
    for i in range(n):
        events.append((R_min[i], 0, i))  # 0 for left event
        events.append((R_max[i], 1, i))  # 1 for right event
    
    # Sort events.
    events.sort()
    
    @njit
    def sweep_line_events(R_min, R_max, events):
        n = len(R_min)
        candidate_pairs = []
        active = np.zeros(n, dtype=np.bool_)
        
        for coord, event_type, rect_idx in events:
            if event_type == 0:  # left event
                # Check containment with all active rectangles.
                for j in range(n):
                    if active[j] and j != rect_idx:
                        # Check if rect_idx is contained by j.
                        if R_min[j] <= R_min[rect_idx] and R_max[j] >= R_max[rect_idx]:
                            candidate_pairs.append((rect_idx, j))
                        # Check if j is contained by rect_idx.
                        elif R_min[rect_idx] <= R_min[j] and R_max[rect_idx] >= R_max[j]:
                            candidate_pairs.append((j, rect_idx))
                
                # Add current rectangle to active list.
                active[rect_idx] = True
            else:  # right event
                # Remove from active list.
                active[rect_idx] = False
        
        return candidate_pairs
    
    return sweep_line_events(R_min, R_max, events)


def _filter_maximal_pairs_truly_parallel(candidate_pairs, strict_superset_graph, strict_interior_subset_graph):
    """
    Truly parallel verification of maximal pair conditions - Correct version.
    Uses Numba parallelization and optimized memory access.
    """
    if len(candidate_pairs) == 0:
        return []
    
    # Convert to numpy array.
    candidate_pairs = np.array(candidate_pairs, dtype=np.int32)
    
    # Use Numba for parallel optimization.
    @njit(parallel=True)
    def check_maximality_parallel_numba(pairs, ss_graph, is_graph):
        maximal = np.ones(len(pairs), dtype=np.bool_)
        n = len(ss_graph)
        
        # Use Numba's parallel loop.
        for i in numba.prange(len(pairs)):
            a, b = pairs[i]  # a = rho_idx, b = rho_hat_idx
            
            # Find all strict supersets of rho (excluding itself).
            supersets = ss_graph[a]
            
            # Find all strict interior subsets of rho_hat.
            subsets = is_graph[:, b]
            
            # Check for intersection.
            conflict = False
            for j in range(n):
                # Exclude rho_hat (b) from supersets.
                if j == b:
                    continue
                if supersets[j] and subsets[j]:
                    conflict = True
                    break
                    
            maximal[i] = not conflict
        
        return maximal
    
    print("    Checking maximality (numba parallel)...")
    maximal_mask = check_maximality_parallel_numba(candidate_pairs, strict_superset_graph, strict_interior_subset_graph)
    final_pairs = candidate_pairs[maximal_mask]
    
    return final_pairs

def generate_pair_for_range_predicate_1d_auto_optimized(R_i):
    """
    1D auto-optimized method: automatically selects the optimal algorithm based on the number of candidate pairs.
    Based on empirical data:
    - Candidate pairs < 400,000: Use ultra-fast optimized.
    - Candidate pairs >= 400,000: Use parallel correct.
    """
    if not R_i:
        return []
    
    print("  Using auto-optimized method selection...")
    candidate_pairs = _optimized_sweep_line_1d(R_i)
    candidate_count = len(candidate_pairs)
    print(f"1D sweep line found {candidate_count:,} candidate pairs")
    
    # Automatically select the optimal method based on the number of candidate pairs.
    if candidate_count >= 400000:
        print(f"  Auto-selecting: Parallel method (candidate pairs: {candidate_count:,} >= 400,000)")
        strict_superset_graph, strict_interior_subset_graph = _compute_containment_relationships_1d(R_i)
        maximal_pairs = _filter_maximal_pairs_truly_parallel(candidate_pairs, strict_superset_graph, strict_interior_subset_graph)
        # Convert to original format.
        result = [(R_i[int(a)], R_i[int(b)]) for a, b in maximal_pairs]
        print(f"  Parallel filter found {len(result):,} maximal pairs")
        return result
    else:
        print(f"  Auto-selecting: Ultra-fast optimized method (candidate pairs: {candidate_count:,} < 400,000)")
        # Convert to numpy array.
        candidate_pairs = np.array(candidate_pairs)
        return ultra_fast_maximal_pairs_filter(candidate_pairs, R_i)
       






















# def generate_pair_for_range_predicate_1d_sweep_line(R_i):
#     """
#     1D sweep line method for maximal pairs using sorted containers.
#     This method is more efficient than brute force for 1D cases.
#     """
#     if not R_i:
#         return []
    
#     # Create events (position, type, index)
#     events = []
#     for i, rect in enumerate(R_i):
#         start, end = rect['min_coords'][0], rect['max_coords'][0]
#         events.append((start, 'left', i))
#         events.append((end, 'right', i))
    
#     # Sort events by coordinate
#     events.sort()
    
#     # Use a sorted list to track active rectangles
#     # Each entry: (rect_idx, start, end)
#     active = []
#     candidate_pairs = []
    
#     for coord, event_type, rect_idx in events:
#         rect = R_i[rect_idx]
#         start, end = rect['min_coords'][0], rect['max_coords'][0]
        
#         if event_type == 'left':
#             # Check both directions: current rectangle contained by active rectangles
#             # AND current rectangle contains active rectangles
#             for active_rect_idx, active_start, active_end in active:
#                 # Check if active rectangle contains current rectangle
#                 if (active_start <= start and active_end >= end):
#                     # Format: (contained_idx, container_idx) - same as brute force
#                     candidate_pairs.append((rect_idx, active_rect_idx))
                
#                 # Check if current rectangle contains active rectangle
#                 if (start <= active_start and end >= active_end):
#                     # Format: (contained_idx, container_idx) - same as brute force
#                     candidate_pairs.append((active_rect_idx, rect_idx))
            
#             # Add current rectangle to active list
#             active.append((rect_idx, start, end))
            
#         else:  # right event
#             # Remove current rectangle from active list
#             active = [(idx, s, e) for idx, s, e in active if idx != rect_idx]
    
#     print(f"1D sweep line found {len(candidate_pairs)} candidate pairs")
#     return filter_maximal_pairs(candidate_pairs, R_i)

# def filter_maximal_pairs_optimized(candidate_pairs, R_i):
#     """
#     Optimized 1D maximal pair filtering using numpy and numba.
#     Correctly implements the same logic as the original filter_maximal_pairs.
#     """
#     if len(candidate_pairs) == 0:
#         return []
    
#     # Convert to numpy arrays for faster processing
#     candidate_pairs = np.array(candidate_pairs)
    
#     # Use shared containment relationship computation
#     strict_superset_graph, strict_interior_subset_graph = _compute_containment_relationships_1d(R_i)
    
#     # Check each candidate pair for maximality with optimized logic
#     @njit
#     def check_maximality(pairs, ss_graph, is_graph):
#         maximal = np.ones(len(pairs), dtype=np.bool_)
#         n = len(ss_graph)
        
#         for i in range(len(pairs)):
#             a, b = pairs[i]  # a = rho_idx, b = rho_hat_idx
            
#             # Use precomputed relationship graphs for direct access
#             # Get all strict supersets of rho (a)
#             supersets = ss_graph[a]
            
#             # Get all strict interior subsets of rho_hat (b)
#             # is_graph[:, b] gives all rectangles that are strict interior subsets of rectangle b
#             subsets = is_graph[:, b]
            
#             # Exclude rho_hat (b) from supersets if it's there
#             if b < n and supersets[b]:
#                 # Create a copy and set b to False
#                 supersets_copy = np.copy(supersets)
#                 supersets_copy[b] = False
#                 supersets = supersets_copy
            
#             # Quick intersection check
#             conflict = False
#             for j in range(n):
#                 if supersets[j] and subsets[j]:
#                     conflict = True
#                     break
                    
#             maximal[i] = not conflict
        
#         return maximal
    
#     maximal_mask = check_maximality(candidate_pairs, strict_superset_graph, strict_interior_subset_graph)
#     final_pairs = candidate_pairs[maximal_mask]
    
#     return [(R_i[int(a)], R_i[int(b)]) for a, b in final_pairs]


# def generate_pair_for_range_predicate_2d_sweep(
#     R_i: List[Dict[str, np.ndarray]]
# ) -> List[Tuple]:
#     """
#     Pure sweep line method for 2D case.
#     Uses x-axis as sweep line and maintains active rectangles sorted by y-coordinates.
#     Returns only maximal pairs.
#     """
#     if not R_i:
#         return []
    
#     # Create events based on the x dimension
#     events = []
#     for i, rect in enumerate(R_i):
#         x_min = rect['min_coords'][0]
#         x_max = rect['max_coords'][0]
#         events.append((x_min, 'left', i))
#         events.append((x_max, 'right', i))
    
#     # Sort events by coordinate
#     events.sort()
    
#     # Use a sorted list to track active rectangles by y-coordinates
#     # Each entry: (rect_idx, y_min, y_max, x_min, x_max)
#     active = []
#     candidate_pairs = []
    
#     for coord, event_type, rect_idx in events:
#         rect = R_i[rect_idx]
#         x_min, x_max = rect['min_coords'][0], rect['max_coords'][0]
#         y_min, y_max = rect['min_coords'][1], rect['max_coords'][1]
        
#         if event_type == 'left':
#             # Check both directions: current rectangle contained by active rectangles
#             # AND current rectangle contains active rectangles
#             for active_rect_idx, active_y_min, active_y_max, active_x_min, active_x_max in active:
#                 # Check if active rectangle contains current rectangle
#                 if (active_x_min <= x_min and 
#                     active_x_max >= x_max and
#                     active_y_min <= y_min and 
#                     active_y_max >= y_max):
#                     # Format: (contained_idx, container_idx) - same as brute force
#                     candidate_pairs.append((rect_idx, active_rect_idx))
#                     # print(f"  Found candidate pair: rect {active_rect_idx} [{active_x_min:.3f},{active_y_min:.3f}]x[{active_x_max:.3f},{active_y_max:.3f}] contains rect {rect_idx} [{x_min:.3f},{y_min:.3f}]x[{x_max:.3f},{y_max:.3f}]")
                
#                 # Check if current rectangle contains active rectangle
#                 if (x_min <= active_x_min and 
#                     x_max >= active_x_max and
#                     y_min <= active_y_min and 
#                     y_max >= active_y_max):
#                     # Format: (contained_idx, container_idx) - same as brute force
#                     candidate_pairs.append((active_rect_idx, rect_idx))
#                     # print(f"  Found candidate pair: rect {rect_idx} [{x_min:.3f},{y_min:.3f}]x[{x_max:.3f},{y_max:.3f}] contains rect {active_rect_idx} [{active_x_min:.3f},{active_y_min:.3f}]x[{active_x_max:.3f},{active_y_max:.3f}]")
            
#             # Add current rectangle to active list, maintaining sorted order by y_min
#             active.append((rect_idx, y_min, y_max, x_min, x_max))
#             active.sort(key=lambda x: x[1])  # Sort by y_min
            
#         else:  # right event
#             # Remove current rectangle from active list
#             active = [(idx, y_min, y_max, x_min, x_max) 
#                      for idx, y_min, y_max, x_min, x_max in active if idx != rect_idx]
    
#     print(f"Sweep line found {len(candidate_pairs)} candidate pairs")
    
#     # Filter to get maximal pairs - pass index pairs directly
#     maximal_pairs = filter_maximal_pairs(candidate_pairs, R_i)
    
#     return maximal_pairs

def generate_pair_for_range_predicate_nd_optimized(R_i: List[Dict[str, np.ndarray]], d: int, use_hierarchical: bool = False) -> List[Tuple]:
    """
    Optimized nD sweep line method using hierarchical approach and dimension reduction.
    For d>=3, this method is more efficient than the basic R-tree approach.
    
    param use_hierarchical: If True, use hierarchical sweep line for remaining dimensions
                           If False, use R-tree for remaining dimensions
    """
    
    # For d>=3, use hierarchical sweep line approach
    # Strategy: Use sweep line in the dimension with most variation
    # Find the dimension with maximum spread
    spreads = []
    for dim in range(d):
        min_coords = [rect['min_coords'][dim] for rect in R_i]
        max_coords = [rect['max_coords'][dim] for rect in R_i]
        spread = max(max_coords) - min(min_coords)
        spreads.append(spread)
    
    # Use the dimension with maximum spread as primary sweep dimension
    primary_dim = np.argmax(spreads)
    secondary_dims = [i for i in range(d) if i != primary_dim]
    
    print(f"Using dimension {primary_dim} as primary sweep dimension (spread: {spreads[primary_dim]:.3f})")
    
    # Create events based on the primary dimension
    events = []
    for i, rect in enumerate(R_i):
        min_coord = rect['min_coords'][primary_dim]
        max_coord = rect['max_coords'][primary_dim]
        events.append((min_coord, 'left', i))
        events.append((max_coord, 'right', i))
    
    # Sort events by coordinate
    events.sort()
    
    # Choose method based on parameter
    if use_hierarchical:
        # Use hierarchical sweep line for remaining dimensions
        return _sweep_line_with_hierarchical_approach(R_i, events, primary_dim, d)
    else:
        # Use optimized R-tree with dynamic parameters
        return _sweep_line_with_optimized_rtree(R_i, events, primary_dim, d)


def _sweep_line_with_optimized_rtree(
    R_i: List[Dict[str, np.ndarray]], 
    events: List[Tuple], 
    primary_dim: int, 
    d: int
) -> List[Tuple]:
    """
    动态调整R-tree参数的高维包含检测（d >= 4）
    时间复杂度：O(n log n) ~ O(n²)（取决于数据分布）
    """
    from rtree import index
    
    secondary_dims = [i for i in range(d) if i != primary_dim]
    print(f"R-tree method: d={d}, primary_dim={primary_dim}, secondary_dims={secondary_dims}")
    
    # 动态调整R-tree参数
    p = index.Property()
    p.dimension = len(secondary_dims)
    
    # 根据维度动态调整参数
    if len(secondary_dims) >= 5:
        # 超高维度优化
        p.fill_factor = 0.3  # 进一步减少节点重叠
        p.index_capacity = max(15, len(secondary_dims) * 3)
        p.leaf_capacity = max(15, len(secondary_dims) * 3)
        p.near_minimum_overlap_factor = 5  # 修复参数
        print(f"  Ultra-high-dim R-tree: fill_factor={p.fill_factor}, index_capacity={p.index_capacity}")
    elif len(secondary_dims) >= 4:
        # 高维度优化
        p.fill_factor = 0.4  # 减少节点重叠
        p.index_capacity = max(10, len(secondary_dims) * 2)
        p.leaf_capacity = max(10, len(secondary_dims) * 2)
        p.near_minimum_overlap_factor = 5  # 修复参数
        print(f"  High-dim R-tree: fill_factor={p.fill_factor}, index_capacity={p.index_capacity}")
    else:
        # 中等维度使用默认参数
        p.fill_factor = 0.7
        p.index_capacity = 10
        p.leaf_capacity = 10
        p.near_minimum_overlap_factor = 5  # 修复参数
        print(f"  Standard R-tree: fill_factor={p.fill_factor}, index_capacity={p.index_capacity}")
    
    # 初始化R-tree
    rtree = index.Index(properties=p)
    bbox_dict = {}  # 存储bbox用于删除
    candidate_pairs = set()
    
    print(f"Processing {len(events)} events...")
    
    for coord, event_type, rect_idx in events:
        rect = R_i[rect_idx]
        remaining_min = [rect['min_coords'][dim] for dim in secondary_dims]
        remaining_max = [rect['max_coords'][dim] for dim in secondary_dims]
        bbox = tuple(remaining_min + remaining_max)
        
        if event_type == 'left':
            # 查询R-tree找包含当前矩形的容器
            intersections = list(rtree.intersection(bbox))
            
            for c_idx in intersections:
                if c_idx != rect_idx:
                    # 检查当前矩形是否被容器矩形包含
                    if is_subset(rect, R_i[c_idx]):
                        candidate_pairs.add((rect_idx, c_idx))
                     
                    # 检查容器矩形是否被当前矩形包含
                    elif is_subset(R_i[c_idx], rect):
                        candidate_pairs.add((c_idx, rect_idx))
                      
            
            # 插入当前矩形
            rtree.insert(rect_idx, bbox)
            bbox_dict[rect_idx] = bbox
            
        else:  # right event
            # 安全删除（需精确匹配插入时的bbox）
            if rect_idx in bbox_dict:
                rtree.delete(rect_idx, bbox_dict[rect_idx])
                del bbox_dict[rect_idx]
    
    print(f"R-tree method found {len(candidate_pairs)} candidate pairs")
    return filter_maximal_pairs(list(candidate_pairs), R_i)


def _sweep_line_with_hierarchical_approach(
    R_i: List[Dict[str, np.ndarray]], 
    events: List[Tuple], 
    primary_dim: int, 
    d: int
) -> List[Tuple]:
    """
    Hierarchical sweep line method: Uses sweep line in the primary dimension, and also for remaining dimensions.
    Time complexity: O(n log n) for each dimension.
    """
    secondary_dims = [i for i in range(d) if i != primary_dim]
    print(f"Hierarchical sweep: d={d}, primary_dim={primary_dim}, secondary_dims={secondary_dims}")
    
    candidate_pairs = set()
    
    # Create sweep line events for each remaining dimension.
    for sec_dim in secondary_dims:
        print(f"  Processing secondary dimension {sec_dim}")
        
        # Create events for the current secondary dimension.
        sec_events = []
        for i, rect in enumerate(R_i):
            min_coord = rect['min_coords'][sec_dim]
            max_coord = rect['max_coords'][sec_dim]
            sec_events.append((min_coord, 'left', i))
            sec_events.append((max_coord, 'right', i))
        
        sec_events.sort()
        
        # Use sweep line on the secondary dimension.
        active_rectangles = []
        
        for coord, event_type, rect_idx in sec_events:
            rect = R_i[rect_idx]
            
            if event_type == 'left':
                # Check containment with active rectangles.
                for active_rect_idx in active_rectangles:
                    active_rect = R_i[active_rect_idx]
                    
                    # Check full containment (all dimensions).
                    if is_subset(rect, active_rect):
                        candidate_pairs.add((rect_idx, active_rect_idx))
                    elif is_subset(active_rect, rect):
                        candidate_pairs.add((active_rect_idx, rect_idx))
                
                # Add to active rectangles.
                active_rectangles.append(rect_idx)
                
            else:  # right event
                # Remove from active rectangles.
                active_rectangles = [idx for idx in active_rectangles if idx != rect_idx]
    
    print(f"Hierarchical sweep found {len(candidate_pairs)} candidate pairs")
    return filter_maximal_pairs(list(candidate_pairs), R_i)




