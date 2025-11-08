"""
Enhanced test with nD datasets (2D and 3D) to verify the current Ptile implementation works.
This file creates synthetic nD histograms and tests the threshold and range Ptile queries.
Now includes ground truth validation and detailed result analysis.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import numpy as np
from typing import List, Tuple, Dict, Any
from main_algo.data_processing.histograms import Histogram
from main_algo.execution.Ptilethreshold import construct_T_threshold, query_T_threshold
from main_algo.execution.Ptilerange import construct_T_range, query_T_range
from main_algo.execution.setups4threshold import compute_R_prime_threshold, weighted_random_sampling_from_histogram
from main_algo.execution.setups4range import compute_R_prime_range, get_all_datasets, compute_global_bounding_box, project_to_bounding_box, generate_combinatorial_rectangles, generate_pair_for_range_predicate, compute_weights_for_hyperrectangles


def create_simple_2d_histograms() -> List[Tuple[np.uint32, Histogram]]:
    """Create simple 2D histograms for testing with only 3 data points per dataset."""
    synopses = []
    hist_id = 0
    
    # Dataset 0: X dimension - 3 points in [1,5] range
    counts_x0 = np.array([2, 1], dtype=np.float32)  # 2 points in [1,3], 1 point in [3,5]
    bin_edges_x0 = np.array([1, 3, 5], dtype=np.float64)
    hist_x0 = (counts_x0, bin_edges_x0)
    synopses.append((hist_id, hist_x0))
    hist_id += 1
    
    # Dataset 0: Y dimension - 3 points in [1,5] range
    counts_y0 = np.array([1, 2], dtype=np.float32)  # 1 point in [1,3], 2 points in [3,5]
    bin_edges_y0 = np.array([1, 3, 5], dtype=np.float64)
    hist_y0 = (counts_y0, bin_edges_y0)
    synopses.append((hist_id, hist_y0))
    hist_id += 1
    
    # Dataset 1: X dimension - 3 points in [3,7] range
    counts_x1 = np.array([1, 2], dtype=np.float32)  # 1 point in [3,5], 2 points in [5,7]
    bin_edges_x1 = np.array([3, 5, 7], dtype=np.float64)
    hist_x1 = (counts_x1, bin_edges_x1)
    synopses.append((hist_id, hist_x1))
    hist_id += 1
    
    # Dataset 1: Y dimension - 3 points in [3,7] range
    counts_y1 = np.array([2, 1], dtype=np.float32)  # 2 points in [3,5], 1 point in [5,7]
    bin_edges_y1 = np.array([3, 5, 7], dtype=np.float64)
    hist_y1 = (counts_y1, bin_edges_y1)
    synopses.append((hist_id, hist_y1))
    hist_id += 1
    
    return synopses


def create_simple_3d_histograms() -> List[Tuple[np.uint32, Histogram]]:
    """Create simple 3D histograms for testing with only 3 data points per dataset."""
    synopses = []
    hist_id = 0
    
    # Dataset 0: X dimension - 3 points in [1,4] range
    counts_x0 = np.array([2, 1], dtype=np.float32)  # 2 points in [1,2.5], 1 point in [2.5,4]
    bin_edges_x0 = np.array([1, 2.5, 4], dtype=np.float64)
    hist_x0 = (counts_x0, bin_edges_x0)
    synopses.append((hist_id, hist_x0))
    hist_id += 1
    
    # Dataset 0: Y dimension - 3 points in [1,4] range
    counts_y0 = np.array([1, 2], dtype=np.float32)  # 1 point in [1,2.5], 2 points in [2.5,4]
    bin_edges_y0 = np.array([1, 2.5, 4], dtype=np.float64)
    hist_y0 = (counts_y0, bin_edges_y0)
    synopses.append((hist_id, hist_y0))
    hist_id += 1
    
    # Dataset 0: Z dimension - 3 points in [1,4] range
    counts_z0 = np.array([1, 2], dtype=np.float32)  # 1 point in [1,2.5], 2 points in [2.5,4]
    bin_edges_z0 = np.array([1, 2.5, 4], dtype=np.float64)
    hist_z0 = (counts_z0, bin_edges_z0)
    synopses.append((hist_id, hist_z0))
    hist_id += 1
    
    # Dataset 1: X dimension - 3 points in [5,8] range
    counts_x1 = np.array([1, 2], dtype=np.float32)  # 1 point in [5,6.5], 2 points in [6.5,8]
    bin_edges_x1 = np.array([5, 6.5, 8], dtype=np.float64)
    hist_x1 = (counts_x1, bin_edges_x1)
    synopses.append((hist_id, hist_x1))
    hist_id += 1
    
    # Dataset 1: Y dimension - 3 points in [5,8] range
    counts_y1 = np.array([2, 1], dtype=np.float32)  # 2 points in [5,6.5], 1 point in [6.5,8]
    bin_edges_y1 = np.array([5, 6.5, 8], dtype=np.float64)
    hist_y1 = (counts_y1, bin_edges_y1)
    synopses.append((hist_id, hist_y1))
    hist_id += 1
    
    # Dataset 1: Z dimension - 3 points in [5,8] range
    counts_z1 = np.array([1, 2], dtype=np.float32)  # 1 point in [5,6.5], 2 points in [6.5,8]
    bin_edges_z1 = np.array([5, 6.5, 8], dtype=np.float64)
    hist_z1 = (counts_z1, bin_edges_z1)
    synopses.append((hist_id, hist_z1))
    hist_id += 1
    
    return synopses



def calculate_ground_truth_probabilities(synopses: List[Tuple[np.uint32, Histogram]], R_min: np.ndarray, R_max: np.ndarray, d: int) -> List[float]:
    """Calculate the true probability P(x ∈ R) for each dataset."""
    probabilities = []
    
    # Group histograms by dataset
    num_datasets = len(synopses) // d
    
    for dataset_idx in range(num_datasets):
        # Sample from each dimension
        S_multi = []
        for dim in range(d):
            synopsis_idx = dataset_idx * d + dim
            hist_id, synopsis = synopses[synopsis_idx]
            S_dim = weighted_random_sampling_from_histogram(synopsis, 5, seed=42)  # Use 5 points to match tree construction
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


def evaluate_result(result: List[int], expected: List[int], query_type: str) -> Dict[str, Any]:
    """Evaluate query result against ground truth."""
    result_set = set(result)
    expected_set = set(expected)
    
    # Calculate metrics
    true_positives = len(expected_set & result_set)
    false_positives = len(result_set - expected_set)
    false_negatives = len(expected_set - result_set)
    
    precision = true_positives / len(result_set) if result_set else 1.0
    recall = true_positives / len(expected_set) if expected_set else 1.0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "query_type": query_type,
        "ground_truth": list(expected_set),
        "result": result,
        "correct": expected_set == result_set,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives
    }


def test_threshold_query_2d():
    """Test threshold query with 2D data."""
    print("=== Testing Threshold Query (2D) ===")

    # Create test data
    synopses = create_simple_2d_histograms()
    
    # Set parameters
    epsilon = 0
    phi = 0.1
    delta = 0
    d = 2  # 2D data
    
    # Create query rectangle: [2,6] x [2,6]
    R_min = np.array([2, 2])
    R_max = np.array([6, 6])
    
    # Create threshold query: P(x ∈ R) ≥ 0.3
    theta = (0.3, 1.0)
    
    print(f"Query rectangle: [{R_min[0]}, {R_max[0]}] x [{R_min[1]}, {R_max[1]}]")
    print(f"Threshold: P(x ∈ R) ≥ {theta[0]}")
    
    try:
        # Calculate ground truth probabilities
        true_probs = calculate_ground_truth_probabilities(synopses, R_min, R_max, d)
        print(f"Ground truth probabilities: {[f'{p:.3f}' for p in true_probs]}")
        
        # Calculate expected result based on threshold
        expected = [i for i, p in enumerate(true_probs) if p >= theta[0]]
        print(f"Expected datasets (P ≥ {theta[0]}): {expected}")
        
        # Build range tree
        T = construct_T_threshold(synopses, epsilon, phi, d)
        
        # Query the tree
        R_prime = compute_R_prime_threshold(R_min, R_max)
        result = query_T_threshold(T, R_prime, theta, epsilon, delta)
        
        print(f"Range tree result: {result}")
        
        # Evaluate result
        evaluation = evaluate_result(result, expected, "threshold")
        
        # Print results
        print(f"Status: {'✅ PASS' if evaluation['correct'] else '❌ FAIL'}")
        
        return evaluation["correct"]
        
    except Exception as e:
        print(f"Error in 2D threshold query: {e}")
        return False


def test_range_query_2d():
    """Test range query with 2D data."""
    print("\n=== Testing Range Query (2D) ===")
    
    # Create test data
    synopses = create_simple_2d_histograms()
    
    # Set parameters
    epsilon = 0.01
    phi = 0.1
    delta = 0
    d = 2  # 2D data
    
    # Create query rectangle: [3,7] x [3,7]
    R_min = np.array([3, 3])
    R_max = np.array([7, 7])
    
    # Create range query: P(x ∈ R) ∈ [0.2, 0.8]
    theta = (0.2, 0.8)
    
    print(f"Query rectangle: [{R_min[0]}, {R_max[0]}] x [{R_min[1]}, {R_max[1]}]")
    print(f"Range: P(x ∈ R) ∈ [{theta[0]}, {theta[1]}]")
    
    try:
        # Calculate ground truth probabilities
        true_probs = calculate_ground_truth_probabilities(synopses, R_min, R_max, d)
        print(f"Ground truth probabilities: {[f'{p:.3f}' for p in true_probs]}")
        
        # Calculate expected result based on range
        expected = [i for i, p in enumerate(true_probs) if theta[0] <= p <= theta[1]]
        print(f"Expected datasets (P ∈ [{theta[0]}, {theta[1]}]): {expected}")
        
        # Build range tree
        T = construct_T_range(synopses, epsilon, phi, d)
        
        # Query the tree
        result = query_T_range(T, R_min, R_max, theta, epsilon, delta, synopses)
        
        print(f"Range tree result: {result}")
        
        # Evaluate result
        evaluation = evaluate_result(result, expected, "range")
        
        # Print results
        print(f"Status: {'✅ PASS' if evaluation['correct'] else '❌ FAIL'}")
        
        return evaluation["correct"]
        
    except Exception as e:
        print(f"Error in 2D range query: {e}")
        return False


def test_threshold_query_3d():
    """Test threshold query with 3D data."""
    print("\n=== Testing Threshold Query (3D) ===")

    # Create test data
    synopses = create_simple_3d_histograms()
    
    # Set parameters
    epsilon = 0
    phi = 0.1
    delta = 0
    d = 3  # 3D data
    
    # Create query rectangle: [2,7] x [2,7] x [2,7]
    R_min = np.array([2, 2, 2])
    R_max = np.array([7, 7, 7])
    
    # Create threshold query: P(x ∈ R) ≥ 0.4
    theta = (0.4, 1.0)
    
    print(f"Query rectangle: [{R_min[0]}, {R_max[0]}] x [{R_min[1]}, {R_max[1]}] x [{R_min[2]}, {R_max[2]}]")
    print(f"Threshold: P(x ∈ R) ≥ {theta[0]}")
    
    try:
        # Calculate ground truth probabilities
        true_probs = calculate_ground_truth_probabilities(synopses, R_min, R_max, d)
        print(f"Ground truth probabilities: {[f'{p:.3f}' for p in true_probs]}")
        
        # Calculate expected result based on threshold
        expected = [i for i, p in enumerate(true_probs) if p >= theta[0]]
        print(f"Expected datasets (P ≥ {theta[0]}): {expected}")
        
        # Build range tree
        T = construct_T_threshold(synopses, epsilon, phi, d)
        
        # Query the tree
        R_prime = compute_R_prime_threshold(R_min, R_max)
        result = query_T_threshold(T, R_prime, theta, epsilon, delta)
        
        print(f"Range tree result: {result}")
        
        # Evaluate result
        evaluation = evaluate_result(result, expected, "threshold")
        
        # Print results
        print(f"Status: {'✅ PASS' if evaluation['correct'] else '❌ FAIL'}")
        
        return evaluation["correct"]
        
    except Exception as e:
        print(f"Error in 3D threshold query: {e}")
        return False


def test_range_query_3d():
    """Test range query with 3D data."""
    print("\n=== Testing Range Query (3D) ===")
    
    # Create test data
    synopses = create_simple_3d_histograms()
    
    # Set parameters
    epsilon = 0.01
    phi = 0.1
    delta = 0.05
    d = 3  # 3D data
    
    # Create query rectangle: [4,8] x [4,8] x [4,8]
    R_min = np.array([4, 4, 4])
    R_max = np.array([8, 8, 8])
    
    # Create range query: P(x ∈ R) ∈ [0.3, 0.7]
    theta = (0.3, 0.7)
    
    print(f"Query rectangle: [{R_min[0]}, {R_max[0]}] x [{R_min[1]}, {R_max[1]}] x [{R_min[2]}, {R_max[2]}]")
    print(f"Range: P(x ∈ R) ∈ [{theta[0]}, {theta[1]}]")
    
    try:
        # Calculate ground truth probabilities
        true_probs = calculate_ground_truth_probabilities(synopses, R_min, R_max, d)
        print(f"Ground truth probabilities: {[f'{p:.3f}' for p in true_probs]}")
        
        # Calculate expected result based on range
        expected = [i for i, p in enumerate(true_probs) if theta[0] <= p <= theta[1]]
        print(f"Expected datasets (P ∈ [{theta[0]}, {theta[1]}]): {expected}")
        
        # Build range tree
        T = construct_T_range(synopses, epsilon, phi, d)
        
        # Query the tree
        result = query_T_range(T, R_min, R_max, theta, epsilon, delta, synopses)
        
        print(f"Range tree result: {result}")
        
        # Evaluate result
        evaluation = evaluate_result(result, expected, "range")
        
        # Print results
        print(f"Status: {'✅ PASS' if evaluation['correct'] else '❌ FAIL'}")
        
        return evaluation["correct"]
        
    except Exception as e:
        print(f"Error in 3D range query: {e}")
        return False


def test_multiple_queries_nd():
    """Test multiple queries with different dimensions."""
    print("\n=== Testing Multiple nD Queries ===")
    
    # Test 2D queries
    print("--- 2D Queries ---")
    synopses_2d = create_simple_2d_histograms()
    epsilon = 0.01
    phi = 0.1
    delta = 0.05
    
    # test_queries_2d = [
    #     {
    #         "name": "2D Query 1: [1,5]x[1,5] threshold ≥ 0.4",
    #         "R_min": np.array([1, 1]),
    #         "R_max": np.array([5, 5]),
    #         "theta": (0.4, 1.0),
    #         "type": "threshold",
    #         "d": 2
    #     },
    #     {
    #         "name": "2D Query 2: [4,8]x[4,8] range [0.2,0.6]",
    #         "R_min": np.array([4, 4]),
    #         "R_max": np.array([8, 8]),
    #         "theta": (0.2, 0.6),
    #         "type": "range",
    #         "d": 2
    #     }
    # ]
    
    # results_2d = []
    # for query in test_queries_2d:
    #     print(f"\n{query['name']}")
    #     try:
    #         true_probs = calculate_ground_truth_probabilities(synopses_2d, query["R_min"], query["R_max"], query["d"])
    #         print(f"Ground truth: {[f'{p:.3f}' for p in true_probs]}")
            
    #         if query["type"] == "threshold":
    #             expected = [i for i, p in enumerate(true_probs) if p >= query["theta"][0]]
    #             T = construct_T_threshold(synopses_2d, epsilon, phi, query["d"])
    #             R_prime = compute_R_prime_threshold(query["R_min"], query["R_max"])
    #             result = query_T_threshold(T, R_prime, query["theta"], epsilon, delta)
    #         else:  # range
    #             expected = [i for i, p in enumerate(true_probs) if query["theta"][0] <= p <= query["theta"][1]]
    #             T = construct_T_range(synopses_2d, epsilon, phi, query["d"])
    #             result = query_T_range(T, query["R_min"], query["R_max"], query["theta"], epsilon, delta, synopses_2d)
            
    #         evaluation = evaluate_result(result, expected, query["type"])
    #         results_2d.append(evaluation)
            
    #         status = "✅ PASS" if evaluation["correct"] else "❌ FAIL"
    #         print(f"Result: {result}, Expected: {expected} - {status}")
            
    #     except Exception as e:
    #         print(f"Error: {e}")
    #         results_2d.append({"correct": False})
    
    # Test 3D queries
    print("\n--- 3D Queries ---")
    synopses_3d = create_simple_3d_histograms()
    
    test_queries_3d = [
        {
            "name": "3D Query 1: [1,6]x[1,6]x[1,6] threshold ≥ 0.5",
            "R_min": np.array([1, 1, 1]),
            "R_max": np.array([6, 6, 6]),
            "theta": (0.5, 1.0),
            "type": "threshold",
            "d": 3
        },
        {
            "name": "3D Query 2: [5,9]x[5,9]x[5,9] range [0.3,0.7]",
            "R_min": np.array([5, 5, 5]),
            "R_max": np.array([9, 9, 9]),
            "theta": (0.3, 0.7),
            "type": "range",
            "d": 3
        }
    ]
    
    results_3d = []
    for query in test_queries_3d:
        print(f"\n{query['name']}")
        try:
            true_probs = calculate_ground_truth_probabilities(synopses_3d, query["R_min"], query["R_max"], query["d"])
            print(f"Ground truth: {[f'{p:.3f}' for p in true_probs]}")
            
            if query["type"] == "threshold":
                expected = [i for i, p in enumerate(true_probs) if p >= query["theta"][0]]
                T = construct_T_threshold(synopses_3d, epsilon, phi, query["d"])
                R_prime = compute_R_prime_threshold(query["R_min"], query["R_max"])
                result = query_T_threshold(T, R_prime, query["theta"], epsilon, delta)
            else:  # range
                expected = [i for i, p in enumerate(true_probs) if query["theta"][0] <= p <= query["theta"][1]]
                T = construct_T_range(synopses_3d, epsilon, phi, query["d"])
                result = query_T_range(T, query["R_min"], query["R_max"], query["theta"], epsilon, delta, synopses_3d)
            
            evaluation = evaluate_result(result, expected, query["type"])
            results_3d.append(evaluation)
            
            status = "✅ PASS" if evaluation["correct"] else "❌ FAIL"
            print(f"Result: {result}, Expected: {expected} - {status}")
            
        except Exception as e:
            print(f"Error: {e}")
            results_3d.append({"correct": False})
    
    # Summary
    print(f"\n--- Multiple nD Queries Summary ---")
    # passed_2d = sum(1 for r in results_2d if r["correct"])
    # total_2d = len(results_2d)
    passed_3d = sum(1 for r in results_3d if r["correct"])
    total_3d = len(results_3d)
    
    # print(f"2D queries: {passed_2d}/{total_2d} passed ({passed_2d/total_2d*100:.1f}%)")
    print(f"3D queries: {passed_3d}/{total_3d} passed ({passed_3d/total_3d*100:.1f}%)")
    # print(f"Overall: {passed_2d + passed_3d}/{total_2d + total_3d} passed ({(passed_2d + passed_3d)/(total_2d + total_3d)*100:.1f}%)")


def main():
    """Main test function."""
    print("Enhanced nD Ptile Implementation Test")
    print("=" * 60)
    
    # Test individual queries
    # threshold_2d_success = test_threshold_query_2d()
    # range_2d_success = test_range_query_2d()
    # threshold_3d_success = test_threshold_query_3d()
    range_3d_success = test_range_query_3d()
    
    # Test multiple queries
    # test_multiple_queries_nd()
    
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    # print(f"2D threshold query: {'✅ PASS' if threshold_2d_success else '❌ FAIL'}")
    # print(f"2D range query: {'✅ PASS' if range_2d_success else '❌ FAIL'}")
    # print(f"3D threshold query: {'✅ PASS' if threshold_3d_success else '❌ FAIL'}")
    print(f"3D range query: {'✅ PASS' if range_3d_success else '❌ FAIL'}")
    
    # total_passed = sum([threshold_3d_success, range_3d_success])
    total_tests = 4
    
    # if total_passed == total_tests:
    #     print(f"\n🎉 All {total_tests} tests passed!")
    # elif total_passed >= total_tests * 0.75:
    #     print(f"\n✅ Most tests passed ({total_passed}/{total_tests}).")
    # else:
    #     print(f"\n⚠️  Only {total_passed}/{total_tests} tests passed.")
    
    print("\nTest complete!")


if __name__ == "__main__":
    main() 