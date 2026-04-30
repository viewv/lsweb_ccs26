import os


class Config:
    ID: str = os.environ.get("ID", "0")
    ZMQ_SOCK: str = os.environ.get("ZMQ_HOST", "tcp://0.0.0.0:5555")
