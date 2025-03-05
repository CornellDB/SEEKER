from qbe_module.query_by_example import ExampleColumn

class Transform:
    def __init__(self, example_column: ExampleColumn, transform_function):
        self.example_column = example_column
        self.transform_function = transform_function

    def apply_transform(self):
        return self.transform_function(self.example_column)
    
