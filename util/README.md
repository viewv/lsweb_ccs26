# Core Utilities (`util/`)

This directory contains shared Python utilities, database models, and offline analysis scripts used across the framework.

## Directory Structure

- **`database/`**: Contains the Tortoise ORM definitions and initialization logic.
  - `model/`: The database schemas (e.g., `Site`) that map to the PostgreSQL tables. This ensures consistent data structures are used for tracking targets and recording security experiment results.
  - `db.py` & `db_config.py`: Scripts for configuring and establishing the connection to the PostgreSQL database.
- **`config/`**: Contains the configuration settings for the Python utilities.
- **`headers_issues/`**: Offline analysis scripts designed to detect security header vulnerabilities and misconfigurations from the scraped data. It includes a standalone analyzer (`header_analyzer.py`) and a reproducible example dataset.
- **`shapley/`**: Dataset and analysis code (Jupyter notebook) for computing Shapley values to compare the effectiveness and stability of different sampling strategies (bucket, random, and stratified).
- **`source_tranco_async.py`**: An asynchronous script used to fetch the Tranco top sites list and seed the PostgreSQL database with these crawling targets. It uses the ORM to efficiently insert records and is often used during the initial setup phase.
