from seeker-0.0.0 import (
    DataSeeker,
    DatasetModel,
    DataLoader
)

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
