# AGENTS.md

> **Note:** This file is for AI agents (Claude Code, etc.). For human-readable documentation, see:
> - [README.md](README.md) - Project overview and quick start
> - [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Production deployment guide
> - [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture details
> - [docs/CUSTOMIZATION.md](docs/CUSTOMIZATION.md) - Customization guide
> - [docs/PRIVACY.md](docs/PRIVACY.md) - Privacy considerations

This file provides technical guidance to AI agents working with code in this repository.

## Project Overview

WhatsApp Memories is a full-stack application that processes WhatsApp chat exports to extract meaningful message exchanges using LLMs. The pipeline uses Gemini models to identify "cute" or memorable conversations from chat history and stores them in a SQLite database. A Next.js frontend provides a WhatsApp-like interface to browse and manage these memories.

## Architecture

### Backend (Python/FastAPI)

**Core Processing Pipeline:**

- Entry point: `backend/process_whatsapp_messages.py` - Async CLI tool that chunks WhatsApp chat by day
- LLM Integration: `backend/utils/llm_utils.py` - Handles OpenAI-compatible API calls to Gemini models with caching
- Prompts: `backend/utils/prompts.py` - Contains prompt engineering for message extraction
- Models: `backend/utils/models.py` - Pydantic schemas (`MessageDetail`, `CuteMessagesResult`)

**API Layer:**

- `backend/main.py` - FastAPI application with health check at `/health`
- `backend/routers/messages.py` - Two routers:
  - `exchanges_router` (`/api/exchanges`) - List, detail, delete, and merge operations on exchanges
  - `messages_router` (`/api/messages`) - Bulk message deletion by IDs

**Data Layer:**

- `backend/utils/cache_utils.py` - SQLite database abstraction with:
  - `cache_data` table: Raw JSON storage of LLM results
  - `indexed_keys` table: Tracks which cache keys to display
  - `exchanges` table: Normalized exchange metadata (foreign key to cache_data)
  - `messages_normalized` table: Individual messages with chronological ordering
  - Foreign key cascades handle deletions automatically
  - Transaction management with explicit BEGIN/COMMIT/ROLLBACK
  - Functions for pagination, sorting, merging exchanges, and chronological re-indexing

**Key Design Patterns:**

- Responses are cached by hash of input parameters to avoid redundant LLM calls
- Cache keys use context disambiguation: `{filename}::{function_name}` prefixes
- All DB operations enable `PRAGMA foreign_keys = ON` for referential integrity
- Async/await throughout with semaphore-based rate limiting for LLM calls

### Frontend (Next.js 15/React 19/TypeScript)

**Structure:**

- `frontend/app/page.tsx` - Main WhatsApp clone interface with infinite scroll
- `frontend/app/exchanges/page.tsx` - Server-side rendered list view (alternative interface)
- `frontend/app/exchanges/[exchangeId]/page.tsx` - Dynamic route for individual exchanges
- `frontend/app/components/` - `MessageBubble.tsx`, `SidebarItem.tsx`

**API Routes (BFF Pattern):**

- `frontend/app/api/messages/route.ts` - Proxies to backend `/api/exchanges` with pagination
- `frontend/app/api/messages/delete/route.ts` - Proxies message deletion
- `frontend/app/api/exchanges/[exchangeId]/route.ts` - Fetches single exchange details
- `frontend/app/api/exchanges/merge-multiple/route.ts` - Merges multiple exchanges

**Features:**

- Responsive mobile/desktop layout with view state management
- Message selection mode for bulk deletion
- Exchange merge mode with source file validation
- Infinite scroll using Intersection Observer
- Real-time UI updates after delete/merge operations
- Browser history integration for back button navigation

**UI Stack:**

- Radix UI components (Dialog, DropdownMenu, AlertDialog, etc.)
- Tailwind CSS for styling
- shadcn/ui component library

## Development Commands

### Backend

```bash
# Setup environment
make init                  # Clean and create virtual environment with uv

# Run processing pipeline
make start ARGS="--file_in=backend/data_in/_chat.txt --log_level=DEBUG"

# Start API server
make run-backend           # Runs on http://0.0.0.0:8000 with hot reload

# Testing
make test-<module>         # Run tests for specific module (e.g., test-utils)

# Code quality
make format                # Format code with ruff
make lint                  # Lint and fix with ruff

# Database
make clear-cache           # Delete backend_cache.db (or SQLITE_DB_PATH if set)
```

### Frontend

```bash
cd frontend

# Install dependencies
pnpm install

# Development
pnpm run dev                # Start dev server (usually http://localhost:3000)

# Production
pnpm run build              # Build for production
pnpm start                  # Start production server

# Linting
pnpm run lint               # Next.js ESLint
```

## Environment Variables

Backend requires:

- `GEMINI_API_KEY` - API key for Gemini models (used with OpenAI-compatible endpoint)
- `SQLITE_DB_PATH` (optional) - Custom path for SQLite database (defaults to `backend_cache.db`)

Frontend requires:

- Backend API accessible (configure base URL in API routes if not localhost:8000)

## Important Implementation Details

**LLM Processing:**

- Default model: `gemini-2.5-flash-preview-05-20` for extraction
- Batching is commented out but supported (BATCH_SIZE = 500)
- Temperature set to 0.0 for deterministic outputs
- Structured output parsing via Pydantic models
- Max 10 retries for API calls

**Database Schema:**

- Messages maintain `message_index_in_exchange` for ordering within an exchange
- Merge operation re-indexes messages chronologically using date/time parsing
- Date format: `DD.MM.YY`, Time format: `HH:MM:SS` or `HH:MM`
- Exchange merging moves all messages to the exchange with the smallest ID

**Frontend State Management:**

- Main list uses paginated summary data (first message only)
- Detail view fetches full exchange with all messages on selection
- `currentExchangeDetails` holds the active exchange data
- Merge mode restricts selection to same `sourceFile` to maintain context

**API Response Formats:**

- Backend returns `ExchangeDetailResponse` with nested `MessageResponse[]`
- Frontend BFF transforms backend responses to include `exchange_id` and `sourceFile`
- Pagination metadata: `currentPage`, `pageSize`, `totalItems`, `totalPages`, `hasMore`

## Common Gotchas

1. **Foreign Keys**: Always check that `PRAGMA foreign_keys = ON` is set before operations that rely on cascading
2. **Cache Context**: When adding new LLM calls, ensure `calling_context` is set for proper cache namespacing
3. **Message IDs**: Frontend relies on `message_id` from backend; filtering out undefined IDs prevents errors
4. **Date Parsing**: Message chronological sorting assumes 21st century dates (20XX) in merge operations
5. **Mobile Navigation**: Use browser history state for proper back button behavior in mobile view

## Testing Notes

- Test framework: pytest with pytest-asyncio
- Mocking: pytest-mock for async operations
- Run tests from project root using `make test-<module>` syntax
