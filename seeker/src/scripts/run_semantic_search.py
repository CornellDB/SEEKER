from ..index_creation.dataset_model import DatasetModel
from ..seeker_service_modules.search_module import DataSeeker
import pandas as pd

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
    print("Searching in data:")
    result_data = data_seeker.semantic_search(datasets, query, search_in_metadata=False)

    # Search in metadata
    print("\nSearching in metadata:")
    result_metadata = data_seeker.semantic_search(datasets, query, search_in_metadata=True)

