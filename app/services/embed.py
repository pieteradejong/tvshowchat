import numpy as np
import json
import redis
from app.config.config import logger, K_RESULTS

from sentence_transformers import SentenceTransformer

from redis.commands.search.field import (
    TextField,
    VectorField,
)
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query

# Constants
REDIS_HOST = "localhost"
REDIS_PORT = 6379
CONTENT_PATH = "app/content/buffy_data.json"
VECTOR_DIMENSION = 384  # all-MiniLM-L6-v2 uses 384 dimensions

client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
embedder = SentenceTransformer("all-MiniLM-L6-v2")  # Fast, good for dialogue, small memory footprint


def load_content(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


"""
Pipeline is tailored to this particular content.
"""


def create_pipeline(buffy_json):
    pipeline = client.pipeline()
    key_prefix = "buffy:"

    for ix, season_label in enumerate(buffy_json, start=1):
        key_full = f"{key_prefix}s{ix:02}"  # 'buffy:s03'

        synopsis = "".join(buffy_json[season_label]["Synopsis"])
        summary = "".join(buffy_json[season_label]["Summary"])

        synopsis_embedding = embedder.encode(synopsis).astype(np.float32).tolist()
        summary_embedding = embedder.encode(summary).astype(np.float32).tolist()

        obj = {
            "synopsis": synopsis,
            "summary": summary,
            "synopsis_embedding": synopsis_embedding,
            "summary_embedding": summary_embedding,
        }

        pipeline.json().set(key_full, "$", obj)

    return pipeline


def execute_pipeline(pipeline):
    try:
        res = pipeline.execute()
        logger.info(f"Pipeline successfully executed: {res}")
    except Exception as e:
        logger.info(f"Error executing pipeline: {e}")
    # TODO return execution result


def create_index():
    schema = (
        TextField("$.synopsis", no_stem=False, as_name="synopsis"),
        TextField("$.summary", no_stem=False, as_name="summary"),
        VectorField(
            "$.synopsis_embedding",
            "FLAT",
            {
                "TYPE": "FLOAT32",
                "DIM": VECTOR_DIMENSION,
                "DISTANCE_METRIC": "COSINE",
            },
            as_name="synopsis_embedding",
        ),
        VectorField(
            "$.summary_embedding",
            "FLAT",
            {
                "TYPE": "FLOAT32",
                "DIM": VECTOR_DIMENSION,
                "DISTANCE_METRIC": "COSINE",
            },
            as_name="summary_embedding",
        ),
    )

    definition = IndexDefinition(prefix=["buffy:"], index_type=IndexType.JSON)
    try:
        client.ft("idx:buffy_vss").create_index(fields=schema, definition=definition)

        index_info = client.ft("idx:buffy_vss").info()

        index_name = index_info.get("index_name", "N/A")
        duration = index_info.get("total_indexing_time", "N/A")
        num_docs = index_info.get("num_docs", "N/A")

        logger.info(
            (
                f"Index [{index_name}] was created "
                f"in [{duration}] seconds with [{num_docs}] documents"
            )
        )

    except Exception as e:
        logger.error(f"Error creating index: {e}")
        return {}

    return index_info


def fetch_search_results(query_text: str = "", k: int = None) -> list[str]:
    if k is None:
        k = K_RESULTS
    if not query_text:
        logger.warn("Empty query text submitted.")
        return []

    query_text_embedding = embedder.encode(query_text)

    redis_query = (
        Query("(*)=>[KNN 3 @summary_embedding $query_vector AS vector_score]")
        .sort_by("vector_score")
        .return_fields("vector_score", "synopsis", "summary")
        .dialect(2)
    )

    query_result = (
        client.ft("idx:buffy_vss")
        .search(redis_query, {"query_vector": query_text_embedding.tobytes()})
        .docs
    )

    res = []
    for document in query_result:
        res.append(
            {
                prop: document[prop]
                for prop in ["id", "vector_score", "summary", "synopsis"]
            }
        )

    return sorted(res, key=lambda x: x["vector_score"])


def main_new():
    client.flushdb()

    content_json = load_content(CONTENT_PATH)
    pipeline = create_pipeline(content_json)
    execute_pipeline(pipeline)
    create_index()
    fetch_search_results()


if __name__ == "__main__":
    main_new()
