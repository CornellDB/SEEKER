
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from seeker.src.index_creation import DatasetModel
from seeker.src.query_processor import QueryProcessorClass
from seeker.src.metadata_dataset_separation import DataLoader

class SEEKER:
    def __init__(self, input_string, dataset_models, search_in_metadata=False):
        self.input_string = input_string
        self.dataset_models = dataset_models
        self.search_in_metadata = search_in_metadata
    def parse_string(self):
        # Dummy implementation of parsing, should be replaced with actual parsing logic
        operations = self.input_string.split(",")
        return operations

    def process(self):
        operations = self.parse_string()
        print(f"Operations: {operations}")
        query_processor = QueryProcessorClass(self.dataset_models, operations, self.search_in_metadata)
        query_processor.build_query_plan()

# Command to run the script
# python -m app.src.interpreter.interpreter

if __name__ == "__main__":

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
    data_loader = DataLoader()
    dataset_models = data_loader.upload_multiple("dataset_examples", include_metadata=True)
    input_string = "semantic:population,vector:economy,cause_and_consequences:climate change"
    search_in_metadata = True
    interpreter = SEEKER(input_string, dataset_models, search_in_metadata)
    interpreter.process()
