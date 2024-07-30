from ..query_processor.query_processor import QueryProcessorClass
from ..metadata_dataset_separation.data_import import DataLoader
from ..index_creation.dataset_model import DatasetModel
import pandas as pd

class Interpreter:
    def __init__(self, input_string):
        self.input_string = input_string

    def parse_string(self):
        # Dummy implementation of parsing, should be replaced with actual parsing logic
        operations = self.input_string.split(",")
        return operations

    def process(self):
        operations = self.parse_string()
        print(f"Operations: {operations}")
        query_processor = QueryProcessorClass(operations=operations)
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

    input_string = "semantic:population,vector:economy,cause_and_consequences:climate change"
    interpreter = Interpreter(input_string, dataset_models, search_in_metadata)
    interpreter.process()
