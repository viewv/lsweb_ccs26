# Artifact Data: Overall Random Sampling

This directory contains the dataset `overall_abs_sampling.csv`, which is generated as part of the sampling strategy evaluation for the paper. 

This dataset records the performance and statistical stability of the random sampling strategy at various sample sizes. It tracks how the deviation (error) from the true baseline changes as the sample size increases, which is crucial for evaluating the reliability and convergence of the sampling methodology.

## File Structure: `overall_abs_sampling.csv`

The CSV file contains the following columns:

- **`Ratio`**: The sampling ratio, calculated as the sample size divided by the total population size.
- **`Size`**: The absolute number of domains/hosts sampled in this iteration.
- **`Mean Error(%)`**: The mean estimation error (deviation from the true baseline) across all randomized runs at this specific sample size, measured in percentage points.
- **`CI Lower(%)`**: The lower bound of the error interval (typically the 25th percentile, representing the lower bound of the 50% median interval) across the runs.
- **`CI Upper(%)`**: The upper bound of the error interval (typically the 75th percentile, representing the upper bound of the 50% median interval) across the runs.
- **`Over(%)`**: The percentage of sampling runs that resulted in an over-estimation of the true baseline value.
- **`Under(%)`**: The percentage of sampling runs that resulted in an under-estimation of the true baseline value.
- **`Peak Signed(%)`**: The maximum signed deviation (the peak error, either positive or negative) observed among all runs at this sample size.
- **`RMS(%)`**: The Root Mean Square (RMS) error of the estimates at this sample size. This is a key metric used in the paper to evaluate the overall variance, bias, and stability of the estimator.

## Usage

This dataset is used to generate the prevalence and impact deviation plots (e.g., Deviation vs. Sample Size) and to compute the stability metrics (Peak error, RMS, Over/Under ratios) presented in the evaluation sections of the paper. It provides empirical evidence of how probability sampling converges and stabilizes as the absolute sample size grows.
