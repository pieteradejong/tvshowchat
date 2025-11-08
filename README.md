# TV Show Chat

A semantic search and chat application for TV show transcripts, built with Python and React.

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

Use the crawler helper script for manual checks or to refresh scraped data (Season 1 currently supported):
```bash
python3.12 scripts/scrape_episodes.py --status      # snapshot of pipeline health
python3.12 scripts/scrape_episodes.py --all --force  # re-crawl and regenerate content JSON
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.



