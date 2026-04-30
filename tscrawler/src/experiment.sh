#!/bin/bash

echo "Start Experiment"

# Fix pm2 use shared home export PM2_HOME=/tmp/my_pm2_dir/$PGDATA
export PM2_HOME=/tmp/my_new_pm2_dir/$PGDATA
mkdir -p "$PM2_HOME"
chmod 777 "$PM2_HOME"

CWD=$(pwd)
TIMESTAMP=$(date '+%Y_%m_%d_%H_%M_%S')

# load .env file
# comment for docker load
source .env

POSTGRES_DB="$EXPERIMENT"_"$TIMESTAMP"
# STDOUT_LOG_PATH=/mnt/shared/data/crawl_$TIMESTAMP/log      # Path for normal log output
# STDERR_LOG_PATH=/mnt/shared/data/crawl_$TIMESTAMP/err      # Path for error log output
# DATA_PATH=/mnt/shared/data/crawl_$TIMESTAMP/data           # Path for crawl artifacts

STDOUT_LOG_PATH=/tmp/data/crawl_$TIMESTAMP/log      # Path for normal log output
STDERR_LOG_PATH=/tmp/data/crawl_$TIMESTAMP/err      # Path for error log output
DATA_PATH=/tmp/data/crawl_$TIMESTAMP/data           # Path for crawl artifacts

# Create new database for the experiment
# psql -h $POSTGRES_HOST -U $POSTGRES_USER -p $POSTGRES_PORT -c "CREATE DATABASE $POSTGRES_DB;";
# node $(pwd)/dist/utils/create-db.js -h $POSTGRES_HOST -U $POSTGRES_USER -p $POSTGRES_PORT --password=$POSTGRES_PASSWORD -d $POSTGRES_DB
node $(pwd)/dist/utils/create-database.js -h $POSTGRES_HOST -U $POSTGRES_USER -p $POSTGRES_PORT --password="$POSTGRES_PASSWORD" -d "$POSTGRES_DB" --pgbouncerPort "$PGBOUNCER_PORT"
export POSTGRES_DB=$POSTGRES_DB;

# # Make postgres database name/password available for crawler
echo "POSTGRES_DB=$POSTGRES_DB" >> .env;

echo "Prepare database and check disk folders"
mkdir -p $DATA_PATH
mkdir -p $STDOUT_LOG_PATH
mkdir -p $STDERR_LOG_PATH
bash ./setup/prepare.sh $(pwd) $STDOUT_LOG_PATH $STDERR_LOG_PATH $DATA_PATH --module $EXPERIMENT 

# Start crawler and cheng POSTGRES_PORT to PGBOUNCER_PORT
echo "Start crawler"

# Set POSTGRES_PORT to PGBOUNCER_PORT
export POSTGRES_PORT=$PGBOUNCER_PORT;

if [[ "$EXPERIMENT" == "cxss" ]]; then 
    BROWSER_EXECUTABLE_PATH=./foxhound/foxhound    # Location of the browser engine to use with playwright
    # To start cxss, we specify firefox and browser executable path (set to foxhound binary):
    bash ./setup/spawn.sh $(pwd) $STDOUT_LOG_PATH $STDERR_LOG_PATH $EXPERIMENT $CRAWLER_START $CRAWLER_COUNT --module $EXPERIMENT --polling $POLLING_INTERVAL --datapath $DATA_PATH --forever --firefox --browser_executable_path $BROWSER_EXECUTABLE_PATH
fi

#  only fetch mode
if [[ "$ZMQ_ENABLE" == "true" ]]; then 
    ZMQ_FETCH_INTERVAL=5   # Interval which is waited between calls to ZMQ server for new session in seconds
    echo "[experiment] Starting zmq listener for session fetching."
        node --max-old-space-size=65536 $(pwd)/dist/utils/zmq/zmq-listener.js --crawlers $CRAWLER_COUNT --fetchinterval $ZMQ_FETCH_INTERVAL 2>> $STDERR_LOG_PATH/zmq-listener.log >> $STDOUT_LOG_PATH/zmq-listener.log &
fi

echo "[experiment] Started the experiment"
