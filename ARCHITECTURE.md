# TV Show Chat - System Architecture

## 🏗️ **Overall Architecture**

TV Show Chat is a **semantic search and chat application** for Buffy the Vampire Slayer episodes, built with a modern microservices architecture using Redis as the primary database and vector store.

## 🎯 **Core Components**

### **1. Backend (Python FastAPI)**
- **Framework**: FastAPI 0.104.1 with automatic OpenAPI documentation
- **Language**: Python 3.12
- **Server**: Uvicorn ASGI server
- **Database**: Redis with RediSearch and RedisJSON modules
- **Vector Store**: Redis with vector similarity search capabilities

### **2. Frontend (React + TypeScript)**
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite 5.x
- **Styling**: TailwindCSS
- **State Management**: React Query for API state management
- **UI Components**: Headless UI for accessible components

### **3. AI/ML Layer**
- **Embeddings**: Sentence Transformers `all-MiniLM-L6-v2`
- **Vector Search**: Redis vector similarity search with cosine similarity
- **Semantic Understanding**: Advanced query processing with character and theme detection

## 🗄️ **Database Architecture**

### **Primary Database: Redis**
- **Redis Version**: 6.x or later
- **Modules**: 
  - **RediSearch 2.2+**: Full-text and vector search
  - **RedisJSON 2.0+**: JSON document storage
- **Connection**: Local Redis instance on port 6379

### **Data Storage Strategy**

#### **Episode Data Structure**
```json
{
  "buffy:s01:e01": {
    "synopsis": "Episode synopsis text...",
    "summary": "Episode summary text...",
    "synopsis_embedding": [0.1, 0.2, ...], // 384-dimensional vector
    "summary_embedding": [0.3, 0.4, ...], // 384-dimensional vector
    "metadata": {
      "season": 1,
      "episode": "01",
      "title": "Welcome to the Hellmouth",
      "airdate": "March 10, 1997"
    }
  }
}
```

#### **Vector Search Index**
- **Index Name**: `idx:buffy_vss`
- **Vector Dimensions**: 384 (all-MiniLM-L6-v2)
- **Distance Metric**: COSINE
- **Vector Type**: FLOAT32
- **Index Type**: FLAT (for small to medium datasets)

### **Data Flow**
1. **Data Ingestion**: Episode data imported from JSON files
2. **Embedding Generation**: Text converted to 384-dimensional vectors
3. **Redis Storage**: Data stored as JSON documents with vector embeddings
4. **Index Creation**: RediSearch index created for vector similarity search
5. **Query Processing**: Natural language queries converted to vectors and searched

## 🔍 **Search Architecture**

### **Semantic Search Pipeline**
1. **Query Processing**: Natural language query received
2. **Vector Encoding**: Query converted to embedding using Sentence Transformers
3. **Vector Search**: Redis vector similarity search performed
4. **Result Ranking**: Results ranked by cosine similarity score
5. **Metadata Enrichment**: Additional context and metadata added
6. **Response Formatting**: Structured response with rich metadata

### **Advanced Search Features**
- **Character Relationship Detection**: Automatically identifies character interactions
- **Theme Recognition**: Detects themes like romance, magic, vampire, etc.
- **Context-Aware Scoring**: Boosts results based on query intent
- **Multi-Modal Search**: Supports episode, quote, scene, and relationship queries

## 🚀 **API Architecture**

### **RESTful Endpoints**
- **Base URL**: `http://localhost:8000`
- **API Prefix**: `/api`
- **Documentation**: Automatic OpenAPI docs at `/docs`

#### **Core Endpoints**
- `POST /api/search` - Semantic episode search
- `GET /api/test-search` - Test search functionality
- `GET /api/test` - System health and status
- `GET /health` - Overall system health
- `GET /health/redis` - Redis connection status
- `GET /health/model` - Embedding model status

