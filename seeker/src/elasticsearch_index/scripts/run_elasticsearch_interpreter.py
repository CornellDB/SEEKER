import pandas as pd
import sys
import os

from seeker.src.index_creation import DatasetModel
from seeker.src.metadata_dataset_separation import DataLoader
from seeker.src.elasticsearch_index.elasticsearch_interpreter import ElasticSEEKER
from seeker.src.elasticsearch_index import ElasticBenchmark

if __name__ == "__main__":
    # Load datasets
    data_loader = DataLoader()
    dataset_models = data_loader.upload_multiple("dataset_examples", include_metadata=True)
    
    # Define example queries
    example_queries = [
        ("semantic:house,semantic:price,cause_and_consequences:market", False),
        ("semantic:apartment,semantic:rent,cause_and_consequences:location", True)
    ]
    
    # Run queries with different configurations
    for query, search_in_metadata in example_queries:
        print("\n" + "="*50)
        print(f"Query: {query}")
        print(f"Search in metadata: {search_in_metadata}")
        
        # Run with original SEEKER
        print("\n--- Original SEEKER ---")
        original_interpreter = ElasticSEEKER(query, dataset_models, search_in_metadata, use_elasticsearch=False)
        original_interpreter.process()
        
        # Run with Elasticsearch full dataset index
        print("\n--- Elasticsearch (Di, Mi) ---")
        elastic_full_interpreter = ElasticSEEKER(query, dataset_models, search_in_metadata, use_elasticsearch=True, use_summaries=False)
        elastic_full_interpreter.process()
        
        # Run with Elasticsearch summary index
        print("\n--- Elasticsearch (Si, Mi) ---")
        elastic_summary_interpreter = ElasticSEEKER(query, dataset_models, search_in_metadata, use_elasticsearch=True, use_summaries=True)
        elastic_summary_interpreter.process()
    
    # Run benchmark if requested
    run_benchmark = input("\nRun performance benchmark? (y/n): ")
    if run_benchmark.lower() == 'y':
        benchmark_queries = ["house", "price", "real estate", "apartment", "bedroom"]
        benchmark = ElasticBenchmark()
        benchmark.run_benchmark(dataset_models, benchmark_queries, max_datasets=len(dataset_models), step=1)
        print("Benchmark complete. Results saved to 'seeker_query_performance.png'")

# Run with: python -m seeker.src.scripts.run_elasticsearch_interpreter
