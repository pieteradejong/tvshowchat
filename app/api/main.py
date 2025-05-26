from fastapi import FastAPI, HTTPException
import uvicorn
from app.config.config import logger

from app.api import api

from app.services.embed import (
    client,
    load_content,
    create_pipeline,
    execute_pipeline,
    create_index,
)
from app.services.embed import CONTENT_PATH

from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Dict, Any

app = FastAPI()
app.include_router(api.router)
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.parent.absolute() / "static"),
    name="static",
)

# Track service status
service_status: Dict[str, Any] = {
    "redis": {"status": "unknown", "error": None},
    "model": {"status": "unknown", "error": None},
    "data": {"status": "unknown", "error": None}
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

    # Load and process data if Redis is healthy
    if service_status["redis"]["status"] == "healthy":
        try:
            client.flushdb()
            logger.info("Flushed the Redis database.")

            buffy_json = load_content(CONTENT_PATH)
            logger.info("Loaded Buffy data.")

            pipeline = create_pipeline(buffy_json)
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

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
