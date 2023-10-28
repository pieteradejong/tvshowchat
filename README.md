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

## Thoughts/observations during dev
* As I assemble the data set, I wonder what queries will return relevant results given the nature of the data (essentially descriptions of what occurs on the show) and the construction of the content embeddings for "similarity". It could be that the only useful queries are of the form "when did x happen" and not e.g. "what would character x say to character y".
* Verifying data integrity, structure, and completeness, is an interesting task. I optimized for readability, main structure of the `json` object, and meta data most relevant to the nature of the data, namely the presence of all seasons, and the exact set of expected episodes. As well as to a limited extent the expected metadata per episode. 
  * Locality of documentation: since this is a one-off, and the structure of the crawled data is highly coupled with both the crawling and its testing, there are many semi-hardcoded elements througout.

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
`curl -X POST "http://127.0.0.1:8000/search" -H "Content-Type: application/json" -d '{"query": "my test query"}'
`



