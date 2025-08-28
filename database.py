import os
from typing import Optional

# Re-export the DB manager from the diagnostic_test_folder to provide a stable import path.
# This avoids circular dependencies and keeps a clean import structure.
from diagnostic_test_folder.cat_bkt_system import EnhancedMongoDBManager as _EnhancedMongoDBManager  # noqa: F401


class EnhancedMongoDBManager(_EnhancedMongoDBManager):
    """
    A thin wrapper around the original EnhancedMongoDBManager to allow for a centralized
    and stable import path (`from database import EnhancedMongoDBManager`).

    This class sets default values for the MongoDB connection string and database name
    from environment variables, with fallback values for local development.
    """

    def __init__(self, connection_string: Optional[str] = None, database_name: Optional[str] = None):
        """
        Initializes the EnhancedMongoDBManager.

        Args:
            connection_string (Optional[str]): The MongoDB connection string.
                If not provided, it defaults to the value of the MONGODB_URI environment variable,
                or "mongodb://localhost:27017/" if the environment variable is not set.
            database_name (Optional[str]): The name of the database.
                If not provided, it defaults to the value of the DATABASE_NAME environment variable,
                or "cat_assessment" if the environment variable is not set.
        """
        # Set default connection string from environment variables or a local default
        connection_string = connection_string or os.getenv("MONGODB_URI", "mongodb://localhost:27017/")

        # Set default database name from environment variables or a local default
        database_name = database_name or os.getenv("DATABASE_NAME", "cat_assessment")

        # Call the parent class's constructor with the determined values
        super().__init__(connection_string=connection_string, database_name=database_name)



