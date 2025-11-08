'''
This file contains the necessary setups for Ptile problem, especially for threshold predicate.
Note that from the paper, every dataset should have the same dimension, thus is applicable to the range tree.
'''
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import numpy as np
import pandas as pd
import zstandard as zstd
from typing import List, Tuple, Dict
import itertools
from concurrent.futures import ProcessPoolExecutor, as_completed
# from loguru import logger

from main_algo.data_processing.histograms import Histogram


INF=1e20 # simulate the infinite value

# this function is used to compute coresets for each synopsis
# ε is [0,1]
def weighted_random_sampling_from_histogram(histogram, n_samples, seed=42):
    """
    weighted random sampling from histogram, return the samples(i.e. the coreset)
    histogram format: (counts, bins) where counts is array of counts and bins is array of bin edges
    """
    
    counts, bins = histogram[0], histogram[1]

    total_count = counts.sum()
    if total_count == 0:
        # If histogram is empty, use uniform weights
        weights = np.ones(len(counts)) / len(counts)
    else:
        # normalize the weights
        weights = counts / total_count 
    
    # Ensure n_samples is an integer
    n_samples = int(round(n_samples))
    if n_samples <= 0:
        n_samples = 1  # Sample at least 1 point
    
    # Select the bins according to the weights
    rng = np.random.default_rng(seed)
    selected_bin_indices = rng.choice(len(counts), size=n_samples, p=weights, replace=True)
    
    # Uniform sampling in the selected bins
    samples = []
    for idx in selected_bin_indices:
        start, end = bins[idx], bins[idx + 1]
        sample = rng.uniform(start, end) 
        samples.append(sample)
    return np.array(samples)

def _rect_chunk_worker(min_chunk, dim_candidates):
    rectangles = []
    max_coords_all = list(itertools.product(*dim_candidates))
    for min_coords in min_chunk:
        for max_coords in max_coords_all:
            if all(mi <= ma for mi, ma in zip(min_coords, max_coords)):
                rectangles.append({
                    'min_coords': np.array(min_coords),
                    'max_coords': np.array(max_coords),
                })
    return rectangles


# this function is used to precompute all possible combinatorially different query rectangles
def generate_hyperrectangles_auto(each_coreset: np.ndarray, d: int, n_jobs=1, parallel_threshold=10000):
    """
    Automatically choose serial or parallel method to generate all combinatorially different hyperrectangles.
    - each_coreset: n x d data
    - d: dimension
    - n_jobs: number of parallel processes
    - parallel_threshold: automatically parallelize when number of min_coords combinations exceeds this threshold
    """
    if d == 1:
        unique_values = np.unique(each_coreset)
        rectangles = []
        for i, min_val in enumerate(unique_values):
            for max_val in unique_values[i:]:
                rectangles.append({
                    'min_coords': np.array([min_val]),
                    'max_coords': np.array([max_val]),
                })
        return rectangles

    assert each_coreset.shape[1] == d, f"dimension of points {each_coreset.shape[1]} is not equal to d= {d}"
    dim_candidates = [np.unique(each_coreset[:, dim]) for dim in range(d)]
    max_coords_all = list(itertools.product(*dim_candidates))
    min_coords_all = list(itertools.product(*dim_candidates))
    if len(min_coords_all) < parallel_threshold or n_jobs <= 1:
        # Serial processing
        rectangles = []
        for min_coords in min_coords_all:
            for max_coords in max_coords_all:
                if all(mi <= ma for mi, ma in zip(min_coords, max_coords)):
                    rectangles.append({
                        'min_coords': np.array(min_coords),
                        'max_coords': np.array(max_coords),
                    })
        return rectangles
    else:
        # Parallel processing
        chunk_size = (len(min_coords_all) + n_jobs - 1) // n_jobs
        chunks = [min_coords_all[i:i+chunk_size] for i in range(0, len(min_coords_all), chunk_size)]
        rectangles = []
        with ProcessPoolExecutor(max_workers=n_jobs) as executor:
            futures = [executor.submit(_rect_chunk_worker, chunk, dim_candidates) for chunk in chunks]
            for fut in as_completed(futures):
                rectangles.extend(fut.result())
        return rectangles







def compute_weights_for_hyperrectangles(
        coreset: np.ndarray, #S_i in pseudocode
        rectangles: List[Dict[str, np.ndarray]], #rho in pseudocode
) -> List[float]:
    """
    Compute the corresponding weights for each rectangle. w_{q_rho} = |rho ∩ S_i| / |S_i|
    Returns a list of weights, one for each rectangle
    """
    weights = []
    for rectangle in rectangles:
        # Handle 1D data differently
        if coreset.ndim == 1:
            in_range = (coreset >= rectangle['min_coords'][0]) & (coreset <= rectangle['max_coords'][0])
        else:
            in_range = np.all(
                (coreset >= rectangle['min_coords']) & (coreset <= rectangle['max_coords']),
                axis=1,
            )
        weight = np.sum(in_range) / len(coreset)
        weights.append(weight)
    return weights


