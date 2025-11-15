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

The repository includes the complete `btvs_all_seasons.json` dataset (all 7 seasons, 144 episodes). The pipeline is fully set up and verified.

1. **Initialize dependencies & environment**
   ```bash
   ./init.sh
   ```
   Creates/updates the Python 3.12 virtualenv, installs requirements, prepares data directories, and downloads the embedding model.

2. **Run the backend (FastAPI + ChromaDB)**
   ```bash
   ./run.sh
   ```
   Starts the API at http://localhost:8000. The document store and ChromaDB will auto-populate from the existing dataset on first startup.

3. **Run the frontend (React/Vite)**
   ```bash
   ./run_frontend.sh
   ```
   Serves the UI at http://localhost:5173 and proxies API calls to the backend.

4. **Run the integrated test suite (optional)**
   ```bash
   ./test.sh
   ```
   Requires the backend to be running. Verifies health endpoints, search across all seasons, document store, embeddings, and ensures the content/Chroma counts match (144 total episodes across all 7 seasons).

To refresh the dataset later, follow the [Multi-Season Refresh Workflow](#multi-season-refresh-workflow); otherwise no scraping is required.

## Features

- **Semantic Search**: Find relevant episodes and scenes using natural language queries
- **Vector Storage**: Efficient storage and retrieval of episode embeddings using ChromaDB
- **Modern UI**: Clean, responsive interface built with React and TailwindCSS
- **FastAPI Backend**: High-performance API with automatic OpenAPI documentation

## Tech Stack

### Backend
- Python 3.11+ (3.11 recommended for deployment platforms)
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

- Python 3.11 or later (3.11 recommended for deployment platforms)
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
- Pipeline Health: http://localhost:8000/health/pipeline (shows episode counts at each stage)
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

- `ROADMAP.md` – **Consolidated roadmap and implementation plan** (start here for planning)
- `ARCHITECTURE.md` – High-level system design and diagrams
- `docs/DATA_PIPELINE.md` – Detailed ingestion and storage pipeline
- `docs/TESTING_GUIDE.md` – Automated and manual testing instructions

**Current Status**: All 7 seasons (144 episodes) are ingested and searchable. The pipeline is fully verified and tested. See `ROADMAP.md` for complete details.

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
1. **Health Endpoints** - `/health`, `/health/vector-store`, `/health/model`, `/health/pipeline`
2. **System State** - `/api/test` (vector store stats, sample episode, test search)
3. **Search Functionality** - `/api/test-search` (default and custom queries)
4. **Search Across All Seasons** - Verifies search works for all 7 seasons
5. **Vector Store Status** - Verifies ChromaDB is healthy with 144 episodes
6. **Data Directories** - Checks for episode files and ChromaDB data
7. **Crawler Status** - Runs `scripts/scrape_episodes.py --status`
8. **Pipeline Integrity** - Verifies all stages match (content → document store → ChromaDB)

**Expected Results:**
- All endpoints return `200 OK`
- Search returns relevant episode results across all 7 seasons
- Vector store shows healthy status with 144 episodes
- Data directories contain expected files (7 season files in episodes and embeddings)
- Pipeline integrity verified (all stages match: 144 episodes)

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

## Docker Deployment

The project includes Docker configuration for consistent, reproducible deployments on Render or any Docker-compatible platform.

### Local Docker Testing

Test the Docker setup locally before deploying:

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build and run directly
docker build -t tvshowchat-api .
docker run -p 8000:8000 tvshowchat-api
```

The API will be available at `http://localhost:8000`.

### Deploying to Render

Render supports Docker deployments for maximum consistency. Two options:

#### Option 1: Using Dockerfile (Recommended)

1. **Connect your repository** to Render
2. **Create a new Web Service**
3. **Set the following:**
   - **Environment**: Docker
   - **Dockerfile Path**: `./Dockerfile` (or leave blank if in root)
   - **Docker Context**: `.` (root directory)
   - **Plan**: Starter (512MB) or Standard (2GB recommended)
   - **Health Check Path**: `/health`

4. **Environment Variables** (optional, defaults work):
   - `PORT=8000` (Render sets this automatically)
   - `PYTHONUNBUFFERED=1`
   - `PYTHONDONTWRITEBYTECODE=1`

5. **Deploy!** Render will:
   - Build the Docker image from your Dockerfile
   - Run the container with the optimized settings
   - Handle health checks automatically

#### Option 2: Using render.yaml (Blueprint)

The repository includes a `render.yaml` blueprint for automated setup:

1. In Render Dashboard, click **New** → **Blueprint**
2. Connect your repository
3. Render will automatically detect `render.yaml` and create the service

The blueprint is configured for:
- **Starter tier** (512MB RAM) - should work after memory optimizations
- **Standard tier** (2GB RAM) - recommended for production (uncomment in render.yaml)

### Docker Features

- **Multi-stage build**: Smaller final image size (~500MB vs ~2GB)
- **Optimized layers**: Better caching for faster rebuilds
- **Health checks**: Automatic container health monitoring
- **Production-ready**: Only production dependencies included
- **Memory optimized**: Lazy-loading of expensive operations

### Data Persistence

For production deployments, ensure data persistence:

1. **Mount volumes** for `app/data/` (episodes, embeddings, ChromaDB)
2. **Use Render's disk storage** or external storage (S3, etc.)
3. **Backup strategy**: Regular backups of `app/data/` directory

The Docker setup creates necessary directories but data should be:
- Pre-populated in the image, OR
- Mounted from persistent storage, OR
- Loaded on first startup (current behavior)

### Troubleshooting

**Out of memory errors:**
- Upgrade to Standard tier (2GB RAM)
- Check memory usage: `docker stats`
- Review lazy-loading optimizations in code

**Slow startup:**
- First request may take 2-5s longer (builds embeddings on demand)
- Subsequent requests are fast
- Consider pre-warming on deployment

**Health check failures:**
- Check logs: `docker logs <container-id>`
- Verify port is correct (Render sets PORT env var)
- Ensure `/health` endpoint is accessible

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.



