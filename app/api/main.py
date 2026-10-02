from fastapi import FastAPI, HTTPException
import uvicorn
from app.config.config import logger
from app.api import api
from app.api.routes import search as search_router
from app.api.routes import series as series_router
from app.api.routes import experiments as experiments_router
from fastapi.middleware.cors import CORSMiddleware
from app.services.storage.document_store import get_store
from app.services.vector_store import get_vector_store
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Dict, Any
from app.services.series_vis_data import build_v1_datasets

ROOT_DIR = Path(__file__).resolve().parents[2]
CONTENT_FILE = ROOT_DIR / "app/content/btvs_all_seasons.json"
EPISODES_LIST_FILE = ROOT_DIR / "app/data/episodes/episodes.json"
CHAR_ARCS_FILE = ROOT_DIR / "app/data/episodes/character_arcs.json"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5175",  # React dev server
        "https://tvshowchat1.onrender.com",  # Production deployment
    ],
    allow_credentials=False,  # no cookies or auth; never send credentials cross-origin
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes FIRST (before static files) so they take precedence
app.include_router(search_router.router, prefix="/api")
app.include_router(series_router.router, prefix="/api")
app.include_router(experiments_router.router, prefix="/api")
app.include_router(api.router)  # Root route must come after API routes

# Mount static files for frontend assets (CSS, JS, images, etc.)
# This serves files from app/static/assets/ and other static files
static_dir = Path(__file__).parent.parent.absolute() / "static"
if static_dir.exists() and static_dir.is_dir():
    # Mount assets directory for Vite-built assets
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=assets_dir),
            name="assets",
        )
        logger.info(f"Assets mounted from {assets_dir}")
    
    # Also mount root static directory for other static files (vite.svg, etc.)
    app.mount(
        "/static",
        StaticFiles(directory=static_dir),
        name="static",
    )
    logger.info(f"Static files mounted from {static_dir}")
else:
    logger.warning(f"Static directory not found at {static_dir}, skipping static file mount")

# Track service status
service_status: Dict[str, Any] = {
    "model": {"status": "unknown", "error": None},
    "data": {"status": "unknown", "error": None},
    "store": {"status": "unknown", "error": None},
    "vector_store": {"status": "unknown", "error": None}
}

@app.on_event("startup")
async def startup_event():
    logger.info("Main.py: Starting application...")

    # Initialize Document Store
    try:
        store = get_store()
        # Test store by checking if any seasons exist (exclude season_stats.json)
        season_files = [f for f in store.episodes_path.glob("season_*.json") if f.name != "season_stats.json"]
        if not season_files:
            logger.info("Store empty, importing data...")
            if CONTENT_FILE.exists():
                store.import_from_json(str(CONTENT_FILE))
                logger.info(f"Imported data from {CONTENT_FILE.relative_to(ROOT_DIR)}")
            else:
                logger.warning(f"Content file missing at {CONTENT_FILE.relative_to(ROOT_DIR)}")
        
        service_status["store"]["status"] = "healthy"
        logger.info("Document store initialized successfully")

    except Exception as e:
        service_status["store"]["status"] = "unhealthy"
        service_status["store"]["error"] = type(e).__name__
        logger.error(f"Document store initialization failed: {e}")

    # Initialize Vector Store - the index itself is built lazily on first search
    try:
        get_vector_store()
        service_status["vector_store"]["status"] = "healthy"
        logger.info("Vector store initialized successfully")
    except Exception as e:
        service_status["vector_store"]["status"] = "unhealthy"
        service_status["vector_store"]["error"] = type(e).__name__
        logger.error(f"Vector store initialization failed: {e}")

    # Verify model through vector store (model is already loaded there)
    try:
        if service_status["vector_store"]["status"] == "healthy":
            # Test model by encoding a simple string using the vector store's embedder
            vector_store = get_vector_store()
            vector_store.embedder.encode("test")
            service_status["model"]["status"] = "healthy"
            logger.info("Model verification successful (via vector store)")
        else:
            service_status["model"]["status"] = "unhealthy"
            service_status["model"]["error"] = "Vector store not initialized"
            logger.warning("Model verification skipped: vector store not healthy")
    except Exception as e:
        service_status["model"]["status"] = "unhealthy"
        service_status["model"]["error"] = type(e).__name__
        logger.error(f"Model verification failed: {e}")
    
    # Mark data as healthy if store and vector store are healthy
    if (service_status["store"]["status"] == "healthy" and 
        service_status["vector_store"]["status"] == "healthy"):
        service_status["data"]["status"] = "healthy"
    else:
        service_status["data"]["status"] = "unhealthy"

    # Build v1 visualization datasets if missing (lightweight, fast)
    try:
        if not (EPISODES_LIST_FILE.exists() and CHAR_ARCS_FILE.exists()):
            logger.info("Building v1 visualization datasets...")
            build_v1_datasets(
                episodes_dir=ROOT_DIR / "app/data/episodes",
                output_dir=ROOT_DIR / "app/data/episodes",
            )
            logger.info("Visualization datasets created.")
    except Exception as e:
        logger.error(f"Failed to build visualization datasets: {e}")

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
    """Redis health check endpoint (deprecated - use /health/vector-store)."""
    raise HTTPException(
        status_code=410,
        detail="Redis endpoint deprecated. Use /health/vector-store instead."
    )

@app.get("/health/chromadb")
async def chromadb_health_check():
    """ChromaDB health check endpoint (removed - ChromaDB is no longer used)."""
    raise HTTPException(
        status_code=410,
        detail="ChromaDB was replaced by an in-memory index. Use /health/vector-store instead."
    )

