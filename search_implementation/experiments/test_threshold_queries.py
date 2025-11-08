"""
File dedicated to testing threshold queries, including 1D, 2D, and 3D datasets.
Tests threshold query functionality for different dimensions and outputs detailed debugging information.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import numpy as np
from typing import List, Tuple, Dict, Any
from main_algo.data_processing.histograms import Histogram
from main_algo.execution.Ptilethreshold import construct_T_threshold, query_T_threshold
from main_algo.execution.setups4threshold import compute_R_prime_threshold, weighted_random_sampling_from_histogram


def create_1d_histograms() -> List[Tuple[np.uint32, Histogram]]:
    """Creates 1D histogram data for testing"""
    synopses = []
    
    # Dataset 0: Most data within range [1,4]
    counts_0 = np.array([3, 2], dtype=np.float32)  # 3 points in [1,3], 2 points in [3,5]
    bin_edges_0 = np.array([1, 3, 5], dtype=np.float64)
    hist_0 = (counts_0, bin_edges_0)
    synopses.append((0, hist_0))
    
    # Dataset 1: Most data within range [4,8]
    counts_1 = np.array([1, 4], dtype=np.float32)  # 1 point in [2,5], 4 points in [5,8]
    bin_edges_1 = np.array([2, 5, 8], dtype=np.float64)
    hist_1 = (counts_1, bin_edges_1)
    synopses.append((1, hist_1))
    
    return synopses


def create_2d_histograms() -> List[Tuple[np.uint32, Histogram]]:
    """Creates 2D histogram data for testing"""
    synopses = []
    hist_id = 0
    
    # Dataset 0: X-dimension - data concentrated in [1,4]
    counts_x0 = np.array([3, 2], dtype=np.float32)
    bin_edges_x0 = np.array([1, 3, 5], dtype=np.float64)
    hist_x0 = (counts_x0, bin_edges_x0)
    synopses.append((hist_id, hist_x0))
    hist_id += 1
    
    # Dataset 0: Y-dimension - data concentrated in [1,4]
    counts_y0 = np.array([2, 3], dtype=np.float32)
    bin_edges_y0 = np.array([1, 3, 5], dtype=np.float64)
    hist_y0 = (counts_y0, bin_edges_y0)
    synopses.append((hist_id, hist_y0))
    hist_id += 1
    
    # Dataset 1: X-dimension - data concentrated in [4,7]
    counts_x1 = np.array([1, 4], dtype=np.float32)
    bin_edges_x1 = np.array([2, 5, 8], dtype=np.float64)
    hist_x1 = (counts_x1, bin_edges_x1)
    synopses.append((hist_id, hist_x1))
    hist_id += 1
    
    # Dataset 1: Y-dimension - data concentrated in [4,7]
    counts_y1 = np.array([2, 3], dtype=np.float32)
    bin_edges_y1 = np.array([2, 5, 8], dtype=np.float64)
    hist_y1 = (counts_y1, bin_edges_y1)
    synopses.append((hist_id, hist_y1))
    hist_id += 1
    
    return synopses


def create_3d_histograms() -> List[Tuple[np.uint32, Histogram]]:
    """Creates 3D histogram data for testing"""
    synopses = []
    hist_id = 0
    
    # Dataset 0: X-dimension - data concentrated in [1,3]
    counts_x0 = np.array([3, 2], dtype=np.float32)
    bin_edges_x0 = np.array([1, 2.5, 4], dtype=np.float64)
    hist_x0 = (counts_x0, bin_edges_x0)
    synopses.append((hist_id, hist_x0))
    hist_id += 1
    
    # Dataset 0: Y-dimension - data concentrated in [1,3]
    counts_y0 = np.array([2, 3], dtype=np.float32)
    bin_edges_y0 = np.array([1, 2.5, 4], dtype=np.float64)
    hist_y0 = (counts_y0, bin_edges_y0)
    synopses.append((hist_id, hist_y0))
    hist_id += 1
    
    # Dataset 0: Z-dimension - data concentrated in [1,3]
    counts_z0 = np.array([2, 3], dtype=np.float32)
    bin_edges_z0 = np.array([1, 2.5, 4], dtype=np.float64)
    hist_z0 = (counts_z0, bin_edges_z0)
    synopses.append((hist_id, hist_z0))
    hist_id += 1
    
    # Dataset 1: X-dimension - data concentrated in [5,7]
    counts_x1 = np.array([1, 4], dtype=np.float32)
    bin_edges_x1 = np.array([3, 6, 9], dtype=np.float64)
    hist_x1 = (counts_x1, bin_edges_x1)
    synopses.append((hist_id, hist_x1))
    hist_id += 1
    
    # Dataset 1: Y-dimension - data concentrated in [5,7]
    counts_y1 = np.array([2, 3], dtype=np.float32)
    bin_edges_y1 = np.array([3, 6, 9], dtype=np.float64)
    hist_y1 = (counts_y1, bin_edges_y1)
    synopses.append((hist_id, hist_y1))
    hist_id += 1
    
    # Dataset 1: Z-dimension - data concentrated in [5,7]
    counts_z1 = np.array([1, 4], dtype=np.float32)
    bin_edges_z1 = np.array([3, 6, 9], dtype=np.float64)
    hist_z1 = (counts_z1, bin_edges_z1)
    synopses.append((hist_id, hist_z1))
    hist_id += 1
    
    return synopses


def calculate_ground_truth_probabilities(synopses: List[Tuple[np.uint32, Histogram]], R_min: np.ndarray, R_max: np.ndarray, d: int) -> List[float]:
    """Calculates the true probability P(x ∈ R) for each dataset"""
    probabilities = []
    
    if d == 1:
        # 1D case: Each histogram is processed independently
        for hist_id, synopsis in synopses:
            dataset = weighted_random_sampling_from_histogram(synopsis, 5, seed=42)
            print(f"Dataset {hist_id}: data points = {dataset}")
            
            # Calculate probability
            in_range_mask = (dataset >= R_min[0]) & (dataset <= R_max[0])
            p = np.sum(in_range_mask) / len(dataset)
            
            print(f"  Query range: [{R_min[0]:.1f}, {R_max[0]:.1f}]")
            print(f"  Points in range: {in_range_mask}")
            print(f"  Probability: {p:.3f}")
            
            probabilities.append(p)
    else:
        # nD case: Each dataset consists of d histograms
        num_datasets = len(synopses) // d
        
        for dataset_idx in range(num_datasets):
            # Sample from each dimension
            S_multi = []
            for dim in range(d):
                synopsis_idx = dataset_idx * d + dim
                hist_id, synopsis = synopses[synopsis_idx]
                S_dim = weighted_random_sampling_from_histogram(synopsis, 5, seed=42)
                S_multi.append(S_dim)
            dataset = np.column_stack(S_multi)
            
            print(f"Dataset {dataset_idx}: data points:")
            for i, point in enumerate(dataset):
                print(f"  Point {i}: {point}")
            
            # Calculate probability
            in_range_mask = np.all((dataset >= R_min) & (dataset <= R_max), axis=1)
            p = np.sum(in_range_mask) / len(dataset)
            
            print(f"  Query range: [{R_min}] to [{R_max}]")
            print(f"  Points in range: {in_range_mask}")
            print(f"  Probability: {p:.3f}")
            
            probabilities.append(p)
    
    return probabilities


def test_threshold_query_1d():
    """Tests 1D threshold query"""
    print("=" * 60)
    print("Testing 1D Threshold Query")
    print("=" * 60)
    
    # Create test data
    synopses = create_1d_histograms()
    print(f"Created {len(synopses)} 1D histograms")
    
    # Parameter settings
    epsilon = 0
    phi = 0.1
    delta = 0
    d = 1
    
    # Query settings
    R_min = np.array([2])
    R_max = np.array([6])
    theta = (0.4, 1.0)  # threshold ≥ 0.4
    
    print(f"Query range: [{R_min[0]}, {R_max[0]}]")
    print(f"Threshold: P(x ∈ R) ≥ {theta[0]}")
    print(f"Parameters: ε={epsilon}, φ={phi}, δ={delta}")
    
    try:
        # Calculate ground truth
        print("\n--- Ground Truth Calculation ---")
        true_probs = calculate_ground_truth_probabilities(synopses, R_min, R_max, d)
        expected = [i for i, p in enumerate(true_probs) if p >= theta[0]]
        print(f"Ground truth probabilities: {[f'{p:.3f}' for p in true_probs]}")
        print(f"Expected result: {expected}")
        
        # Build tree and query
        print("\n--- Building Threshold Tree ---")
        T = construct_T_threshold(synopses, epsilon, phi, d)
        
        print("\n--- Executing Query ---")
        R_prime = compute_R_prime_threshold(R_min, R_max)
        result = query_T_threshold(T, R_prime, theta, epsilon, delta)
        
        # Evaluate result
        print(f"\nQuery result: {result}")
        print(f"Expected result: {expected}")
        
        correct = set(result) == set(expected)
        status = "✅ PASS" if correct else "❌ FAIL"
        print(f"Status: {status}")
        
        return correct
        
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_threshold_query_2d():
    """Tests 2D threshold query"""
    print("\n" + "=" * 60)
    print("Testing 2D Threshold Query")
    print("=" * 60)
    
    # Create test data
    synopses = create_2d_histograms()
    print(f"Created {len(synopses)} 2D histograms")
    
    # Parameter settings
    epsilon = 0
    phi = 0.1
    delta = 0
    d = 2
    
    # Query settings
    R_min = np.array([2, 2])
    R_max = np.array([6, 6])
    theta = (0.3, 1.0)  # threshold ≥ 0.3
    
    print(f"Query range: [{R_min[0]}, {R_max[0]}] x [{R_min[1]}, {R_max[1]}]")
    print(f"Threshold: P(x ∈ R) ≥ {theta[0]}")
    print(f"Parameters: ε={epsilon}, φ={phi}, δ={delta}")
    
    try:
        # Calculate ground truth
        print("\n--- Ground Truth Calculation ---")
        true_probs = calculate_ground_truth_probabilities(synopses, R_min, R_max, d)
        expected = [i for i, p in enumerate(true_probs) if p >= theta[0]]
        print(f"Ground truth probabilities: {[f'{p:.3f}' for p in true_probs]}")
        print(f"Expected result: {expected}")
        
        # Build tree and query
        print("\n--- Building Threshold Tree ---")
        T = construct_T_threshold(synopses, epsilon, phi, d)
        
        print("\n--- Executing Query ---")
        R_prime = compute_R_prime_threshold(R_min, R_max)
        result = query_T_threshold(T, R_prime, theta, epsilon, delta)
        
        # Evaluate result
        print(f"\nQuery result: {result}")
        print(f"Expected result: {expected}")
        
        correct = set(result) == set(expected)
        status = "✅ PASS" if correct else "❌ FAIL"
        print(f"Status: {status}")
        
        return correct
        
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_threshold_query_3d():
    """Tests 3D threshold query"""
    print("\n" + "=" * 60)
    print("Testing 3D Threshold Query")
    print("=" * 60)
    
    # Create test data
    synopses = create_3d_histograms()
    print(f"Created {len(synopses)} 3D histograms")
    
    # Parameter settings
    epsilon = 0
    phi = 0.1
    delta = 0
    d = 3
    
    # Query settings
    R_min = np.array([2, 2, 2])
    R_max = np.array([7, 7, 7])
    theta = (0.4, 1.0)  # threshold ≥ 0.4
    
    print(f"Query range: [{R_min[0]}, {R_max[0]}] x [{R_min[1]}, {R_max[1]}] x [{R_min[2]}, {R_max[2]}]")
    print(f"Threshold: P(x ∈ R) ≥ {theta[0]}")
    print(f"Parameters: ε={epsilon}, φ={phi}, δ={delta}")
    
    try:
        # Calculate ground truth
        print("\n--- Ground Truth Calculation ---")
        true_probs = calculate_ground_truth_probabilities(synopses, R_min, R_max, d)
        expected = [i for i, p in enumerate(true_probs) if p >= theta[0]]
        print(f"Ground truth probabilities: {[f'{p:.3f}' for p in true_probs]}")
        print(f"Expected result: {expected}")
        
        # Build tree and query
        print("\n--- Building Threshold Tree ---")
        T = construct_T_threshold(synopses, epsilon, phi, d)
        
        print("\n--- Executing Query ---")
        R_prime = compute_R_prime_threshold(R_min, R_max)
        result = query_T_threshold(T, R_prime, theta, epsilon, delta)
        
        # Evaluate result
        print(f"\nQuery result: {result}")
        print(f"Expected result: {expected}")
        
        correct = set(result) == set(expected)
        status = "✅ PASS" if correct else "❌ FAIL"
        print(f"Status: {status}")
        
        return correct
        
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_multiple_threshold_queries():
    """Tests multiple threshold queries with different thresholds"""
    print("\n" + "=" * 60)
    print("Testing Multiple Threshold Queries")
    print("=" * 60)
    
    # Test configurations
    test_configs = [
        {
            "name": "1D Query: [1,5] threshold ≥ 0.3",
            "synopses": create_1d_histograms(),
            "R_min": np.array([1]),
            "R_max": np.array([5]),
            "theta": (0.3, 1.0),
            "d": 1
        },
        {
            "name": "1D Query: [3,7] threshold ≥ 0.6",
            "synopses": create_1d_histograms(),
            "R_min": np.array([3]),
            "R_max": np.array([7]),
            "theta": (0.6, 1.0),
            "d": 1
        },
        {
            "name": "2D Query: [1,5]x[1,5] threshold ≥ 0.4",
            "synopses": create_2d_histograms(),
            "R_min": np.array([1, 1]),
            "R_max": np.array([5, 5]),
            "theta": (0.4, 1.0),
            "d": 2
        },
        {
            "name": "3D Query: [1,6]x[1,6]x[1,6] threshold ≥ 0.5",
            "synopses": create_3d_histograms(),
            "R_min": np.array([1, 1, 1]),
            "R_max": np.array([6, 6, 6]),
            "theta": (0.5, 1.0),
            "d": 3
        }
    ]
    
    # Parameter settings
    epsilon = 0
    phi = 0.1
    delta = 0
    
    results = []
    
    for config in test_configs:
        print(f"\n--- {config['name']} ---")
        
        try:
            # Calculate ground truth
            true_probs = calculate_ground_truth_probabilities(config['synopses'], config['R_min'], config['R_max'], config['d'])
            expected = [i for i, p in enumerate(true_probs) if p >= config['theta'][0]]
            print(f"Ground truth probabilities: {[f'{p:.3f}' for p in true_probs]}")
            print(f"Expected result: {expected}")
            
            # Build tree and query
            T = construct_T_threshold(config['synopses'], epsilon, phi, config['d'])
            R_prime = compute_R_prime_threshold(config['R_min'], config['R_max'])
            result = query_T_threshold(T, R_prime, config['theta'], epsilon, delta)
            
            # Evaluate result
            correct = set(result) == set(expected)
            status = "✅ PASS" if correct else "❌ FAIL"
            print(f"Query result: {result}")
            print(f"Status: {status}")
            
            results.append({
                "name": config['name'],
                "correct": correct,
                "result": result,
                "expected": expected
            })
            
        except Exception as e:
            print(f"Error: {e}")
            results.append({
                "name": config['name'],
                "correct": False,
                "result": [],
                "expected": []
            })
    
    # Summary
    print(f"\n--- Multiple Query Test Summary ---")
    passed = sum(1 for r in results if r['correct'])
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result['correct'] else "❌ FAIL"
        print(f"{result['name']}: {status}")
    
    print(f"\nOverall result: {passed}/{total} passed ({passed/total*100:.1f}%)")
    
    return results


def main():
    """Main test function"""
    print("Threshold Query Test")
    print("=" * 60)
    
    # Run individual tests
    print("Running individual dimension tests...")
    test_1d = test_threshold_query_1d()
    test_2d = test_threshold_query_2d()
    test_3d = test_threshold_query_3d()
    
    # Run multiple query tests
    print("\nRunning multiple query tests...")
    multi_results = test_multiple_threshold_queries()
    
    # Final summary
    print("\n" + "=" * 60)
    print("FINAL TEST SUMMARY")
    print("=" * 60)
    
    single_tests = [test_1d, test_2d, test_3d]
    single_passed = sum(single_tests)
    single_total = len(single_tests)
    
    multi_passed = sum(1 for r in multi_results if r['correct'])
    multi_total = len(multi_results)
    
    print(f"Individual dimension tests: {single_passed}/{single_total} passed")
    print(f"Multiple query tests: {multi_passed}/{multi_total} passed")
    print(f"Overall pass rate: {(single_passed + multi_passed)/(single_total + multi_total)*100:.1f}%")
    
    if single_passed == single_total and multi_passed == multi_total:
        print("\n🎉 All tests passed!")
    elif (single_passed + multi_passed) >= (single_total + multi_total) * 0.8:
        print("\n✅ Most tests passed!")
    else:
        print("\n⚠️  Failed tests need to be checked!")
    
    print("\nTest complete!")


if __name__ == "__main__":
    main() 