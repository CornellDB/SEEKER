from typing import List
from qbe_module.query_by_example import ExampleColumn
from transform_module.transform import Transform
import networkx as nx

class QueryFilter:
    def __init__(self, transform: Transform, queries: List[ExampleColumn]):
        self.transform = transform
        self.queries = queries
        self.query_to_group_id = {}

    def filter_queries(self):
        unique_transformed = {}
        group_id_counter = 0

        for query in self.queries:
            transformed_queries = self.transform.apply_transform([query])
            transformed_set = frozenset(tq.attr for tq in transformed_queries)
            if transformed_set not in unique_transformed:
                unique_transformed[transformed_set] = group_id_counter
                group_id_counter += 1

            self.query_to_group_id[query.attr] = unique_transformed[transformed_set]

        return list(unique_transformed.keys())

    def generate_graph(self):
        graph = nx.Graph()
        for query, group_id in self.query_to_group_id.items():
            if group_id not in graph:
                graph.add_node(group_id, label=f"Group {group_id}")
            graph.add_edge(group_id, query)
            
        return graph
