# crawlerServer

This repository contains the `crawlerServer` module, a key component used in our paper artifact to manage and coordinate crawling tasks.

## Overview

The `crawlerServer` handles the queuing, allocation, and tracking of websites to be crawled during our experiments. For this artifact review version, it is pre-configured with a simplified setup that automatically injects a configurable list of example websites into the database, removing the need for large-scale external ranking lists (like CRUX or Tranco) and complex ID-based partitioning.

## Getting Started

To evaluate and run this component:

### Prerequisites
- Docker (for spinning up a local PostgreSQL database quickly)
- Python 3.11+

### Setup & Execution (Standalone Testing)

If you want to run this module independently to see how it serves tasks:

1. **Start a local PostgreSQL database:**
   ```bash
   docker run -d --name ccs-postgres -e POSTGRES_PASSWORD=strongpassword -e POSTGRES_USER=postgres -e POSTGRES_DB=sites -p 5432:5432 postgres:15
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Populate the database with the example ranking list:**
   This script will read `src/example.csv` and insert the targets into the database.
   ```bash
   # Export environment variables so the script knows how to connect
   export POSTGRES_PASSWORD=strongpassword
   export PGUSER=postgres
   export POSTGRES_DB=sites
   export DB_HOST=127.0.0.1
   export PG_PORT=5432

   python src/source_tranco_async.py --csv src/example.csv
   ```

4. **Start the ZMQ Server:**
   ```bash
   export ZMQ_HOST=tcp://0.0.0.0:5555
   python src/zmq_server.py
   ```

*(Note: When integrated with the larger project suite, the root `entrypoint.sh` automatically handles the PostgreSQL setup, PgBouncer initialization, and data seeding.)*

