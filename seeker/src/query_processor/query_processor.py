
from seeker.src.seeker_service_modules import DataSeeker
from seeker.src.suna.service import execute_from_cli, SunaDiscoveryResult
class QueryProcessorClass:
    def __init__(self,dataset_models, query, search_in_metadata):
        self.service_modules = {
            "semantic": self.semantic_search,
            "vector": self.vector_search,
            "cause_and_consequences": self.cause_and_consequences_search,
            "query_by_example": self.query_by_example_search,
        }
        self.service_modules.update({
            "suna_discover": self.suna_discover_search
        })
        self.dataset_models = dataset_models
        self.search_query = query
        self.search_in_metadata = search_in_metadata

    def build_query_plan(self):
        for operation in self.search_query:
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
        seeker.semantic_search(self.dataset_models, search_query, self.search_in_metadata)

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

    def suna_discover_search(self, *args):
        try:
            result: SunaDiscoveryResult = execute_from_cli(
                self.dataset_models,
                args,
                search_query="suna_discover",
            )
        except ValueError as exc:
            print(f"Suna discovery error: {exc}")
            return

        findings_df = result.to_dataframe()
        if findings_df.empty:
            print(
                f"Suna discovery completed for dataset '{result.dataset_name}' "
                "with no confounders selected."
            )
        else:
            display_cols = [
                "confounder",
                "mi_drop",
                "bootstrap_quantile",
                "bootstrap_mean",
            ]
            print("Suna discovery findings:")
            print(findings_df[display_cols].to_string(index=False))
        if result.ate is not None:
            print(
                f"Estimated ATE of treatment '{result.treatment}' on outcome "
                f"'{result.outcome}': {result.ate:.4f} "
                f"(std err: {result.ate_std_err:.4f})"
                if result.ate_std_err is not None
                else f"{result.ate:.4f}"
            )
