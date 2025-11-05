# WhatsApp Memory Curator

> Extract meaningful conversations from years of WhatsApp chat history using AI

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)

## The Problem

You have 50,000 WhatsApp messages spanning 5 years with someone important to you. Somewhere in there are beautiful moments—inside jokes, vulnerable conversations, shared memories. But they're buried under "What time tonight?" and "Did you see this meme?"

## The Solution

WhatsApp Memory Curator uses **Gemini 2.5 Flash** to extract memorable exchanges from WhatsApp exports. It reduces 50,000 messages to ~400 curated moments you'll actually want to revisit.

**Key Features:**
- 🎯 **AI-powered extraction** using few-shot learning
- 💰 **Cost-efficient**: ~$3 for 50k messages
- ⚡ **Fast**: Async processing with smart caching
- 🎨 **WhatsApp-clone UI** for browsing memories
- 🔒 **Privacy-first**: All processing happens locally
- ✂️ **Human-in-the-loop**: Delete and merge functionality

## Tech Stack

**Backend:**
- Python 3.11+ with FastAPI
- Gemini 2.5 Flash (via OpenAI-compatible API)
- SQLite for caching & storage
- Async processing with semaphore rate limiting

**Frontend:**
- Next.js 15 with App Router
- React 19
- TailwindCSS + shadcn/ui
- Infinite scroll, responsive design

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Gemini API key](https://aistudio.google.com/apikey)

### Backend Setup

```bash
# Install dependencies (using uv)
uv sync

# Configure environment
cp .env.example .env
# Add your GEMINI_API_KEY to .env

# Run with demo data
make start ARGS="--file_in=backend/data_in/demo_chat.txt --log_level=INFO"

# Start API server
make run-backend
```

### Frontend Setup

```bash
cd frontend
pnpm install
pnpm run dev
```

Visit **http://localhost:3000** to see the WhatsApp clone UI with demo data.

## How It Works

1. **Export** your WhatsApp chat (Settings → Chats → Export Chat)
2. **Chunk** the history by day (optimal LLM context window)
3. **Extract** memorable exchanges using structured output
4. **Cache** results in SQLite (smart deduplication)
5. **Browse** in a polished WhatsApp UI
6. **Curate** with delete/merge features

**The Secret Sauce:** Few-shot examples teach the LLM your personal definition of "memorable." The model learns to recognize patterns—playful banter, vulnerable moments, inside jokes—specific to your relationship.

## Documentation

**Getting Started:**
- [README.md](README.md) - You're here! Project overview and quick start
- [docs/USER_GUIDE.md](docs/USER_GUIDE.md) - How to use the deployed app

**Technical Details:**
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design and data flow
- [docs/CUSTOMIZATION.md](docs/CUSTOMIZATION.md) - Customize prompts and examples

**Production:**
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Deploy to Vercel + Fly.io
- [docs/OPERATIONS.md](docs/OPERATIONS.md) - Day-to-day maintenance and ops
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Quick solutions to common issues

**Privacy & Security:**
- [docs/PRIVACY.md](docs/PRIVACY.md) - Privacy considerations and best practices

## Privacy

- All processing happens **locally** on your machine
- Only your LLM provider (Google/Gemini) sees messages during API calls
- No data stored on external servers
- See [docs/PRIVACY.md](docs/PRIVACY.md) for best practices

## Cost & Performance

**Real-world stats (Nov 2025):**
- **Input:** 50,000 messages over 5 years
- **Output:** 400 exchanges (~2,000 messages)
- **Cost:** ~$3 USD with Gemini 2.5 Flash
- **Time:** 15-20 minutes (async processing)
- **Reduction:** 95% filtered while keeping all meaningful moments

## Development

```bash
# Backend
make format    # Format with ruff
make lint      # Lint and fix

# Frontend
cd frontend
pnpm run lint   # ESLint
```

## Deployment

**For Local Use (Recommended):**

This tool is designed to run locally to maximize privacy and minimize costs:
- All chat processing happens on your machine
- No server stores your conversations
- Pay only for LLM API calls (~$3 per 50k messages)

**For Production Deployment:**

Want to share your curated memories online? See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for a complete guide to deploying on:
- **Vercel** (frontend) - Free tier with global CDN
- **Fly.io** (backend + SQLite) - Free tier with persistent storage

Deployment takes ~30-45 minutes and stays within free tier limits for personal use.

## Why This Project?

I built this as a 7th anniversary gift to curate 5 years of WhatsApp chats with my girlfriend. The goal was to extract the truly meaningful conversations—the inside jokes, the vulnerable moments, the shared adventures—from tens of thousands of mundane messages.

**Key insights:**
- Few-shot learning makes Gemini Flash perform like GPT-4 for this specific task
- Over-extraction (with human curation via UI) is better than under-extraction
- SQLite is simpler than Redis for this use case
- Single-pass extraction is sufficient (no need for two-pass filtering)

Presented at **AI Tinkerers Cologne** (Nov 2025).

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Acknowledgments

- [AI Tinkerers](https://aitinkerers.org/) for the community and speaking opportunity
- Claude Code for help with evaluation and iteration
- The WhatsApp team for exportable chat history

## Support

This is a personal project, but issues and PRs are welcome! For questions:
- Open an issue on GitHub
- Or reach out at [@aspannagel](https://twitter.com/aspannagel)

---

**Built with ❤️ and AI by Andreas Spannagel**
