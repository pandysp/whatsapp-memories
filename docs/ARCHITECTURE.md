# Architecture

This document describes the system design and technical decisions behind WhatsApp Memory Curator.

## System Overview

```
WhatsApp Export (txt)
         ↓
    Processing Pipeline (Python)
    - Chunk by day
    - Extract with Gemini Flash
    - Cache in SQLite
         ↓
    FastAPI Backend
    - REST API
    - CRUD operations
         ↓
    Next.js Frontend
    - WhatsApp Clone UI
    - Browse & Curate
```

## Backend Architecture

### Processing Pipeline

**Entry Point:** `backend/process_whatsapp_messages.py`

The core extraction pipeline:
1. **Read** WhatsApp export file
2. **Chunk** messages by day using regex pattern matching
3. **Extract** memorable exchanges via async LLM calls
4. **Cache** results in SQLite with normalized schema

**Key Design Decision:** Day-based chunking provides optimal context window for the LLM—enough context to understand conversations, but small enough for fast, cheap API calls.

### LLM Integration

**File:** `backend/utils/llm_utils.py`

- Uses OpenAI-compatible API to call Gemini 2.5 Flash
- Structured output with Pydantic models (no JSON parsing!)
- Async/await with semaphore rate limiting (5 concurrent requests)
- Hash-based caching with context disambiguation

**Why Gemini 2.5 Flash?**
- **Cost**: ~$3 for 50k messages (vs. ~$50 with GPT-4)
- **Speed**: 1-2 seconds per daily chunk
- **Quality**: With good few-shot examples, performs like GPT-4

### Caching Strategy

**File:** `backend/utils/cache_utils.py`

**Cache Key Generation:**
```python
cache_key = hash(input_data + context)
# Example: hash("chunk_text" + "process_whatsapp_messages.py::process_chunk_llm")
```

**Why context matters:** Prevents cache collisions if you add a second LLM pass or modify prompts later.

**Why SQLite over Redis?**
- Already using SQLite for the app database
- Cache hit rate is ~99% after initial processing
- Simpler deployment (one database, not two)
- Fast enough for this use case

### Database Schema

Three main tables:

```sql
cache_data
├── cache_key (TEXT PRIMARY KEY)
├── data (TEXT)  -- JSON blob from LLM
└── calling_context (TEXT)

exchanges
├── exchange_id (INTEGER PRIMARY KEY)
├── cache_key (TEXT, FOREIGN KEY)
└── source_file (TEXT)

messages_normalized
├── message_id (INTEGER PRIMARY KEY)
├── exchange_id (INTEGER, FOREIGN KEY)
├── message_index_in_exchange (INTEGER)
├── date (TEXT)
├── time (TEXT)
├── person (TEXT)
└── quote (TEXT)
```

**Key Features:**
- Foreign key cascades for automatic cleanup
- Messages maintain chronological order via `message_index_in_exchange`
- Merge operation re-indexes messages by parsing dates/times
- Transaction management with explicit BEGIN/COMMIT/ROLLBACK

### API Layer

**FastAPI** application with two routers:

**Exchanges Router** (`/api/exchanges`):
- `GET /api/exchanges` - List with pagination
- `GET /api/exchanges/{id}` - Get single exchange with all messages
- `DELETE /api/exchanges/{id}` - Delete exchange (cascades to messages)
- `POST /api/exchanges/merge-multiple` - Merge exchanges

**Messages Router** (`/api/messages`):
- `POST /api/messages/delete` - Bulk delete by message IDs

## Frontend Architecture

### Tech Stack

- **Next.js 15** with App Router
- **React 19**
- **TailwindCSS** + **shadcn/ui**
- **TypeScript** for type safety

### Page Structure

```
app/
├── page.tsx                          # Main UI (WhatsApp clone)
├── exchanges/
│   ├── page.tsx                     # List view (alternative)
│   └── [exchangeId]/page.tsx        # Detail view
├── api/                              # BFF routes
│   ├── messages/route.ts            # Proxy to backend
│   └── exchanges/                   # Proxy endpoints
└── components/
    ├── MessageBubble.tsx
    └── SidebarItem.tsx
```

### BFF Pattern

Frontend API routes proxy to backend FastAPI:
- Handles CORS
- Adds pagination logic
- Transforms responses for frontend format
- Keeps backend URL private from client

