from ..seeker_service_modules import DataSeeker
from .qgram_indexer import QgramIndexer
from ..data_visualization.search_visualizer import SearchResultsVisualizer

class QgramSearchSeeker(DataSeeker):
    """
    Extension of DataSeeker that uses Q-grams for indexing and querying.
    """
    def __init__(self, search_query, use_summaries=False, q=2):
        """
        Initialize QgramSearchSeeker.
        
        Args:
            search_query (str): The search query
            use_summaries (bool): Whether to use summaries instead of full datasets
            q (int): Size of the q-grams
        """
        super().__init__(search_query)
        self.indexer = QgramIndexer(use_summaries=use_summaries, q=q)
    
    def index_datasets(self, dataset_models):
        """
        Index the datasets using Q-grams.
        
        Args:
            dataset_models (dict): Dictionary of dataset models
        
        Returns:
            dict: Results of ingestion
        """
        return self.indexer.ingest_multiple(dataset_models)
    
    def semantic_search(self, dataset_models, query, search_in_metadata):
        """
        Perform semantic search using Q-grams.
        
        Args:
            dataset_models (dict): Dictionary of dataset models
            query (str): The search query
            search_in_metadata (bool): Whether to search in metadata
            
        Returns:
            list: List of search results
        """
        # Index datasets if they are not already indexed
        self.index_datasets(dataset_models)
        
        # Perform search
        results, query_time = self.indexer.query(query)
        
        # Format results for SEEKER compatibility
        formatted_results = []
        for result in results:
            dataset_name = result["dataset_name"]
            formatted_result = {
                "dataset_name": dataset_name,
                "score": result["score"],
                "metadata": dataset_models[dataset_name].metadata if dataset_name in dataset_models else None,
                "top_words": {},  # We could add this from the actual result
                "query_time": query_time
            }
            formatted_results.append(formatted_result)
        
        # Display results if there are any matches
        if formatted_results and any(r["score"] > 0 for r in formatted_results):
            visualizer = SearchResultsVisualizer(formatted_results, query)
            visualizer.display()
        else:
            print(f"No results found for search query: '{query}'")
        
        return formatted_results
