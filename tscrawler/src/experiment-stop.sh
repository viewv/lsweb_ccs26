#!/bin/bash
CWD=$(pwd)

# Note: change to use the pm2 to manage all process
echo "[kill] Killing crawler management processes";
pm2 stop all
pm2 del all

pm2 save --force
