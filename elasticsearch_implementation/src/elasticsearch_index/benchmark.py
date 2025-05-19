import matplotlib.pyplot as plt
from .elastic_indexer import ElasticIndexer

class ElasticBenchmark:
    """
    Benchmark class to measure performance of different indexing approaches.
    """
    def __init__(self):
        pass
    
    def run_benchmark(self, dataset_models, queries, max_datasets=100, step=10):
        """
        Benchmark both approaches (full dataset and summary) and plot the results.
        
        Args:
            dataset_models (dict): Dictionary of dataset models
            queries (list): List of keywords to search for
            max_datasets (int): Maximum number of datasets to use
            step (int): Step size for increasing the number of datasets
            
        Returns:
            tuple: (full_times, summary_times, full_sizes, summary_sizes)
        """
        full_times = []
        summary_times = []
        full_sizes = []
        summary_sizes = []
        
        # Convert dict to list and limit to max_datasets
        datasets = list(dataset_models.values())[:max_datasets]
        
        # Create searchers for both approaches
        full_indexer = ElasticIndexer(use_summaries=False)
        summary_indexer = ElasticIndexer(use_summaries=True)
        
        # Clear indices to start fresh
        full_indexer.clear_indices()
        summary_indexer.clear_indices()
        
        dataset_counts = range(step, len(datasets) + 1, step)
        
        for count in dataset_counts:
            print(f"Benchmarking with {count} datasets...")
            
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
            
            # Clear indices for next iteration
            full_indexer.clear_indices()
            summary_indexer.clear_indices()
        
        # Plot results
        self.plot_results(dataset_counts, full_times, summary_times, full_sizes, summary_sizes)
        
        return full_times, summary_times, full_sizes, summary_sizes
    
    def plot_results(self, dataset_counts, full_times, summary_times, full_sizes, summary_sizes):
        """
        Plot the benchmarking results.
        
        Args:
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
        ax1.plot(dataset_counts, full_times, 'bo-', label='Full Dataset (Di, Mi)')
        ax1.plot(dataset_counts, summary_times, 'ro-', label='Summary (Si, Mi)')
        ax1.set_xlabel('Number of Datasets')
        ax1.set_ylabel('Average Query Time (seconds)')
        ax1.set_title('Query Time vs Number of Datasets')
        ax1.legend()
        ax1.grid(True)
        
        # Plot query time vs index size
        ax2.plot(full_sizes_mb, full_times, 'bo-', label='Full Dataset (Di, Mi)')
        ax2.plot(summary_sizes_mb, summary_times, 'ro-', label='Summary (Si, Mi)')
        ax2.set_xlabel('Index Size (MB)')
        ax2.set_ylabel('Average Query Time (seconds)')
        ax2.set_title('Query Time vs Index Size')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig('seeker_query_performance.png')
        plt.show()
