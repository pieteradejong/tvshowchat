from fastapi import FastAPI, HTTPException
import uvicorn
from app.config.config import logger
from app.api import api
from app.api.routes import search as search_router
from fastapi.middleware.cors import CORSMiddleware
from app.services.embed import (
    client,
    load_content,
    create_pipeline,
    execute_pipeline,
    create_index,
)
from app.services.embed import CONTENT_PATH
from app.services.storage.document_store import get_store
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Dict, Any
import json

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5175"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api.router)
app.include_router(search_router.router, prefix="/api")
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.parent.absolute() / "static"),
    name="static",
)

# Track service status
service_status: Dict[str, Any] = {
    "redis": {"status": "unknown", "error": None},
    "model": {"status": "unknown", "error": None},
    "data": {"status": "unknown", "error": None},
    "store": {"status": "unknown", "error": None}
}

@app.on_event("startup")
async def startup_event():
    logger.info("Main.py: Starting application...")

    # Initialize Redis
    try:
        client.ping()
        service_status["redis"]["status"] = "healthy"
        logger.info("Redis connection successful")
    except Exception as e:
        service_status["redis"]["status"] = "unhealthy"
        service_status["redis"]["error"] = str(e)
        logger.error(f"Redis connection failed: {e}")

    # Initialize Document Store
    try:
        store = get_store()
        # Test store by checking if any seasons exist
        if not list(store.episodes_path.glob("season_*.json")):
            logger.info("Store empty, importing data...")
            # Find latest JSON file
            content_dir = Path(CONTENT_PATH).parent
            json_files = list(content_dir.glob("buffy_all_seasons_*.json"))
            if json_files:
                latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
                store.import_from_json(str(latest_file))
                logger.info(f"Imported data from {latest_file}")
            else:
                logger.warning("No JSON data files found to import")
        
        service_status["store"]["status"] = "healthy"
        logger.info("Document store initialized successfully")

    except Exception as e:
        service_status["store"]["status"] = "unhealthy"
        service_status["store"]["error"] = str(e)
        logger.error(f"Document store initialization failed: {e}")

    # Load and process data if Redis is healthy
    if service_status["redis"]["status"] == "healthy":
        try:
            client.flushdb()
            logger.info("Flushed the Redis database.")

            # Load data from document store
            store = get_store()
            buffy_data = {}
            
            # Load each season
            for season_file in store.episodes_path.glob("season_*.json"):
                season_num = int(season_file.stem.split('_')[1])
                with open(season_file, 'r') as f:
                    season_data = json.load(f)
                buffy_data[f"season_{season_num}"] = season_data

            pipeline = create_pipeline(buffy_data)
            logger.info("Created pipeline.")

            execute_pipeline(pipeline)
            logger.info("Executed pipeline.")

            create_index()
            logger.info("Created index.")

            service_status["data"]["status"] = "healthy"
        except Exception as e:
            service_status["data"]["status"] = "unhealthy"
            service_status["data"]["error"] = str(e)
            logger.error(f"Data processing failed: {e}")

    # Verify model
    try:
        from app.services.embed import embedder
        # Test model with a simple string
        embedder.encode("test")
        service_status["model"]["status"] = "healthy"
        logger.info("Model verification successful")
    except Exception as e:
        service_status["model"]["status"] = "unhealthy"
        service_status["model"]["error"] = str(e)
        logger.error(f"Model verification failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Main.py: Shutting down application...")
    # No need to close document store as it's file-based
    pass

@app.get("/health")
async def health_check():
    """Overall health check endpoint."""
    overall_status = "healthy" if all(s["status"] == "healthy" for s in service_status.values()) else "degraded"
    return {
        "status": overall_status,
        "services": service_status
    }

@app.get("/health/redis")
async def redis_health_check():
    """Redis health check endpoint."""
    if service_status["redis"]["status"] == "healthy":
        return {"status": "healthy", "message": "Redis connection is healthy"}
    raise HTTPException(
        status_code=503,
        detail=f"Redis is unhealthy: {service_status['redis']['error']}"
    )

@app.get("/health/model")
async def model_health_check():
    """Model health check endpoint."""
    if service_status["model"]["status"] == "healthy":
        return {"status": "healthy", "message": "Model is healthy"}
    raise HTTPException(
        status_code=503,
        detail=f"Model is unhealthy: {service_status['model']['error']}"
    )

@app.get("/health/store")
async def store_health_check():
    """Document store health check endpoint."""
    if service_status["store"]["status"] == "healthy":
        return {"status": "healthy", "message": "Document store is healthy"}
    raise HTTPException(
        status_code=503,
        detail=f"Document store is unhealthy: {service_status['store']['error']}"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
