# 🎮 Backend - RPG Gaming Assistant API

**FastAPI backend with CrewAI multi-agent system, ChromaDB RAG, and smart rate limit fallback.**

Core backend service that powers the game assistant sidebar widget. Handles intelligent search routing, conversation persistence, and seamless LLM fallback when API quotas are exhausted.

## ✨ Key Features

*   **FastAPI REST API**: 7 endpoints for chat, conversations, and widget serving
*   **🧠 Intelligent Query Routing**:
  *   **Default (Normal)**: Full CrewAI crew with Groq LLM for formatted responses
    *   **Fallback (Rate Limited)**: Direct search on 429 errors - no LLM calls
    *   **Auto-Detection**: Catches rate limits and switches automatically
*   **Hybrid Search Engine**:
    *   **ChromaDB RAG**: Semantic search on cached game data (instant, free)
    *   **Web Search**: Serper API + DuckDuckGo for non-cached queries
    *   **Auto-Indexing**: Web results automatically cached for future queries
    *   **Strict Relevance**: 0.45 distance threshold prevents false positives
*   **Persistent Conversations**:
    *   SQLite database with game-level separation
    *   Message history with timestamps
    *   Indexed queries for fast retrieval
*   **Multi-Agent Workflow**:
    *   **Researcher Agent**: Searches and gathers information
    *   **Game Expert Agent**: Formats answers to 1-3 sentences max

## 🚀 Quick Start

