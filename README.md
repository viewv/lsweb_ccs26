# Distributed Security Crawler Framework

This repository contains a scalable, distributed web crawling framework designed to analyze and detect security vulnerabilities (e.g., Client-side XSS, Security Headers, Inclusions) across a large set of websites. It is built for artifact review to be clean, anonymized, and easy to run locally or on a high-performance compute cluster (e.g., Slurm).

## Architecture

The framework consists of two main components:

1. **`crawlerserver`**: A central queue and dispatch server. It uses PostgreSQL and PgBouncer to manage the state of crawling targets and distributes sessions to connected crawlers via ZeroMQ (ZMQ). 
2. **`tscrawler`**: A headless-browser-based worker written in TypeScript (using Playwright). It connects to the `crawlerserver`, fetches target websites, and runs detailed security experiments (e.g., executing client-side XSS checks, inspecting headers) before returning the results.

## Repository Structure

- `crawlerserver/`: Source code for the backend task dispatcher.
- `tscrawler/`: Source code for the frontend headless-browser crawler workers.
- `Dockerfile`: Single unified Docker image that packages both components and sets up the environment (PostgreSQL, PgBouncer, Node.js, Python, Playwright).
- `entrypoint.sh`: The main entrypoint for the Docker container that initializes the database, seeds it with targets, and starts the `crawlerserver` along with the `tscrawler` workers via PM2/Supervisor.
- `run.sh`, `job.sh`: Utility scripts for deploying the containerized crawler on a Slurm cluster.
- `shutdown_db.sh`: Utility script for safely terminating the running databases and saving WAL records.

- **Simplified Seeding:** We have a easily modifiable CSV list (`crawlerserver/src/example.csv`). You can add any domains you want to test directly into this file.

## Getting Started

You can run this project either locally using Docker, or on a Slurm-based cluster.

### 1. Running Locally (Docker)

To test the entire workflow locally:

1. **Build the Docker Image:**
   ```bash
   docker build -t anonymous/crawler:latest .
   ```

2. **Run the Container:**
   You can run the container locally. Make sure to mount volumes if you want persistent data, or just run it ephemerally:
   ```bash
   docker run -it --rm \
       -e PGDATA=/tmp/pgdata \
       -e PG_PORT=5432 \
       -e PGBOUNCER_PORT=6432 \
       -e CRAWLER_ID=0 \
       -e ZMQ_HOST=tcp://127.0.0.1:5555 \
       anonymous/crawler:latest
   ```
   *(Note: The `entrypoint.sh` will automatically initialize PostgreSQL, start PgBouncer, seed the database from `example.csv`, and start the ZMQ server and TS crawler workers.)*

### 2. Running on a Slurm Cluster

For distributed crawling across multiple nodes:

1. Ensure the Docker image is available on your cluster (e.g., via a registry or Enroot/Singularity).
2. Use the provided wrapper script:
   ```bash
   ./run.sh <CRAWLER_ID> <SLURM_NODELIST>
   ```
   This script creates a `tmux` session, configures the necessary environment variables (`PGDATA`, ports, `ZMQ_HOST`), and submits the job via `srunmail`/`srun`.

## Clean Shutdown

If you are running persistent instances and need to stop them safely while preserving database states (WAL):
```bash
bash shutdown_db.sh
```
