# Artifact Data: Overall Absolute Sampling

This directory contains the dataset `overall_abs_sampling.csv`, which is generated as part of the sampling strategy evaluation for the paper. 

This dataset records the performance and statistical stability of the random sampling strategy at various sample sizes. It tracks how the deviation (error) from the true baseline changes as the sample size increases, which is crucial for evaluating the reliability and convergence of the sampling methodology.

# Artifact: Security Header Analyzer Example

This directory also contains a self-contained, reproducible example of our Security Header detection pipeline, which corresponds to the methodology described in the paper.

## Files

- **`header_analyzer.py`**: The exact Python script used in our data processing pipeline to parse HTTP headers from Common Crawl data and evaluate security misconfigurations (e.g., HSTS, CSP, X-Content-Type-Options). 
- **`example_000000.jsonl`**: A small, real-world data sample extracted from our massive Common Crawl dataset. It contains the raw HTTP response payloads for 15 domains.
- **`run_example.sh`**: A simple shell script to execute the analyzer on the example dataset.

## How to Run

To test the security header detection logic locally, simply run:

```bash
./run_example.sh
```

This script will feed the sample JSONL file into `header_analyzer.py`, evaluate the headers based on the security rules outlined in our paper, and output the detailed findings to `example_results.csv`. 

You can inspect the `example_results.csv` to see how issues are classified (e.g., severity levels, specific missing directives, invalid values).
