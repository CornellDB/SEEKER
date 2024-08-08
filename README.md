# SEEKER: Search Engine for Efficient Knowledge Extraction and Retrieval

SEEKER is an advanced database architecture system built as a Python library, designed to meet diverse data discovery needs through a comprehensive and scalable architecture. This system facilitates seamless integration and querying of multiple datasets, empowering users to derive meaningful insights and knowledge from their data collections. The architecture of SEEKER, ensures high performance, flexibility, and efficiency in various data discovery contexts.

## Key Features

1. **Multi-Dataset Import and Metadata Integration**: SEEKER allows users to import multiple datasets along with their corresponding metadata. This feature enables users to perform comprehensive queries across a selected group of datasets, ensuring a holistic view of the data landscape. By supporting diverse datasets and metadata, SEEKER ensures that users can efficiently manage and query large and complex data collections.

2. **Advanced Query Interpreter**: The core of SEEKER's functionality is its powerful query interpreter, capable of handling multiple types of searches across various datasets. This interpreter not only processes different query types but also provides a scoring mechanism, allowing users to evaluate and rank the relevance of search results. The ability to perform nuanced searches and receive scored results ensures that users can extract precise and valuable insights from their data.

## Design

Documentation on the design of the SEEKER system can be found in the repository's wiki. The following pages are available:

- [Architecture Diagram](https://github.com/CornellDB/SEEKER/wiki/Architecture-Diagram)
- [Architecture Explanation](https://github.com/CornellDB/SEEKER/wiki/Architecture-Explanation)

## Using the Package
To use this package it can be installed using pip just like its shown in the `run_notebook.ipynb`

## Local Development Environment Setup
To make changes inside the package and to upload it again so it can be properly installed you must follow the steps specified here in the [Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/).

The file that is building the wheel and other necessary files for the upload of the package is `setup.py`, it contains all the information about the library and the initial configuration.

You can also run the files inside **seeker/src/scripts/** the command to run them are commented and must be run in the terminal.

## Running functionalities (Notebook)

To make changes and run locally some of the functionalities it's necessary to complete the following steps:

1. Create a virtual environment

   ```shell
   python -m venv venv
   ```

2. Activate the virtual environment

   Unix:

   ```shell
   source venv/bin/activate
   ```

   Windows:

   ```batch
   venv\Scripts\activate.bat
   ```

3. Uncomment all the dependencies under `#Dev` and install dependencies

   ```shell
   pip install -r requirements.txt
   ```

