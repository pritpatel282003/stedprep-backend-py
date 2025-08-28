from typing import Optional
from fastapi import HTTPException
from database import EnhancedMongoDBManager

# Global database manager instance, shared across different modules/routers.
# This variable is initialized at application startup.
db_manager: Optional[EnhancedMongoDBManager] = None


def get_db() -> EnhancedMongoDBManager:
    """
    FastAPI dependency function to get the shared database manager instance.
    This function is used in route handlers to access the database.

    Raises:
        HTTPException: If the database manager has not been initialized.

    Returns:
        EnhancedMongoDBManager: The initialized database manager instance.
    """
    global db_manager
    if db_manager is None:
        # This should not happen in a normal application lifecycle,
        # as the db_manager is initialized at startup.
        raise HTTPException(status_code=500, detail="Database not initialized")
    return db_manager


