import pandas as pd
import sys
import os

from seeker.src.index_creation import DatasetModel
from seeker.src.metadata_dataset_separation import DataLoader
from seeker.src.elasticsearch_index import ElasticBenchmark

if __name__ == "__main__":
    # Load datasets
    data_loader = DataLoader()
    dataset_models = data_loader.upload_multiple("dataset_examples", include_metadata=True)
    
    # Define benchmark queries
    benchmark_queries = ["house", "price", "real estate", "apartment", "bedroom"]
    
    # Run benchmark
    benchmark = ElasticBenchmark()
    benchmark.run_benchmark(dataset_models, benchmark_queries, max_datasets=3, step=1)
    
    print("Benchmark complete. Results saved to 'seeker_query_performance.png'")

# Run with: python -m seeker.src.scripts.run_elasticsearch_benchmark