def construct_T_input_threshold(
    synopses: List[Tuple[np.uint32, Histogram]], 
    epsilon: float,
    phi: float,
    d: int,
    seed: int = 42
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    construct input for dynamic range tree T with epsilon-approximate sampling
    For 1D data, each interval [a,b] is mapped to a point (a,b) in 2D
    For nD data, each d histograms form one dataset
    
    Sampling strategy:
    - n_samples = O(1/ε²) for epsilon-approximate guarantee
    
    param synopses: List of (histogram_id, histogram) tuples
    param epsilon: ε-approximation parameter (controls sampling size: n = 1/ε²)
    param phi: privacy parameter  
    param d: dimension of the data
    param seed: random seed for reproducibility
    return:
        - Q: Union of all hyperrectangles representations
        - W: Weights of all hyperrectangles
        - I: Index of the dataset (not histogram)
    """
    Q_list = []
    W_list = []
    I_list = []
    
    # Calculate base sampling size from epsilon
    base_samples = int(1 / epsilon**2)
    
    # Check data dimension
    if d == 1:
        # 1D case: process each histogram independently
        for hist_id, synopsis in synopses:
            # Epsilon-approximate sampling
            S_i = weighted_random_sampling_from_histogram(synopsis, base_samples, seed=seed)
            R_i = generate_hyperrectangles_auto(S_i, d)
            weights = compute_weights_for_hyperrectangles(S_i, R_i)
            Qi, Wi, Ii = [], [], []
            for idx, rho in enumerate(R_i):
                q_rho = np.array([rho['min_coords'][0], rho['max_coords'][0]])  # (a,b) point
                Qi.append(q_rho)
                Wi.append(weights[idx])
                Ii.append(hist_id)  # Use histogram_id as dataset_id for 1D
            if Qi:
                Q_list.append(np.array(Qi))
                W_list.append(np.array(Wi))
                I_list.append(np.array(Ii))
    else:
        # nD case: group histograms by dataset
        num_datasets = len(synopses) // d
        if len(synopses) % d != 0:
            raise ValueError(f"Number of synopses ({len(synopses)}) must be divisible by dimension ({d})")
        
        for dataset_idx in range(num_datasets):
            # Epsilon-approximate sampling
            # Sample for each dimension
            S_multi = []
            for dim in range(d):
                synopsis_idx = dataset_idx * d + dim
                hist_id, synopsis = synopses[synopsis_idx]
                S_dim = weighted_random_sampling_from_histogram(synopsis, base_samples, seed=seed)
                S_multi.append(S_dim)
            S_i = np.column_stack(S_multi)
            
            R_i = generate_hyperrectangles_auto(S_i, d)
            weights = compute_weights_for_hyperrectangles(S_i, R_i)
            Qi, Wi, Ii = [], [], []
            for idx, rho in enumerate(R_i):
                q_rho = np.concatenate([rho['min_coords'], rho['max_coords']])
                Qi.append(q_rho)
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
    return Q, W, I

# R prime is the query hyperrectangle
def compute_R_prime_threshold( 
            R_min: np.ndarray, 
            R_max: np.ndarray
    ) -> list:
        """
        For 1D case: map query interval [R_min, R_max] to a 2D query rectangle.
        The query rectangle finds all points (a,b) such that a >= R_min and b <= R_max.
        param R_min: left-bottom corner of the query hyperrectangle
        param R_max: right-top corner of the query hyperrectangle
        return: R' as a flat list of coordinates [min_x, min_y, max_x, max_y] for rtree intersection
        """
        # Handle zero-dimensional arrays
        if R_min.ndim == 0:
            R_min = np.array([R_min])
        if R_max.ndim == 0:
            R_max = np.array([R_max])
            
        d = len(R_min)  # dimension of the input space
        
        # For 1D case
        if d == 1:
            # For query R=[R_min, R_max], we search for points (a,b)
            # where a >= R_min and b <= R_max.
            # This corresponds to the query orthant [R_min, ∞) x (-∞, R_max].
            # The query rectangle is set to [R_min, -INF, INF, R_max].
            # This way intersection() will return all (a,b) satisfying a >= R_min and b <= R_max.
            coords = [
                float(R_min[0]), # min_x
                float(-INF),     # min_y
                float(INF),      # max_x
                float(R_max[0])  # max_y
            ]
            return coords
        else:
            # For higher dimensions, maintain the same logic
            min_bounds = np.concatenate([R_min, np.array([-INF] * d)])
            max_bounds = np.concatenate([np.array([INF] * d), R_max])
            return min_bounds.tolist() + max_bounds.tolist()


