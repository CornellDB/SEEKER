# Federated Percentile Query Pipeline

This project implements a federated percentile query pipeline that supports both range and threshold queries using a multiple epsilon sampling strategy. The core idea is to perform queries on synopses (histograms) of datasets rather than raw data, enhancing privacy and efficiency in a federated learning setting.

## Algorithms

The pipeline leverages advanced spatial data structures and optimized algorithms to efficiently process queries.

### 1. Data Processing (`main_algo/data_processing/`)

*   **`histograms.py`**: This module is responsible for computing and loading histograms from CSV files. These histograms act as compressed representations (synopses) of individual datasets, crucial for the federated setting. It supports 1D and multi-dimensional data, automatically generating histograms per dimension.
*   **`load_german_credit_dataset.py`**: A utility script to download and prepare the German Credit Dataset, which can be used for testing and demonstration purposes.

### 2. Range Query (`main_algo/execution/Ptilerange.py`, `main_algo/execution/maximalpair4range.py`)

The range query algorithm aims to find datasets whose data distribution, represented by maximal pairs (rho, rho_hat), intersects a specified query range within a given weight interval.

*   **Epsilon-Sampling**: A privacy-preserving sampling mechanism is applied to the histograms, generating a sampled representation of each dataset. This is done multiple times in parallel across trials.
*   **Maximal Pair Generation**: From the sampled data, maximal rectangles (pairs of inner and outer bounding boxes `(rho, rho_hat)`) are identified. This process is highly optimized based on data dimensionality:
    *   **Brute-Force**: Used for smaller datasets or very low dimensions.
    *   **Sweep-Line Algorithm**: Highly optimized with Numba for 1D, 2D, and 3D data.
    *   **R-tree Based Method**: Employed for `d >= 4` dimensions, featuring dynamic parameter adjustments for optimal performance.
*   **Dynamic Range Tree (R-tree)**: An R-tree is constructed to efficiently store and query these generated maximal pairs.
*   **Parallelized Multiple Epsilon Sampling Strategy**: The `main.py` script orchestrates this process. It performs multiple sampling trials for each dataset in parallel. An "early stopping" mechanism is implemented, where sampling for a particular dataset ceases once an intersection is confirmed, significantly speeding up the query process.

### 3. Threshold Query (`main_algo/execution/Ptilethreshold.py`)

The threshold query algorithm focuses on identifying datasets where the count of data points within a specified query range exceeds a certain threshold.

*   **Epsilon-Sampling**: Similar to the range query, epsilon-sampling is performed on the histograms.
*   **Hyperrectangle Generation**: Instead of maximal pairs, hyperrectangles (rho) are generated directly from the sampled data.
*   **Dynamic Range Tree (R-tree)**: An R-tree is used to store and query these hyperrectangles.
*   **Parallelized Multiple Epsilon Sampling Strategy**: `main.py` also manages this process in parallel across multiple trials with early stopping. The `query_threshold_with_parallel_sampling` function specifically handles the iterative querying and in-memory removal of matching datasets to adhere to the algorithm's privacy guarantees.

## User-Adjustable Parameters

The project offers extensive configurability through `config.py` and command-line arguments in `main.py`.

### `config.py`

This file defines global parameters for algorithms, queries, data processing, performance, validation, and logging.

*   **`AlgorithmConfig`**:
    *   `EPSILON`: Epsilon approximation parameter (e.g., `0.1`). Smaller values mean higher accuracy but require more samples.
    *   `PHI`: Probability parameter (e.g., `0.01`). Guarantees that with at least `1-phi` probability, the sample is an epsilon+delta-sample of the synopsis.
    *   `DELTA`: Additional error term (e.g., `0.01`).
    *   `DIMENSION`: Default data dimension (e.g., `1`). Can be overridden by query input.
    *   `USE_SWEEP_LINE`: Boolean, whether to use the faster sweep-line algorithm for maximal pair generation.
    *   `RANDOM_SEED`: Seed for reproducibility (e.g., `42`).
*   **`QueryConfig`**:
    *   `DEFAULT_THETA`: Default weight interval `[a_theta, b_theta]` for range queries (e.g., `(0.1, 0.9)`).
    *   `DEFAULT_THRESHOLD`: Default threshold value for threshold queries (e.g., `0.2`).
*   **`DataConfig`**:
    *   `BIN_RANGE`: Tuple `(min_bins, max_bins)` for histogram binning, or `None` for automatic determination.
    *   `COMPUTE_FREQUENCIES`: Boolean, `True` to compute frequencies, `False` for densities.
    *   `SCALING_FACTOR`: Factor to downsample or upsample the dataset.
    *   `ROUNDING_PRECISION`: Decimal places for rounding data values.
