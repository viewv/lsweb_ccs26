FROM mcr.microsoft.com/playwright:v1.33.0-focal
ENV TZ=Europe/Berlin
ENV DEBIAN_FRONTEND noninteractive
ARG EXPERIMENT

# Set container timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -y nano build-essential software-properties-common

# Create directory for crawler source & crawler data path
RUN mkdir -p /typescript-crawler
RUN mkdir -p /typescript-crawler-data
RUN mkdir -p /foxhound

# Install VNC and fluxbox to interact with headfull runs
# RUN apt-get install -y x11vnc fluxbox

# Install database client
RUN apt-get install -y postgresql-client

# Install python3 and 
RUN apt-get install -y python3.10 python3-pip
# Install dependencies for pmsecurity experiment (pmforce)
RUN pip3 install z3-solver==4.8.7.0 ply

# Install python2
RUN apt-get install -y python2.7 python2.7-dev
# Install dependencies for cxss experiment (exploit generator)
RUN apt-get install -y libxml2-dev libxslt-dev cmake pkg-config 
RUN mkdir -p /install 
WORKDIR /install
# Install pip for python2 to install exploit generator dependencies later
RUN curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py
RUN python2.7 get-pip.py 

# COPY foxhound
COPY ./.resource/foxhound /foxhound
RUN chmod +x /foxhound/foxhound

# Copy project source
COPY ./src/ /typescript-crawler 
WORKDIR /typescript-crawler 

# Install dependencies for cxss experiment (exploit generator)
WORKDIR /typescript-crawler/snippets/cxss/persistent-clientside-xss/src 
RUN pip install -r requirements.txt

# Go back to crawler directory
WORKDIR /typescript-crawler 

# Install dependencies of crawler code (npm)
RUN npm install

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Make required experiment scripts executable
RUN chmod +x experiment-analysis.sh
RUN chmod +x experiment-stop.sh
RUN chmod +x experiment.sh

RUN chmod +x setup/prepare.sh 
RUN chmod +x setup/spawn.sh 

# Install dependencies for test server (local testing)
WORKDIR /typescript-crawler/snippets/insecure-webpages 
RUN npm install

# Install PM2
RUN npm install pm2 -g

# Add unprivileged user
RUN useradd -ms /bin/bash typescriptcrawler

# Change ownership of relevant files for crawler to new user
RUN chown -R typescriptcrawler /typescript-crawler 
RUN chown -R typescriptcrawler /typescript-crawler-data 
RUN chown -R typescriptcrawler /foxhound

USER typescriptcrawler

# Update workdir
WORKDIR /typescript-crawler 

# Start entrypoint script, which starts Xvfb and opens VNC session
ENTRYPOINT ["/bin/bash", "/typescript-crawler/entrypoint.sh"]