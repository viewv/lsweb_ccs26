#!/bin/bash

PROJECT_ROOT=$1
STDOUT_LOG_PATH=$2
STDERR_LOG_PATH=$3
EXPERIMENT=$4

# Ensure PM2 is installed
if ! command -v pm2 &> /dev/null
then
    echo "PM2 is not installed. Installing PM2..."
    npm install -g pm2
fi

# Start up all crawlers
# for i in `seq $5 $6`; do
#     echo "[spawn] Starting crawler with id $i";
#     pm2 start $PROJECT_ROOT/dist/index.js \
#         --name "crawler-$EXPERIMENT-$i" \
#         --output $STDOUT_LOG_PATH/crawler-$i.log \
#         --error $STDERR_LOG_PATH/crawler-$i.log \
#         --max-memory-restart 16G \
#         --no-autorestart \
#         -- "${@:7}";
#     sleep 1
# done

for i in `seq $5 $6`; do
    echo "[spawn] Starting crawler with id $i";
    pm2 start $PROJECT_ROOT/dist/index.js \
        --name "crawler-$EXPERIMENT-$i" \
        --output /dev/null \
        --error $STDERR_LOG_PATH/crawler-$i.log \
        --max-memory-restart 16G \
        --no-autorestart \
        -- "${@:7}";
    sleep 1
done

# Save the PM2 process list
pm2 save

echo "All crawlers have been started. Use 'pm2 list' to see their status."
