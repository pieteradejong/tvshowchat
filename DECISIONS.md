# Decisions

Append-only. Supersede an entry with a new one that links back; don't edit old ones.

## 1. Replace ChromaDB with an exact in-memory cosine index
**Date:** 2026-10-01
**Context:** ChromaDB 0.4.22 carried one critical and one high Dependabot advisory with no patched
release in the 0.4 line, and the corpus is 144 vectors of 384 dims — far below the size where an
approximate index pays for itself. `docs/SEARCH_ACCURACY.md` had already concluded a vector
database was unnecessary.
**Decision:** Exact brute-force cosine over a unit-normalised NumPy matrix, built from the
document store on first search (`AdvancedVectorStore._nearest`). The candidate-then-boost pipeline
is unchanged: top `limit×3` (or `limit×2` with a season filter) by cosine, then character/theme
boosts. Rejected: upgrading ChromaDB (a large API jump to keep a dependency the data doesn't need).
**Verified:** `./venv/bin/pytest tests/unit/test_vector_index.py` → 9 passed;
`./venv/bin/pytest` → 47 passed.

## 2. Re-record the search ranking baseline on the exact engine
**Date:** 2026-10-01
**Context:** `tests/fixtures/search_baseline.json` (2026-09-12) was meant to prove the engine swap
changed nothing. Running `scripts/capture_search_baseline.py verify` twice against the *unchanged*
ChromaDB engine drifted on 9 and then 7 of 23 queries: HNSW is approximate, so the candidate set
fed into the boosts varied between runs. The baseline was one random draw and could not certify
anything.
**Decision:** Re-record the baseline on the exact engine, which drifted from the old baseline on
5 of 23 queries (all at rank 4–5 except the stopword query "the") — less than the old engine
drifted from itself. The new baseline is deterministic and is now the regression net for the
dependency upgrades. Rejected: tolerating drift in `verify` (it would also hide real regressions).
**Verified:** two `verify` runs on the exact engine produced identical rankings
(`diff` of both outputs, excluding log lines → no difference); after recapture,
`verify` → `OK - all 23 queries return identical top-5 rankings.`

## 3. Upgrade every Python dependency and lock with hashes
**Date:** 2026-10-01
**Context:** 53 open Dependabot alerts against `requirements.txt` (torch critical; aiohttp, lxml,
chromadb high), and nothing pinned transitive packages or their content.
**Decision:** Direct dependencies in `requirements.in` / `requirements-dev.in`, compiled by
`scripts/lock.sh` (uv, `--universal --generate-hashes`, PyPI only) into hash-locked
`requirements.txt` / `requirements-dev.txt`; installs use `--require-hashes`. Upgraded to current
releases (torch 2.2.1→2.14.1, sentence-transformers 2.5.1→6.1.0, numpy 1.26→2.5, FastAPI
0.104→0.142). Dropped `chromadb`, `aiohttp` (only dead modules used it), `websockets`,
`huggingface_hub`, `python-json-logger`, `python-dotenv` as direct pins (unused or transitive);
moved `black`/`mypy`/`ruff`/`pytest` out of the runtime image.
**Verified:** after a clean `--require-hashes` install, `scripts/capture_search_baseline.py verify`
→ `OK - all 23 queries return identical top-5 rankings.`; the corpus-vs-query model check in
`tests/integration/test_search_quality.py` passes (cosine > 0.999 on 4 episodes).
`pip-audit --strict --require-hashes --disable-pip -r requirements.txt` → `No known
vulnerabilities found` (same for `requirements-dev.txt`). The first lock had kept a stale
`python-dotenv==1.0.0` (uv prefers pins already in the output file); `scripts/lock.sh --upgrade`
re-resolved it to 1.2.4.

## 4. Pin the embedding model to a Hugging Face commit
**Date:** 2026-10-01
**Context:** Every load site called `SentenceTransformer("all-MiniLM-L6-v2")`, which resolves the
`main` revision on huggingface.co at each start. An upstream change — benign or not — would alter
query vectors silently while the corpus vectors stayed fixed. The `app/models/` copy was never
used (and its weights are gitignored).
**Decision:** `app/services/embedder.py` is the only loader, pinned to
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41` (the revision the corpus vectors match; it ships
`model.safetensors`, not a pickle). A unit test fails if any app code constructs the model
directly.
**Verified:** `./venv/bin/pytest tests/unit/test_embedder.py tests/integration/test_search_quality.py`
→ passed.
