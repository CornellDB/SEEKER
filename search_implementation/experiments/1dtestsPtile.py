"""
Enhanced test with 1D datasets to verify the current Ptile implementation works.
This file creates synthetic 1D histograms and tests the threshold and range Ptile queries.
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


def create_simple_1d_histograms() -> List[Tuple[np.uint32, Histogram]]:
    """Create simple 1D histograms for testing."""
    counts_1 = np.array([2, 8], dtype=np.float32)
    bin_edges_1 = np.array([1, 4, 8], dtype=np.float64)
    hist_1 = (counts_1, bin_edges_1)
    
    counts_2 = np.array([7, 3], dtype=np.float32)
    bin_edges_2 = np.array([2, 5, 10], dtype=np.float64)
    hist_2 = (counts_2, bin_edges_2)
    
    return [
        (0, hist_1),
        (1, hist_2)
    ]


def calculate_ground_truth_probabilities(synopses: List[Tuple[np.uint32, Histogram]], R_min: np.ndarray, R_max: np.ndarray, epsilon: float = 0.1) -> List[float]:
    """Calculate the true probability P(x ∈ R) for each dataset using epsilon-approximate sampling."""
    datasets = []
    # Use epsilon-approximate sampling
    n_samples = max(int(1 / epsilon**2), 100)
    for hist_id, hist in synopses:
        dataset = weighted_random_sampling_from_histogram(hist, n_samples, seed=42)
        datasets.append(dataset)
    
    probabilities = []
    for i, dataset in enumerate(datasets):
        print(f"Dataset {i}: data={dataset}, range=[{R_min[0]:.3f}, {R_max[0]:.3f}]")
        
        # Handle 1D arrays correctly
        if dataset.ndim == 1:
            in_range_mask = (dataset >= R_min[0]) & (dataset <= R_max[0])
        else:
            in_range_mask = np.all((dataset >= R_min) & (dataset <= R_max), axis=1)
        
        p = np.sum(in_range_mask) / len(dataset)
        print(f"  P(x ∈ R) = {p:.3f}")
        probabilities.append(p)
    
    return probabilities


def evaluate_result(result: List[int], expected: List[int], query_type: str) -> Dict[str, Any]:
    """Evaluate query result against ground truth."""
    result_set = set(result)
    expected_set = set(expected)
    
    correct = expected_set == result_set
    precision = len(expected_set & result_set) / len(result_set) if result_set else 1.0
    recall = len(expected_set & result_set) / len(expected_set) if expected_set else 1.0
    
    return {
        "query_type": query_type,
        "ground_truth": list(expected_set),
        "result": result,
        "correct": correct,
        "precision": precision,
        "recall": recall
    }


def test_threshold_query():
    """Test threshold query with 1D data."""
    print("=== Testing Threshold Query (1D) ===")
    
    # Create test data
    synopses = create_simple_1d_histograms()
    print(f"Created {len(synopses)} 1D synopses")
    
    # Parameters
    epsilon = 0
    phi = 0.1
    delta = 0
    d = 1
    
    # Query
    R_min = np.array([3])
    R_max = np.array([8])
    theta = (0.2, 1.0)  # threshold ≥ 0.2
    
    print(f"Query: [{R_min[0]}, {R_max[0]}], threshold ≥ {theta[0]}")
    print(f"Parameters: ε={epsilon}, φ={phi}, δ={delta}")
    
    try:
        # Calculate ground truth
        true_probs = calculate_ground_truth_probabilities(synopses, R_min, R_max)
        expected = [i for i, p in enumerate(true_probs) if p >= theta[0]]
        print(f"Expected datasets: {expected}")
        
        # Build tree and query
        T = construct_T_threshold(synopses, epsilon, phi, d)
        R_prime = compute_R_prime_threshold(R_min, R_max)
        result = query_T_threshold(T, R_prime, theta, epsilon, delta)
        
        # Evaluate
        evaluation = evaluate_result(result, expected, "threshold")
        status = "✅ PASS" if evaluation["correct"] else "❌ FAIL"
        print(f"Result: {result} - {status}")
        
        return evaluation["correct"]
        
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_range_query():
    """Test range query with 1D data."""
    print("\n=== Testing Range Query (1D) ===")
    
    # Create test data
    synopses = create_simple_1d_histograms()
    print(f"Created {len(synopses)} 1D synopses")
    
    # Parameters
    epsilon = 0
    phi = 0.1
    delta = 0
    d = 1
    
    # Query
    R_min = np.array([3])
    R_max = np.array([8])
    theta = (0.2, 0.4)  # range [0.2, 0.4]
    
    print(f"Query: [{R_min[0]}, {R_max[0]}], range [{theta[0]}, {theta[1]}]")
    print(f"Parameters: ε={epsilon}, φ={phi}, δ={delta}")
    
    try:
        # Calculate ground truth
        true_probs = calculate_ground_truth_probabilities(synopses, R_min, R_max)
        expected = [i for i, p in enumerate(true_probs) if theta[0] <= p <= theta[1]]
        print(f"Expected datasets: {expected}")
        
        # Build tree and query
        T = construct_T_range(synopses, epsilon, phi, d)
        result = query_T_range(T, R_min, R_max, theta, epsilon, delta, synopses)
        
        # Evaluate
        evaluation = evaluate_result(result, expected, "range")
        status = "✅ PASS" if evaluation["correct"] else "❌ FAIL"
        print(f"Result: {result} - {status}")
        
        return evaluation["correct"]
        
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_multiple_queries():
    """Test multiple queries to verify algorithm performance."""
    print("\n=== Testing Multiple Queries ===")
    
    # Create test data
    synopses = create_simple_1d_histograms()
    
    # Parameters
    epsilon = 0
    phi = 0.1
    delta = 0
    d = 1
    
    # Test queries
    test_queries = [
        {
            "name": "Threshold [2,5] ≥ 0.3",
            "R_min": np.array([2]),
            "R_max": np.array([5]),
            "theta": (0.3, 1.0),
            "type": "threshold"
        },
        {
            "name": "Range [6,10] ∈ [0.2,0.8]",
            "R_min": np.array([6]),
            "R_max": np.array([10]),
            "theta": (0.2, 0.8),
            "type": "range"
        },
        {
            "name": "Threshold [1,3] ≥ 0.5",
            "R_min": np.array([1]),
            "R_max": np.array([3]),
            "theta": (0.5, 1.0),
            "type": "threshold"
        }
    ]
    
    results = []
    
    for query in test_queries:
        print(f"\n--- {query['name']} ---")
        
        try:
            # Calculate ground truth
            true_probs = calculate_ground_truth_probabilities(synopses, query["R_min"], query["R_max"])
            
            if query["type"] == "threshold":
                expected = [i for i, p in enumerate(true_probs) if p >= query["theta"][0]]
                T = construct_T_threshold(synopses, epsilon, phi, d)
                R_prime = compute_R_prime_threshold(query["R_min"], query["R_max"])
                result = query_T_threshold(T, R_prime, query["theta"], epsilon, delta)
            else:  # range
                expected = [i for i, p in enumerate(true_probs) if query["theta"][0] <= p <= query["theta"][1]]
                T = construct_T_range(synopses, epsilon, phi, d)
                result = query_T_range(T, query["R_min"], query["R_max"], query["theta"], epsilon, delta, synopses)
            
            evaluation = evaluate_result(result, expected, query["type"])
            results.append(evaluation)
            
            status = "✅ PASS" if evaluation["correct"] else "❌ FAIL"
            print(f"Result: {result}, Expected: {expected} - {status}")
            
        except Exception as e:
            print(f"Error: {e}")
            results.append({"correct": False})
    
    # Summary
    passed = sum(1 for r in results if r["correct"])
    total = len(results)
    print(f"\nSummary: {passed}/{total} queries passed ({passed/total*100:.1f}%)")


def main():
    """Main test function."""
    print("Enhanced 1D Ptile Implementation Test")
    print("=" * 50)
    
    # Test individual queries
    threshold_success = test_threshold_query()
    range_success = test_range_query()
    
    # Test multiple queries
    test_multiple_queries()
    
    print("\n" + "=" * 50)
    print("FINAL SUMMARY")
    print("=" * 50)
    print(f"Threshold query: {'✅ PASS' if threshold_success else '❌ FAIL'}")
    print(f"Range query: {'✅ PASS' if range_success else '❌ FAIL'}")
    
    if threshold_success and range_success:
        print("\n🎉 All basic tests passed! Your P-tile implementation is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
    
    print("\nTest complete!")


if __name__ == "__main__":
    main() 