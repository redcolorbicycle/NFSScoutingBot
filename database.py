import psycopg2
from urllib.parse import urlparse

class Database:
    """Handles database connection and operations."""
    def __init__(self, database_url):
        result = urlparse(database_url)
        self.connection = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port,
        )
    
    def get_cursor(self):
        return self.connection.cursor()
    
    def commit(self):
        self.connection.commit()
    
    def close(self):
        self.connection.close()
