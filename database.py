import psycopg2
import os
from urllib.parse import urlparse

def get_connection():
    """Establish and return a connection to the PostgreSQL database."""
    # Parse database URL
    DATABASE_URL = os.getenv("DATABASE_URL")
    result = urlparse(DATABASE_URL)
    connection = psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )
