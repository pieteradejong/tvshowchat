from fastapi import FastAPI
import uvicorn
from app.config import logger

from app.api import api

from app.services.embed import (
    client,
    load_content,
    create_pipeline,
    execute_pipeline,
    create_index,
)
from app.services.embed import CONTENT_PATH

app = FastAPI()
app.include_router(api.router)


@app.on_event("startup")
async def startup_event():
    logger.info("Main.py: Starting application...")

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

    except Exception as e:
        logger.error(f"Startup failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Main.py: Shutting down application...")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
