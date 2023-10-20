# TV Show Chat
Get answers to questions about tv shows based on vector embeddings.

[![pytest](https://github.com/pieteradejong/tvshowchat/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/pieteradejong/tvshowchat/actions/workflows/ci.yml)

**Purpose**
Experiment with vector databases.

**Audience**:
Anyone interested in FastAPI and vector databases.


## Design
* Crawl: Script tailored for crawling specific content from specific URLs, for
Buffy the Vampire Slayer. Sole purpose is to generate initial content to 
seed vector database. Creating quality content for such purposes is likely
to remain closer to one-off tasks than automatable.
* API

```python
GET /question
```


## Run


## Test


## TODO
[ ] Crawl 


## Roadmap
### MVP: 
* Backend:
  * API endpoint for query, a few fozen saved HTML/content files, a vector database with embeddings.
* Frontend:
  * Question field, and room for answer text.

