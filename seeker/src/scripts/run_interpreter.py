import pandas as pd
import sys
import os

from seeker.src.index_creation import DatasetModel
from seeker.src.query_processor import QueryProcessorClass
from seeker.src.metadata_dataset_separation import DataLoader
from seeker.src.interpreter import SEEKER

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
    input_string = "semantic:information,semantic:relevant,cause_and_consequences:climate change"
    search_in_metadata = False
    interpreter = SEEKER(input_string, datasets, search_in_metadata)
    interpreter.process()

#Run the script using the following command:
#python -m seeker.src.scripts.run_interpreter