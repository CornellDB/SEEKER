import re
import pandas as pd
from ..index_creation.dataset_model import DatasetModel

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

    def semantic_search(self, dataset_models, query, search_in_metadata=False):
        query_words = self.preprocess_text(query).split()
        dataset_scores = {}

        for dataset_name, dataset_model in dataset_models.items():
            if search_in_metadata and dataset_model.metadata:
                # Combine title and description for searching
                text = self.preprocess_text(dataset_model.metadata.get("title", "") + " " +
                                            dataset_model.metadata.get("description", ""))
                word_counts = pd.Series(text.split()).value_counts()
            else:
                # Get word counts from DataFrame
                word_counts = self.get_word_counts(dataset_model.dataset)
            
            score = sum(word_counts.get(word, 0) for word in query_words)
            dataset_scores[dataset_name] = score

        # Sort datasets by score in descending order
        sorted_datasets = sorted(dataset_scores.items(), key=lambda item: item[1], reverse=True)
        return sorted_datasets

    def vector_search(self, dataset_models, query):
        # Placeholder for vector search implementation
        # Perform the search using dataset_models and query
        return f"Performing vector search for: '{query}' in content: {self.search_query}"

    def cause_and_consequences_search(self, dataset_models, query):
        # Placeholder for cause and consequences search implementation
        # Perform the search using dataset_models and query
        return f"Performing cause and consequences search for: '{query}' in content: {self.search_query}"

    def query_by_example_search(self, dataset_models, query):
        # Placeholder for query by example search implementation
        # Perform the search using dataset_models and query
        return f"Performing query by example search for: '{query}' in content: {self.search_query}"

# Example usage
if __name__ == "__main__":
    # Example dictionaries for dataset models
    datasets = {
        "dataset1": DatasetModel(
            "dataset1", 
            pd.DataFrame({
                'Column1': ['This is an example data set with some relevant information.'],
                'Column2': ['Additional info in dataset 1.']
            }),
            {"title": "Example Dataset 1", "description": "This is a description of example dataset 1."}
        ),
        "dataset2": DatasetModel(
            "dataset2", 
            pd.DataFrame({
                'Column1': ['Another dataset that might be relevant to the search query.'],
                'Column2': ['It contains relevant data and information.']
            }),
            {"title": "Relevant Dataset", "description": "This dataset is relevant to the query."}
        ),
        "dataset3": DatasetModel(
            "dataset3", 
            pd.DataFrame({
                'Column1': ['This dataset does not contain much relevant information.'],
                'Column2': ['Irrelevant data.']
            }),
            {"title": "Irrelevant Dataset", "description": "This dataset is not relevant."}
        )
    }

    data_seeker = DataSeeker("Example dataset search")
    query = "relevant information"

    # Search in data
    result_data = data_seeker.semantic_search(datasets, query, search_in_metadata=False)
    print("Search in data:", result_data)

    # Search in metadata
    result_metadata = data_seeker.semantic_search(datasets, query, search_in_metadata=True)
    print("Search in metadata:", result_metadata)

## Command to run the script
# python -m app.src.seeker_service_modules.search_module