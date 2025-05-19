import pandas as pd
import sys
import os

from seeker.src.index_creation import DatasetModel
from seeker.src.metadata_dataset_separation import DataLoader
from seeker.src.elasticsearch_index.seeker_integration import ElasticSearchSeeker

if __name__ == "__main__":
    # Load datasets
    data_loader = DataLoader()
    dataset_models = data_loader.upload_multiple("dataset_examples", include_metadata=True)
    
    # Run search with full dataset indexing
    print("\n=== Full Dataset Search (Di, Mi) ===")
    full_seeker = ElasticSearchSeeker("house price", use_summaries=False)
    full_results = full_seeker.semantic_search(dataset_models, "house price", False)
    
    # Run search with summary indexing
    print("\n=== Summary Search (Si, Mi) ===")
    summary_seeker = ElasticSearchSeeker("house price", use_summaries=True)
    summary_results = summary_seeker.semantic_search(dataset_models, "house price", False)
    
    # Compare query times
    if full_results and summary_results:
        full_time = full_results[0].get("query_time", 0)
        summary_time = summary_results[0].get("query_time", 0)
        
        print(f"\n=== Performance Comparison ===")
        print(f"Full Dataset (Di, Mi) Query Time: {full_time:.6f} seconds")
        print(f"Summary (Si, Mi) Query Time: {summary_time:.6f} seconds")
        
        if summary_time < full_time:
            improvement = ((full_time - summary_time) / full_time) * 100
            print(f"Performance Improvement: {improvement:.2f}%")
        else:
            degradation = ((summary_time - full_time) / full_time) * 100
            print(f"Performance Degradation: {degradation:.2f}%")

# Run with: python -m seeker.src.scripts.run_elasticsearch_search
