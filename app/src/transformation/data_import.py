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
        
        return dataset, metadata
    
    def upload_multiple(self, folder_path, include_metadata=True):
        datasets = {}
        metadata_files = {}

        for file in os.listdir(folder_path):
            if file.endswith('.csv') and not file.endswith('_metadata.csv'):
                dataset_name = file[:-4]
                dataset, metadata = self.upload(folder_path, dataset_name, include_metadata)
                datasets[dataset_name] = dataset
                
                if include_metadata:
                    metadata_files[dataset_name] = metadata

        return datasets, metadata_files


