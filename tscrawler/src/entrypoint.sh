#!/bin/bash

npm run build

# Check if should start insecure webserver containing sample pages for testing (environment variable START_INSECURE_WEBSERVER)
if [[ "$START_INSECURE_WEBSERVER" == "true" ]]; then 
    node $(pwd)/snippets/insecure-webpages/server.js &
fi

echo "[entrypoint] Startup complete"
tail -f /dev/null