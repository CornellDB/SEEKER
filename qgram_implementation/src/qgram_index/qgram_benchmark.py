import matplotlib.pyplot as plt
import numpy as np
from .qgram_indexer import QgramIndexer

class QgramBenchmark:
    """
    Benchmark class to measure performance of different Q-gram approaches.
    """
    def __init__(self):
        pass
    
    def run_benchmark(self, dataset_models, queries, q_values=[2, 3, 4], max_datasets=10, step=1):
        """
        Benchmark Q-gram approaches with different q values and plot the results.
        
        Args:
            dataset_models (dict): Dictionary of dataset models
            queries (list): List of keywords to search for
            q_values (list): List of q values to test
            max_datasets (int): Maximum number of datasets to use
            step (int): Step size for increasing the number of datasets
            
        Returns:
            dict: Dictionary with q values as keys and (times, sizes) tuples as values
        """
        results = {}
        
        # Convert dict to list and limit to max_datasets
        datasets = list(dataset_models.values())[:max_datasets]
        
        dataset_counts = range(step, min(len(datasets) + 1, max_datasets + 1), step)
        
        for q in q_values:
            full_times = []
            summary_times = []
            full_sizes = []
            summary_sizes = []
            
            # Create indexers for both approaches
            full_indexer = QgramIndexer(use_summaries=False, q=q)
            summary_indexer = QgramIndexer(use_summaries=True, q=q)
            
            for count in dataset_counts:
                print(f"Benchmarking with {count} datasets and q={q}...")
                
                # Clear indices to start fresh
                full_indexer.clear_indices()
                summary_indexer.clear_indices()
                
                # Ingest datasets
                for i in range(count):
                    full_indexer.ingest(datasets[i])
                    summary_indexer.ingest(datasets[i])
                
                # Measure query times
                full_query_times = []
                summary_query_times = []
                
                for query in queries:
                    # Run query on full dataset index
                    _, full_time = full_indexer.query(query)
                    full_query_times.append(full_time)
                    
                    # Run query on summary index
                    _, summary_time = summary_indexer.query(query)
                    summary_query_times.append(summary_time)
                
                # Calculate average query times
                avg_full_time = sum(full_query_times) / len(full_query_times)
                avg_summary_time = sum(summary_query_times) / len(summary_query_times)
                
                # Get index sizes
                full_size = full_indexer.get_index_size()
                summary_size = summary_indexer.get_index_size()
                
                # Record results
                full_times.append(avg_full_time)
                summary_times.append(avg_summary_time)
                full_sizes.append(full_size)
                summary_sizes.append(summary_size)
            
            # Store results for this q value
            results[q] = {
                "full_times": full_times,
                "summary_times": summary_times,
                "full_sizes": full_sizes,
                "summary_sizes": summary_sizes,
                "dataset_counts": list(dataset_counts)
            }
            
            # Plot results for this q value
            self.plot_results(q, dataset_counts, full_times, summary_times, full_sizes, summary_sizes)
        
        # Plot comparison across q values
        self.plot_comparison(results, dataset_counts)
        
        return results
    
    def plot_results(self, q, dataset_counts, full_times, summary_times, full_sizes, summary_sizes):
        """
        Plot the benchmarking results for a specific q value.
        
        Args:
            q (int): Q-gram size
            dataset_counts (list): List of dataset counts
            full_times (list): List of query times for full dataset approach
            summary_times (list): List of query times for summary approach
            full_sizes (list): List of index sizes for full dataset approach
            summary_sizes (list): List of index sizes for summary approach
        """
        # Convert sizes to MB for better readability
        full_sizes_mb = [size / (1024 * 1024) for size in full_sizes]
        summary_sizes_mb = [size / (1024 * 1024) for size in summary_sizes]
        
        # Create figure with 2 subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot query time vs dataset count
        ax1.plot(dataset_counts, full_times, 'bo-', label=f'Full Dataset (Di, Mi), q={q}')
        ax1.plot(dataset_counts, summary_times, 'ro-', label=f'Summary (Si, Mi), q={q}')
        ax1.set_xlabel('Number of Datasets')
        ax1.set_ylabel('Average Query Time (seconds)')
        ax1.set_title(f'Query Time vs Number of Datasets (q={q})')
        ax1.legend()
        ax1.grid(True)
        ax1.set_xlim(left=0)  # Force positive x-axis
        ax1.set_ylim(bottom=0)  # Force positive y-axis
        
        # Plot query time vs index size
        ax2.plot(full_sizes_mb, full_times, 'bo-', label=f'Full Dataset (Di, Mi), q={q}')
        ax2.plot(summary_sizes_mb, summary_times, 'ro-', label=f'Summary (Si, Mi), q={q}')
        ax2.set_xlabel('Index Size (MB)')
        ax2.set_ylabel('Average Query Time (seconds)')
        ax2.set_title(f'Query Time vs Index Size (q={q})')
        ax2.legend()
        ax2.grid(True)
        ax2.set_xlim(left=0)  # Force positive x-axis
        ax2.set_ylim(bottom=0)  # Force positive y-axis
        
        plt.tight_layout()
        plt.savefig(f'seeker_qgram_performance_q{q}.png')
        plt.close()
    
    def plot_comparison(self, results, dataset_counts):
        """
        Plot comparison of different q values.
        
        Args:
            results (dict): Dictionary with q values as keys and results as values
            dataset_counts (list): List of dataset counts
        """
        # Create figure with 2 subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Colors for different q values
        colors = ['b', 'r', 'g', 'c', 'm', 'y', 'k']
        
        # Plot query time vs dataset count for full dataset
        for i, (q, data) in enumerate(results.items()):
            color = colors[i % len(colors)]
            ax1.plot(data["dataset_counts"], data["full_times"], f'{color}o-', label=f'q={q}, Full Dataset')
            ax1.plot(data["dataset_counts"], data["summary_times"], f'{color}x--', label=f'q={q}, Summary')
        
        ax1.set_xlabel('Number of Datasets')
        ax1.set_ylabel('Average Query Time (seconds)')
        ax1.set_title('Query Time vs Number of Datasets (All q values)')
        ax1.legend()
        ax1.grid(True)
        ax1.set_xlim(left=0)  # Force positive x-axis
        ax1.set_ylim(bottom=0)  # Force positive y-axis
        
        # Plot index size vs q value for maximum dataset count
        q_values = list(results.keys())
        full_sizes = [results[q]["full_sizes"][-1] / (1024 * 1024) for q in q_values]
        summary_sizes = [results[q]["summary_sizes"][-1] / (1024 * 1024) for q in q_values]
        
        ax2.bar(np.array(q_values) - 0.2, full_sizes, width=0.4, label='Full Dataset (Di, Mi)')
        ax2.bar(np.array(q_values) + 0.2, summary_sizes, width=0.4, label='Summary (Si, Mi)')
        ax2.set_xlabel('Q-gram Size')
        ax2.set_ylabel('Index Size (MB)')
        ax2.set_title(f'Index Size vs Q-gram Size (for {max(dataset_counts)} datasets)')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig('seeker_qgram_comparison.png')
        plt.close()
