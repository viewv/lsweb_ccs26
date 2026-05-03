# Common crawl Analysis Artifacts

This directory contains the code and data necessary to reproduce the prevalence analysis plots presented in the paper.

## Directory Structure

- `data/`: Contains pre-computed statistical summaries.
    - `overall_abs_sampling.csv`: Monte Carlo sampling results from the Common Crawl dataset.
    - `tranco_abs_sampling.csv`: Pre-computed Monte Carlo sampling results for the Tranco dataset.
    - `metadata.json`: Ground truth prevalence values for both datasets.

## Ethical & Privacy Considerations

Due to privacy concerns and the sensitivity of raw security scan data for specific domains, the raw crawling results and vulnerability mappings are not included in this public artifact.

Instead, we provide comprehensive statistical summaries that preserve the mathematical properties of the distributions (including median, CI, Peak error, and RMS) required for the Artifact Review. This allows for full reproduction of the paper's analytical plots without exposing raw domain-level security data.
- `plot_merged_cc_baseline.py`: Generates the prevalence deviation plot relative to the Common Crawl ground truth.
- `plot_merged_own_baseline.py`: Generates the prevalence deviation plot relative to each dataset's own ground truth.
- `plot_prevalence_ratio_tranco_cc.py`: Generates the prevalence ratio plot (Tranco vs. Common Crawl) as a function of sample size.

## Requirements

- Python 3.x
- `pandas`
- `numpy`
- `matplotlib`

## How to Run

For the plots, execute the scripts from this directory.

```bash
# Generate the merged prevalence plot (Common Crawl baseline)
python3 plot_merged_cc_baseline.py

# Generate the merged prevalence plot (Own baselines)
python3 plot_merged_own_baseline.py

# Generate the prevalence ratio analysis
python3 plot_prevalence_ratio_tranco_cc.py
```

Each script will output a PDF file containing the corresponding plot.

