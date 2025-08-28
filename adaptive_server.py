# main.py

from fastapi import FastAPI
import os
from contextlib import asynccontextmanager
import app_context
from routes import router as api_router
from database import EnhancedMongoDBManager

# Global variable for database manager
db_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous context manager for managing the application's lifespan.
    This function is executed at startup and shutdown of the application.
    """
    # Startup: Initialize the database manager and connect to MongoDB
    app_context.db_manager = EnhancedMongoDBManager(
        connection_string=os.getenv("MONGODB_URI", "mongodb://localhost:27017/"),
        database_name=os.getenv("DATABASE_NAME", "cat_assessment")
    )
    print("Connected to MongoDB")

    yield

    # Shutdown: Close the MongoDB connection if the database manager exists
    if app_context.db_manager:
        app_context.db_manager.close_connection()
        print("Disconnected from MongoDB")

# Initialize FastAPI app with the defined lifespan
app = FastAPI(title="STEDPrep API", version="5.0.0", lifespan=lifespan)

# Include the main API router
app.include_router(api_router)

@app.get("/")
async def root():
    """
    Root endpoint for the API.
    Returns the name and version of the API.
    """
    return {"name": "STEDPrep API", "version": "5.0.0"}

