import re
import pandas as pd

from .text_processing import TextProcessor
from ..data_visualization.search_visualizer import SearchResultsVisualizer

class DataSeeker:
    def __init__(self, search_query):
        self.search_query = search_query
        self.text_processor = TextProcessor()

    def semantic_search(self, dataset_models, query, search_in_metadata):
        query_words = self.text_processor.preprocess_text(query).split()
        dataset_scores = {}

        for dataset_name, dataset_model in dataset_models.items():
            if search_in_metadata and dataset_model.metadata:
                # Combine title and description for searching
                text = self.text_processor.preprocess_text(dataset_model.metadata.get("title", "") + " " +
                                                           dataset_model.metadata.get("description", ""))
                word_counts = pd.Series(text.split()).value_counts()
            else:
                # Get word counts from DataFrame
                word_counts = self.text_processor.get_word_counts(dataset_model.dataset)
            
            score = sum(word_counts.get(word, 0) for word in query_words)
            dataset_scores[dataset_name] = score

        # Sort datasets by score in descending order
        sorted_datasets = sorted(dataset_scores.items(), key=lambda item: item[1], reverse=True)
        
        # Format the output
        results = []
        for dataset_name, score in sorted_datasets:
            result = {
                "dataset_name": dataset_name,
                "score": score,
                "metadata": dataset_models[dataset_name].metadata if search_in_metadata else None,
                "top_words": self.text_processor.get_word_counts(dataset_models[dataset_name].dataset).head(10).to_dict() if not search_in_metadata else None
            }
            results.append(result)
        
        #Only Visualize the results if the search query is not empty and score is greater than 0
        flag_search_query = False
        for result in results:
            if result["score"] > 0 and query != '':
                visualizer = SearchResultsVisualizer(results, query)
                visualizer.display()
                flag_search_query = True
        
        if not flag_search_query:
            print(f"No results found for search query: '{query}'")
        return results

    def vector_search(self, dataset_models, query):
        # Placeholder for vector search implementation
        # Perform the search using dataset_models and query
        return f"Performing cause and consequences search for: '{query}' in dataset of size: {len(dataset_models)}"

    def cause_and_consequences_search(self, dataset_models, query):
        # Placeholder for cause and consequences search implementation
        # Perform the search using dataset_models and query
        return f"Performing cause and consequences search for: '{query}' in dataset of size: {len(dataset_models)}"

    def query_by_example_search(self, dataset_models, query):
        # Placeholder for query by example search implementation
        # Perform the search using dataset_models and query
        return f"Performing query by example search for: '{query}' in dataset of size: {len(dataset_models)}"


