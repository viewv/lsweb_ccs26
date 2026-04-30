#!/bin/bash

# Read arguments
ID="$1"
NODELIST="$2"

if [ -z "$ID" ] || [ -z "$NODELIST" ]; then
  echo "Usage: $0 <ID> <NODELIST>"
  exit 1
fi

# Two-digit format
ID_PADDED=$(printf "%02d" "$ID")

# Construct arguments
PGDATA="/home/worker/pgdatas/data_$ID"
WALDATA="/home/worker/WAL/wal_$ID"
PG_PORT="54$ID_PADDED"
PGBOUNCER_PORT="64$ID_PADDED"
CRAWLER_ID="$ID"
ZMQ_HOST="ipc:///tmp/zmq$ID.sock"

# Construct srunmail command (multi-line is clearer)
CMD="srunmail \
--container-image=anonymous/crawler:latest \
--export=ALL,PGDATA=$PGDATA,WALDATA=$WALDATA,PG_PORT=$PG_PORT,PGBOUNCER_PORT=$PGBOUNCER_PORT,CRAWLER_ID=$CRAWLER_ID,ZMQ_HOST=$ZMQ_HOST \
--pty \
-p wdr \
--cpus-per-task=128 \
--time=6-23:30:00 \
--nodelist=$NODELIST \
bash"

# Session name
SESSION_NAME="c$ID"

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
  echo "Error: tmux is not installed, please install it first."
  exit 1
fi

# Check if tmux session exists
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  echo "tmux session already exists $SESSION_NAME，attaching and executing command..."
  tmux send-keys -t "$SESSION_NAME" "$CMD" C-m
  tmux attach -t "$SESSION_NAME"
else
  echo "Creating new tmux session $SESSION_NAME and running auto_kinit.sh and command..."

  # Start bash session but do not attach
  tmux new-session -d -s "$SESSION_NAME" bash

  # Send commands: authenticate first, then execute main command
  tmux send-keys -t "$SESSION_NAME" "/home/worker/auto_kinit.sh" C-m
  tmux send-keys -t "$SESSION_NAME" "$CMD" C-m

  # Attach to session
  tmux attach -t "$SESSION_NAME"
fi