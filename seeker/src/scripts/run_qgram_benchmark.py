import pandas as pd
import sys
import os

from seeker.src.index_creation import DatasetModel
from seeker.src.metadata_dataset_separation import DataLoader
from seeker.src.qgram_index import QgramBenchmark

if __name__ == "__main__":
    # Load datasets
    data_loader = DataLoader()
    dataset_models = data_loader.upload_multiple("dataset_examples", include_metadata=True)
    
    # Define benchmark queries
    benchmark_queries = ["house", "price", "real estate", "apartment", "bedroom"]
    
    # Define q values to test
    q_values = [2, 3, 4]
    
    # Run benchmark
    benchmark = QgramBenchmark()
    results = benchmark.run_benchmark(dataset_models, benchmark_queries, q_values=q_values, max_datasets=10, step=1)
    
    print("Benchmark complete. Results saved to 'seeker_qgram_performance_q*.png' and 'seeker_qgram_comparison.png'")
