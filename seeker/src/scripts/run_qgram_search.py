import pandas as pd
import sys
import os

from seeker.src.index_creation import DatasetModel
from seeker.src.metadata_dataset_separation import DataLoader
from seeker.src.qgram_index.qgram_seeker import QgramSearchSeeker

if __name__ == "__main__":
    # Load datasets
    data_loader = DataLoader()
    dataset_models = data_loader.upload_multiple("dataset_examples", include_metadata=True)
    
    # Define q values to test
    q_values = [2, 3, 4]
    
    for q in q_values:
        # Run search with full dataset indexing
        print(f"\n=== Full Dataset Search (Di, Mi) with q={q} ===")
        full_seeker = QgramSearchSeeker("house price", use_summaries=False, q=q)
        full_results = full_seeker.semantic_search(dataset_models, "house price", False)
        
        # Run search with summary indexing
        print(f"\n=== Summary Search (Si, Mi) with q={q} ===")
        summary_seeker = QgramSearchSeeker("house price", use_summaries=True, q=q)
        summary_results = summary_seeker.semantic_search(dataset_models, "house price", False)
        
        # Compare query times
        if full_results and summary_results:
            full_time = full_results[0].get("query_time", 0)
            summary_time = summary_results[0].get("query_time", 0)
            
            print(f"\n=== Performance Comparison (q={q}) ===")
            print(f"Full Dataset (Di, Mi) Query Time: {full_time:.6f} seconds")
            print(f"Summary (Si, Mi) Query Time: {summary_time:.6f} seconds")
            
            if summary_time < full_time:
                improvement = ((full_time - summary_time) / full_time) * 100
                print(f"Performance Improvement: {improvement:.2f}%")
            else:
                degradation = ((summary_time - full_time) / full_time) * 100
                print(f"Performance Degradation: {degradation:.2f}%")
