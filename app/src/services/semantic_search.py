import re
import pandas as pd

class DataSeeker:
    def __init__(self, search_query):
        self.search_query = search_query

    def preprocess_text(self, text):
        # Simple text preprocessing to remove non-alphanumeric characters and convert to lowercase
        text = re.sub(r'\W+', ' ', text)
        return text.lower()

    def get_word_counts(self, df):
        # Convert all data in the DataFrame to lowercase string
        all_text = df.astype(str).apply(lambda x: ' '.join(x), axis=1).str.cat(sep=' ').lower()
        # Preprocess the text
        all_text = self.preprocess_text(all_text)
        # Convert the text to a pandas Series
        words = pd.Series(all_text.split())
        # Get word counts
        return words.value_counts()

    def semantic_search(self, datasets, metadata, query, search_in_metadata=False):
        query_words = self.preprocess_text(query).split()
        dataset_scores = {}

        for dataset_name, dataset_content in datasets.items():
            if search_in_metadata:
                # Combine title and description for searching
                text = self.preprocess_text(metadata[dataset_name].get("title", "") + " " +
                                            metadata[dataset_name].get("description", ""))
                word_counts = pd.Series(text.split()).value_counts()
            else:
                # Get word counts from DataFrame
                word_counts = self.get_word_counts(dataset_content)
            
            score = sum(word_counts.get(word, 0) for word in query_words)
            dataset_scores[dataset_name] = score

        # Sort datasets by score in descending order
        sorted_datasets = sorted(dataset_scores.items(), key=lambda item: item[1], reverse=True)
        return sorted_datasets

    def vector_search(self, datasets, metadata, query):
        # Placeholder for vector search implementation
        # Perform the search using datasets, metadata, and query
        return f"Performing vector search for: '{query}' in content: {self.search_query}"

    def cause_and_consequences_search(self, datasets, metadata, query):
        # Placeholder for cause and consequences search implementation
        # Perform the search using datasets, metadata, and query
        return f"Performing cause and consequences search for: '{query}' in content: {self.search_query}"

    def query_by_example_search(self, datasets, metadata, query):
        # Placeholder for query by example search implementation
        # Perform the search using datasets, metadata, and query
        return f"Performing query by example search for: '{query}' in content: {self.search_query}"
