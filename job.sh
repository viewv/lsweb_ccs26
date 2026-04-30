#!/bin/bash
#SBATCH --job-name=tscrawler_0
#SBATCH --partition=wdr
#SBATCH --mail-type=ALL
#SBATCH --mail-user=anonymous@example.com
#SBATCH --output=pg_setup_%j.log
#SBATCH --error=pg_setup_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --container-image=anonymous/crawler:latest
#SBATCH --export=ALL,PGDATA=/home/worker/pgdatas/data_0,PG_PORT=5432,PGBOUNCER_PORT=6432,PGUSER=postgres,CRAWLER_ID=0,ZMQ_HOST=ipc:///tmp/zmq0.sock

srun --container-name=tscrawler_container --export=ALL bash /entrypoint.sh
