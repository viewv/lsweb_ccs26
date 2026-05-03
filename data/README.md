# Experimental Data and Analysis Results

This directory contains the non-identifying results and analysis scripts derived from our measurements. The data is organized into subdirectories based on the specific analysis or figure in the paper.

## Directory Structure

- `commconcrawl/`: Data and scripts for the prevalence analysis comparing our measurements with the Common Crawl baseline. 
- `hybrid/`: Data and plotting scripts for evaluating hybrid sampling strategies.
- `impact/`: Baseline JSON data and scripts for analyzing the impact of different sample sizes (10k to 100k) on prevalence estimation.
- `sensitivity/`: Analysis of sensitivity to data size and sample size across various security issues (CORS, HSTS, SSL, etc.). Contains a Jupyter notebook for visualization.
- `shapley/`: Data and analysis of Shapley values for different sampling strategies (random, stratified, bucket-based) to determine their contribution to measurement accuracy.

## Ethical & Privacy Considerations

To protect the privacy of scanned domains and avoid exposing potentially sensitive security vulnerabilities, we provide statistical summaries and aggregated results rather than raw domain-level logs. These summaries are sufficient to reproduce the analysis and plots presented in the paper.

