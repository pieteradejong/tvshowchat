# TV Show Chat
Get answers to questions about tv shows based on vector embeddings.

[![pytest](https://github.com/pieteradejong/tvshowchat/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/pieteradejong/tvshowchat/actions/workflows/ci.yml)

**Purpose**
Experiment with vector databases.

**Audience**:
Anyone interested in FastAPI and vector databases.

## Lessons learned
* Start with MVP, with emphasis on the M.
* Pay close attention to what library/module methods accept and return (even if it seems obvious).
* Bug: was pre-formatting the embedding vectors into json, and then sending them to `pipeline.json()`, which was redundant.
* 

## Architecture
1) Data corpus (set of content, e.g. json)
2) "bit" of content -> "Embedding-encoder" -> Vector-embedding
3) query -> "Embedding-encoder" -> Query-embedding -> use index to search within distance, e.g. HNWS within cosine distance.
4) Retreive similar(*) vectors and return to user via API.

(*) = The embedding is the crux of this retrieval method: it determines how "similar" any two data units are. 

Schema example:

```
buffy:s01 {
            synopsis: "mfklfjlskgjfkldhgfdkhvgfjkd"
            synopsis_embedding: "[<vector>]"
            summary: "mfckljfrieoufhgrjohdughfu"
            summary_embedding: [<vector>]
}
```




## Architecture
* Frontend (React) (Docker container)
* FastAPI (Docker)
* Redis (Docker)

## Design
* Crawl: Script tailored for crawling specific content from specific URLs, for
Buffy the Vampire Slayer. Sole purpose is to generate initial content to 
seed vector database. Creating quality content for such purposes is likely
to remain closer to one-off tasks than automatable.
* API
  * Query endpoint: Something like `GET /query`, but first we need to understand the vector database's API and what a req/resp looks like.
* Embedding. 
* Vector database: go with redis because widely used and to gain experience.


## MVP TODO 
* [ DONE ] Crawl 
* [ ] API query endpoint
* [ ] add embeddings to database
* [ ] frontend: question field and room for answer text.


## Run


## Test




