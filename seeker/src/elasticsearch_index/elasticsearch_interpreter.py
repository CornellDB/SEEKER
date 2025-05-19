import pandas as pd
import sys
import os

from ..interpreter.interpreter import SEEKER
from ..query_processor import QueryProcessorClass
from .seeker_integration import ElasticSearchSeeker

class ElasticSEEKER(SEEKER):
    """
    Extended SEEKER interpreter with Elasticsearch support.
    """
    def __init__(self, input_string, dataset_models, search_in_metadata, use_elasticsearch=True, use_summaries=False):
        """
        Initialize ElasticSEEKER.
        
        Args:
            input_string (str): The input query string
            dataset_models (dict): Dictionary of dataset models
            search_in_metadata (bool): Whether to search in metadata
            use_elasticsearch (bool): Whether to use Elasticsearch for search
            use_summaries (bool): Whether to use summaries instead of full datasets
        """
        super().__init__(input_string, dataset_models, search_in_metadata)
        self.use_elasticsearch = use_elasticsearch
        self.use_summaries = use_summaries
    
    def process(self):
        """
        Process the input string and execute the search.
        """
        operations = self.parse_string()
        print(f"Operations: {operations}")
        
        if self.use_elasticsearch:
            self._process_with_elasticsearch(operations)
        else:
            # Use the original SEEKER processor
            query_processor = QueryProcessorClass(self.dataset_models, operations, self.search_in_metadata)
            query_processor.build_query_plan()
    
    def _process_with_elasticsearch(self, operations):
        """
        Process operations using Elasticsearch.
        
        Args:
            operations (list): List of operations to perform
        """
        for operation in operations:
            operation_name, *args = operation.split(":")
            
            if operation_name == "semantic":
                search_query = args[0] if args else ""
                seeker = ElasticSearchSeeker(search_query, use_summaries=self.use_summaries)
                seeker.semantic_search(self.dataset_models, search_query, self.search_in_metadata)
            else:
                # For operations not supported by Elasticsearch, fall back to original implementation
                print(f"Operation '{operation_name}' not supported by Elasticsearch, using original implementation")
                temp_operations = [operation]
                query_processor = QueryProcessorClass(self.dataset_models, temp_operations, self.search_in_metadata)
                query_processor.build_query_plan()
