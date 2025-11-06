# TV Show Chat

A semantic search and chat application for TV show transcripts, built with Python and React.

## Features

- **Semantic Search**: Find relevant episodes and scenes using natural language queries
- **Vector Storage**: Efficient storage and retrieval of episode embeddings using Redis with RediSearch
- **Modern UI**: Clean, responsive interface built with React and TailwindCSS
- **FastAPI Backend**: High-performance API with automatic OpenAPI documentation

## Tech Stack

### Backend
- Python 3.12
- FastAPI 0.104.1
- Redis 6.x with RediSearch 2.2+ and RedisJSON 2.0+ (Vector Database)
- Sentence Transformers (Embeddings)
- Uvicorn (ASGI Server)

### Frontend
- React 18
- TypeScript
- TailwindCSS
- Vite

## Prerequisites

- Python 3.12 or later
- Redis 6.x or later with RediSearch 2.2+ and RedisJSON 2.0+ modules
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
- Initialize the Redis vector store
- Download the embedding model

## Running the Application

1. Start the application:
```bash
./run.sh
```

This will:
- Start the FastAPI server
- Initialize the Redis vector store
- Load the embedding model
- Make the API available at http://localhost:8000

2. Access the application:
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Redis Status: http://localhost:8000/health/redis
- Model Status: http://localhost:8000/health/model

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
4. **Vector Storage**: Embeddings are stored in Redis with RediSearch for efficient retrieval
5. **Search**: Semantic search is performed using Redis vector similarity search

## Development

### Adding New Episodes

1. Place episode transcripts in `app/data/episodes/` in JSON format
2. Run the initialization script to update the Redis vector store:
```bash
python scripts/init_data.py
```

### Testing

Run the test suite:
```bash
./test.sh
```

This will:
- Check system health
- Verify Redis connection and vector store status
- Test search functionality
- Validate model availability

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.



