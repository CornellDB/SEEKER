

class QueryProcessorClass:
    def __init__(self,dataset_models, query, search_in_metadata=False):
        self.service_modules = {
            "semantic": self.semantic_search,
            "vector": self.vector_search,
            "cause_and_consequences": self.cause_and_consequences_search,
            "query_by_example": self.query_by_example_search
        }
        self.dataset_models = dataset_models
        self.search_query = query
        self.search_in_metadata = search_in_metadata

    def build_query_plan(self, operations):
        for operation in operations:
            self.call_service_module(operation)

    def call_service_module(self, operation):
        operation_name, *args = operation.split(":")
        if operation_name in self.service_modules:
            self.service_modules[operation_name](*args)
        else:
            print(f"Unknown operation: {operation_name}")

    def semantic_search(self, *args):
        search_query = args[0] if args else self.search_query
        seeker = DataSeeker(search_query)
        seeker.semantic_search(self.dataset_models, search_query)

    def vector_search(self, *args):
        search_query = args[0] if args else self.search_query
        seeker = DataSeeker(search_query)
        print(seeker.vector_search(self.dataset_models, search_query))

    def cause_and_consequences_search(self, *args):
        search_query = args[0] if args else self.search_query
        seeker = DataSeeker(search_query)
        print(seeker.cause_and_consequences_search(self.dataset_models, search_query))

    def query_by_example_search(self, *args):
        search_query = args[0] if args else self.search_query
        seeker = DataSeeker(search_query)
        print(seeker.query_by_example_search(self.dataset_models, search_query))
