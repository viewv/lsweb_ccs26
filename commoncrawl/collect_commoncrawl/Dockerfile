FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    locales redis-server supervisor procps net-tools \
    curl wget bash zsh tmux screen \
  && sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen \
  && locale-gen \
  && rm -rf /var/lib/apt/lists/* \
  && apt-get clean \
  && pip install --upgrade pip 

# Copy all files into the app directory
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
