from typing import List
from qbe_module.query_by_example import ExampleColumn

class Transform:
    def __init__(self, example_columns: List[ExampleColumn], transform_function):
        self.example_columns = example_columns
        self.transform_function = transform_function

    def apply_transform(self):
        new_queries = []
        for column in self.example_columns:
            new_queries.append(ExampleColumn(attr=self.transform_function(column.attr), examples=column.examples))
        
        return self.example_columns + new_queries


class DateTransform(Transform):
    def __init__(self, example_columns: List[ExampleColumn], transform_function=None):
        if transform_function is None:
            transform_function = self.default_date_transform
        super().__init__(example_columns, transform_function)

    def default_date_transform(self, attr):
        month_map = {
            1: "January",
            2: "February",
            3: "March",
            4: "April",
            5: "May",
            6: "June",
            7: "July",
            8: "August",
            9: "September",
            10: "October",
            11: "November",
            12: "December"
        }
        return month_map.get(attr, attr)

