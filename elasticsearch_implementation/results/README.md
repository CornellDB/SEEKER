# Elasticsearch Implementation Results

This folder contains visualizations and performance metrics from the Elasticsearch implementation for SEEKER.

## Visualizations

### seeker_query_performance.png
This visualization compares the query performance between full dataset (Di, Mi) and summary-based (Si, Mi) indexing approaches. The summary approach consistently outperforms the full dataset approach by 5-8×, with significantly smaller index sizes.

Key findings:
- Summary approach maintains consistent performance regardless of dataset count
- Full dataset approach shows performance degradation after 6-7 datasets
- Summary indices are ~25× smaller than full dataset indices

### [Additional Image Descriptions]
[Add descriptions for each additional image you've included]

## Performance Summary

The summary-based approach demonstrates superior performance characteristics:
- Query Times: 0.006-0.009 seconds (vs. 0.030-0.048 seconds for full dataset)
- Index Size: <1MB (vs. up to 25MB for full dataset)
- Scalability: Flat performance curve regardless of dataset count


### Figure 1-Initial Benchmark with Small Dataset Count.png

This initial benchmark with 1-3 datasets shows:
•	Full dataset query times: 0.008-0.018 seconds
•	Summary query times: 0.0075-0.011 seconds
•	Performance gap: ~30-40% improvement with summaries
•	Index size difference: Summaries <0.5MB vs full datasets at 2.5-3.0MB



### Figure 2-Expanded Benchmark with 10 Datasets.png

The expanded benchmark with up to 10 datasets reveals:
•	Full dataset query times: 0.030-0.050 seconds
•	Summary query times: 0.006-0.007 seconds
•	Performance gap: 5-7× improvement with summaries
•	Index size difference: Summaries <1MB vs full datasets at 25MB
•	Performance breakpoint: Significant degradation in full dataset performance at 7+ datasets



### Figure 3-Same Test with Slightly Different Scale.png


This benchmark confirms:
•	Full dataset peak query time: 0.061 seconds
•	Summary peak query time: 0.007 seconds
•	Maximum performance gap: ~8× improvement
•	Consistent storage efficiency: Summary indices remain near 0MB



### Figure 4-Most Recent Benchmark with Y-Axis Scaling.png


The final benchmark with adjusted scaling shows:
•	Full dataset query times: 0.030-0.048 seconds
•	Summary query times: 0.006-0.010 seconds
•	Consistent performance ratio: 5-6× improvement
•	Scale-up pattern: Full dataset performance degrades at 7+ datasets
•	Storage efficiency: Maintained across all tests

