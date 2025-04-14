from typing import List
from qbe_module.query_by_example import ExampleColumn
from transform import Transform

class QueryFilter:
    def __init__(self, transform: Transform):
        self.transform = transform

    def filter_queries(self, queries: List[ExampleColumn]):
        unique_queries = set()
        filtered_queries = []

        for query in queries:
            transformed_queries = self.transform.apply_transform()
            
