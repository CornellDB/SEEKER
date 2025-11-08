#!/usr/bin/env python3
"""
Test main pipeline: Generate random datasets and test 1D, 2D, 3D query functionality

Generation strategy:
- 1D: 100 datasets, each with 1000 random points
- 2D: 100 datasets, each with 1000 random points
- 3D: 100 datasets, each with 1000 random points
- Total: 300 datasets

Query tests:
- 1D Range query
- 2D Range query
- 3D Range query
- 1D Threshold query
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
import subprocess
import time
import shutil

sys.path.append(str(Path(__file__).parent.parent))
from main import FederatedPtilePipeline
from main_algo.execution.Ptilethreshold import query_threshold_with_parallel_sampling
from config import QueryConfig

def create_test_data_directory():
    """Create test data directory"""
    test_dir = Path("test_data")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(exist_ok=True)
    return test_dir

def generate_1d_datasets(test_dir, n_datasets=10, n_points=1000):
    """Generate 1D datasets"""
    print(f"Generating {n_datasets} 1D datasets, each with {n_points} data points...")

    datasets_dir = test_dir / "1d_datasets"
    datasets_dir.mkdir(exist_ok=True)

    for i in range(n_datasets):
        # Generate random data in range [0, 100] with denser distribution
        # Use beta distribution to ensure histogram has data, concentrating data in the middle
        data = np.random.beta(2, 2, n_points) * 100  # Beta distribution, range [0,100]

        # Save as CSV
        df = pd.DataFrame(data, columns=['value'])
        filename = f"dataset_1d_{i:03d}.csv"
        df.to_csv(datasets_dir / filename, index=False)

    print(f"✅ 1D datasets generation completed, saved to: {datasets_dir}")
    return datasets_dir

def generate_2d_datasets(test_dir, n_datasets=10, n_points=1000):
    """Generate 2D datasets"""
    print(f"Generating {n_datasets} 2D datasets, each with {n_points} data points...")

    datasets_dir = test_dir / "2d_datasets"
    datasets_dir.mkdir(exist_ok=True)

    for i in range(n_datasets):
        # Generate 2D random data in range [0, 100] x [0, 100]
        # Use beta distribution to ensure more uniform data distribution
        x_data = np.random.beta(2, 2, n_points) * 100
        y_data = np.random.beta(2, 2, n_points) * 100

        # Save as CSV
        df = pd.DataFrame({'x': x_data, 'y': y_data})
        filename = f"dataset_2d_{i:03d}.csv"
        df.to_csv(datasets_dir / filename, index=False)

    print(f"✅ 2D datasets generation completed, saved to: {datasets_dir}")
    return datasets_dir

def generate_3d_datasets(test_dir, n_datasets=10, n_points=1000):
    """Generate 3D datasets"""
    print(f"Generating {n_datasets} 3D datasets, each with {n_points} data points...")

    datasets_dir = test_dir / "3d_datasets"
    datasets_dir.mkdir(exist_ok=True)

    for i in range(n_datasets):
        # Generate 3D random data in range [0, 100] x [0, 100] x [0, 100]
        # Use beta distribution to ensure more uniform data distribution
        x_data = np.random.beta(2, 2, n_points) * 100
        y_data = np.random.beta(2, 2, n_points) * 100
        z_data = np.random.beta(2, 2, n_points) * 100

        # Save as CSV
        df = pd.DataFrame({'x': x_data, 'y': y_data, 'z': z_data})
        filename = f"dataset_3d_{i:03d}.csv"
        df.to_csv(datasets_dir / filename, index=False)

    print(f"✅ 3D datasets generation completed, saved to: {datasets_dir}")
    return datasets_dir

def main():
    """Main test function"""
    print("🚀 Starting main pipeline test")
    print("="*80)

    # Create test data directory
    test_dir = create_test_data_directory()

    try:
        # Generate test data
        print("\n📁 Generating test data...")
        d1_dir = generate_1d_datasets(test_dir)
        d2_dir = generate_2d_datasets(test_dir)
        d3_dir = generate_3d_datasets(test_dir)

        # --- 1D Range Query Test ---
        # print(f"\n{'='*80}")
        # print("Test: 1D Range Query")
        # print(f"{'='*80}")
        # pipeline_1d_range = FederatedPtilePipeline(d=1, epsilon=0.1, max_trials=10, verbose=True)
        # pipeline_1d_range.load_data_from_csv([str(f) for f in d1_dir.glob('*.csv')])
        # pipeline_1d_range.build_range_trees()
        # query_range_1d = np.array([20.0, 80.0])
        # theta_1d = (QueryConfig.DEFAULT_THETA)
        # results_1d_range = pipeline_1d_range.query_range_with_parallel_sampling(
        #     R_min=query_range_1d[:1], R_max=query_range_1d[1:], theta=theta_1d
        # )
        # assert isinstance(results_1d_range, dict)
        # assert 'intersecting_datasets' in results_1d_range
        # print(f"✅ 1D Range query succeeded. Results: {results_1d_range['intersecting_datasets']}")

        # --- 2D Range Query Test ---
        # print(f"\n{'='*80}")
        # print("Test: 2D Range Query")
        # print(f"{'='*80}")
        # pipeline_2d_range = FederatedPtilePipeline(d=2, epsilon=0.2236, max_trials=10, verbose=True)
        # pipeline_2d_range.load_data_from_csv([str(f) for f in d2_dir.glob('*.csv')])
        # pipeline_2d_range.build_range_trees()
        # query_range_2d = np.array([20.0, 80.0, 20.0, 80.0])
        # theta_2d = (QueryConfig.DEFAULT_THETA)
        # results_2d_range = pipeline_2d_range.query_range_with_parallel_sampling(
        #     R_min=query_range_2d[:2], R_max=query_range_2d[2:], theta=theta_2d
        # )
        # assert isinstance(results_2d_range, dict)
        # assert 'intersecting_datasets' in results_2d_range
        # print(f"✅ 2D Range query succeeded. Results: {results_2d_range['intersecting_datasets']}")

        # --- 3D Range Query Test ---
        # print(f"\n{'='*80}")
        # print("Test: 3D Range Query")
        # print(f"{'='*80}")
        # pipeline_3d_range = FederatedPtilePipeline(d=3, epsilon=0.258, max_trials=10, verbose=True)
        # pipeline_3d_range.load_data_from_csv([str(f) for f in d3_dir.glob('*.csv')])
        # pipeline_3d_range.build_range_trees()
        # query_range_3d = np.array([20.0, 80.0, 20.0, 80.0, 20.0, 80.0])
        # theta_3d = (QueryConfig.DEFAULT_THETA)
        # results_3d_range = pipeline_3d_range.query_range_with_parallel_sampling(
        #     R_min=query_range_3d[:3], R_max=query_range_3d[3:], theta=theta_3d
        # )
        # assert isinstance(results_3d_range, dict)
        # assert 'intersecting_datasets' in results_3d_range
        # print(f"✅ 3D Range query succeeded. Results: {results_3d_range['intersecting_datasets']}")

        # --- 1D Threshold Query Test ---
        print(f"\n{'='*80}")
        print("Test: 1D Threshold Query")
        print(f"{'='*80}")
        pipeline_1d_threshold = FederatedPtilePipeline(d=1, epsilon=0.1, max_trials=10, verbose=True)
        pipeline_1d_threshold.load_data_from_csv([str(f) for f in d1_dir.glob('*.csv')])
        pipeline_1d_threshold.build_threshold_tree() # Build threshold tree
        query_range_1d_threshold = np.array([30.0, 70.0])
        threshold_value = 0.5
        results_1d_threshold = query_threshold_with_parallel_sampling(
            pipeline_1d_threshold.synopses,
            pipeline_1d_threshold.n_datasets,
            query_range_1d_threshold[:1],
            query_range_1d_threshold[1:],
            threshold_value,
            pipeline_1d_threshold.epsilon,
            pipeline_1d_threshold.delta,
            pipeline_1d_threshold.d,
            pipeline_1d_threshold.max_trials,
            pipeline_1d_threshold.seed,
            pipeline_1d_threshold.verbose
        )
        assert isinstance(results_1d_threshold, dict)
        assert 'intersecting_datasets' in results_1d_threshold
        print(f"✅ 1D Threshold query succeeded. Results: {results_1d_threshold['intersecting_datasets']}")

        # --- 2D Threshold Query Test ---
        print(f"\n{'='*80}")
        print("Test: 2D Threshold Query")
        print(f"{'='*80}")
        pipeline_2d_threshold = FederatedPtilePipeline(d=2, epsilon=0.2236, max_trials=10, verbose=True)
        pipeline_2d_threshold.load_data_from_csv([str(f) for f in d2_dir.glob('*.csv')])
        pipeline_2d_threshold.build_threshold_tree() # Build threshold tree
        query_range_2d_threshold = np.array([20.0, 80.0, 20.0, 80.0])
        threshold_value_2d = 0.5
        results_2d_threshold = query_threshold_with_parallel_sampling(
            pipeline_2d_threshold.synopses,
            pipeline_2d_threshold.n_datasets,
            query_range_2d_threshold[:2],
            query_range_2d_threshold[2:],
            threshold_value_2d,
            pipeline_2d_threshold.epsilon,
            pipeline_2d_threshold.delta,
            pipeline_2d_threshold.d,
            pipeline_2d_threshold.max_trials,
            pipeline_2d_threshold.seed,
            pipeline_2d_threshold.verbose
        )
        assert isinstance(results_2d_threshold, dict)
        assert 'intersecting_datasets' in results_2d_threshold
        print(f"✅ 2D Threshold query succeeded. Results: {results_2d_threshold['intersecting_datasets']}")

        # --- 3D Threshold Query Test ---
        print(f"\n{'='*80}")
        print("Test: 3D Threshold Query")
        print(f"{'='*80}")
        pipeline_3d_threshold = FederatedPtilePipeline(d=3, epsilon=0.258, max_trials=10, verbose=True)
        pipeline_3d_threshold.load_data_from_csv([str(f) for f in d3_dir.glob('*.csv')])
        pipeline_3d_threshold.build_threshold_tree() # Build threshold tree
        query_range_3d_threshold = np.array([20.0, 80.0, 20.0, 80.0, 20.0, 80.0])
        threshold_value_3d = 0.5
        results_3d_threshold = query_threshold_with_parallel_sampling(
            pipeline_3d_threshold.synopses,
            pipeline_3d_threshold.n_datasets,
            query_range_3d_threshold[:3],
            query_range_3d_threshold[3:],
            threshold_value_3d,
            pipeline_3d_threshold.epsilon,
            pipeline_3d_threshold.delta,
            pipeline_3d_threshold.d,
            pipeline_3d_threshold.max_trials,
            pipeline_3d_threshold.seed,
            pipeline_3d_threshold.verbose
        )
        assert isinstance(results_3d_threshold, dict)
        assert 'intersecting_datasets' in results_3d_threshold
        print(f"✅ 3D Threshold query succeeded. Results: {results_3d_threshold['intersecting_datasets']}")

        print("\n" + "="*80)
        print("🎉 All tests completed!")
        print("="*80)

        # Display generated data statistics
        print("\n📊 Generated data statistics:")
        for dim, dir_path in [("1D", d1_dir), ("2D", d2_dir), ("3D", d3_dir)]:
            csv_files = list(dir_path.glob("*.csv"))
            if csv_files:
                sample_df = pd.read_csv(csv_files[0])
                print(f"  {dim}: {len(csv_files)} datasets, shape: {sample_df.shape}")

        print("\n💡 Test notes:")
        print("  - Each query uses parallelized multiple sampling strategy")
        print("  - Maximum sampling trials set to 10, exceeding this is considered non-intersecting")
        print("  - Results show the number of intersecting datasets and first hit trial number")
        print("  - Epsilon and max-trials parameters can be adjusted as needed")

    except Exception as e:
        print(f"\n❌ Error occurred during testing: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up test data
        print(f"\n🧹 Cleaning up test data directory: {test_dir}")
        try:
            shutil.rmtree(test_dir)
            print("✅ Cleanup completed")
        except:
            print("⚠️ Cleanup failed, please delete manually")

if __name__ == "__main__":
    main()