**Example:** `frontend/app/api/messages/route.ts`
```typescript
// Fetches from backend: http://localhost:8000/api/exchanges
// Returns to frontend with transformed pagination metadata
```

### State Management

**Main exchange list:**
- Server-fetched, paginated
- Shows only first message per exchange (preview)

**Selected exchange details:**
- Fetched separately when user clicks
- Full message history loaded
- Stored in `currentExchangeDetails` state

**Why separate?**
- Keeps initial load fast (summaries only)
- Full details only when needed
- Reduces memory footprint for large histories

### Features

**Infinite Scroll:**
- Uses Intersection Observer API
- Loads next page when sentinel element is visible
- Smooth, no pagination buttons

**Selection Modes:**
- **Message selection**: Click messages to mark for deletion
- **Merge mode**: Select multiple exchanges to combine

**Mobile Support:**
- Responsive layout with view state (`'list' | 'chat'`)
- Browser history integration for back button
- Touch-friendly UI

## Key Design Decisions

### 1. Single-Pass Extraction

**Decision:** Only one LLM pass, no secondary filtering.

**Why:** Gemini Flash with good few-shot examples is accurate enough. A second pass would:
- Double the cost
- Double the time
- Only remove 10-15% more messages

**Better approach:** Over-extract slightly, let user curate via UI.

### 2. SQLite vs. Redis

**Decision:** SQLite for everything (cache + app data).

**Why:**
- Simpler deployment (one database)
- Cache hits are 99% after initial processing
- SQLite is fast enough (<10ms queries)
- Easier to inspect data (just open the .db file)

**When would Redis make sense?** If you needed:
- Distributed caching across multiple machines
- TTL-based expiration
- Sub-millisecond latency at scale

### 3. Day-Based Chunking

**Decision:** Split chat history by calendar day.

**Why:**
- Conversations naturally cluster by day
- Optimal context window size for LLM
- Easy to parallelize (each day = one API call)
- Handles multi-line messages correctly

**Alternative considered:** Fixed token-count chunks. **Rejected** because:
- Would split conversations mid-exchange
- Harder to debug
- No performance benefit

### 4. Few-Shot Learning

**Decision:** Use few-shot examples instead of fine-tuning.

**Why:**
- Works immediately (no training time)
- Easy to iterate (just change prompt)
- Costs $0 (vs. fine-tuning costs)
- Sufficient for this use case

**How it works:** Show the LLM 3-4 GOOD examples (playful, vulnerable, meaningful) and 3-4 BAD examples (logistics, mundane). The model learns the pattern.

### 5. Over-Extraction Bias

**Decision:** Extract slightly more than needed, provide delete UI.

**Why:**
- False negatives (missing good stuff) hurt more than false positives
- Easy to delete unwanted messages
- Impossible to recover if you miss something
- Human judgment beats LLM on borderline cases

## Development Workflow

```bash
# 1. Process new data
make start ARGS="--file_in=backend/data_in/my_chat.txt"

# 2. Start backend
make run-backend

# 3. Start frontend
cd frontend && pnpm run dev

# 4. Curate in UI
# Browse, delete unwanted, merge related exchanges

# 5. Iterate
# Adjust prompts, re-process, repeat
```

## Performance Characteristics

**Processing:**
- 50,000 messages = ~1,800 daily chunks
- 5 concurrent API calls
- ~2 seconds per chunk average
- **Total: 15-20 minutes**

**Caching:**
- First run: 15-20 minutes
- Subsequent runs: <1 second (cache hits)
- Cache key includes prompt context

**API Latency:**
- List exchanges: ~10ms (SQLite query)
- Get single exchange: ~50ms (join query)
- Delete: ~20ms (cascade delete)
- Merge: ~100ms (re-index messages)

**Frontend:**
- Initial load: <1s (first 20 exchanges)
- Infinite scroll: <500ms per page
- UI interactions: <100ms (optimistic updates)

## Future Improvements

**Potential enhancements:**

1. **Support other LLM providers** (OpenAI, Claude, local models)
2. **Support other chat platforms** (Telegram, Signal, Slack)
3. **Better evaluation metrics** (automated quality testing)
4. **UI search/filters** (date ranges, keyword search)
5. **Export functionality** (PDF, HTML, JSON)
6. **Docker containerization** (easier deployment)

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js App Router](https://nextjs.org/docs/app)
- [Gemini API](https://ai.google.dev/docs)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
