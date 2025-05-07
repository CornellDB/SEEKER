# Q-gram Implementation Results

This folder contains visualizations and performance metrics from the Q-gram implementation for SEEKER.

## Visualizations

### seeker_qgram_comparison.png
This visualization compares performance across different q values (2, 3, 4). Higher q values generally provide better query performance but result in larger indices. The summary approach consistently outperforms the full dataset approach across all q values.

### seeker_qgram_performance_q2.png
Performance metrics for q=2, showing query time vs dataset count and index size. The summary approach maintains ~2× performance advantage over full dataset approach with small index sizes.

### seeker_qgram_performance_q3.png
Performance metrics for q=3, showing the best balance between performance and storage requirements. Query times are improved over q=2 while maintaining reasonable index sizes.

### seeker_qgram_performance_q4.png
Performance metrics for q=4, showing the best query performance but largest index sizes. The summary approach achieves up to 4× faster queries than the full dataset approach.

### qgram (query time vs index size).png
Demonstrates the relationship between query performance and storage requirements. Summary indices remain small regardless of q value, while full dataset indices grow significantly with higher q values.

### [Additional Image Descriptions]
[Add descriptions for each additional image you've included]

## Performance Summary

The q=3 value offers the optimal balance of performance and storage:
- Summary approach achieves 0.008-0.010 second query times
- Index sizes remain under 1MB for summary approach
- Performance advantage grows with dataset count