### **Request/Response Format**
```json
// Search Request
{
  "query": "Buffy and Angel romantic scenes",
  "limit": 5,
  "season": 1
}

// Search Response
[
  {
    "season": 1,
    "episode": "01",
    "title": "Welcome to the Hellmouth",
    "airdate": "March 10, 1997",
    "content_type": "summary",
    "text": "Relevant episode text...",
    "score": 0.85,
    "characters": ["Buffy", "Angel"],
    "themes": ["romance", "vampire"],
    "context": "Features characters: Buffy, Angel | Themes: romance, vampire"
  }
]
```

## 🔧 **Service Architecture**

### **Backend Services**
- **Main Application** (`app/api/main.py`): FastAPI app with middleware and routing
- **Search Service** (`app/api/routes/search.py`): Search endpoint handlers
- **Embedding Service** (`app/services/embed.py`): Redis operations and vector search
- **Document Store** (`app/services/storage/document_store.py`): File-based backup storage
- **Vector Store** (`app/services/vector_store.py`): Advanced semantic search logic

### **Data Processing Pipeline**
1. **Data Loading**: Episode data loaded from JSON files
2. **Pipeline Creation**: Redis pipeline for batch operations
3. **Embedding Generation**: Text converted to vectors
4. **Data Storage**: Episodes stored in Redis as JSON documents
5. **Index Creation**: RediSearch index created for vector search
6. **Health Verification**: System components verified

## 🌐 **Frontend Architecture**

### **Component Structure**
- **App.tsx**: Main application with tab navigation
- **Search.tsx**: Advanced search interface with rich results
- **ChatWindow.tsx**: Chat interface (future feature)
- **Components**: Reusable UI components

### **State Management**
- **React Query**: API state management and caching
- **Local State**: Component-level state with React hooks
- **Error Handling**: Comprehensive error states and user feedback

## 📊 **Performance Characteristics**

### **Vector Search Performance**
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions, ~80MB)
- **Search Latency**: <100ms for typical queries
- **Index Size**: ~1MB per 100 episodes
- **Memory Usage**: ~200MB for full Season 1 dataset

### **Scalability**
- **Redis**: Can handle thousands of episodes efficiently
- **Vector Search**: Linear scaling with dataset size
- **Concurrent Users**: Limited by Redis connection pool (default 100)

## 🔒 **Security & Configuration**

### **CORS Configuration**
- **Allowed Origins**: `http://localhost:5173`, `http://localhost:5175`
- **Methods**: All HTTP methods
- **Headers**: All headers
- **Credentials**: Enabled

### **Environment Configuration**
- **Redis Host**: localhost
- **Redis Port**: 6379
- **API Port**: 8000
- **Frontend Port**: 5173

## 🚀 **Deployment Architecture**

### **Development Environment**
- **Backend**: Python virtual environment with uvicorn
- **Frontend**: Vite development server with hot reload
- **Redis**: Local Redis instance
- **Data**: Local JSON files and Redis storage

### **Production Considerations**
- **Redis**: Redis Cluster for high availability
- **API**: Gunicorn with multiple workers
- **Frontend**: Static build served by CDN
- **Monitoring**: Redis monitoring and API health checks

## 📈 **Future Architecture Enhancements**

### **Planned Improvements**
1. **Multi-Season Support**: Expand to all 7 seasons of Buffy
2. **Chat Functionality**: LLM integration for conversational search
3. **Real-time Features**: WebSocket support for live updates
4. **Advanced Analytics**: Search analytics and user behavior tracking
5. **Multi-Show Support**: Extend to other TV shows

### **Scalability Roadmap**
1. **Redis Cluster**: Distributed Redis for larger datasets
2. **Microservices**: Split into separate search and chat services
3. **CDN Integration**: Global content delivery
4. **API Gateway**: Centralized API management
5. **Container Orchestration**: Kubernetes deployment

---

*This architecture document reflects the current implementation using Redis as the primary database and vector store, not local file system storage.*
