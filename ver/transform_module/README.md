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

## QueryFilter
The `QueryFilter` class is designed to filter and group queries based on their transformed results. It uses the `Transform` classes to apply transformations and groups queries that produce the same transformed results.

### Features
- **Duplicate Removal**: Filters out duplicate queries based on their transformed results.
- **Query Grouping**: Groups queries that transform into the same results and assigns them a unique group ID.
- **Graph Generation**: Creates a graph-like structure using `networkx` to visualize the relationships between queries and their groups.

### Example Usage
```python
from transform_module.query_filter import QueryFilter
from transform_module.transform import DateTransform
from qbe_module.query_by_example import ExampleColumn
import networkx as nx
import matplotlib.pyplot as plt

# Example queries
queries = [
    ExampleColumn(attr="1", examples=["example1"]),
    ExampleColumn(attr="January", examples=["example2"]),
    ExampleColumn(attr="Jan", examples=["example3"]),
]

# Apply DateTransform
date_transform = DateTransform()
query_filter = QueryFilter(date_transform, queries)

# Filter queries and generate graph
query_filter.filter_queries()
graph = query_filter.generate_graph()

# Visualize the graph
nx.draw(graph, with_labels=True, node_color="lightblue", font_weight="bold")
plt.show()