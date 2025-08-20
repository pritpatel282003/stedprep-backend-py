from typing import Optional
from fastapi import HTTPException
from database import EnhancedMongoDBManager

# Global DB manager shared across routers
db_manager: Optional[EnhancedMongoDBManager] = None


def get_db() -> EnhancedMongoDBManager:
    """FastAPI dependency to access the shared DB manager"""
    global db_manager
    if db_manager is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return db_manager


