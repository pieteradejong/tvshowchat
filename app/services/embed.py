import numpy as np
import json
import redis

from sentence_transformers import SentenceTransformer

from redis.commands.search.field import (
    TextField,
    VectorField,
)
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query

"""
Steps:
- choose model
- create embeddings for data
- store embeddings in db
- create index in db

"""
"""
    redis schema design:
    key: <show_name:season_number>; 
        field: [summary:, synopsis], v: string
        field: embedding, v: list of numbers
    example: buffy:s1 summary text synopsis text


"""


def get_index_info(redis: redis.Redis, index_id: str) -> dict:
    info = redis.ft(index_id).info()
    num_docs = info["num_docs"]
    indexing_failures = info["hash_indexing_failures"]
    print(f"{num_docs} documents indexed with {indexing_failures} failures")
    return info


def get_redis() -> redis.Redis:
    client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    client.flushdb()
    return client


def load_data() -> dict:
    pass


def search(query: str = "", top_k: int = 3) -> list[str]:
    """
    Returns top k matches for query.
    - embedder.encode(query)
    """
    pass

    return []


def main():
    client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    client.flushdb()

    with open("content/buffy_data.json", "r") as f:
        buffy_json = json.load(f)

    embedder = SentenceTransformer("msmarco-distilbert-base-v4")
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

    res = pipeline.execute()
    print(f"pipeline successfully executed: {res}")

    VECTOR_DIMENSION = 768  # TODO is this number related to our chosen embedding model?
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
    client.ft("idx:buffy_vss").create_index(fields=schema, definition=definition)

    # TODO insert print/logger index created and how many docs, etc

    query_text_embedding = embedder.encode("this is a buffy summary query")

    query = (
        Query("(*)=>[KNN 3 @summary_embedding $query_vector AS vector_score]")
        .sort_by("vector_score")
        .return_fields("vector_score", "synopsis", "summary")
        .dialect(2)
    )

    result = (
        client.ft("idx:buffy_vss")
        .search(query, {"query_vector": query_text_embedding.tobytes()})
        .docs
    )

    res = []
    for d in result:
        res.append(
            {prop: d[prop] for prop in ["id", "vector_score", "summary", "synopsis"]}
        )
    return sorted(res, key=lambda x: x["vector_score"])


if __name__ == "__main__":
    main()
