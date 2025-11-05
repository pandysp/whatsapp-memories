# Deployment Plan: WhatsApp Memories to Production

## Overview

Deploy WhatsApp Memories application using a hybrid architecture:
- **Frontend**: Vercel (Next.js hosting)
- **Backend**: Fly.io (FastAPI + SQLite with persistent storage)

**Why this approach:**
- KISS principle - minimal code changes
- Keep SQLite unchanged (no database adapter needed)
- Each platform does what it's best at
- Free tier available on both platforms

**Estimated Time:** ~30-45 minutes

---

## Prerequisites

### Required Accounts
- [ ] GitHub account (for version control and Vercel deployment)
- [ ] Vercel account (free tier) - sign up at vercel.com
- [ ] Fly.io account (free tier) - sign up at fly.io
  - **Note:** Fly.io requires credit card for verification, but won't charge within free tier limits

### Required CLI Tools
```bash
# Install Fly.io CLI
curl -L https://fly.io/install.sh | sh

# Verify installation
fly version

# Install Vercel CLI (optional, can use web UI instead)
npm install -g vercel
```

### Environment Variables Needed
- `GEMINI_API_KEY` - Your Gemini API key (already have this)
- `ALLOWED_ORIGINS` - CORS origins for backend (will set during deployment)

---

## Phase 1: Prepare Backend for Deployment

### 1.1 Add CORS Middleware to FastAPI

**File:** `backend/main.py`

**Add after imports:**
```python
from fastapi.middleware.cors import CORSMiddleware
import os
```

**Add after `app = FastAPI()`:**
```python
# CORS configuration for cross-origin requests from frontend
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000"  # Default for local development
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Why:** Frontend on Vercel needs permission to call backend API on Fly.io

### 1.2 Create Dockerfile for Backend

**File:** `Dockerfile` (in project root)

```dockerfile
# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv for dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml .
COPY uv.lock .

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY backend ./backend

# Expose port
EXPOSE 8000

# Run FastAPI with uvicorn
CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Why:** Fly.io needs a Docker container to run the backend

### 1.3 Create fly.toml Configuration

**File:** `fly.toml` (in project root)

```toml
app = "whatsapp-memories-api"  # Change this to your desired app name

[build]

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256

[mounts]
  source = "whatsapp_memories_data"
  destination = "/data"
```

**Why:** Configures Fly.io app settings and persistent storage mount

### 1.4 Update SQLite Database Path for Production

**File:** `backend/utils/cache_utils.py`

**Find the line:**
```python
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "backend_cache.db")
```

**Replace with:**
```python
# Use /data volume on Fly.io, local file for development
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "/data/backend_cache.db" if os.path.exists("/data") else "backend_cache.db")
```

**Why:** Fly.io persistent volume is mounted at `/data`, local dev uses current directory

### 1.5 Create .dockerignore

**File:** `.dockerignore` (in project root)

```
# Python
__pycache__
*.pyc
.pytest_cache
.venv
.ruff_cache
.mypy_cache

# Local database
backend_cache.db

# Environment
.env
.env.local

# Frontend
frontend/
node_modules/

# Git
.git/
.gitignore

# Documentation
docs/
*.md
!README.md

# IDE
.vscode/
.idea/

# macOS
.DS_Store

# Data
backend/data_in/*.txt
!backend/data_in/demo_chat.txt
```

**Why:** Reduce Docker image size by excluding unnecessary files

---

## Phase 2: Deploy Backend to Fly.io

### 2.1 Login to Fly.io

```bash
fly auth login
```

This will open a browser window for authentication.

### 2.2 Launch Fly.io Application

```bash
# From project root
fly launch --no-deploy
```

**Interactive prompts - answer as follows:**
- App name: Choose a unique name (e.g., `whatsapp-memories-api-yourname`)
- Region: Choose closest to you (e.g., `iad` for US East, `ams` for Europe)
- Postgres database: **No**
- Redis database: **No**
- Deploy now: **No** (we need to set up volume first)

