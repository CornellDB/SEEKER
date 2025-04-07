from typing import List
from qbe_module.query_by_example import ExampleColumn
from datetime import datetime
import inflect
from nltk.stem import PorterStemmer


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

        transformed_columns = []
        for month in month_map:
            if month in column.attr.split():
                for month_name in month_map[month]:
                    transformed_columns.append(ExampleColumn(attr=month_name, examples=column.examples))
        
        return transformed_columns
                

class DateFormatTransform(Transform):
    def __init__(self, example_columns: List[ExampleColumn], transform_function=None):
        if transform_function is None:
            transform_function = self.default_date_format_transform
        super().__init__(example_columns, transform_function)

    def default_date_format_transform(self, column: ExampleColumn):
        date_formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%m/%d/%Y",
            "%B %d, %Y",
            "%d %B %Y"
        ]

        transformed_columns = []
        for date_format in date_formats:
            for d in column.attr.split():
                try:
                    date_obj = datetime.strptime(d, date_format)
                    for fmt in date_formats:
                        transformed_columns.append(ExampleColumn(attr=date_obj.strftime(fmt), examples=column.examples))
                except ValueError:
                    continue

        return transformed_columns
    
class NumberToWordTransform(Transform):
    def __init__(self, example_columns: List[ExampleColumn], transform_function=None):
        if transform_function is None:
            transform_function = self.default_number_to_word_transform
        super().__init__(example_columns, transform_function)

    def default_number_to_word_transform(self, column: ExampleColumn):
        p = inflect.engine()

        transformed_columns = []
        for d in column.attr.split():
            try:
                num = int(d)
                transformed_columns.append(ExampleColumn(attr=p.number_to_words(num), examples=column.examples))
            except ValueError:
                continue

        return transformed_columns

class WordToNumberTransform(Transform):
    def __init__(self, example_columns: List[ExampleColumn], transform_function=None):
        if transform_function is None:
            transform_function = self.default_word_to_number_transform
        super().__init__(example_columns, transform_function)

    def default_word_to_number_transform(self, column: ExampleColumn):
        p = inflect.engine()
        
        transformed_columns = []
        for d in column.attr.split():
            try:
                num = p.word_to_number(d)
                transformed_columns.append(ExampleColumn(attr=str(num), examples=column.examples))
            except ValueError:
                continue

        return transformed_columns
class StemmingTransform(Transform):
    def __init__(self, example_columns: List[ExampleColumn], transform_function=None):
        if transform_function is None:
            transform_function = self.default_stemming_transform
        super().__init__(example_columns, transform_function)
    
    def default_stemming_transform(self, column: ExampleColumn):
        ps = PorterStemmer()
        transformed_columns = []
        for d in column.attr.split():
            stemmed = ps.stem(d)
            transformed_columns.append(ExampleColumn(attr=stemmed, examples=column.examples))

        return transformed_columns
    