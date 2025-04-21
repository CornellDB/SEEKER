# Transform Module

## Overview
The Transform Module is designed to apply various transformations to queries represented as `ExampleColumn` objects. These transformations are useful for generating variations of queries, normalizing data, and improving query matching by handling different formats, synonyms, and representations.

## Features
- **Date Transformations**: Converts numeric representations of months (e.g., "1") into full month names (e.g., "January") or abbreviations (e.g., "Jan").
- **Date Format Transformations**: Converts dates into multiple formats (e.g., `YYYY-MM-DD`, `DD-MM-YYYY`, etc.).
- **Number-to-Word Transformations**: Converts numeric values into their word equivalents (e.g., "1" to "one").
- **Word-to-Number Transformations**: Converts word representations of numbers into numeric values (e.g., "one" to "1").
- **Stemming Transformations**: Reduces words to their root forms using stemming (e.g., "running" to "run").
- **Custom N-Gram Transformations**: Generates n-grams from query attributes for advanced query matching.

## Usage
The module provides a base `Transform` class that can be extended to implement custom transformations. Each transformation class takes a list of `ExampleColumn` objects and applies the specified transformation logic.

### Example
```python
from transform_module.transform import DateTransform
from qbe_module.query_by_example import ExampleColumn

# Example query
queries = [ExampleColumn(attr="1", examples=["example1"])]

# Apply DateTransform
date_transform = DateTransform()
transformed_queries = date_transform.apply_transform(queries)

# Output transformed queries
for query in transformed_queries:
    print(query.attr)