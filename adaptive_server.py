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
    # Startup
    app_context.db_manager = EnhancedMongoDBManager(
        connection_string=os.getenv("MONGODB_URI", "mongodb://localhost:27017/"),
        database_name=os.getenv("DATABASE_NAME", "cat_assessment")
    )
    print("Connected to MongoDB")
    yield
    # Shutdown
    if app_context.db_manager:
        app_context.db_manager.close_connection()
        print("Disconnected from MongoDB")

# Initialize FastAPI app with lifespan
app = FastAPI(title="STEDPrep API", version="5.0.0", lifespan=lifespan)

app.include_router(api_router)

@app.get("/")
async def root():
    return {"name": "STEDPrep API", "version": "5.0.0"}

