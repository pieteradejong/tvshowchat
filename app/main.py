import json
import logging.config
from fastapi import FastAPI
import uvicorn

from app.api import api

with open("logging_config.json", "r") as f:
    config = json.load(f)

logging.config.dictConfig(config)
logger = logging.getLogger("sampleApp")

app = FastAPI()
app.include_router(api.router)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting application...")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

