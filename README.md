# TV Show Chat

A semantic search and chat application for TV show transcripts, built with Python and React.

## Table of Contents

- [Quick Start](#quick-start)
- [Features](#features)
- [Tech Stack](#tech-stack)
  - [Backend](#backend)
  - [Frontend](#frontend)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
  - [Backend](#backend-1)
  - [Frontend](#frontend-1)
- [Project Structure](#project-structure)
- [Data Pipeline](#data-pipeline)
- [Documentation](#documentation)
- [Development](#development)
  - [Adding New Episodes](#adding-new-episodes)
  - [Testing](#testing)
  - [Data Pipeline Utilities](#data-pipeline-utilities)
- [Contributing](#contributing)
- [License](#license)

## Quick Start

The repository already includes the full `btvs_all_seasons.json` dataset (Seasons 1–7). You only need to crawl if you want to refresh the source data.

1. **Initialize dependencies & environment**
   ```bash
   ./init.sh
   ```
   Creates/updates the Python 3.12 virtualenv, installs requirements, prepares data directories, and downloads the embedding model.

2. **Run the backend (FastAPI + Chroma)**
   ```bash
   ./run.sh
   ```
   Starts the API at http://localhost:8000 and ensures the document store/ChromaDB are populated from the existing dataset.

3. **Run the frontend (React/Vite)**
   ```bash
   ./run_frontend.sh
   ```
   Serves the UI at http://localhost:5173 and proxies API calls to the backend.

4. **Run the integrated test suite (optional)**
   ```bash
   ./test.sh
   ```
   Requires the backend to be running. Verifies health endpoints, search, document store, embeddings, and ensures the content/Chroma counts match (144 total episodes).

To refresh the dataset later, follow the [Multi-Season Refresh Workflow](#multi-season-refresh-workflow); otherwise no scraping is required.

## Features

- **Semantic Search**: Find relevant episodes and scenes using natural language queries
- **Vector Storage**: Efficient storage and retrieval of episode embeddings using ChromaDB
- **Modern UI**: Clean, responsive interface built with React and TailwindCSS
- **FastAPI Backend**: High-performance API with automatic OpenAPI documentation

## Tech Stack

### Backend
- Python 3.12
- FastAPI 0.104.1
- ChromaDB 0.4.22 (Vector Database)
- Sentence Transformers (Embeddings)
- Uvicorn (ASGI Server)

### Frontend
- React 18
- TypeScript
- TailwindCSS
- Vite

## Prerequisites

- Python 3.12 or later
- pip (Python package manager)
- git

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/tvshowchat.git
cd tvshowchat
```

2. Run the initialization script:
```bash
./init.sh
```

This will:
- Create a Python virtual environment
- Install all required dependencies
- Set up the data directories
- Initialize the ChromaDB vector store
- Download the embedding model

## Running the Application

### Backend

1. Start the backend server:
```bash
./run.sh
```

This will:
- Start the FastAPI server
- Initialize the ChromaDB vector store
- Load the embedding model
- Make the API available at http://localhost:8000

2. Access the backend:
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- ChromaDB Status: http://localhost:8000/health/chromadb
- Vector Store Status: http://localhost:8000/health/vector-store
- Model Status: http://localhost:8000/health/model

### Frontend

1. Start the frontend (in a new terminal):
```bash
./run_frontend.sh
```

This will:
- Start the Vite development server
- Make the frontend available at http://localhost:5173
- Automatically reload on file changes

2. Open your browser:
- Frontend: http://localhost:5173
- The frontend will connect to the backend API automatically

**Note:** Make sure the backend is running before starting the frontend, otherwise API calls will fail.

## Project Structure

```
tvshowchat/
├── app/
│   ├── api/            # FastAPI routes and endpoints
│   ├── services/       # Business logic and services
│   │   ├── scraping/   # Web scraping utilities
│   │   ├── pipeline/   # Data processing pipeline
│   │   └── embeddings/ # Embedding generation
│   ├── models/         # Data models and schemas
│   ├── data/          # Data storage
│   │   ├── episodes/  # Episode transcripts (backup)
│   │   └── embeddings/ # Vector embeddings (backup)
│   └── logs/          # Application logs
├── scripts/           # Utility scripts
├── tests/            # Test suite
├── requirements.txt  # Python dependencies
└── README.md        # This file
```

## Data Pipeline

1. **Data Collection**: Episode transcripts are collected and stored in JSON format
2. **Text Processing**: Transcripts are cleaned and prepared for embedding
3. **Embedding Generation**: Text is converted to vector embeddings using Sentence Transformers
4. **Vector Storage**: Embeddings are stored in ChromaDB for efficient retrieval
5. **Search**: Semantic search is performed using ChromaDB vector similarity search

## Documentation

- `ARCHITECTURE.md` – High-level system design and diagrams
- `docs/ROADMAP.md` – Current implementation roadmap and priorities
- `docs/DATA_PIPELINE.md` – Detailed ingestion and storage pipeline
- `docs/TESTING_GUIDE.md` – Automated and manual testing instructions

## Development

### Adding New Episodes

1. Place episode transcripts in `app/data/episodes/` in JSON format
2. Run the initialization script to update the ChromaDB vector store:
```bash
python scripts/init_data.py
```

### Testing

Run the automated test suite:
```bash
./test.sh
```

**Prerequisites:** The server must be running (`./run.sh`)

**What it tests:**
1. **Health Endpoints** - `/health`, `/health/vector-store`, `/health/model`
2. **System State** - `/api/test` (vector store stats, sample episode, test search)
3. **Search Functionality** - `/api/test-search` (default and custom queries)
4. **Vector Store Status** - Verifies ChromaDB is healthy
5. **Data Directories** - Checks for episode files and ChromaDB data
6. **Crawler Status** - Runs `scripts/scrape_episodes.py --status`

**Expected Results:**
- All endpoints return `200 OK`
- Search returns relevant episode results
- Vector store shows healthy status
- Data directories contain expected files

See `docs/TESTING_GUIDE.md` for detailed testing documentation.

### Data Pipeline Utilities

Use the crawler helper scripts for manual checks or to refresh scraped data:
```bash
python3.12 scripts/scrape_episodes.py --status          # snapshot of pipeline health
python3.12 scripts/scrape_episodes.py --import-latest    # import latest crawl into document store
python3.12 scripts/scrape_episodes.py --reindex-chroma   # rebuild ChromaDB from document store
python3.12 scripts/scrape_episodes.py --all --force      # re-crawl and regenerate content JSON
./scripts/crawl.sh                                       # crawl any seasons missing from btvs_all_seasons.json
./scripts/crawl.sh --season 5                            # crawl a specific season
./scripts/crawl.sh --all --force                         # force a full re-crawl
```

### Multi-Season Refresh Workflow

The canonical dataset lives at `app/content/btvs_all_seasons.json`. To regenerate embeddings and Chroma for all seven seasons:

1. `./scripts/crawl.sh` — fetch missing seasons (no-op if coverage is complete).
2. `python3.12 scripts/scrape_episodes.py --import-latest` — sync the document store (`app/data/episodes` + embeddings).
3. `python3.12 scripts/scrape_episodes.py --reindex-chroma` — rebuild the `buffy_episodes` collection from the document store.
4. `./test.sh` — validates that content, document store, embeddings, vector store, and API all report 144 episodes across Seasons 1–7.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.



