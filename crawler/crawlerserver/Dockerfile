# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /src
COPY ./src /src

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir pyzmq tranco tortoise-orm[asyncpg] tortoise-orm[accel]

# Make port 5555 available to the world outside this container
EXPOSE 5555

# Run zmq_server.py when the container launches
CMD ["python3", "zmq_server.py"]