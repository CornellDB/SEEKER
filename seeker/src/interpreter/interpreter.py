
import pandas as pd
import sys
import os

from seeker.src.index_creation import DatasetModel
from seeker.src.query_processor import QueryProcessorClass
from seeker.src.metadata_dataset_separation import DataLoader

class SEEKER:
    def __init__(self, input_string, dataset_models, search_in_metadata):
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

