import uuid
import os
import pandas as pd
import json

class DataLoader:
    def __init__(self, path=None):
        self.path = path
    
    def upload(self, folder_path, dataset_name, include_metadata=True):
        dataset_path = os.path.join(folder_path, f"{dataset_name}.csv")
        metadata_path = os.path.join(folder_path, f"{dataset_name}_metadata.json")

        dataset = pd.read_csv(dataset_path)
        
        if include_metadata:
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            else:
                raise FileNotFoundError(f"Metadata file {metadata_path} not found.")
        else:
            metadata = None
        
        dataset_model = DatasetModel(dataset_name, dataset, metadata)
        return dataset_model
    
    def upload_multiple(self, folder_path, include_metadata=True):
        dataset_models = {}

        for file in os.listdir(folder_path):
            if file.endswith('.csv') and not file.endswith('_metadata.csv'):
                dataset_name = file[:-4]
                dataset_model = self.upload(folder_path, dataset_name, include_metadata)
                dataset_models[dataset_name] = dataset_model

        return dataset_models


class DatasetModel:
    def __init__(self, dataset_name, dataset, metadata):
        self.id = str(uuid.uuid4())
        self.name = dataset_name
        self.dataset = dataset
        self.metadata = metadata

    def __repr__(self):
        return f"DatasetModel(id={self.id}, name={self.name})"


# Example usage
if __name__ == "__main__":
    # Now you can import DataSeeker from a.py
    from ..seeker_service_modules.search_module import DataSeeker
    # Initialize the DataLoader with a specific path if needed
    loader = DataLoader()

    # Upload a single dataset and its metadata
    folder_path = 'dataset_examples'
    dataset_name = 'data'
    dataset_model = loader.upload(folder_path, dataset_name, include_metadata=True)
    print("Single Dataset Model:", dataset_model)

    # Upload multiple datasets and their metadata from a folder
    dataset_models = loader.upload_multiple(folder_path, include_metadata=True)
    print("All Dataset Models:", dataset_models)

    # Initialize the DataSeeker
    data_seeker = DataSeeker("Example dataset search")

    # Perform a semantic search
    query = "Housing America"
    search_results = data_seeker.semantic_search(dataset_models, query, search_in_metadata=True)
    print("Semantic Search Results:", search_results)

    search_results_2 = data_seeker.semantic_search(dataset_models, query, search_in_metadata=False)
    print("Semantic Search Results:", search_results_2)

# Command to run the script
# python -m app.src.metadata_dataset_separation.data_import