@app.get("/health/vector-store")
async def vector_store_health_check():
    """Vector store health check endpoint."""
    if service_status["vector_store"]["status"] == "healthy":
        return {"status": "healthy", "message": "Vector store is healthy"}
    raise HTTPException(
        status_code=503,
        detail="Vector store is unhealthy"
    )

@app.get("/health/model")
async def model_health_check():
    """Model health check endpoint."""
    if service_status["model"]["status"] == "healthy":
        return {"status": "healthy", "message": "Model is healthy"}
    raise HTTPException(
        status_code=503,
        detail="Model is unhealthy"
    )

@app.get("/health/store")
async def store_health_check():
    """Document store health check endpoint."""
    if service_status["store"]["status"] == "healthy":
        return {"status": "healthy", "message": "Document store is healthy"}
    raise HTTPException(
        status_code=503,
        detail="Document store is unhealthy"
    )

@app.get("/health/pipeline")
async def pipeline_health_check():
    """Pipeline health check endpoint showing episode counts at each stage."""
    try:
        from app.services.vector_store import get_vector_store
        from app.services.storage.document_store import get_store
        import json
        
        pipeline_status = {
            "status": "healthy",
            "stages": {}
        }
        
        # Stage 1: Content JSON
        content_file = ROOT_DIR / "app" / "content" / "btvs_all_seasons.json"
        if content_file.exists():
            with content_file.open("r", encoding="utf-8") as f:
                content_data = json.load(f)
            content_counts = {
                int(k.split("_")[1]): len(v)
                for k, v in content_data.items()
                if k.startswith("season_")
            }
            pipeline_status["stages"]["content"] = {
                "status": "healthy",
                "file": str(content_file.relative_to(ROOT_DIR)),
                "total_episodes": sum(content_counts.values()),
                "season_counts": content_counts,
                "seasons": len(content_counts)
            }
        else:
            pipeline_status["stages"]["content"] = {
                "status": "missing",
                "file": str(content_file.relative_to(ROOT_DIR)),
                "error": "Content file not found"
            }
            pipeline_status["status"] = "degraded"
        
        # Stage 2: Document Store
        try:
            store = get_store()
            doc_counts = {}
            episodes_dir = store.episodes_path
            if episodes_dir.exists():
                for season_file in sorted(episodes_dir.glob("season_*.json")):
                    if season_file.name == "season_stats.json":
                        continue
                    try:
                        season_num = int(season_file.stem.split("_")[1])
                    except (ValueError, IndexError):
                        continue
                    with season_file.open("r", encoding="utf-8") as f:
                        doc_counts[season_num] = len(json.load(f))
                
                # Check embeddings
                embed_counts = {}
                embeddings_dir = store.embeddings_path
                if embeddings_dir.exists():
                    for embed_file in sorted(embeddings_dir.glob("season_*_embeddings.json")):
                        season_num = int(embed_file.stem.split("_")[1])
                        with embed_file.open("r", encoding="utf-8") as f:
                            embed_counts[season_num] = len(json.load(f))
                
                pipeline_status["stages"]["document_store"] = {
                    "status": "healthy",
                    "total_episodes": sum(doc_counts.values()),
                    "season_counts": doc_counts,
                    "seasons": len(doc_counts),
                    "embeddings": {
                        "total": sum(embed_counts.values()),
                        "season_counts": embed_counts,
                        "seasons": len(embed_counts)
                    } if embed_counts else None
                }
            else:
                pipeline_status["stages"]["document_store"] = {
                    "status": "missing",
                    "error": "Document store directory not found"
                }
                pipeline_status["status"] = "degraded"
        except Exception as e:
            pipeline_status["stages"]["document_store"] = {
                "status": "error",
                "error": type(e).__name__
            }
            pipeline_status["status"] = "degraded"
        
        # Stage 3: Vector index
        try:
            vector_store = get_vector_store()
            stats = vector_store.get_stats()
            pipeline_status["stages"]["vector_index"] = {
                "status": "healthy",
                "total_episodes": stats.get("total_episodes", 0),
                "indexed_episodes": stats.get("indexed_episodes", 0),
                "season_counts": {
                    int(k): v for k, v in stats.get("season_counts", {}).items()
                },
                "seasons": len(stats.get("seasons", [])),
                "collection_name": stats.get("collection_name", "unknown")
            }
        except Exception as e:
            pipeline_status["stages"]["vector_index"] = {
                "status": "error",
                "error": type(e).__name__
            }
            pipeline_status["status"] = "degraded"
        
        # Validate consistency
        stages = pipeline_status["stages"]
        if all(s.get("status") == "healthy" for s in stages.values()):
            totals = [
                stages.get("content", {}).get("total_episodes"),
                stages.get("document_store", {}).get("total_episodes"),
                stages.get("vector_index", {}).get("total_episodes")
            ]
            if totals and all(t == totals[0] for t in totals if t is not None):
                pipeline_status["status"] = "healthy"
                pipeline_status["consistency"] = "all_stages_match"
            else:
                pipeline_status["status"] = "degraded"
                pipeline_status["consistency"] = "counts_mismatch"
                pipeline_status["totals"] = {
                    "content": totals[0],
                    "document_store": totals[1],
                    "vector_index": totals[2]
                }
        
        return pipeline_status
        
    except Exception as e:
        logger.error(f"Pipeline health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Pipeline health check failed"
        ) from e

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
