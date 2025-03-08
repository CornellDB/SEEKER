from typing import List
from qbe_module.query_by_example import ExampleColumn

class Transform:
    def __init__(self, example_columns: List[ExampleColumn], transform_function):
        self.example_columns = example_columns
        self.transform_function = transform_function

    def apply_transform(self):
        new_queries = []
        for column in self.example_columns:
            new_queries += self.transform_function(column)
        
        return self.example_columns + new_queries


class DateTransform(Transform):
    def __init__(self, example_columns: List[ExampleColumn], transform_function=None):
        if transform_function is None:
            transform_function = self.default_date_transform
        super().__init__(example_columns, transform_function)

    def default_date_transform(self, column: ExampleColumn):
        month_map = {
            "1": ["January", "Jan"], 
            "2": ["February", "Feb"],
            "3": ["March", "Mar"],
            "4": ["April", "Apr"],
            "5": ["May"],
            "6": ["June", "Jun"],
            "7": ["July", "Jul"],
            "8": ["August", "Aug"],
            "9": ["September", "Sep"],
            "10": ["October", "Oct"],
            "11": ["November", "Nov"],
            "12": ["December", "Dec"]
        }

        
        if column.attr not in month_map:
            return []
        
        return [ExampleColumn(attr=mm, examples=column.examples) for mm in month_map[column.attr]]
                