### Prerequisites
| Component | Version |
|-----------|---------|
| **Python** | 3.10+ |
| **Groq API Key** | [Get here](https://console.groq.com/keys) |
| **Serper API Key** | [Get here](https://serper.dev/) |

### Installation

1. **Install dependencies** (in this directory)
   ```bash
   pip install -e .
   ```

2. **Configure API keys** (create `.env` in project root)
   ```env
  GROQ_API_KEY=your_key_here
   SERPER_API_KEY=your_key_here
   CHROMA_DB_PATH=./chroma_db
   ```

### Run Backend

```bash
# Option 1: Start API server (recommended for widget)
python main.py api

# Option 2: Interactive CLI
python main.py

# Option 3: Direct with uvicorn
uvicorn src.rpgagents.api:app --host 127.0.0.1 --port 8000
```

✅ API running on: **http://127.0.0.1:8000**  
📖 OpenAPI docs: **http://127.0.0.1:8000/docs**

## 📡 API Endpoints

### Chat Endpoint (Main)
```
POST /chat

Request:
{
  "game_name": "Valorant",
  "message": "best agent for beginners?",
  "conversation_id": "optional-uuid"  # Auto-generated if omitted
}

Response:
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "game_name": "Valorant",
  "answer": "Phoenix, Sage, and Brimstone are great for beginners...",
  "timestamp": "2026-05-02T12:34:56.789Z"
}
```

### Conversation Management

```
POST /conversations
Create new conversation

GET /conversations?game_name=Valorant
List conversations by game

GET /conversations/{conversation_id}
Get single conversation details

GET /conversations/{conversation_id}/messages
Fetch all messages in conversation
```

### Widget
```
GET /widget
Serves embeddable HTML sidebar UI
```

## 🧠 Query Processing Pipeline

### Flow Diagram
```
POST /chat
    ↓
quick_search(game_name, query)
    ├─ Try: crew_search() [Full LLM Crew]
    │   ├─ Researcher Agent → GameSearchTool
    │   │   ├─ ChromaDB Search (distance < 0.45?)
    │   │   └─ Web Search (Serper + DuckDuckGo) if no cache
    │   │   └─ Auto-Index results into ChromaDB ✅
    │   └─ Game Expert Agent → Format to 1-3 sentences
    │
    └─ Catch 429/429 RESOURCE_EXHAUSTED Error
       └─ Fallback: direct_search() [No LLM]
           └─ GameSearchTool only → Return raw results
    
    ↓
ConversationStore.add_message()
    ├─ Store user message
    └─ Store assistant response
    
    ↓
Response to client
    └─ conversation_id, answer, timestamp
```

### Search Strategy

**Scenario 1: First Query (No Cache)**
```
Query: "best Valorant agent for beginners?"
  ↓
crew_search() with Groq LLM
  ├─ Researcher searches ChromaDB → not found
  └─ Fallback to web search
     └─ Serper API returns 10 results
        └─ Results indexed in ChromaDB ✅
  ↓
Game Expert formats: "Phoenix, Sage, Brimstone..."
  ↓
Response sent + stored in SQLite
```

**Scenario 2: Cached Query**
```
Query: "Valorant agents for new players?"
  ↓
crew_search() with Groq LLM
  ├─ Researcher searches ChromaDB → FOUND! ✅
  │  (distance 0.36 < 0.45 threshold)
  └─ No web search needed
  ↓
Game Expert formats cached results
  ↓
Response sent instantly ⚡ (0 API calls)
```

**Scenario 3: Rate Limit Hit**
```
Query: "Elden Ring build?"
  ↓
crew_search() attempts → Groq rate limit exceeded ❌
  └─ Catches "429" or "RESOURCE_EXHAUSTED"
  ↓
Fallback: direct_search() [no LLM]
  └─ Returns raw search results
  ↓
Response continues working ✅ (graceful degradation)
```

## 🏗️ Architecture

### Directory Structure
```
src/rpgagents/
├── main.py                    # Entry point, CLI, API startup
├── api.py                     # FastAPI app, 7 endpoints
├── crew.py                    # CrewAI agents definition
├── conversation_store.py      # SQLite conversation storage
│
├── config/
│   ├── agents.yaml            # Agent personality/roles
│   └── tasks.yaml             # Task descriptions/outputs
│
└── tools/
    ├── game_search_tool.py    # RAG search + fallback logic
    └── web_search_tool.py     # Serper API + DuckDuckGo
```

### Database Schema

#### conversations table
```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    game_name TEXT NOT NULL,
    title TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
CREATE INDEX idx_game_name ON conversations(game_name)
```

#### messages table
```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT FOREIGN KEY,
    role TEXT,  -- 'user' or 'assistant'
    content TEXT,
    created_at TIMESTAMP
)
CREATE INDEX idx_conversation ON messages(conversation_id)
```

Location: `knowledge/conversations.sqlite3`

### ChromaDB Structure

**Location**: `chroma_db/`

**Collections**: One per game
- `game_valorant`
- `game_hollow_knight`
- `game_elden_ring`
- etc.

**Documents**: Web search results, indexed automatically
- **Metadata**: game_name, source URL, timestamp
- **Embedding**: Sentence Transformers (all-MiniLM-L6-v2)
- **Distance Threshold**: 0.45 (strict relevance filter)

## ⚙️ Configuration

### Relevance Threshold (RAG)
**File**: [tools/game_search_tool.py](src/rpgagents/tools/game_search_tool.py#L86)
**Current**: `0.45`
- Distance < 0.45 = confidence > 0.55 (return result)
- Distance > 0.45 = trigger web search

### Response Format
**File**: [config/tasks.yaml](src/rpgagents/config/tasks.yaml)
**Current**: 1-3 sentences maximum
- Direct answer
- Key details/tips
- Source URL if available

### LLM Settings
**File**: [crew.py](src/rpgagents/crew.py)
**Temperature**: 0.3 (more deterministic, less creative)
**Model**: `groq/llama-3.1-70b-versatile`
**Max Tokens**: None (default)

### Web Search
**Primary**: Serper API (google.serper.dev)
**Fallback**: DuckDuckGo (ddgs package)
**Filters**:
- Language: English only
- Domains: Gaming wikis only (fandom.com, fextralife.com, ign.com, etc.)
- Blocks: Non-English sites (baidu.com, qq.com, etc.)

## 🔄 Error Handling

### Rate Limit (429)
**Behavior**:
- Detects `"429"` or `"RESOURCE_EXHAUSTED"` in error
- Automatically falls back to direct_search()
- No LLM formatting (returns raw results)
- System continues working ✅

**Example Log**:
```
[INFO] Rate limit detected. Fallback: direct_search()
[INFO] Returning results without LLM formatting
```

### No Results
**Behavior**:
1. ChromaDB search → No matches above threshold
2. Falls back to web search
3. Caches new results
4. Retries with cache on future queries

### Network Errors
**Behavior**:
- Serper API down → Falls back to DuckDuckGo
- DuckDuckGo also down → Returns cached results only
- Returns error message to client if no fallback available

## 📊 Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API** | FastAPI 0.104+ | REST endpoints |
| **Server** | Uvicorn | ASGI server |
| **RAG** | ChromaDB | Semantic search |
| **Embeddings** | Sentence Transformers | Vector generation |
| **Search** | Serper API + DuckDuckGo | Web search |
| **Web Scraping** | BeautifulSoup4 | Extract search results |
| **LLM** | Groq Llama 3.1 70B Versatile | Response formatting |
| **Agents** | CrewAI | Multi-agent orchestration |
| **Database** | SQLite | Message storage |
| **Task Queue** | Optional: Celery/Redis | Async processing |

## 🧪 Testing

### Test Chat Endpoint
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"game_name":"Valorant","message":"best agent for beginners?"}'
```

### Test Caching
1. Query 1: "Valorant agent tips" → uses web search
2. Query 2: Same query again → should be instant (cached)
3. Check logs for `"Local Source"` vs `"Web Index"`

### Test Rate Limit Fallback
1. Make enough queries to hit your Groq rate limit
2. Next query should return results (no error)
3. Check logs for `"Fallback: direct_search()"`

### Check Database
```bash
sqlite3 knowledge/conversations.sqlite3
sqlite> SELECT * FROM conversations;
sqlite> SELECT * FROM messages;
```

### Monitor ChromaDB
```python
from chromadb import Client
client = Client()
collection = client.get_collection("game_valorant")
print(f"Documents in collection: {collection.count()}")
```

## 🚀 Production Deployment

### Optimizations
1. **Disable reload**: Remove `reload=True` in main.py
2. **Use Gunicorn**: `gunicorn src.rpgagents.api:app --workers 4`
3. **Environment Variables**: Use `python-dotenv` (already integrated)
4. **Database**: Consider migrating from SQLite to PostgreSQL for multi-user
5. **Caching**: Add Redis for query result caching

### Security
1. Enable CORS only for trusted domains
2. Add API key authentication for `/chat` endpoint
3. Rate limit endpoints (FastAPI middleware)
4. Validate input length (prevent injection)
5. Use HTTPS in production

### Scaling
1. Implement request queuing (Celery + Redis)
2. Shard ChromaDB collections by game/region
3. Cache Groq responses in Redis
4. Use connection pooling for SQLite → PostgreSQL
5. Monitor API quota usage

## 📝 Known Limitations

1. **ChromaDB Size**: In-memory by default, grows with cached queries
   - Solution: Implement periodic cleanup or use persistent backend

2. **Groq Rate Limits**: Vary by plan and model
  - Solution: Automatic fallback works ✅ or upgrade tier

3. **Serper Quota**: Limited free tier calls
   - Solution: Prioritize cached searches, upgrade if needed

4. **SQLite Concurrency**: Not ideal for multi-user
   - Solution: Use PostgreSQL in production

## 🔧 Troubleshooting

### "Cannot find module rpgagents"
```bash
cd backend/rpgagents
pip install -e . --force-reinstall --no-deps
```

### "429 RESOURCE_EXHAUSTED"
- ✅ Expected - system auto-falls back
- Check logs for confirmation
- Upgrade API tier if frequently hitting limit

### "No results found"
1. Verify ChromaDB is initialized: `ls chroma_db/`
2. Check distance threshold isn't too strict
3. Try web search with: `SERPER_API_KEY` set

### "API won't start"
1. Verify port 8000 is free: `lsof -i :8000`
2. Check Python version: `python --version` (need 3.10+)
3. Verify dependencies: `pip list | grep fastapi`

## 📄 License

MIT License - See [LICENSE](../../LICENSE) file
