import pandas as pd

class SearchResultsVisualizer:
    def __init__(self, search_results, search_query):
        self.search_results = search_results
        self.search_query = search_query

    def display(self):
        print("-" * 12, "Search Results", "-" * 12)
        for result in self.search_results:
            print(f"Dataset: {result['dataset_name']} for search query: '{self.search_query}'")
            print(f"Score: {result['score']}")
            if result['top_words']:
                print("Top Words:")
                for word, count in result['top_words'].items():
                    print(f"  {word}: {count}")
            print("-" * 40)
    
    def to_dataframe(self):
        # Convert the search results to a pandas DataFrame for further analysis or export
        return pd.DataFrame(self.search_results)
