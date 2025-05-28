import os
import glob
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List

# --- Data Loading ---
CONTENT_DIR = "app/content"
MODEL_NAME = "all-MiniLM-L6-v2"

# Find the latest season 1 data file
def get_latest_data_file():
    files = sorted(glob.glob(os.path.join(CONTENT_DIR, "buffy_all_seasons_*.json")), reverse=True)
    for f in files:
        with open(f, "r") as file:
            data = json.load(file)
            if "season_1" in data:
                return f
    raise FileNotFoundError("No season 1 data file found.")

# Load data and model at startup
DATA_FILE = get_latest_data_file()
with open(DATA_FILE, "r") as f:
    DATA = json.load(f)["season_1"]

MODEL = SentenceTransformer(MODEL_NAME)

# --- API Schema ---
class SearchRequest(BaseModel):
    query: str
    top_k: int = 3

class SearchResult(BaseModel):
    episode_number: str
    episode_title: str
    episode_airdate: str
    episode_summary: List[str]
    score: float

class SearchResponse(BaseModel):
    results: List[SearchResult]

# --- Cosine Similarity ---
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# --- Router ---
router = APIRouter()

@router.post("/search", response_model=SearchResponse)
def search_episodes(req: SearchRequest):
    query_embedding = MODEL.encode(req.query)
    results = []
    for ep in DATA.values():
        ep_embedding = np.array(ep["summary_embedding"])
        score = cosine_similarity(query_embedding, ep_embedding)
        results.append({
            "episode_number": ep["episode_number"],
            "episode_title": ep["episode_title"],
            "episode_airdate": ep["episode_airdate"],
            "episode_summary": ep["episode_summary"],
            "score": score,
        })
    # Sort by score descending
    results = sorted(results, key=lambda x: x["score"], reverse=True)[:req.top_k]
    return {"results": results} 