*   **`PerformanceConfig`**:
    *   `N_WORKERS`: Number of CPU cores to use for parallel processing.
    *   `CHUNK_SIZE`: Batch processing size (e.g., `1000`).
*   **`ValidationConfig`**:
    *   `N_TRIALS`: Number of validation trials.
    *   `ACCEPTANCE_THRESHOLD`: Accuracy threshold for validation.
    *   `MIN_EPSILON`, `MAX_EPSILON`, `TARGET_ACCURACY`: Parameters for adaptive epsilon selection.
*   **`LogConfig`**:
    *   `LOG_LEVEL`: Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
    *   `LOG_FORMAT`: Log message format.
    *   `ENABLE_FILE_LOG`: Boolean, `True` to enable logging to a file.

### `main.py` (Command-Line Arguments)

The `main.py` script accepts various command-line arguments to control the query execution.

*   `--mode {range,threshold}`: **Required**. Specifies the query type.
*   `--data-dir SRC`: **Required**. Path to the directory containing CSV dataset files.
*   `--query-range min1,max1,min2,max2,...`: **Required**. Comma-separated query range coordinates. For example, `3.0,5.0` for 1D, `3.0,5.0,2.0,4.0` for 2D. The dimension (`d`) is automatically inferred from this input.
*   `--threshold FLOAT`: Threshold value (used only with `--mode threshold`, default: `0.2`).
*   `--theta-min FLOAT`: Minimum weight interval for range queries (used only with `--mode range`, default: `0.1`).
*   `--theta-max FLOAT`: Maximum weight interval for range queries (used only with `--mode range`, default: `0.9`).
*   `--epsilon FLOAT`: Epsilon parameter. Defaults to `0.258`, but automatically adjusts based on inferred dimension if the default is used (e.g., `0.1` for 1D, `0.224` for 2D, `0.258` for 3D).
*   `--max-trials INT`: Maximum number of sampling trials (default: `10`).
*   `--phi FLOAT`: Phi parameter (default: `0.01`).
*   `--delta FLOAT`: Delta parameter (default: `0.01`).
*   `--seed INT`: Random seed for reproducibility (default: `42`).
*   `--no-sweep-line`: Flag to disable the sweep-line algorithm, forcing brute-force maximal pair generation.
*   `--output FILENAME`: Output filename for query results (default: `results.json`).
*   `--quiet`: Flag to suppress verbose output.

## How to Use the Project

The `main.py` script is the primary entry point for executing range and threshold queries.

### 1. Prepare Your Data

Place your CSV dataset files into a directory. Each CSV file is treated as a separate dataset for the federated query. For multi-dimensional data, ensure each row in the CSV represents a data point with `d` features.

### 2. Run a Query

Navigate to the project root directory and execute `main.py` with the desired parameters.

#### Example: 1D Range Query

This example performs a 1D range query on synthetic data located in `experiments/synthetic_data/`, looking for datasets where data points fall between 3.0 and 5.0, with an epsilon of 0.2 and a maximum of 10 sampling trials.

```bash
python main.py --mode range --data-dir experiments/synthetic_data \
    --query-range 3.0,5.0 --epsilon 0.2 --max-trials 10
```

#### Example: Multi-dimensional (2D) Range Query

This example demonstrates a 2D range query, where data points are expected to be within `[3.0, 5.0]` for the first dimension and `[2.0, 4.0]` for the second dimension.

```bash
python main.py --mode range --data-dir experiments/synthetic_data \
    --query-range 3.0,5.0,2.0,4.0 --epsilon 0.2 --max-trials 10
```

#### Example: Threshold Query

This example executes a threshold query on 1D data, looking for datasets where the count of data points within the range `[3.0, 5.0]` exceeds a threshold of 0.2.

```bash
python main.py --mode threshold --data-dir experiments/synthetic_data \
    --query-range 3.0,5.0 --threshold 0.2 --max-trials 10
```

## Usage Case: `test_main_pipeline.py`

The `test_main_pipeline.py` script serves as a comprehensive example and validation suite for the entire pipeline. It demonstrates how to generate synthetic 1D, 2D, and 3D datasets and then run various range and threshold queries against them.

To run the tests and see a full usage example:

```bash
python test_main_pipeline.py
```

This script will:
1.  Create a temporary `test_data` directory.
2.  Generate synthetic 1D, 2D, and 3D CSV datasets within `test_data`.
3.  Execute range queries for 1D, 2D, and 3D datasets.
4.  Execute threshold queries for 1D, 2D, and 3D datasets.
5.  Print detailed results and statistics for each query.
6.  Clean up the `test_data` directory upon completion.

This provides a clear, end-to-end demonstration of the project's capabilities and how different parameters and query types behave.
