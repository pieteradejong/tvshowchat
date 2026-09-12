# Search accuracy: measurement and findings

Semantic search is the point of this app. Until 2026-09-12 there was no way to
tell whether a change to it helped or hurt — `tests/` held one 19-line file that
passes on a 404. This document records how accuracy is now measured, what the
measurements showed, and what follows from them.

Reproduce anything here with:

```bash
./venv/bin/python scripts/eval_retrieval.py            # both models
./venv/bin/python scripts/eval_retrieval.py minilm     # one model
```

---

## 1. How accuracy is measured

`scripts/eval_retrieval.py` scores a retrieval strategy against ground truth and
reports Recall@1, Recall@5, Recall@10 and MRR. Two kinds of query:

| Set | n | What it is | What it tests |
|---|---|---|---|
| `title` | 144 | Each episode's exact title | Entity lookup. Objective and free — every episode is its own ground truth. Not how users actually search, but a floor the system must clear. |
| `known` | 20 | Hand-written descriptions of memorable events ("episode where Buffy dies" → `s05e22`) | **Real usage.** This is the set that matters. |

The `all` row is dominated by the 144 title queries, so **read `known` when judging
semantic quality**. A big `all` number mostly means entity lookup works.

The known-answer set lives in `KNOWN_ANSWERS` in the script. It is the yardstick
everything else is judged against, so correcting a wrong entry there is worth more
than any amount of tuning. Twenty queries is small: a single query is 5 percentage
points of R@1, and differences under ~10 points on that set are noise.

---

## 2. The root cause: ~85% of the corpus was never indexed

`app/services/scraping/crawl.py:297` builds one vector per episode from the entire
joined summary:

```python
summary_text = " ".join(episode_page_data.get("summary", []))
episode_data["summary_embedding"] = embedder.encode(summary_text)...
```

`all-MiniLM-L6-v2` has `max_seq_length = 256`. Median episode summary: **~1,537
tokens**. Everything past the first 256 is silently discarded — no error, no warning.

Verified directly on `s05e22` *The Gift*:

- summary is **2,462 tokens** → **90% discarded**
- `cosine(vector_of_full_text, vector_of_first_256_tokens) = 1.0000`

The second line is the proof: the stored vector is computed from the opening of the
summary and nothing else. *The Gift* is the episode where Buffy dies; that event is
in the discarded 90%. Which is why the app's own example query, "episode where Buffy
dies", could not find it.

This is an indexing bug. It is unrelated to ChromaDB, the vector store, or the
hosting platform — all of which faithfully stored and searched a vector that only
ever represented the first paragraph or two.

---

## 3. Results

Same corpus, same 144 episodes. Two independent variables: how the text is chunked,
and which model embeds it.

**Indexing strategies**
- **A — episode-level:** one vector per episode from the whole joined summary. *What shipped.*
- **B — chunk-level:** one vector per summary paragraph, each prefixed with the episode title, scored max-over-chunks. 1,837 vectors, 2.7 MB as float32.

### `known` — the semantic set that matters (n=20)

| | R@1 | R@5 | R@10 | MRR |
|---|---|---|---|---|
| A · MiniLM **(shipped)** | 30.0% | 50.0% | 55.0% | 0.399 |
| A · BGE-small | 30.0% | 45.0% | 60.0% | 0.365 |
| B · MiniLM | 25.0% | 65.0% | 70.0% | 0.394 |
| **B · BGE-small** | **50.0%** | **80.0%** | **85.0%** | **0.624** |

### `title` — entity lookup (n=144)

| | R@1 | R@5 | MRR |
|---|---|---|---|
| A · MiniLM **(shipped)** | 8.3% | 17.4% | 0.122 |
| A · BGE-small | 10.4% | 19.4% | 0.146 |
| B · MiniLM | **93.8%** | **99.3%** | **0.964** |
| B · BGE-small | 92.4% | 97.9% | 0.948 |

### The finding that matters most

**Neither fix works alone. Both together work very well.**

- Better model, old chunking (A·MiniLM → A·BGE): MRR `0.399 → 0.365`. **No gain.**
  A stronger model is worthless when it can only see the first 256 tokens.
- Better chunking, old model (A·MiniLM → B·MiniLM): MRR `0.399 → 0.394` on the
  semantic set. Fixes title lookup spectacularly (8.3% → 93.8%) but semantic recall
  barely moves — MiniLM becomes the bottleneck as soon as truncation stops being one.
- **Both (A·MiniLM → B·BGE): R@5 `50% → 80%`, MRR `0.399 → 0.624`.**

Had we changed only one variable, the evidence would have said "this didn't help"
and the real fix might have been abandoned.

Note `bge-small-en-v1.5` is also **384-dimensional**, the same as MiniLM: the entire
accuracy gain costs nothing in index size.

---

## 4. What this implies for the architecture

- **Chunk-level indexing is required**, not an optimization. Paragraph granularity
  with a title prefix; keep the episode id on each chunk and aggregate max-over-chunks.
- **Include the title in indexed text.** Titles were never searchable before.
- **The embedding model is the lever on semantic quality**, but only after chunking.
- **Corpus size stays trivial.** 1,837 chunks ≈ 2.7 MB float32; two shows ≈ 5 MB.
  A vector database is still unnecessary — brute-force cosine over a few thousand
  vectors is microseconds. This does not change the lightweight plan.
- **Query and corpus vectors must come from the same model.** Whatever embeds the
  corpus offline must also embed the query at request time. That is the constraint
  that decides the deployment question, not bundle size.

### Open question

The deployment constraint is *no self-hosted model*, so the runtime query embedder
must be a hosted API. `bge-small` demonstrates that **model quality matters a great
deal once chunking is fixed**, and the mainstream hosted retrieval models are in or
above its quality class — but that is an inference, not a measurement.

**Before committing to a hosted model, run this harness against it.** The script
takes a model key; add the hosted provider as another entry in `MODELS` and compare
on the same ground truth. Indexing 1,837 chunks is a one-time offline cost of roughly
185k tokens.

---

## 5. Guarding against regressions

Two different harnesses, two different jobs:

| Script | Question | When |
|---|---|---|
| `scripts/eval_retrieval.py` | *Is retrieval accurate?* Ground truth, absolute score. | Any change to chunking, model, or ranking. |
| `scripts/capture_search_baseline.py` | *Did the ranked output change unintentionally?* No ground truth, pure diff against a recorded snapshot. | Refactors meant to preserve behaviour — e.g. the ChromaDB → brute-force rewrite. |

Use `capture_search_baseline.py` to prove a refactor changed nothing, holding the
model constant. Use `eval_retrieval.py` to prove a deliberate change improved things,
and re-record the baseline afterwards.
