# Crawler Framework

This directory contains the distributed web crawling framework designed to analyze and detect security vulnerabilities (e.g., Client-side XSS, Security Headers, Inclusions) across a large set of websites. It is built for artifact review to be clean, anonymized, and easy to run locally or on a high-performance compute cluster (e.g., Slurm).

## Architecture

The framework consists of two main components:

1. **`crawlerserver`**: A central queue and dispatch server. It uses PostgreSQL and PgBouncer to manage the state of crawling targets and distributes sessions to connected crawlers via ZeroMQ (ZMQ). 
2. **`tscrawler`**: A headless-browser-based worker written in TypeScript (using Playwright). It connects to the `crawlerserver`, fetches target websites, and runs detailed security experiments (e.g., executing client-side XSS checks, inspecting headers) before returning the results.

## Directory Structure

- `crawlerserver/`: Source code for the backend task dispatcher.
- `tscrawler/`: Source code for the frontend headless-browser crawler workers.
- `Dockerfile`: Single unified Docker image that packages both components and sets up the environment (PostgreSQL, PgBouncer, Node.js, Python, Playwright).
- `entrypoint.sh`: The main entrypoint for the Docker container that initializes the database, seeds it with targets, and starts the workers via PM2/Supervisor.
- `run.sh`, `job.sh`: Utility scripts for deploying the containerized crawler on a Slurm cluster.
- `shutdown_db.sh`: Utility script for safely terminating the running databases and saving WAL records.

## Getting Started

You can run this project either locally using Docker, or on a Slurm-based cluster.

### 1. Running Locally (Docker)

Follow these steps to run a complete crawling experiment on your local machine.

#### Step 1: Build the Docker Image

```bash
docker build -t anonymous/crawler:latest .
```

#### Step 2: Prepare Local Data Directory

```bash
rm -rf local_data && mkdir -p local_data
```

#### Step 3: Start the Container in Background

The container initializes PostgreSQL, PgBouncer, seeds the target database, and starts the ZMQ dispatch server automatically.

```bash
docker run -d --name crawler_test \
    -v $(pwd)/local_data:/mnt/local_data \
    -e PGDATA=/mnt/local_data/pgdata \
    -e WALDATA=pg_wal \
    -e TMP_WAL_BASE=/mnt/local_data \
    -e PG_PORT=5432 \
    -e PGBOUNCER_PORT=6432 \
    -e CRAWLER_ID=0 \
    -e ZMQ_HOST=tcp://127.0.0.1:5555 \
    anonymous/crawler:latest
```

#### Step 4: Wait for Initialization

Monitor the startup logs and wait until you see `Successfully added to the database` before proceeding:

```bash
docker logs -f crawler_test
```

Press `Ctrl+C` to stop following logs once the initialization is complete.

#### Step 5: Enter the Container Shell

```bash
docker exec -it crawler_test bash
```

#### Step 6: Start the Experiment

Navigate to the crawler source directory and run the experiment script:

```bash
cd /run/tscrawler/src
bash experiment.sh
```

This script will:
- Create a new timestamped experiment database (e.g., `cxss_2026_05_02_19_00_00`)
- Start up to 50 parallel crawler workers via PM2 using the foxhound browser
- Start the ZMQ listener to pull crawl sessions from the dispatch server

#### Step 7: Monitor Crawlers

```bash
# Set the correct PM2 home to see crawler processes
export PM2_HOME=/tmp/my_new_pm2_dir/mnt/local_data/pgdata
pm2 list

# View logs for a specific crawler
pm2 logs crawler-cxss-1

# Interactive monitor
pm2 monit
```

Check that the ZMQ server is running:
```bash
supervisorctl -c /etc/supervisor/supervisord.conf status
# Expected: zmq_server   RUNNING   pid XX, uptime X:XX:XX
```

#### Step 8: Verify Results in the Database

Connect to PostgreSQL to inspect crawl results:

```bash
# List all databases (find the experiment DB named cxss_YYYY_MM_DD_...)
psql -h 127.0.0.1 -p 5432 -U postgres -c "\l"

# Connect to the experiment database (replace timestamp)
psql -h 127.0.0.1 -p 5432 -U postgres -d cxss_2026_05_02_19_00_00

# Inside psql: view tables
\dt

# Count crawled sessions
SELECT COUNT(*) FROM sessions;

# View the most recent results
SELECT * FROM sessions ORDER BY id DESC LIMIT 10;

# Exit psql
\q
```

#### Step 9: Cleanup

When finished, stop and remove the container from your host terminal:

```bash
docker stop crawler_test && docker rm crawler_test
```

To fully reset and start a fresh experiment:
```bash
rm -rf local_data
```

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
