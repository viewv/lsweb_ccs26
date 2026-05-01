import asyncio
from tortoise import Tortoise

from database.db_config import Config

# Database connection parameters
DB_USER = Config.DB_USER
DB_PASSWORD = Config.DB_PASSWORD
DB_HOST = Config.DB_HOST
DB_PORT = Config.DB_PORT
DB_NAME = Config.DB_NAME

# Construct the database URL
DATABASE_URL = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Tortoise ORM configuration
TORTOISE_ORM = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "models": {
            # Correct reference to your models module
            "models": ["database.model.sites"],
            "default_connection": "default",
        },
    },
}


async def init_db():
    if not Tortoise._inited:
        print("Initializing database connection...")
        await Tortoise.init(config=TORTOISE_ORM)
        await Tortoise.generate_schemas()

        # Create indexes
        await Tortoise.get_connection("default").execute_script("""
            CREATE INDEX IF NOT EXISTS idx_site_rank ON sites (rank);
            CREATE INDEX IF NOT EXISTS idx_site_url ON sites (url);
            CREATE INDEX IF NOT EXISTS idx_headers_state ON sites (experiment_headers_state);
            CREATE INDEX IF NOT EXISTS idx_inclusions_state ON sites (experiment_inclusions_state);
            CREATE INDEX IF NOT EXISTS idx_cxss_state ON sites (experiment_cxss_state);
            CREATE INDEX IF NOT EXISTS idx_pmsecurity_state ON sites (experiment_pmsecurity_state);
        """)
    else:
        print("Database connection already established.")


async def close_db():
    if Tortoise._inited:
        print("Closing database connection...")
        await Tortoise.close_connections()
    else:
        print("Database connection already closed.")


def init():
    asyncio.run(init_db())


if __name__ == "__main__":
    asyncio.run(init_db())
    print("Database and indexes created successfully!")
