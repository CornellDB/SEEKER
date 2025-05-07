# Q-gram Implementation for SEEKER

This folder contains the implementation of Q-gram indexing for the SEEKER system, providing both full dataset (Di, Mi) and summary-based (Si, Mi) approaches with configurable q values.

## Key Components

- `src/qgram_index/qgram_indexer.py`: Core indexing functionality
- `src/qgram_index/qgram_benchmark.py`: Performance measurement
- `src/qgram_index/qgram_seeker.py`: SEEKER system integration
- `src/qgram_index/qgram_interpreter.py`: SEEKER interpreter extension

## Features

- Character-level q-gram indexing (q=2, 3, 4)
- Full dataset and summary-based approaches
- Set-based representation of datasets
- Performance benchmarking tools

## Performance

- Summary-based approach (Si, Mi) provides 2-3× faster query times than full dataset
- Higher q values (q=4) offer better performance but larger indices
- q=3 provides the best balance of performance and storage requirements

See the results folder for visualizations.
