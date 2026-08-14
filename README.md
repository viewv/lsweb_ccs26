# Sampling strategies

## Repository Structure

- `crawler/`: Contains the distributed web crawling framework, including the backend dispatcher (`crawlerserver`) and the headless-browser workers (`tscrawler`). `crawler/README.md` for specific execution instructions and details.
- `commoncrawl/`: Scripts and tools for collecting, processing, and analyzing historical web data from the Common Crawl dataset for baseline comparison. `commoncrawl/README.md` for specific execution instructions and details.
- `util/`: Core Python utilities, including Tortoise ORM database definitions, database seeding scripts, and offline security analysis scripts like `headers_issues/` and `shapley/` (Shapley value analysis for sampling strategies). `util/README.md` and `util/headers_issues/README.md` for detailed instructions.
- `data/`: Contains non-identifying measurement results, statistical summaries, and analysis scripts (e.g., Shapley value analysis, hybrid sampling, survey papers list, and sensitivity studies). See `data/README.md` for a detailed breakdown of the available datasets.
- `tools/`: Contains the Adaptive Sampling Assistant, an interactive CLI tool implementing the paper's adaptive probability sampling strategy for deciding stage by stage when a sample is sufficient. `tools/README.md` for specific execution instructions and details.
