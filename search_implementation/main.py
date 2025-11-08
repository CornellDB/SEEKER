#!/usr/bin/env python3
"""
Main entry script: Federated percentile query pipeline with multiple Epsilon samplings

Core strategy:
1. User inputs raw dataset (CSV file directory)
2. User inputs query range, determining data dimension
3. Multiple random samplings are performed on all datasets (default 10 times, configurable)
4. After each sampling, a Range Tree is built and a query is executed
5. Early stopping: once an intersection is determined, sampling for that dataset stops immediately
6. Parallelization: multiple samplings of multiple datasets are executed in parallel
7. Returns indices of all intersecting datasets

Usage:
    # Range query (automatically determines dimension)
    python main.py --mode range --data-dir experiments/synthetic_data \
        --query-range 3.0,5.0 --epsilon 0.2 --max-trials 10

    # Multi-dimensional query
    python main.py --mode range --data-dir experiments/synthetic_data \
        --query-range 3.0,5.0,2.0,4.0 --epsilon 0.2 --max-trials 10

    # Threshold query
    python main.py --mode threshold --data-dir experiments/synthetic_data \
        --query-range 3.0,5.0 --threshold 0.2 --max-trials 10
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import argparse
import numpy as np
import pandas as pd
import time
from typing import List, Tuple, Optional, Dict
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

# Import configuration
from config import (
    AlgorithmConfig, QueryConfig, DataConfig, LogConfig,
    get_query_rectangle_1d, print_config, OUTPUT_DIR
)

# Import core modules
from main_algo.data_processing.histograms import (
    Histogram, compute_histogram, load_compressed_histograms
)
from main_algo.execution.Ptilerange import (
    RangeDynamicRangeTree, query_T_range
)
from main_algo.execution.Ptilethreshold import (
    construct_T_threshold, query_T_threshold, query_threshold_with_parallel_sampling, _process_sampling_and_hyperrectangles
)
from main_algo.execution.setups4threshold import (
    compute_R_prime_threshold,
    weighted_random_sampling_from_histogram,
    compute_weights_for_hyperrectangles,
    generate_hyperrectangles_auto
)
from main_algo.execution.setups4range import (
    compute_global_bounding_box,
    project_to_bounding_box,
    generate_combinatorial_rectangles
)
from main_algo.execution.maximalpair4range import (
    generate_pair_for_range_predicate_sweep_line,
    generate_pair_for_range_predicate_brute_force
)


class FederatedPtilePipeline:
    """Federated Percentile Query Pipeline (supports multiple epsilon samplings)"""

    def __init__(
        self,
        epsilon: float = None,
        phi: float = None,
        delta: float = None,
        d: int = None,
        max_trials: int = 10,
        use_sweep_line: bool = None,
        seed: int = None,
        verbose: bool = True
    ):
        """
        Initializes the Pipeline

        Args:
            epsilon: ε-approximation parameter (None uses default config, recommended 0.2 for nD data)
            phi: φ parameter
            delta: δ parameter
            d: Data dimension (automatically determined from query range)
            max_trials: Maximum number of sampling trials (default 10)
            use_sweep_line: Whether to use sweep line algorithm
            seed: Random seed
            verbose: Whether to print detailed information
        """
        self.epsilon = epsilon if epsilon is not None else AlgorithmConfig.EPSILON
        self.phi = phi or AlgorithmConfig.PHI
        self.delta = delta or AlgorithmConfig.DELTA
        self.d = d or AlgorithmConfig.DIMENSION
        self.max_trials = max_trials  # Default changed to 10
        self.use_sweep_line = use_sweep_line if use_sweep_line is not None else AlgorithmConfig.USE_SWEEP_LINE
        self.seed = seed or AlgorithmConfig.RANDOM_SEED
        self.verbose = verbose

        self.synopses = None
        self.threshold_tree = None

        # Calculate number of datasets
        self.n_datasets = 0

        if self.verbose:
            self._print_header()
    
    def _print_header(self):
        """Prints Pipeline header information"""
        print("\n" + "="*80)
        print("  Federated Percentile Query Pipeline")
        print("  Parallelized Multiple Epsilon Sampling Strategy")
        print("="*80)
        print(f"  Epsilon (ε): {self.epsilon}")
        print(f"  Samples per trial: {int(1/self.epsilon**2)} points")
        print(f"  Max sampling trials: {self.max_trials}")
        print(f"  Phi (φ): {self.phi}")
        print(f"  Delta (δ): {self.delta}")
        print(f"  Dimension: {self.d}D")
        print(f"  Sweep line algorithm: {'Enabled' if self.use_sweep_line else 'Disabled'}")
        print(f"  Random seed: {self.seed}")
        print("="*80 + "\n")
    
    def load_data_from_csv(
        self,
        csv_files: List[str],
        convert_to_histogram: bool = True
    ) -> List[Tuple[np.uint32, Histogram]]:
        """
        Loads data from CSV files
        
        Args:
            csv_files: List of CSV file paths
            convert_to_histogram: Whether to convert to histograms
        
        Returns:
            List of synopses or raw data
        """
        if self.verbose:
            print(f"\n[Step 1] Loading data...")
            print(f"  Number of files: {len(csv_files)}")
        
        datasets = []
        for i, csv_file in enumerate(csv_files):
            df = pd.read_csv(csv_file)
            if self.verbose:
                print(f"  Loading {csv_file}: {df.shape[0]} rows")
            
            # Extract first column as data (can be modified as needed)
            if self.d == 1:
                data = df.iloc[:, 0].values
            else:
                data = df.iloc[:, :self.d].values
            
            datasets.append(data)
        
        if convert_to_histogram:
            if self.verbose:
                print(f"\n[Step 2] Converting to histograms...")
            
            synopses = []
            for i, dataset in enumerate(datasets):
                # Create histogram
                if dataset.ndim == 1:
                    hist = np.histogram(dataset, bins='auto', density=False)
                else:
                    # Multi-dimensional data: one histogram per dimension
                    for dim in range(self.d):
                        hist = np.histogram(dataset[:, dim], bins='auto', density=False)
                        synopses.append((np.uint32(len(synopses)), 
                                       (hist[0].astype(np.uint32), hist[1])))
                    continue
                
                synopses.append((np.uint32(i), (hist[0].astype(np.uint32), hist[1])))
            
            self.synopses = synopses
            
            # Calculate number of datasets
            if self.d == 1:
                self.n_datasets = len(synopses)
            else:
                self.n_datasets = len(synopses) // self.d
            
            if self.verbose:
                print(f"  Generated {len(synopses)} histograms")
                print(f"  Number of datasets: {self.n_datasets}")
            
            return synopses
        else:
            return datasets
    
    def load_data_from_histogram(
        self,
        histogram_file: str
    ) -> List[Tuple[np.uint32, Histogram]]:
        """
        Loads from saved histogram file
        
        Args:
            histogram_file: Path to histogram file (.zst format)
        
        Returns:
            List of synopses
        """
        if self.verbose:
            print(f"\n[Step 1] Loading from histogram file...")
            print(f"  File: {histogram_file}")
        
        self.synopses = load_compressed_histograms(histogram_file)
        
        # Calculate number of datasets
        if self.d == 1:
            self.n_datasets = len(self.synopses)
        else:
            self.n_datasets = len(self.synopses) // self.d
        
        if self.verbose:
            print(f"  Loaded {len(self.synopses)} histograms")
            print(f"  Number of datasets: {self.n_datasets}")
        
        return self.synopses
    
    def load_data_from_arrays(
        self,
        datasets: List[np.ndarray],
        convert_to_histogram: bool = True
    ) -> List[Tuple[np.uint32, Histogram]]:
        """
        Loads data from a list of numpy arrays
        
        Args:
            datasets: List of numpy arrays
            convert_to_histogram: Whether to convert to histograms
        
        Returns:
            List of synopses
        """
        if self.verbose:
            print(f"\n[Step 1] Loading from numpy arrays...")
            print(f"  Number of datasets: {len(datasets)}")
        
        if not convert_to_histogram:
            return datasets
        
        if self.verbose:
            print(f"\n[Step 2] Converting to histograms...")
        
        synopses = []
        for i, dataset in enumerate(datasets):
            if self.verbose:
                print(f"  Processing dataset {i}: shape {dataset.shape}")
            
            if dataset.ndim == 1:
                hist = np.histogram(dataset, bins='auto', density=False)
                synopses.append((np.uint32(i), (hist[0].astype(np.uint32), hist[1])))
            else:
                # Multi-dimensional data
                for dim in range(dataset.shape[1]):
                    hist = np.histogram(dataset[:, dim], bins='auto', density=False)
                    synopses.append((np.uint32(len(synopses)), 
                                   (hist[0].astype(np.uint32), hist[1])))
        
        self.synopses = synopses
        
        # Calculate number of datasets
        if self.d == 1:
            self.n_datasets = len(synopses)
        else:
            self.n_datasets = len(synopses) // self.d
        
        if self.verbose:
            print(f"  Generated {len(synopses)} histograms")
            print(f"  Number of datasets: {self.n_datasets}")
        
        return synopses
    
    def build_range_trees(self) -> None:
        """
        Builds Range Tree (for range queries)
        """
        # For range queries, the R-tree is now built dynamically per trial within query_range_with_parallel_sampling.
        # This method is no longer needed for range query setup.
        if self.verbose:
            print("\n[Step 3] Range Tree construction is integrated into the query process, no separate construction needed.")
    
    def build_threshold_tree(self) -> None:
        """
        Builds Threshold Tree (for threshold queries)
        """
        # For threshold queries, the R-tree is now built dynamically per trial within query_threshold_with_parallel_sampling.
        # This method is no longer needed for threshold query setup.
        if self.verbose:
            print("\n[Step 3] Threshold Tree construction is integrated into the query process, no separate construction needed.")

    
    
    @staticmethod
    def _epsilon_sampling_single_dataset_static(dataset_synopses: List, d: int, epsilon: float, seed: int) -> List[np.ndarray]:
        """Performs epsilon sampling for a single dataset (static method, can be used in independent process)"""
        from main_algo.execution.setups4threshold import weighted_random_sampling_from_histogram
        import numpy as np

        n_samples = int(1 / epsilon**2)

        if d == 1:
            # dataset_synopses[0] is (hist_id, Histogram), so extract the Histogram object
            S_i = weighted_random_sampling_from_histogram(dataset_synopses[0][1], n_samples, seed=seed)
            return [S_i]
        else:
            S_multi = []
            for synopsis in dataset_synopses:
                # synopsis is (hist_id, Histogram), so extract the Histogram object
                S_dim = weighted_random_sampling_from_histogram(synopsis[1], n_samples, seed=seed)
                S_multi.append(S_dim)
            S_i = np.column_stack(S_multi)
            return [S_i]

    def _epsilon_sampling_single_dataset(self, dataset_synopses: List, seed: int) -> List[np.ndarray]:
        """Performs epsilon sampling for a single dataset"""
        return self._epsilon_sampling_single_dataset_static(dataset_synopses, self.d, self.epsilon, seed)

    @staticmethod
    def _process_sampling_and_maximal_pairs(dataset_idx: int, R_min: np.ndarray, R_max: np.ndarray,
                                             dataset_synopses: List, d: int, epsilon: float,
                                             delta: float, seed: int, use_sweep_line: bool) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Processes sampling and maximal pair generation for a single dataset (can be run in an independent process)
        """
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent))

        from main_algo.execution.setups4range import (
            compute_global_bounding_box, project_to_bounding_box, generate_combinatorial_rectangles
        )
        from main_algo.execution.maximalpair4range import (
            generate_pair_for_range_predicate_sweep_line, generate_pair_for_range_predicate_brute_force
        )
        from main_algo.execution.setups4threshold import compute_weights_for_hyperrectangles

        # 1. Epsilon sampling (only for this dataset)
        n_samples = int(1 / epsilon**2)
        if d == 1:
            # dataset_synopses[0] is (hist_id, Histogram), so extract the Histogram object
            S_i = weighted_random_sampling_from_histogram(dataset_synopses[0][1], n_samples, seed=seed)
            all_datasets = [S_i]
        else:
            S_multi = []
            for synopsis in dataset_synopses:
                # synopsis is (hist_id, Histogram), so extract the Histogram object
                S_dim = weighted_random_sampling_from_histogram(synopsis[1], n_samples, seed=seed)
                S_multi.append(S_dim)
            S_i = np.column_stack(S_multi)
            all_datasets = [S_i]

        # 2. Compute global bounding box (only for this dataset)
        B_min, B_max = compute_global_bounding_box(all_datasets)

        # 3. Construct maximal pairs for this dataset
        projection_S_i = project_to_bounding_box(all_datasets[0], B_min, B_max)
        R_i = generate_combinatorial_rectangles(all_datasets[0], projection_S_i, d)

        if use_sweep_line:
            maximal_pairs = generate_pair_for_range_predicate_sweep_line(R_i, d)
        else:
            maximal_pairs = generate_pair_for_range_predicate_brute_force(R_i)

        if len(maximal_pairs) == 0:
            return None, None, None

        weights = compute_weights_for_hyperrectangles(all_datasets[0], [rho for rho, rho_hat in maximal_pairs])

        # Prepare R-tree input format
        Qi, Wi, Ii = [], [], []
        for idx, (rho, rho_hat) in enumerate(maximal_pairs):
            q = np.concatenate([
                rho['min_coords'], rho_hat['min_coords'],
                rho['max_coords'], rho_hat['max_coords']
            ])
            Qi.append(q)
            Wi.append(weights[idx])
            Ii.append(dataset_idx)  # Record original dataset index

        return np.array(Qi), np.array(Wi), np.array(Ii)

    def query_range_with_parallel_sampling(
        self,
        R_min: np.ndarray,
        R_max: np.ndarray,
        theta: Optional[Tuple[float, float]] = None
    ) -> Dict:
        """
        Executes Range query using parallelized multiple epsilon sampling strategy

        Strategy:
        1. Process multiple samplings for each dataset in parallel
        2. Each dataset undergoes a maximum of max_trials samplings
        3. Early stopping: once an intersection is determined, sampling for that dataset stops
        4. Returns all intersecting datasets

        Args:
            R_min: Minimum coordinates of the query rectangle
            R_max: Maximum coordinates of the query rectangle
            theta: Weight interval [a_theta, b_theta]

        Returns:
            Result dictionary containing intersecting datasets and statistics
        """
        if self.synopses is None:
            raise ValueError("Please load data first!")

        theta = theta or QueryConfig.DEFAULT_THETA

        if self.verbose:
            print(f"\n{'='*80}")
            print(f"  Starting Parallelized Multiple Sampling Range Query")
            print(f"{'='*80}")
            print(f"  Query Range: {R_min} x {R_max}")
            print(f"  Weight Interval θ: {theta}")
            print(f"  Max sampling trials: {self.max_trials}")
            print(f"{'='*80}\n")

        start_time = time.time()

        # Process each dataset in parallel
        intersecting_datasets = set()
        dataset_first_hit = {}

        if self.verbose:
            print(f"Starting parallel processing for {self.n_datasets} datasets...")

        with ProcessPoolExecutor(max_workers=min(mp.cpu_count(), self.n_datasets)) as executor:
            # Submit all dataset processing tasks

            active_datasets = set(range(self.n_datasets))
            trials_completed = 0

            while active_datasets and trials_completed < self.max_trials:
                trials_completed += 1
                if self.verbose:
                    print(f"\n--- Range Query Trial {trials_completed}/{self.max_trials} ---")
                    print(f"  Active datasets: {sorted(list(active_datasets))}")

                all_maximal_pairs = []
                all_weights = []
                all_dataset_indices = []
                all_synopses_for_trial = []

                futures = {
                    executor.submit(self._process_sampling_and_maximal_pairs, 
                                     dataset_idx, R_min, R_max, 
                                     self.synopses[dataset_idx * self.d:(dataset_idx + 1) * self.d], 
                                     self.d, self.epsilon, self.delta, self.seed + trials_completed + dataset_idx, 
                                     self.use_sweep_line):
                    dataset_idx for dataset_idx in active_datasets
                }

                for future in as_completed(futures):
                    dataset_idx = futures[future]
                    try:
                        Q_i, W_i, I_i = future.result()
                        if Q_i is not None and len(Q_i) > 0:
                            all_maximal_pairs.append(Q_i)
                            all_weights.append(W_i)
                            all_dataset_indices.append(I_i)
                            all_synopses_for_trial.extend(self.synopses[dataset_idx * self.d:(dataset_idx + 1) * self.d])
                    except Exception as exc:
                        print(f'Dataset {dataset_idx} sampling or maximal pair generation failed: {exc}')

                if not all_maximal_pairs:
                    if self.verbose:
                        print("  No maximal pairs generated in this trial. Continuing to next trial.")
                    continue

                # Aggregate all maximal pairs from active datasets into one set for the current trial
                Q_trial = np.concatenate(all_maximal_pairs)
                W_trial = np.concatenate(all_weights)
                I_trial = np.concatenate(all_dataset_indices)

                # Construct a single RangeDynamicRangeTree for this trial
                if self.verbose:
                    print(f"  Building Range Tree for Trial {trials_completed} with {len(Q_trial)} maximal pairs...")
                trial_tree = RangeDynamicRangeTree(self.d)
                trial_tree.insert_maximal_rectangle(Q_trial, W_trial, I_trial)

                # Query the single Range Tree
                if self.verbose:
                    print(f"  Querying Range Tree for Trial {trials_completed}...")
                # Ensure synopses passed to query_T_range is relevant to the data in trial_tree
                # If query_T_range needs global bounds, it should be computed from the *sampled* data in this trial,
                # or the original full synopses, depending on the exact semantic of compute_R_prime_range.
                # For now, pass the original full self.synopses, assuming compute_R_prime_range can handle it.
                current_trial_intersecting_datasets = query_T_range(
                    trial_tree, R_min, R_max, theta, self.epsilon, self.delta, self.synopses
                )

                newly_intersecting = set()
                for ds_idx in current_trial_intersecting_datasets:
                    if ds_idx in active_datasets:
                        newly_intersecting.add(ds_idx)
                        if ds_idx not in dataset_first_hit:
                            dataset_first_hit[ds_idx] = trials_completed
                            intersecting_datasets.add(ds_idx)

                if self.verbose:
                    print(f"  Trial {trials_completed} intersecting datasets: {sorted(list(newly_intersecting))}")

                active_datasets -= newly_intersecting # Remove newly found datasets from active set

                if self.verbose and not active_datasets:
                    print("  All datasets found to be intersecting or no active datasets left. Early stopping.")

        elapsed = time.time() - start_time

        # Summarize results
        # Calculate average first hit trial (as an approximation of total sampling trials)
        avg_first_hit = sum(dataset_first_hit.values()) / len(dataset_first_hit) if dataset_first_hit else 0

        result_summary = {
            'intersecting_datasets': sorted(list(intersecting_datasets)),
            'n_intersecting': len(intersecting_datasets),
            'n_total_datasets': self.n_datasets,
            'total_trials': self.max_trials,  # Parallel query uses max sampling trials
            'max_trials': self.max_trials,
            'dataset_first_hit': dataset_first_hit,
            'epsilon': self.epsilon,
            'samples_per_trial': int(1 / self.epsilon**2),
            'query_range': (R_min.tolist(), R_max.tolist()),
            'elapsed_time': elapsed,
            'avg_time_per_trial': elapsed / self.n_datasets if self.n_datasets > 0 else 0,
            'parallel_query': True  # Mark this as a parallel query
        }

        if self.verbose:
            self._print_query_summary(result_summary)

        return result_summary
    
    def _print_query_summary(self, result: Dict):
        """Prints query result summary"""
        print(f"\n{'='*80}")
        print(f"  Query Results Summary")
        print(f"{'='*80}")
        print(f"  Intersecting datasets: {result['intersecting_datasets']}")
        print(f"  相交数量: {result['n_intersecting']}/{result['n_total_datasets']}")

        # For parallel queries, display different statistics
        if 'total_trials' in result:
            if result.get('parallel_query', False):
                print(f"  Max sampling trials: {result['max_trials']}")
                print(f"  Parallel processing time: {result['elapsed_time']:.2f} seconds")
                if result['dataset_first_hit']:
                    avg_first_hit = sum(result['dataset_first_hit'].values()) / len(result['dataset_first_hit'])
                    print(f"  Average first hit trial: {avg_first_hit:.1f}")
            else:
                print(f"  Total sampling trials: {result['total_trials']}")
                print(f"  Total time elapsed: {result['elapsed_time']:.2f} seconds")
                if 'avg_time_per_trial' in result:
                    print(f"  Average per trial: {result['avg_time_per_trial']:.2f} seconds")

        if result['dataset_first_hit']:
            print(f"\n  First hit trial for each dataset:")
            for dataset_idx in sorted(result['dataset_first_hit'].keys()):
                trial_num = result['dataset_first_hit'][dataset_idx]
                print(f"    Dataset {dataset_idx}: Trial {trial_num}")

        print(f"{'='*80}\n")
    
    def query_range(
        self,
        R_min: np.ndarray,
        R_max: np.ndarray,
        theta: Optional[Tuple[float, float]] = None
    ) -> List[int]:
        """
        Executes Range query (compatible with old interface, internally calls parallelized multiple sampling method)

        Args:
            R_min: Minimum coordinates of the query rectangle
            R_max: Maximum coordinates of the query rectangle
            theta: Weight interval [a_theta, b_theta]

        Returns:
            List of dataset indices that satisfy the conditions
        """
        result_dict = self.query_range_with_parallel_sampling(R_min, R_max, theta)
        return result_dict['intersecting_datasets']

    def save_results(self, results, output_file: str):
        """
        Saves query results
        
        Args:
            results: List or dictionary of results
            output_file: Output filename
        """
        output_path = OUTPUT_DIR / output_file
        
        # If results is a dictionary (multiple sampling results), save directly
        if isinstance(results, dict):
            results['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
        else:
            # If it's a list (single query result), convert to dictionary format
            with open(output_path, 'w') as f:
                json.dump({
                    'results': results,
                    'n_datasets': len(results),
                    'epsilon': self.epsilon,
                    'phi': self.phi,
                    'delta': self.delta,
                    'dimension': self.d,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }, f, indent=2)
        
        if self.verbose:
            print(f"\n✅ Results saved to: {output_path}")


def parse_args():
    """Parses command line arguments"""
    parser = argparse.ArgumentParser(
        description="Federated Percentile Query Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 1D Range query (automatically determines dimension)
  python main.py --mode range --data-dir experiments/synthetic_data \
      --query-range 3.0,5.0 --epsilon 0.2 --max-trials 10

  # 2D Range query
  python main.py --mode range --data-dir experiments/synthetic_data \
      --query-range 3.0,5.0,2.0,4.0 --epsilon 0.2 --max-trials 10

  # Threshold query
  python main.py --mode threshold --data-dir experiments/synthetic_data \
      --query-range 3.0,5.0 --threshold 0.2 --max-trials 10
        """
    )

    # Query mode
    parser.add_argument('--mode', type=str, choices=['range', 'threshold'], required=True,
                       help='Query mode: range or threshold')

    # Data input (only directory input supported)
    parser.add_argument('--data-dir', type=str, required=True,
                       help='Directory containing CSV files')

    # Query parameters (modified to range input)
    parser.add_argument('--query-range', type=str, required=True,
                       help='Query range, format: min1,max1,min2,max2,... (comma-separated)')

    # Threshold query specific parameters
    parser.add_argument('--threshold', type=float, default=0.2,
                       help='Threshold value (threshold mode only)')
    parser.add_argument('--theta-min', type=float, default=0.1,
                       help='Minimum weight interval (range mode only)')
    parser.add_argument('--theta-max', type=float, default=0.9,
                       help='Maximum weight interval (range mode only)')

    # Algorithm parameters
    parser.add_argument('--epsilon', type=float, default=0.258,
                       help='Epsilon parameter (default adjusts by dimension: 1D=0.1(100 points), 2D=0.224(20 points), 3D=0.258(15 points))')
    parser.add_argument('--max-trials', type=int, default=10,
                       help='Maximum sampling trials (default: 10)')
    parser.add_argument('--phi', type=float, default=0.01,
                       help='phi parameter (default: 0.01)')
    parser.add_argument('--delta', type=float, default=0.01,
                       help='delta parameter (default: 0.01)')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed (default: 42)')
    parser.add_argument('--no-sweep-line', action='store_true',
                       help='Disable sweep line algorithm')

    # Output options
    parser.add_argument('--output', type=str, default='results.json',
                       help='Output filename')
    parser.add_argument('--quiet', action='store_true',
                       help='Quiet mode')

    return parser.parse_args()


def main():
    """Main function"""
    args = parse_args()

    # Parse query range and determine dimension
    try:
        query_values = [float(x.strip()) for x in args.query_range.split(',')]
        if len(query_values) % 2 != 0:
            raise ValueError("Query range must have an even number of values (min,max pairs)")

        d = len(query_values) // 2
        R_min = np.array(query_values[::2])   # Even indices: min values
        R_max = np.array(query_values[1::2])  # Odd indices: max values

        print(f"Detected {d}D data, query range: {R_min} x {R_max}")

        # Set epsilon based on dimension (if not specified by user)
        if args.epsilon == 0.258:  # If default value is used, adjust based on dimension
            if d == 1:
                epsilon = 0.1  # Corresponds to 100 samples
                print(f"1D data, using epsilon={epsilon} (approximately 100 samples)")
            elif d == 2:
                epsilon = 0.2236  # Corresponds to 20 samples
                print(f"2D data, using epsilon={epsilon} (approximately 20 samples)")
            elif d == 3:
                epsilon = 0.258  # Corresponds to 15 samples
                print(f"3D data, using epsilon={epsilon} (approximately 15 samples)")
            else:
                epsilon = args.epsilon
                print(f"{d}D data, using specified epsilon={epsilon}")
        else:
            epsilon = args.epsilon
            print(f"Using user-specified epsilon={epsilon}")

    except ValueError as e:
        print(f"Query range format error: {e}")
        print("Format should be: min1,max1,min2,max2,... (comma-separated)")
        sys.exit(1)

    # Initialize Pipeline
    pipeline = FederatedPtilePipeline(
        epsilon=epsilon,
        phi=args.phi,
        delta=args.delta,
        d=d,  # Use detected dimension
        max_trials=args.max_trials,
        use_sweep_line=not args.no_sweep_line,
        seed=args.seed,
        verbose=not args.quiet
    )

    try:
        # Load data (only directory input supported)
        data_path = Path(args.data_dir)
        csv_files = sorted(data_path.glob('*.csv'))
        if not csv_files:
            raise ValueError(f"No CSV files found in {args.data_dir}")
        pipeline.load_data_from_csv([str(f) for f in csv_files])

        # Execute query
        if args.mode == 'range':
            # Range query: using parallelized multiple epsilon sampling strategy
            theta = (args.theta_min, args.theta_max)
            results = pipeline.query_range_with_parallel_sampling(R_min, R_max, theta)
        else:
            # Threshold query: using parallelized multiple epsilon sampling strategy
            results = query_threshold_with_parallel_sampling(
                pipeline.synopses,
                pipeline.n_datasets,
                R_min, R_max,
                args.threshold,
                pipeline.epsilon,
                pipeline.delta,
                pipeline.d,
                pipeline.max_trials,
                pipeline.seed,
                pipeline.verbose
            )

        # Save results
        pipeline.save_results(results, args.output)

        print("\n✅ Pipeline execution successful!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


