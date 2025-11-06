# TV Show Chat - Architecture Diagrams

This document provides comprehensive architecture diagrams using Mermaid.js to visualize the system design, data flow, and implementation planning.

## Table of Contents
1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow](#data-flow)
4. [Storage Architecture](#storage-architecture)
5. [Search Pipeline](#search-pipeline)
6. [Implementation Phases](#implementation-phases)

---

## System Overview

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[React UI<br/>TypeScript + TailwindCSS]
        SearchComp[Search Component]
        ChatComp[Chat Component]
    end
    
    subgraph "API Layer"
        FastAPI[FastAPI Server<br/>Port 8000]
        SearchRoute[/api/search]
        HealthRoute[/health]
        StaticFiles[Static File Server]
    end
    
    subgraph "Service Layer"
        VectorStore[AdvancedVectorStore<br/>Semantic Search Logic]
        EmbeddingService[EmbeddingService<br/>Sentence Transformers]
        DocumentStore[BuffyDocumentStore<br/>File-based Storage]
    end
    
    subgraph "Storage Layer"
        Redis[(Redis<br/>Vector Database<br/>RediSearch + RedisJSON)]
        FileStorage[(File Storage<br/>JSON Files)]
        Embeddings[(Embeddings<br/>JSON Files)]
    end
    
    subgraph "Data Sources"
        ContentFiles[Content JSON Files<br/>buffy_all_seasons_*.json]
    end
    
    UI --> SearchComp
    UI --> ChatComp
    SearchComp --> FastAPI
    ChatComp --> FastAPI
    FastAPI --> SearchRoute
    FastAPI --> HealthRoute
    FastAPI --> StaticFiles
    SearchRoute --> VectorStore
    VectorStore --> EmbeddingService
    VectorStore --> DocumentStore
    VectorStore --> Redis
    DocumentStore --> FileStorage
    DocumentStore --> Embeddings
    EmbeddingService --> Redis
    ContentFiles --> DocumentStore
    
    style UI fill:#e1f5ff
    style FastAPI fill:#fff4e1
    style VectorStore fill:#ffe1f5
    style Redis fill:#ffcccc
    style FileStorage fill:#ccffcc
```

---

## Component Architecture

```mermaid
graph LR
    subgraph "Frontend Components"
        A[App.tsx<br/>Main Application]
        B[Search.tsx<br/>Search Interface]
        C[ChatWindow.tsx<br/>Chat Interface]
        D[ChatInput.tsx<br/>Input Component]
        E[ChatMessage.tsx<br/>Message Component]
    end
    
    subgraph "Backend API"
        F[main.py<br/>FastAPI App]
        G[search.py<br/>Search Routes]
        H[api.py<br/>API Routes]
    end
    
    subgraph "Core Services"
        I[vector_store.py<br/>AdvancedVectorStore]
        J[embed.py<br/>Redis Operations]
        K[document_store.py<br/>BuffyDocumentStore]
        L[embedding_service.py<br/>EmbeddingService]
    end
    
    subgraph "Data Models"
        M[EpisodeDocument<br/>Data Class]
        N[SearchResult<br/>Data Class]
    end
    
    A --> B
    A --> C
    C --> D
    C --> E
    B --> F
    F --> G
    F --> H
    G --> I
    I --> J
    I --> K
    I --> L
    K --> M
    I --> N
    
    style A fill:#e1f5ff
    style F fill:#fff4e1
    style I fill:#ffe1f5
    style M fill:#f0f0f0
```

---

## Data Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend as React Frontend
    participant API as FastAPI Backend
    participant VectorStore as AdvancedVectorStore
    participant Embedder as SentenceTransformer
    participant Redis as Redis Vector DB
    participant FileStore as File Storage
    
    Note over User,FileStore: Data Ingestion Phase
    User->>FileStore: Import Content JSON
    FileStore->>FileStore: Parse Episode Data
    FileStore->>Embedder: Generate Embeddings
    Embedder->>FileStore: Save Embeddings
    FileStore->>Redis: Load Data to Redis
    Redis->>Redis: Create Vector Index
    
    Note over User,FileStore: Search Query Phase
    User->>Frontend: Enter Search Query
    Frontend->>API: POST /api/search
    API->>VectorStore: search_episodes(query)
    VectorStore->>Embedder: Encode Query
    Embedder-->>VectorStore: Query Embedding
    VectorStore->>FileStore: Load Episode Data
    VectorStore->>FileStore: Load Embeddings
    VectorStore->>VectorStore: Calculate Similarity
    VectorStore->>VectorStore: Extract Characters/Themes
    VectorStore->>VectorStore: Boost Scores
    VectorStore-->>API: Search Results
    API-->>Frontend: JSON Response
    Frontend-->>User: Display Results
```

---

## Storage Architecture

```mermaid
graph TB
    subgraph "Primary Storage: Redis"
        Redis[(Redis Server<br/>Port 6379)]
        RediSearch[RediSearch Module<br/>Vector Search]
        RedisJSON[RedisJSON Module<br/>JSON Storage]
        Index[Vector Index<br/>idx:buffy_vss]
        
        Redis --> RediSearch
        Redis --> RedisJSON
        RediSearch --> Index
    end
    
    subgraph "Backup Storage: File System"
        Episodes[app/data/episodes/<br/>season_*.json]
        Embeddings[app/data/embeddings/<br/>season_*_embeddings.json]
        Backups[app/data/backup_*/<br/>Timestamped Backups]
    end
    
    subgraph "Source Data"
        Content[app/content/<br/>buffy_all_seasons_*.json]
    end
    
    Content --> Episodes
    Content --> Embeddings
    Episodes --> Redis
    Embeddings --> Redis
    Episodes --> Backups
    Embeddings --> Backups
    
    style Redis fill:#ffcccc
    style Episodes fill:#ccffcc
    style Embeddings fill:#ccffcc
    style Content fill:#ffffcc
```

---

## Search Pipeline

```mermaid
flowchart TD
    Start([User Query]) --> Encode[Encode Query<br/>SentenceTransformer]
    Encode --> Analyze[Analyze Query Type<br/>relationship/quote/scene/episode]
    Analyze --> ExtractChars[Extract Characters<br/>from Query]
    Analyze --> ExtractThemes[Extract Themes<br/>from Query]
    
    ExtractChars --> LoadData[Load Episode Data<br/>from File Storage]
    ExtractThemes --> LoadData
    LoadData --> LoadEmbeddings[Load Embeddings<br/>from File Storage]
    
    LoadEmbeddings --> CalcSimilarity[Calculate Cosine Similarity<br/>Query vs Episode Embeddings]
    
    CalcSimilarity --> BoostScore[Boost Score Based On:<br/>- Character Matches<br/>- Theme Matches<br/>- Query Type]
    
    BoostScore --> ExtractContent[Extract Relevant Content<br/>Best Matching Summary Part]
    ExtractContent --> ExtractMeta[Extract Metadata:<br/>- Characters in Episode<br/>- Themes in Episode<br/>- Context String]
    
    ExtractMeta --> RankResults[Rank Results<br/>Sort by Score]
    RankResults --> FilterLimit[Filter & Limit Results]
    FilterLimit --> FormatResponse[Format Response<br/>SearchResult Objects]
    FormatResponse --> End([Return Results])
    
    style Start fill:#e1f5ff
    style Encode fill:#fff4e1
    style CalcSimilarity fill:#ffe1f5
    style End fill:#ccffcc
```

---

## Implementation Phases

```mermaid
gantt
    title Implementation Roadmap
    dateFormat YYYY-MM-DD
    section Phase 1: Critical Fixes
    Add Redis Dependencies          :crit, p1-1, 2025-01-01, 1d
    Implement VectorStore            :crit, p1-2, after p1-1, 2d
    Fix API Response Format         :crit, p1-3, after p1-2, 1d
    Test Redis Connection           :crit, p1-4, after p1-3, 1d
    
    section Phase 2: Core Functionality
    Complete Search Implementation   :p2-1, after p1-4, 3d
    Data Pipeline Completion         :p2-2, after p2-1, 2d
    Frontend-Backend Integration     :p2-3, after p2-2, 2d
    End-to-End Testing               :p2-4, after p2-3, 2d
    
    section Phase 3: Enhancements
    Chat Functionality               :p3-1, after p2-4, 5d
    Additional Seasons               :p3-2, after p3-1, 3d
    Advanced Search Features         :p3-3, after p3-2, 4d
    
    section Phase 4: Production Ready
    Comprehensive Testing            :p4-1, after p3-3, 3d
    Deployment Preparation           :p4-2, after p4-1, 2d
    Performance Optimization         :p4-3, after p4-2, 3d
```

---

## Component Dependencies

```mermaid
graph TD
    subgraph "Dependencies"
        A[FastAPI] --> B[Uvicorn]
        C[AdvancedVectorStore] --> D[SentenceTransformer]
        C --> E[BuffyDocumentStore]
        F[Redis Operations] --> G[redis-py]
        F --> H[RediSearch]
        F --> I[RedisJSON]
        J[Frontend] --> K[React]
        J --> L[TypeScript]
        J --> M[Axios]
        J --> N[TailwindCSS]
    end
    
    style A fill:#fff4e1
    style C fill:#ffe1f5
    style F fill:#ffcccc
    style J fill:#e1f5ff
```

---

## Current State vs Target State

```mermaid
graph LR
    subgraph "Current State"
        CS1[Redis Dependencies Missing]
        CS2[VectorStore Empty]
        CS3[API Mismatch]
        CS4[File Storage Only]
    end
    
    subgraph "Target State"
        TS1[Redis Fully Integrated]
        TS2[VectorStore Complete]
        TS3[API Aligned]
        TS4[Hybrid Storage]
    end
    
    CS1 -->|Add redis-py| TS1
    CS2 -->|Implement Class| TS2
    CS3 -->|Fix Response Format| TS3
    CS4 -->|Add Redis Layer| TS4
    
    style CS1 fill:#ffcccc
    style CS2 fill:#ffcccc
    style CS3 fill:#ffcccc
    style TS1 fill:#ccffcc
    style TS2 fill:#ccffcc
    style TS3 fill:#ccffcc
    style TS4 fill:#ccffcc
```

---

## Data Model Relationships

```mermaid
erDiagram
    EPISODE_DOCUMENT ||--o{ SEARCH_RESULT : generates
    EPISODE_DOCUMENT ||--o{ EMBEDDING : has
    EPISODE_DOCUMENT ||--o{ CHARACTER : features
    EPISODE_DOCUMENT ||--o{ THEME : contains
    
    EPISODE_DOCUMENT {
        int season_number
        string episode_number
        string title
        string airdate
        list summary
        list synopsis
        list quotes
    }
    
    EMBEDDING {
        list summary_embedding
        list synopsis_embedding
        list quotes_embedding
    }
    
    SEARCH_RESULT {
        int season
        string episode
        string title
        float score
        list characters
        list themes
        string context
    }
    
    CHARACTER {
        string name
        string type
    }
    
    THEME {
        string name
        list keywords
    }
```

---

## Next Steps

Based on these diagrams, the implementation should follow this order:

1. **Phase 1: Foundation** (Critical Fixes)
   - Add Redis dependencies to requirements.txt
   - Implement VectorStore class properly
   - Fix API response format alignment
   - Test Redis connection

2. **Phase 2: Core Features** (Search Functionality)
   - Complete search implementation
   - Ensure data pipeline works end-to-end
   - Integrate frontend and backend
   - Test complete user flow

3. **Phase 3: Enhancements** (Advanced Features)
   - Add chat functionality
   - Expand to more seasons
   - Add advanced search features

4. **Phase 4: Production** (Polish & Deploy)
   - Comprehensive testing
   - Performance optimization
   - Deployment preparation

