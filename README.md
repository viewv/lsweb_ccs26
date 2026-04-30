# sampling strategies

## Repository Structure

- `crawlerserver/`: Source code for the backend task dispatcher. It manages the state of crawling targets using PostgreSQL and distributes tasks via ZeroMQ.
- `tscrawler/`: Source code for the frontend headless-browser crawler workers. Built with TypeScript and Playwright, it executes the security experiments on target sites.
- `commoncrawl/`: Scripts and tools for collecting, processing, and analyzing historical web data from the Common Crawl dataset for baseline comparison. `commoncrawl/README.md` for specific execution instructions and details.
- `src/`: Core Python utilities, including Tortoise ORM database definitions, database seeding scripts, and offline security analysis scripts like `headers_issues/`. `src/README.md` and `src/headers_issues/README.md`.
- `Dockerfile`: Single unified Docker image that packages both components and sets up the environment (PostgreSQL, PgBouncer, Node.js, Python, Playwright).
- `entrypoint.sh`: The main entrypoint for the Docker container that initializes the database, seeds it with targets, and starts the `crawlerserver` along with the `tscrawler` workers via PM2/Supervisor.
- `run.sh`, `job.sh`: Utility scripts for deploying the containerized crawler on a Slurm cluster.
- `shutdown_db.sh`: Utility script for safely terminating the running databases and saving WAL records.

## Crawler

You can run this project either locally using Docker, or on a Slurm-based cluster.


# TODO
### 1. Running Locally (Docker)

To test the entire workflow locally:

1. **Unzip the Custom Browser (Foxhound):**
   Due to GitHub file size limits, the specialized headless browser is compressed. Unzip it first:
   ```bash
   cd tscrawler/src
   unzip foxhound.zip
   cd ../..
   ```

2. **Build the Docker Image:**
   ```bash
   docker build -t anonymous/crawler:latest .
   ```

3. **Run the Container:**
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
