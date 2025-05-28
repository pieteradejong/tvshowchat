# TV Show Chat

A semantic search and chat application that allows users to interact with TV show content through natural language queries. Currently featuring Buffy the Vampire Slayer, with the ability to search and chat about episodes using advanced vector embeddings.

## Table of Contents
- [TV Show Chat](#tv-show-chat)
  - [Table of Contents](#table-of-contents)
  - [Project Overview](#project-overview)
    - [Goal](#goal)
    - [MVP Goals](#mvp-goals)
    - [Core Components](#core-components)
  - [Architecture](#architecture)
    - [Data Flow](#data-flow)
  - [Features](#features)
  - [Prerequisites](#prerequisites)
  - [Quick Start](#quick-start)
  - [Development](#development)
    - [Backend Development](#backend-development)
      - [API Endpoints](#api-endpoints)
      - [Services](#services)
    - [Frontend Development](#frontend-development)
      - [Project Structure](#project-structure)
      - [Key Components](#key-components)
      - [Development Setup](#development-setup)
      - [Development Guidelines](#development-guidelines)
      - [Building for Production](#building-for-production)
  - [Environment Variables](#environment-variables)
  - [Health Checks](#health-checks)
    - [Backend Health Checks](#backend-health-checks)
    - [Monitoring](#monitoring)
    - [Health Check Usage](#health-check-usage)
  - [Testing](#testing)
    - [System Test](#system-test)
    - [Search Testing](#search-testing)
    - [Expected Test Results](#expected-test-results)
    - [Testing Tips](#testing-tips)
    - [Automated Testing](#automated-testing)
  - [Model Setup](#model-setup)
    - [Model Comparison](#model-comparison)
    - [Automatic Setup](#automatic-setup)
    - [Manual Setup](#manual-setup)
    - [Model Verification](#model-verification)
    - [Performance Considerations](#performance-considerations)
  - [Model Files](#model-files)
  - [Troubleshooting](#troubleshooting)
  - [Project History \& Notes](#project-history--notes)
    - [Development Phases](#development-phases)
    - [Technical Decisions](#technical-decisions)
  - [Development Roadmap & TODOs](#development-roadmap--todos)
    - [Phase 1: Core Search Enhancement (Current Focus)](#phase-1-core-search-enhancement-current-focus)
      - [Storage Improvements](#storage-improvements)
      - [Search Improvements](#search-improvements)
      - [Data Enhancement](#data-enhancement)
    - [Phase 2: Interactive Features](#phase-2-interactive-features)
      - [Basic Chat Interface](#basic-chat-interface)
      - [UI/UX Improvements](#uiux-improvements)
    - [Phase 3: Advanced Features](#phase-3-advanced-features)
      - [Character Analysis](#character-analysis)
      - [Story Analysis](#story-analysis)
    - [Phase 4: Production & Polish](#phase-4-production--polish)
      - [Performance](#performance)
      - [User Experience](#user-experience)
    - [Technical TODOs](#technical-todos)
      - [Backend](#backend)
      - [Frontend](#frontend)
      - [Data](#data)
    - [Immediate Next Steps](#immediate-next-steps)
  - [License](#license)

## Project Overview

### Goal
Create an interactive chat interface that allows users to "talk" with the entire Buffy the Vampire Slayer series, using semantic search to find relevant episode content based on natural language queries.

### MVP Goals
Our immediate focus is on building a minimal viable product with these core components:

1. **Data Collection** (Current)
   - Using buffy.fandom.com as data source
   - Scraping episode summaries and metadata
   - Storing raw data in JSON format
   - Next steps:
     - Validate data quality
     - Add error handling
     - Implement rate limiting
     - Add data cleaning pipeline

2. **Search Service**
   - Implement basic vector search using existing embeddings
   - Simple query processing
   - Return top 3-5 most relevant episodes
   - Next steps:
     - Add basic caching
     - Implement result ranking
     - Add query preprocessing

3. **Minimal Frontend**
   - Single page with two main components:
     - Query input window
     - Results display window
   - Basic styling with Tailwind
   - No authentication required
   - Next steps:
     - Add loading states
     - Implement error handling
     - Add basic result formatting

### Core Components

1. **Data Collection & Processing**
   - Web Scraping Module (`app/services/scraping/`)
     - Episode data collection
     - Content cleaning and normalization
     - Data validation
   - Data Pipeline (`app/services/pipeline/`)
     - Content processing
     - Embedding generation
     - Data storage management

2. **Backend Services**
   - FastAPI Application (`app/api/`)
     - RESTful endpoints
     - WebSocket support for real-time chat
     - Request validation
   - Search Service (`app/services/search/`)
     - Vector similarity search using numpy/scipy
     - Query processing
     - Result ranking
   - Embedding Service (`app/services/embeddings/`)
     - HuggingFace model integration
     - Vector generation
     - Model management

3. **Data Storage**
   - Redis Database
     - Episode data storage
     - Vector embeddings (stored as Redis lists/strings)
     - Query caching
   - Custom Vector Search Implementation
     - Vector similarity using numpy/scipy
     - Efficient storage in Redis
     - Optimized search algorithms

4. **Frontend Application**
   - React + TypeScript
   - Chat Interface
   - Search Results Display
   - Real-time Updates

5. **Infrastructure**
   - Configuration Management
   - Logging System
   - Error Handling
   - Testing Framework
   - CI/CD Pipeline

## Architecture

```
tvshowchat/
├── app/
│   ├── api/                 # FastAPI routes and endpoints
│   ├── data/               # Document storage
│   │   ├── episodes/       # Season JSON files
│   │   ├── embeddings/     # Vector embeddings
│   │   └── backup_*/       # Timestamped backups
│   ├── models/             # Data models and schemas
│   ├── services/           # Core services
│   │   ├── scraping/      # Web scraping
│   │   ├── pipeline/      # Data processing
│   │   ├── embed/         # Vector embeddings
│   │   └── storage/       # Document store
│   ├── config/            # Configuration
│   └── utils/             # Shared utilities
├── frontend/              # React application
├── tests/                 # Test suite
└── scripts/              # Utility scripts
```

### Data Flow
1. **Content Collection**
   ```
   Web Source → Scraping Service → Document Store → Vector Search
   ```

2. **Query Processing**
   ```
   User Query → Embedding Service → Vector Search → Document Store → Response
   ```

3. **Real-time Chat**
   ```
   User Message → WebSocket → Query Processing → Real-time Response
   ```

## Features

- Natural language querying of TV show content
- Semantic search using vector embeddings
- Document-based storage with automatic backups
- Rich episode metadata including:
  - Basic episode info (title, airdate, etc.)
  - Content (summary, synopsis, quotes, trivia)
  - Production details (director, writer, budget, etc.)
  - Cast & Characters (main cast, guest stars, appearances)
  - Story elements (continuity, references, mythology)
  - Awards and reception
- Real-time chat interface
- Responsive and modern UI
- Comprehensive error handling
- Detailed logging

## Prerequisites

- Python 3.9 (required for compatibility with dependencies)
- Node.js 18 or higher
- Redis 6 or higher (for vector search only)
- Git

## Quick Start

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
- Set up Python virtual environment
- Install Python dependencies
- Install frontend dependencies
- Check for required software
- Create necessary directories
- Initialize Redis
- Set up configuration

3. Start the application:
```bash
./run.sh
```
This will:
- Start Redis server
- Start FastAPI backend
- Start React frontend

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Development

### Backend Development

#### API Endpoints
- `POST /api/search`: Semantic search endpoint
- `POST /api/chat`: Chat endpoint
- `GET /api/episodes`: Episode information
- `WebSocket /ws/chat`: Real-time chat

#### Services
- **Scraping Service**: Handles content collection
- **Pipeline Service**: Manages data processing
- **Embedding Service**: Generates vector embeddings
- **Search Service**: Performs semantic search

### Frontend Development

The frontend is built with React, TypeScript, and Vite, providing a modern chat interface for interacting with the TV show content.

#### Project Structure
```
frontend/
├── src/
│   ├── components/     # React components
│   │   ├── ChatWindow.tsx    # Main chat interface
│   │   ├── ChatInput.tsx     # Message input
│   │   ├── ChatMessage.tsx   # Message display
│   │   └── SearchResults.tsx # Search results
│   ├── hooks/         # Custom React hooks
│   │   ├── useChat.ts        # Chat state management
│   │   └── useSearch.ts      # Search functionality
│   ├── services/      # API and WebSocket services
│   │   ├── api.ts           # REST API client
│   │   └── websocket.ts     # WebSocket client
│   ├── types/         # TypeScript definitions
│   │   ├── chat.ts          # Chat types
│   │   └── search.ts        # Search types
│   ├── App.tsx        # Main application
│   └── main.tsx       # Entry point
├── public/            # Static assets
└── index.html         # HTML template
```

#### Key Components

1. **Chat Interface**
   - `ChatWindow`: Main chat container
     - Handles message display and input
     - Manages WebSocket connection
     - Displays search results
   - `ChatInput`: Message input component
     - Text input with send button
     - Enter key support
     - Input validation
   - `ChatMessage`: Individual message
     - Displays user and system messages
     - Shows episode information
     - Supports markdown formatting

2. **Search Results**
   - `SearchResults`: Search display component
     - Shows matching episodes
     - Displays relevance scores
     - Links to episode details

#### Development Setup

1. **Prerequisites**
   - Node.js 18 or higher
   - npm 9 or higher

2. **Installation**
   ```bash
   cd frontend
   npm install
   ```

3. **Development Server**
   ```bash
   npm run dev
   ```
   The frontend will be available at http://localhost:5173

4. **Available Scripts**
   - `npm run dev` - Start development server
   - `npm run build` - Build for production
   - `npm run lint` - Run ESLint
   - `npm run type-check` - Run TypeScript checks
   - `npm run test` - Run tests
   - `npm run preview` - Preview production build

#### Development Guidelines

1. **TypeScript**
   - Use strict type checking
   - Define interfaces for all props
   - Use type inference where possible
   - Example:
     ```typescript
     interface ChatMessage {
       id: string;
       text: string;
       type: 'user' | 'system';
       timestamp: Date;
       episodeInfo?: EpisodeInfo;
     }
     ```

2. **State Management**
   - Use React Query for API data
   - Use WebSocket for real-time updates
   - Keep component state minimal
   - Example:
     ```typescript
     const { data, isLoading } = useQuery({
       queryKey: ['search', query],
       queryFn: () => searchApi.search(query)
     });
     ```

3. **Styling**
   - Use Tailwind CSS for styling
   - Follow mobile-first approach
   - Maintain consistent spacing and colors
   - Example:
     ```tsx
     <div className="flex flex-col h-screen bg-gray-100">
       <div className="flex-1 overflow-y-auto p-4">
         {messages.map(msg => (
           <ChatMessage key={msg.id} message={msg} />
         ))}
       </div>
     </div>
     ```

4. **Testing**
   - Write unit tests for components
   - Test user interactions
   - Mock API and WebSocket calls
   - Example:
     ```typescript
     describe('ChatInput', () => {
       it('sends message on enter', async () => {
         const onSend = jest.fn();
         render(<ChatInput onSend={onSend} />);
         await userEvent.type(screen.getByRole('textbox'), 'Hello{enter}');
         expect(onSend).toHaveBeenCalledWith('Hello');
       });
     });
     ```

#### Building for Production

1. **Build Process**
   ```bash
   cd frontend
   npm run build
   ```
   This creates optimized production files in `frontend/dist/`

2. **Preview Build**
   ```bash
   npm run preview
   ```
   Preview the production build locally

3. **Deployment**
   - Static files in `dist/` can be served by any web server
   - Configure CORS and WebSocket proxy
   - Set environment variables for production

## Environment Variables

Create a `.env` file in the root directory:

```env
# Backend
REDIS_HOST=localhost
REDIS_PORT=6379
MODEL_NAME=msmarco-distilbert-base-v4
MODEL_PATH=app/models/msmarco-distilbert-base-v4
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Health Checks

The application includes several health check endpoints to monitor the status of different services:

### Backend Health Checks

1. **Main Health Check**
   - Endpoint: `GET /health`
   - Purpose: Overall application health
   - Response: `{"status": "healthy", "version": "1.0.0"}`

2. **Redis Health Check**
   - Endpoint: `GET /health/redis`
   - Purpose: Redis connection and basic operations status
   - Response: `{"status": "healthy", "redis": "connected", "operations": "ok"}`

3. **Model Health Check**
   - Endpoint: `GET /health/model`
   - Purpose: Embedding model status
   - Response: `{"status": "healthy", "model": "loaded", "name": "msmarco-distilbert-base-v4"}`

### Monitoring

The health check endpoints can be used with monitoring tools:
- Prometheus metrics available at `/metrics`
- Health check status for load balancers
- Service status for container orchestration

### Health Check Usage

1. Using curl:
```bash
# Check overall health
curl http://localhost:8000/health

# Check Redis status
curl http://localhost:8000/health/redis

# Check model status
curl http://localhost:8000/health/model
```

2. Using the run script:
```bash
# The run.sh script automatically checks health endpoints
./run.sh
```

## Testing

The application includes several test endpoints to verify system functionality and data integrity:

### Automated Testing
```bash
# Run all tests using the test script
./test.sh
```
This script will:
- Check if the server is running
- Test all health endpoints
- Verify system state
- Test search functionality
- Check Redis state
- Verify document store
- Provide a formatted summary

The test script provides color-coded output:
- 🟢 Green: Successful tests
- 🔴 Red: Failed tests
- 🟡 Yellow: Test categories and progress

### Manual Testing

1. **System Test** (`/api/test`) should return:
   ```json
   {
     "status": "healthy",
     "redis": {
       "total_keys": "number of keys",
       "sample_keys": ["buffy:s01:e01", "buffy:s01:e02", ...],
       "index_info": {
         "num_docs": "number of documents",
         "index_name": "idx:buffy_vss"
       }
     },
     "store": {
       "total_seasons": 7,
       "total_episodes": 144,
       "sample_episode": {
         "season": "1",
         "episode": "01",
         "title": "Welcome to the Hellmouth",
         "has_synopsis": true,
         "has_summary": true,
         "has_embedding": true
       }
     },
     "test_search": {
       "query": "Buffy fights vampires",
       "results": [...]
     }
   }
   ```

2. **Search Test** (`/api/test-search`) should return:
   ```json
   {
     "query": "your search query",
     "limit": 3,
     "results": [
       {
         "season": 1,
         "episode": "01",
         "title": "Episode Title",
         "score": 0.85,
         "summary": ["Episode summary..."],
         "synopsis": ["Detailed synopsis..."]
       },
       // ... more results
     ]
   }
   ```

### Testing Tips

1. **Verify Data Loading**
   - Check Redis keys exist: `redis-cli keys "buffy:*"`
   - Verify document store: `ls app/data/episodes/`
   - Confirm embeddings: `ls app/data/embeddings/`

2. **Test Search Quality**
   - Try character-specific queries: "Willow uses magic"
   - Test plot-based queries: "Buffy fights the Master"
   - Try thematic queries: "episodes about love"
   - Verify result relevance and ranking

3. **Monitor Performance**
   - Check response times
   - Verify Redis index creation
   - Monitor memory usage
   - Watch for any errors in logs

4. **Common Issues**
   - If Redis shows 0 keys: Check data import
   - If search returns no results: Verify index creation
   - If embeddings missing: Check model loading
   - If store empty: Verify JSON file import

## Model Setup

The application uses the `all-MiniLM-L6-v2` model for generating embeddings. This model was chosen for its:
- Fast inference speed (crucial for real-time chat)
- Good performance on dialogue and narrative content
- Small memory footprint (384 dimensions vs 768)
- Proven stability in production

### Model Comparison

We evaluated several models for this project:

1. **all-MiniLM-L6-v2** (Current Choice)
   - Dimensions: 384
   - Speed: ⭐⭐⭐⭐⭐ (Fastest)
   - Memory: ⭐⭐⭐⭐⭐ (Smallest)
   - Accuracy: ⭐⭐⭐⭐ (Very Good)
   - Best for: Real-time chat, dialogue understanding
   - Size: ~90MB

2. **all-mpnet-base-v2** (Alternative)
   - Dimensions: 768
   - Speed: ⭐⭐⭐ (Slower)
   - Memory: ⭐⭐⭐ (Larger)
   - Accuracy: ⭐⭐⭐⭐⭐ (Best)
   - Best for: High-accuracy search, when speed isn't critical
   - Size: ~420MB

3. **msmarco-distilbert-base-v4** (Previous)
   - Dimensions: 768
   - Speed: ⭐⭐⭐⭐ (Good)
   - Memory: ⭐⭐⭐⭐ (Medium)
   - Accuracy: ⭐⭐⭐ (Good)
   - Best for: General semantic search
   - Size: ~290MB

### Automatic Setup
The `init.sh` script handles model download and setup:
```bash
# Model is stored in app/models/all-MiniLM-L6-v2
# Approximately 90MB disk space required
```

### Manual Setup
If automatic setup fails:
```bash
# Activate virtual environment
source venv/bin/activate

# Download model manually
python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
model.save('app/models/all-MiniLM-L6-v2')
"
```

### Model Verification
- Check model status: `curl http://localhost:8000/health/model`
- Verify embeddings: `curl -X POST http://localhost:8000/api/test/embed -H "Content-Type: application/json" -d '{"text": "test"}'`

### Performance Considerations
1. **Memory Usage**
   - Model: ~90MB
   - Embeddings: ~1.5KB per episode
   - Total for 144 episodes: ~216KB

2. **Speed**
   - Embedding generation: ~10ms per query
   - Search latency: ~20ms
   - Total response time: <100ms

3. **Scaling**
   - Model can handle concurrent requests
   - Redis efficiently stores and retrieves embeddings
   - System can scale horizontally if needed

## Model Files

The project uses the `all-MiniLM-L6-v2` model from HuggingFace for semantic search. Due to GitHub's file size limitations, the model weights are not included in the repository. The model will be automatically downloaded on first run, but you can also download it manually:

```bash
# From the project root
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

This will download the model to `app/models/all-MiniLM-L6-v2/`. The repository includes all necessary configuration files, but excludes the large model weights (`.bin` files) to comply with GitHub's file size limits.

## Troubleshooting

1. Redis Issues:
   - Check Redis installation: `redis-cli ping`
   - Verify Redis is running: `brew services list` (macOS) or `systemctl status redis` (Linux)
   - Check Redis logs: `redis-cli monitor`
   - Common Redis issues:
     - Connection refused: Ensure Redis is running
     - Memory issues: Check Redis memory usage with `redis-cli info memory`
     - Performance: Monitor Redis with `redis-cli --stat`

2. Backend Issues:
   - Check logs: `tail -f app.log`
   - Verify virtual environment: `source venv/bin/activate`
   - Test API: `curl http://localhost:8000/health`

3. Frontend Issues:
   - Check browser console
   - Verify Node.js version: `node --version`
   - Clear npm cache: `npm cache clean --force`

## Project History & Notes

### Development Phases

1. **Phase 1: MVP** (Current)
   - Basic web scraping
   - Simple vector search
   - Basic chat interface
   - Essential features only

2. **Phase 2: Enhancement**
   - Improved search accuracy
   - Better UI/UX
   - Performance optimization
   - Additional features

3. **Phase 3: Production**
   - Production deployment
   - Monitoring
   - Scaling
   - Security hardening

### Technical Decisions

1. **Storage Implementation**
   - Document-based storage using JSON files
   - Separate storage for content and embeddings
   - Automatic backup system
   - Benefits:
     - Simple to understand and maintain
     - No database dependencies
     - Easy to version control
     - Efficient for our use case
     - Portable and shareable

2. **Vector Search Implementation**
   - Using HuggingFace models for state-of-the-art embeddings
   - Redis for vector search index only
   - Cosine similarity for matching
   - Benefits:
     - Fast semantic search
     - Efficient memory usage
     - Scalable for our needs

3. **Architecture**
   - Modular design for easy extension
   - Clear separation of concerns
   - Document-first approach
   - Efficient vector storage and search

## Development Roadmap & TODOs

### Phase 1: Core Search Enhancement (Current Focus)
- [x] **Storage Improvements**
  - [x] Implement document-based storage
  - [x] Add automatic backups
  - [x] Separate content and embeddings
  - [ ] Add data validation
  - [ ] Implement data versioning

- [ ] **Search Improvements**
  - [ ] Add basic filtering by season/episode
  - [ ] Implement character-based search
  - [ ] Add simple theme categorization
  - [ ] Improve search result display
  - [ ] Add basic caching for frequent searches

- [ ] **Data Enhancement**
  - [x] Add character metadata
  - [x] Implement production details
  - [x] Add story elements
  - [ ] Add episode connections
  - [ ] Improve summary quality

### Phase 2: Interactive Features
- [ ] **Basic Chat Interface**
  - [ ] Simple Q&A about episodes
  - [ ] Episode summary requests
  - [ ] Basic character information queries
  - [ ] Simple recommendation system

- [ ] **UI/UX Improvements**
  - [ ] Redesign search interface
  - [ ] Add episode cards with key information
  - [ ] Implement basic filters
  - [ ] Add loading states and error handling

### Phase 3: Advanced Features
- [ ] **Character Analysis**
  - [ ] Track character appearances
  - [ ] Show character relationships
  - [ ] Display character arcs
  - [ ] Add character-specific search

- [ ] **Story Analysis**
  - [ ] Identify story arcs
  - [ ] Show episode connections
  - [ ] Track recurring themes
  - [ ] Visualize story progression

### Phase 4: Production & Polish
- [ ] **Performance**
  - [ ] Optimize search speed
  - [ ] Implement proper caching
  - [ ] Add rate limiting
  - [ ] Improve error handling

- [ ] **User Experience**
  - [ ] Add user preferences
  - [ ] Implement search history
  - [ ] Add favorite episodes
  - [ ] Create watchlists

### Technical TODOs
- [ ] **Backend**
  - [ ] Refactor search service for better modularity
  - [ ] Add proper logging and monitoring
  - [ ] Implement proper error handling
  - [ ] Add API documentation
  - [ ] Add unit tests

- [ ] **Frontend**
  - [ ] Implement proper state management
  - [ ] Add error boundaries
  - [ ] Improve component structure
  - [ ] Add proper TypeScript types
  - [ ] Add unit tests

- [ ] **Data**
  - [ ] Improve data validation
  - [ ] Add data versioning
  - [ ] Implement data updates
  - [ ] Add data quality checks

### Immediate Next Steps
1. **Search Enhancement**
   - Implement basic character search
   - Add simple theme categorization
   - Improve search result display

2. **Data Structure**
   - Add character metadata
   - Implement basic theme tagging
   - Structure episode connections

3. **UI Improvements**
   - Redesign search interface
   - Add episode cards
   - Implement basic filters

4. **Technical Foundation**
   - Add proper error handling
   - Implement basic caching
   - Add logging
   - Write tests

## License

MIT License - see LICENSE file for details

[![pytest](https://github.com/pieteradejong/tvshowchat/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/pieteradejong/tvshowchat/actions/workflows/ci.yml)



