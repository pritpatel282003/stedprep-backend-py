import os
from typing import Optional

# Re-export the DB manager from the diagnostic_test_folder to provide a stable import path.
from diagnostic_test_folder.cat_bkt_system import EnhancedMongoDBManager as _EnhancedMongoDBManager  # noqa: F401


class EnhancedMongoDBManager(_EnhancedMongoDBManager):
    """
    Thin wrapper to allow importing the DB manager from `database.py`.
    Defaults DATABASE_NAME to env or 'cat_assessment'.
    """

    def __init__(self, connection_string: Optional[str] = None, database_name: Optional[str] = None):
        connection_string = connection_string or os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        database_name = database_name or os.getenv("DATABASE_NAME", "cat_assessment")
        super().__init__(connection_string=connection_string, database_name=database_name)



