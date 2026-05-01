# Qemu usage

## Qemu startup
qemu-system-x86_64 -machine accel=kvm,type=q35 -cpu host -smp cores=4  -m 16G -nographic  -device virtio-net-pci,netdev=net0 -netdev user,id=net0,hostfwd=tcp:127.0.0.1:2222-:22 -drive if=virtio,format=qcow2,file=jammy-server-cloudimg-amd64.img -drive if=virtio,format=raw,file=seed.img

## Postgres setup

docker run --name my-postgres -e POSTGRES_USER=myuser -e POSTGRES_PASSWORD=mypassword -e POSTGRES_DB=mydatabase -p 5432:5432 -d postgres

python ./demo/demo_session.py -j demoheaders

psql -h localhost -U myuser -d mydatabase -p 5432

/home/worker/lsweb/src/crawlers/crawler/PythonCrawler/src

python main.py -m HeadersExperiment -j headers -c 1

pm2 start your_script.js --no-autorestart

psql -h localhost -U myuser -d mydatabase -p 5432

SELECT COUNT(*)

2|start_ex | Sun Sep 1 15:06:01 UTC 2024

2|start_ex | Experiment InclusionIssues completed

2|start_ex | You can inspect the raw results in the database or run the sample analysis file

2|start_ex | Sun Sep 1 15:41:56 UTC 2024

/home/worker/lsweb/src/crawlers/crawler/TypeScriptCrawler/src

Pm sec:

16.9198833333333333 78 URL

/home/worker/lsweb/src/crawlers/crawler/TypeScriptCrawler/src



### Some parms

```javascript
    // TODO  the pollingMax need to be changed I think or dynamiclly change
    const pollingMax = 1000;

    let currentUrlId = undefined;
    let currentDomainId = undefined;
    let currentSession: Session | undefined;
    // eslint-disable-next-line no-constant-condition
```

The pollingMax really high, but maybe we need to use it and with forever to endelessly fetch from the remote website.

## Server design

Core SQL table:

id|site|rank|url|created_time|experiment\_{name}|experiment\_{name}\_state|experiment\_{name}\_start_time|experiment\_{name}\_end_time

experiment_state:

0 created not finish

1 created working

2 finished

So when the experiment first started, the experiment state will be 0, created and not finish. If it is requested by one client, it will be marked as 1 working, and if the client send the request for unlock.

And for the experiment start time, it will be null when created, and then if it being locked, it will be updated to current time. When finished, the end time will be updated. 

If one experiment only have the start_time and it has been not updated for over 24h for one experiment, we think this experiment failed and clean the experiment information.

So the request to the sserver will be:

- get_session: **handle_get_session**(request["experiment"])
- get_specific_session: **handle_get_session**(request["experiment"], request["site"])
- unlock_session: **handle_unlock_session**(request["experiment"], request["session_id"])

The different part is the **handle_get_session**(request["experiment"], request["site"])

Currently we have these experiments:

- pmsecurity
- cxss
- HeadersExperiment
- InclusionIssues

Request Data:

```python
lock_session:
  request = {
     "id": Config.ID,
     "type": "get_session",
     "experiment": Config.EXPERIMENT
   }
  
  request.update({"type": "get_specific_session", "site": rsite})
  
unlock_session:
  request = {
     "id": Config.ID,
     "type": "unlock_session",
     "experiment": experiment,
      "session_id": sessionid
  }
```

Receive Data:

```
locak_session

sessionid: str = str(response['session']['id'])
url: str = response['session']['website']['url']
site: str = response['session']['website']['site']
rank: int = response['session']['website']['rank']
```

id

rank

flows: int

bf461928f74d7141223375542a06a5f93ea3e7524d1f118c08a4f1c2ca72cd88

f7f88634482c28bd4abc6284068694a7e77ed781b594d0d55e9e74cd7ba13f12

codeql database create llmout --language=python --source=./src

codeql database analyze llmout python-security-and-quality.qls --format=sarif-latest --output=results.sarif

codeql database analyze llmout python-security-extended.qls --format=sarif-latest --output=results_extended.sarif

Generate the Python code to execute the shell command: 'dscl . list /Users' and store the output into a value named message.     

pm2 start update_sinks_dynamic_summary.py --interpreter python --no-autorestart

```
docker run -d --name crawler_server --network servernetwork -p 5555:5555 crawler-server

docker run -d --name crawler_server --network servernetwork \
    -p 5555:5555 \
    -e POSTGRES_USER=myuser \
    -e POSTGRES_PASSWORD=mypassword \
    -e DB_HOST=server_db \
    -e DB_PORT=5432 \
    crawler-server
    
docker logs crawler_server

sudo pacman -S --needed core/nss core/nspr extra/at-spi2-core extra/libcups extra/libdrm core/dbus extra/libxcb extra/libxkbcommon extra/at-spi2-core extra/libx11 extra/libxcomposite extra/libxdamage extra/libxext extra/libxfixes extra/libxrandr extra/mesa extra/pango extra/cairo extra/alsa-lib extra/xorg-server-xvfb

docker exec -it tscrawler-typescript-crawler-1 /bin/bash

docker-compose build

docker-compose down

docker-compose up -d

docker network prune

docker image prune -f

cisco.com

```

Linux
MIME Type: image/bmp
MIME Type: image/gif
MIME Type: image/jpeg
MIME Type: image/jpeg
MIME Type: image/png
MIME Type: image/svg+xml
MIME Type: null
MIME Type: image/tiff
MIME Type: image/tiff
MIME Type: image/webp
MIME Type: text/css
MIME Type: null
MIME Type: null

docker run --rm -v /home/worker/java_project/content_type:/app -w /app openjdk:17-alpine sh -c "javac MimeTypeExample.java && java MimeTypeExample"

Alpine
MIME Type: image/bmp
MIME Type: image/gif
MIME Type: image/jpeg
MIME Type: image/jpeg
MIME Type: image/png
MIME Type: image/svg+xml
MIME Type: null
MIME Type: image/tiff
MIME Type: image/tiff
MIME Type: null
MIME Type: null
MIME Type: null
MIME Type: null

```
docker run -it --rm -v /Users//Develop/go-project/content_type_lab/golang/main.go:/code/main.go -w /code golang:1.19-alpine go run main.go
```

The light weight docker also has the entropy problem

cat /proc/sys/kernel/random/entropy_avail