This creates `fly.toml` (if you didn't create it manually in step 1.3)

### 2.3 Create Persistent Volume

```bash
# Create a 1GB volume for SQLite database
fly volumes create whatsapp_memories_data --size 1 --region YOUR_REGION
```

Replace `YOUR_REGION` with the region you chose (e.g., `iad`)

**Verify volume:**
```bash
fly volumes list
```

### 2.4 Set Environment Variables

```bash
# Set Gemini API key
fly secrets set GEMINI_API_KEY="your-actual-gemini-api-key"

# Set CORS origins (we'll update this after Vercel deployment)
fly secrets set ALLOWED_ORIGINS="http://localhost:3000"
```

**Verify secrets:**
```bash
fly secrets list
```

### 2.5 Deploy Backend

```bash
fly deploy
```

**What happens:**
- Builds Docker image
- Pushes to Fly.io registry
- Creates VM instance
- Mounts persistent volume at `/data`
- Starts FastAPI application

**Verify deployment:**
```bash
fly status
fly logs
```

### 2.6 Test Backend API

```bash
# Get your app URL
fly info

# Test health endpoint
curl https://YOUR_APP_NAME.fly.dev/health
```

Expected response: `{"status":"healthy"}`

**Note your backend URL:** `https://YOUR_APP_NAME.fly.dev` - you'll need this for frontend configuration

---

## Phase 3: Update Frontend Configuration

### 3.1 Update API Base URL Logic

**File:** `frontend/app/api/messages/route.ts`

**Find:**
```typescript
const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL || "http://localhost:8000";
```

**Replace with:**
```typescript
const FASTAPI_BASE_URL = process.env.NEXT_PUBLIC_API_URL || process.env.FASTAPI_BASE_URL || "http://localhost:8000";
```

**Do the same for all API route files:**
- `frontend/app/api/messages/route.ts`
- `frontend/app/api/messages/delete/route.ts`
- `frontend/app/api/exchanges/[exchangeId]/route.ts`
- `frontend/app/api/exchanges/merge-multiple/route.ts`

**Why:** `NEXT_PUBLIC_API_URL` can be set in Vercel dashboard

### 3.2 Create .env.example

**File:** `frontend/.env.example`

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# For production, set to your Fly.io backend URL:
# NEXT_PUBLIC_API_URL=https://your-app.fly.dev
```

### 3.3 Update .gitignore (if needed)

Ensure `frontend/.env.local` is ignored:

```bash
# Add to .gitignore if not already there
frontend/.env.local
```

---

## Phase 4: Deploy Frontend to Vercel

### 4.1 Push Code to GitHub

```bash
# Commit all changes
git add .
git commit -m "Prepare for production deployment with Fly.io backend"
git push origin main
```

### 4.2 Deploy to Vercel (Web UI Method)

1. Go to https://vercel.com/new
2. Click "Import Git Repository"
3. Select your GitHub repository
4. **Configure Project:**
   - Framework Preset: **Next.js**
   - Root Directory: `frontend`
   - Build Command: `npm run build` (default)
   - Output Directory: `.next` (default)

5. **Environment Variables:**
   - Key: `NEXT_PUBLIC_API_URL`
   - Value: `https://YOUR_FLY_APP_NAME.fly.dev` (your Fly.io backend URL)

6. Click **Deploy**

### 4.3 Alternative: Deploy via CLI

```bash
cd frontend
vercel

# Follow prompts:
# Set up and deploy? Yes
# Which scope? Your account
# Link to existing project? No
# Project name? whatsapp-memories (or your choice)
# Directory? ./
# Override settings? No

# Set environment variable
vercel env add NEXT_PUBLIC_API_URL production
# Enter value: https://YOUR_FLY_APP_NAME.fly.dev

# Deploy to production
vercel --prod
```

### 4.4 Note Your Frontend URL

After deployment, Vercel will give you a URL like:
`https://whatsapp-memories.vercel.app`

---

## Phase 5: Configure CORS for Production

### 5.1 Update Backend CORS Origins

Now that you have your Vercel frontend URL, update the backend:

```bash
# Update CORS origins to include your Vercel URL
fly secrets set ALLOWED_ORIGINS="https://your-app.vercel.app,http://localhost:3000"
```

Replace `your-app.vercel.app` with your actual Vercel URL.

### 5.2 Restart Backend

```bash
fly apps restart whatsapp-memories-api
```

Or wait ~30 seconds for automatic restart after secret update.

---

## Phase 6: Populate Production Database

### 6.1 SSH into Fly.io Instance

```bash
fly ssh console
```

You're now inside the running container.

### 6.2 Check Database Location

```bash
ls -la /data/
```

You should see `/data/` is empty (no database yet).

Type `exit` to leave SSH session.

### 6.3 Process Data from Local Machine

**Option A: Direct Remote Processing (Recommended)**

Set up a tunnel to Fly.io database:

```bash
# In one terminal, create proxy to Fly.io
fly proxy 8001:8000

# In another terminal, set env vars
export FASTAPI_BASE_URL=http://localhost:8001
export GEMINI_API_KEY=your-key

# Run processing script
make start ARGS="--file_in=backend/data_in/_chat.txt --log_level=INFO"
```

**Option B: Process Locally, Then Copy Database**

```bash
# Process locally first
make start ARGS="--file_in=backend/data_in/_chat.txt --log_level=INFO"

# Copy database to Fly.io
fly ssh sftp shell
# In SFTP:
put backend_cache.db /data/backend_cache.db
exit
```

**Option C: SCP Database File**

```bash
# Get Fly.io machine ID
fly machines list

# Copy database
fly ssh sftp shell -C "put backend_cache.db /data/backend_cache.db"
```

### 6.4 Verify Data

```bash
# Check your production frontend
open https://your-app.vercel.app

# Or test API directly
curl https://your-app.fly.dev/api/exchanges?page=1&page_size=20
```

---

## Phase 7: Verify Deployment

### 7.1 Test Frontend

1. Visit your Vercel URL: `https://your-app.vercel.app`
2. Verify:
   - [ ] Sidebar loads with exchanges
   - [ ] Clicking exchange shows messages
   - [ ] Mobile view works
   - [ ] No CORS errors in browser console

### 7.2 Test Backend

```bash
# Health check
curl https://your-app.fly.dev/health

# List exchanges
curl https://your-app.fly.dev/api/exchanges

# Get specific exchange
curl https://your-app.fly.dev/api/exchanges/1
```

### 7.3 Check Logs

**Backend logs:**
```bash
fly logs
```

**Frontend logs:**
- Vercel dashboard → your project → Deployments → Latest → Logs

---

## Phase 8: Configure Custom Domain (Optional)

### 8.1 Add Domain to Vercel

1. Vercel Dashboard → Project → Settings → Domains
2. Add your domain (e.g., `memories.yourdomain.com`)
3. Follow DNS configuration instructions

### 8.2 Add Domain to Fly.io (Optional)

```bash
# Add custom domain for API
fly certs add api.yourdomain.com

# Get certificate status
fly certs show api.yourdomain.com
```

Update DNS with provided values.

---

## Maintenance & Operations

### Adding New Memories

**Method 1: Local Processing to Production**
```bash
# Set environment to point to production
fly proxy 8001:8000

# In another terminal
export FASTAPI_BASE_URL=http://localhost:8001
export GEMINI_API_KEY=your-key
make start ARGS="--file_in=backend/data_in/new_chat.txt"
```

**Method 2: SSH and Process on Server**
```bash
# Copy chat file to server
fly ssh sftp shell
put backend/data_in/new_chat.txt /tmp/new_chat.txt
exit

# SSH into server
fly ssh console
# Inside container:
cd /app
uv run python -m backend.process_whatsapp_messages --file_in=/tmp/new_chat.txt
exit
```

### Monitoring

**Backend metrics:**
```bash
fly dashboard
fly status
fly logs --follow
```

**Frontend metrics:**
- Vercel Dashboard → Analytics
- Check error rates and performance

### Backups

**Backup SQLite database:**
```bash
# Download database from Fly.io
fly ssh sftp shell
get /data/backend_cache.db ./backup_$(date +%Y%m%d).db
exit
```

**Schedule regular backups:**
Consider setting up a cron job or GitHub Action to backup weekly.

### Scaling

**Backend:**
```bash
# Scale up memory if needed
fly scale memory 512

# Scale up CPU
fly scale vm shared-cpu-2x

# Add more instances
fly scale count 2
```

**Frontend:**
- Vercel automatically scales

### Costs

**Fly.io Free Tier:**
- 3 shared-cpu-1x VMs (256MB RAM)
- 3GB persistent storage
- 160GB outbound transfer/month

**Expected usage for personal project:** Within free tier

**Vercel Free Tier:**
- 100GB bandwidth
- Unlimited deployments
- Automatic HTTPS

**Expected usage:** Within free tier

---

## Troubleshooting

### CORS Errors

**Symptom:** Browser console shows "CORS policy" errors

**Fix:**
```bash
# Verify CORS origins
fly secrets list

# Update if needed
fly secrets set ALLOWED_ORIGINS="https://your-app.vercel.app,http://localhost:3000"

# Restart
fly apps restart
```

### Database Connection Errors

**Symptom:** Backend returns 500 errors, logs show database errors

**Fix:**
```bash
# SSH into container
fly ssh console

# Check if database exists
ls -la /data/

# Check permissions
touch /data/test.txt

# If permission denied, volume may not be mounted correctly
exit

# Recreate volume
fly volumes list
fly volumes destroy vol_xxxxx
fly volumes create whatsapp_memories_data --size 1
fly deploy
```

### Backend Not Starting

**Symptom:** `fly status` shows unhealthy app

**Fix:**
```bash
# Check logs for errors
fly logs

# Common issues:
# 1. Port mismatch - ensure Dockerfile exposes 8000
# 2. Missing dependencies - rebuild: fly deploy --no-cache
# 3. Environment variables - verify: fly secrets list
```

### Frontend Can't Reach Backend

**Symptom:** Frontend loads but shows no data

**Fix:**
1. Check browser console for errors
2. Verify `NEXT_PUBLIC_API_URL` in Vercel: Settings → Environment Variables
3. Test backend directly: `curl https://your-app.fly.dev/health`
4. Redeploy frontend: Vercel dashboard → Deployments → Redeploy

---

## Rollback Plan

### Rollback Backend

```bash
# List deployments
fly releases

# Rollback to previous version
fly releases rollback
```

### Rollback Frontend

1. Vercel Dashboard → Deployments
2. Find previous working deployment
3. Click "..." → "Promote to Production"

---

## Future Improvements

### Phase 9: CI/CD (Optional)

**GitHub Actions for automated deployment:**

**File:** `.github/workflows/deploy.yml`

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
```

### Phase 10: Monitoring (Optional)

- Set up Sentry for error tracking
- Add Plausible/Umami for privacy-friendly analytics
- Configure Fly.io metrics alerts

### Phase 11: Database Backups (Recommended)

**Automated backup script:**

```bash
#!/bin/bash
# backup_db.sh
DATE=$(date +%Y%m%d_%H%M%S)
fly ssh sftp shell -C "get /data/backend_cache.db ./backups/backup_$DATE.db"
# Optional: Upload to S3/Backblaze
```

**Schedule with cron:**
```bash
# Run weekly backups
0 0 * * 0 /path/to/backup_db.sh
```

---

## Security Checklist

- [ ] Environment variables stored securely (not in code)
- [ ] CORS configured with specific origins (not wildcard)
- [ ] HTTPS enforced on both frontend and backend
- [ ] Gemini API key not exposed to frontend
- [ ] Regular backups scheduled
- [ ] Fly.io volume encrypted (default)
- [ ] No sensitive data in git history
- [ ] `.env` files in `.gitignore`

---

## Success Criteria

Deployment is successful when:

- [ ] Frontend loads at Vercel URL
- [ ] Backend health check returns 200
- [ ] Exchanges list loads in frontend
- [ ] Individual exchanges can be viewed
- [ ] No CORS errors in browser console
- [ ] Mobile view works correctly
- [ ] Database persists between backend restarts
- [ ] New data can be processed and appears in production

---

## Resources

- **Fly.io Docs:** https://fly.io/docs/
- **Vercel Docs:** https://vercel.com/docs
- **FastAPI CORS:** https://fastapi.tiangolo.com/tutorial/cors/
- **Next.js Env Variables:** https://nextjs.org/docs/app/building-your-application/configuring/environment-variables

---

## Timeline Estimate

| Phase | Task | Time |
|-------|------|------|
| 1 | Prepare Backend | 10 min |
| 2 | Deploy to Fly.io | 10 min |
| 3 | Update Frontend Config | 5 min |
| 4 | Deploy to Vercel | 5 min |
| 5 | Configure CORS | 2 min |
| 6 | Populate Database | 10 min |
| 7 | Verify Deployment | 5 min |
| **Total** | | **~45 min** |

---

## Next Steps

1. Review this plan thoroughly
2. Create accounts if needed (Vercel, Fly.io)
3. Start with Phase 1: Prepare Backend
4. Work through phases sequentially
5. Test after each phase
6. Document any issues encountered

**Ready to begin?** Start with Phase 1, Step 1.1!
