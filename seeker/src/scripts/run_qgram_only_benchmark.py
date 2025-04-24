import pandas as pd
import time
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

from seeker.src.index_creation import DatasetModel
from seeker.src.metadata_dataset_separation import DataLoader
from seeker.src.qgram_index.qgram_indexer import QgramIndexer

def compare_qgram_methods(dataset_models, queries, q_values=[2, 3, 4]):
    """
    Compare different Q-gram methods.
    
    Args:
        dataset_models (dict): Dictionary of dataset models
        queries (list): List of keywords to search for
        q_values (list): List of q values to test
    """
    results = {}
    
    # Initialize q-gram results
    for q in q_values:
        results[q] = {
            "full": {"times": [], "sizes": []},
            "summary": {"times": [], "sizes": []}
        }
    
    # Create Q-gram indexers
    qgram_indexers = {}
    for q in q_values:
        qgram_indexers[q] = {
            "full": QgramIndexer(use_summaries=False, q=q),
            "summary": QgramIndexer(use_summaries=True, q=q)
        }
    
    # Ingest datasets
    print("Ingesting datasets into Q-gram indices...")
    for q in q_values:
        for name, model in dataset_models.items():
            qgram_indexers[q]["full"].ingest(model)
            qgram_indexers[q]["summary"].ingest(model)
    
    # Measure Q-gram query times
    print("Measuring Q-gram query times...")
    for q in q_values:
        qgram_full_times = []
        qgram_summary_times = []
        
        for query in queries:
            # Run query on full dataset index
            _, full_time = qgram_indexers[q]["full"].query(query)
            qgram_full_times.append(full_time)
            
            # Run query on summary index
            _, summary_time = qgram_indexers[q]["summary"].query(query)
            qgram_summary_times.append(summary_time)
        
        # Calculate average query times
        results[q]["full"]["times"] = sum(qgram_full_times) / len(qgram_full_times)
        results[q]["summary"]["times"] = sum(qgram_summary_times) / len(qgram_summary_times)
        
        # Get index sizes
        results[q]["full"]["sizes"] = qgram_indexers[q]["full"].get_index_size()
        results[q]["summary"]["sizes"] = qgram_indexers[q]["summary"].get_index_size()
    
    # Plot results
    plot_comparison(results, q_values)
    
    return results

def plot_comparison(results, q_values):
    """
    Plot comparison of Q-gram methods.
    
    Args:
        results (dict): Dictionary with results
        q_values (list): List of q values that were tested
    """
    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Prepare data for plotting
    methods = []
    query_times = []
    index_sizes = []
    colors = []
    
    # Add Q-gram results
    for q in q_values:
        methods.extend([f"Q{q} Full", f"Q{q} Summary"])
        query_times.extend([
            results[q]["full"]["times"],
            results[q]["summary"]["times"]
        ])
        index_sizes.extend([
            results[q]["full"]["sizes"] / (1024 * 1024),
            results[q]["summary"]["sizes"] / (1024 * 1024)
        ])
        colors.extend(['darkred', 'salmon'])
    
    # Plot query times
    ax1.bar(range(len(methods)), query_times, color=colors)
    ax1.set_ylabel('Average Query Time (seconds)')
    ax1.set_title('Query Time Comparison')
    ax1.set_xticks(range(len(methods)))
    ax1.set_xticklabels(methods, rotation=45, ha='right')
    ax1.grid(axis='y')
    
    # Plot index sizes
    ax2.bar(range(len(methods)), index_sizes, color=colors)
    ax2.set_ylabel('Index Size (MB)')
    ax2.set_title('Index Size Comparison')
    ax2.set_xticks(range(len(methods)))
    ax2.set_xticklabels(methods, rotation=45, ha='right')
    ax2.grid(axis='y')
    
    plt.tight_layout()
    plt.savefig('seeker_qgram_comparison.png')
    plt.show()

if __name__ == "__main__":
    # Load datasets
    data_loader = DataLoader()
    dataset_models = data_loader.upload_multiple("dataset_examples", include_metadata=True)
    
    # Define queries
    queries = ["house", "price", "real estate", "apartment", "bedroom"]
    
    # Define q values to test
    q_values = [2, 3, 4]
    
    # Run comparison
    print("Running comparison between different Q-gram methods...")
    results = compare_qgram_methods(dataset_models, queries, q_values)
    
    # Print summary
    print("\n=== Performance Comparison Summary ===")
    for q in q_values:
        print(f"\nQ-gram (q={q}) Full Dataset: {results[q]['full']['times']:.6f} seconds, {results[q]['full']['sizes'] / (1024 * 1024):.2f} MB")
        print(f"Q-gram (q={q}) Summary: {results[q]['summary']['times']:.6f} seconds, {results[q]['summary']['sizes'] / (1024 * 1024):.2f} MB")
    
    print("\nResults saved to 'seeker_qgram_comparison.png'")
