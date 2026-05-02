FROM ubuntu:jammy

ENV TZ=Europe/Berlin
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && \
    apt-get install -y postgresql postgresql-contrib pgbouncer wget curl gnupg2 sudo locales bash zsh supervisor && \
    apt-get install -y nano build-essential software-properties-common postgresql-client git tmux curl ca-certificates && \
    apt-get install -y libxml2-dev libxslt-dev cmake pkg-config util-linux postgresql-client libzmq3-dev && \
    apt-get install -y libdbus-glib-1-2 libxt6 libxcomposite1 libxdamage1 libxrandr2 libasound2 libgtk-3-0 libx11-xcb1 && \
    apt-get install -y python3.10 python3-pip unzip && \
    apt-get install -y cron iotop dstat atop inotify-tools && \
    pip3 install z3-solver==4.8.7.0 ply && \
    pip3 install --no-cache-dir pyzmq tranco tortoise-orm[asyncpg] tortoise-orm[accel] && \
    apt-get install -y python2.7 python2.7-dev && \
    curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py && \
    python2.7 get-pip.py && \
    locale-gen en_US.UTF-8 && \
    update-locale LANG=en_US.UTF-8 && \
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get install -y nodejs && \
    npm install pm2 -g

# Copy the src directory to the container
COPY ./src /app/src

# Copy the crawlerserver to the container
COPY ./crawlerserver /app/crawlerserver

# Copy the tscrawler to the container
COPY ./tscrawler /app/tscrawler
WORKDIR /app/tscrawler/src

# RUN unzip foxhound.zip && chmod +x foxhound/foxhound
RUN npm install && npm run build
RUN npx playwright install --with-deps

WORKDIR /app/tscrawler/src/snippets/insecure-webpages
RUN npm install

# Create startup scripts (run in sbatch)
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# COPY entrypoint_crux.sh /entrypoint_crux.sh
# RUN chmod +x /entrypoint_crux.sh

COPY shutdown_db.sh /shutdown_db.sh
RUN chmod +x /shutdown_db.sh

WORKDIR /

RUN mkdir -p \
        /var/run/postgresql \
        /var/run/pgbouncer \
        /var/run/supervisor \
        /var/log/supervisor \
        /etc/supervisor/conf.d \
        /etc/pgbouncer \
    && chown -R postgres:postgres \
        /app \
        /run \
        /tmp \
        /var/log \
        /var/run \
        /etc/supervisor \
        /etc/pgbouncer \
    && chmod +x /app/tscrawler/src/foxhound/foxhound \
    && echo "postgres ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/postgres \
    && chmod 0440 /etc/sudoers.d/postgres

# Override supervisord.conf to use paths writable by the postgres user
RUN printf '[unix_http_server]\nfile=/var/run/supervisor/supervisor.sock\nchmod=0700\n\n[supervisord]\nlogfile=/var/log/supervisor/supervisord.log\npidfile=/var/run/supervisor/supervisord.pid\nchildlogdir=/var/log/supervisor\nnodaemon=false\n\n[rpcinterface:supervisor]\nsupervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface\n\n[supervisorctl]\nserverurl=unix:///var/run/supervisor/supervisor.sock\n\n[include]\nfiles = /etc/supervisor/conf.d/*.conf\n' > /etc/supervisor/supervisord.conf

USER postgres
ENTRYPOINT ["/entrypoint.sh"]
