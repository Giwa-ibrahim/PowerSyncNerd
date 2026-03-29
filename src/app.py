import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database_store.database_client import DatabaseClient
from src.api.routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("powerdigest_app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    db = DatabaseClient()
    db.create_table()
    db.close()
    yield
    # Shutdown actions
    pass

# Initialize main FastAPI application
app = FastAPI(title="PowerDigest API", lifespan=lifespan)

# Include the endpoints
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    # Local automated deployment test
    uvicorn.run("src.app:app", host="0.0.0.0", port=10000, reload=True)
