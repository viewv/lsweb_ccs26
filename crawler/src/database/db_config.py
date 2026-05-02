import os

class Config:
    DB_NAME = os.environ.get("POSTGRES_DB", "sites")  # database name
    DB_USER = os.environ.get("PGUSER", "postgres")
    DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "strongpassword")
    DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")  # database host
    DB_PORT = os.environ.get("PG_PORT", "5432")  # database port
