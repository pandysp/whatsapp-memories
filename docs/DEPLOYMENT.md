# Production Deployment Guide

> Deploy WhatsApp Memories to production using Vercel (frontend) + Fly.io (backend)

## Overview

This guide covers deploying the WhatsApp Memories application to production using a hybrid architecture:

- **Frontend**: Vercel (Next.js hosting with global CDN)
- **Backend**: Fly.io (FastAPI + SQLite with persistent storage)

**Why this architecture?**
- KISS principle - minimal code changes from local development
- Keep SQLite unchanged (no database migration needed)
- Each platform does what it's best at
- Free tier available on both platforms
- Privacy-focused: your data stays on infrastructure you control

**Estimated deployment time:** ~30-45 minutes

---

## Prerequisites

### Required Accounts

- **GitHub account** - For version control and Vercel integration
- **Vercel account** - [Sign up](https://vercel.com/signup) (free tier)
- **Fly.io account** - [Sign up](https://fly.io/signup) (free tier)
  - Note: Fly.io requires credit card for verification, but won't charge within free tier limits

### Required CLI Tools

```bash
# Install Fly.io CLI (macOS)
brew install flyctl

# Or using curl
curl -L https://fly.io/install.sh | sh

# Verify installation
fly version

# Optional: Install Vercel CLI (can use web UI instead)
npm install -g vercel
```

### Environment Variables

You'll need:
- `GEMINI_API_KEY` - Your Gemini API key
- `ALLOWED_ORIGINS` - CORS origins (will be set during deployment)
- `NEXT_PUBLIC_API_URL` - Backend URL for frontend

---

## Phase 1: Deploy Backend to Fly.io

### 1.1 Login to Fly.io

```bash
fly auth login
```

This opens a browser window for authentication.

### 1.2 Launch Application

```bash
# From project root
fly launch --no-deploy
```

**Answer the prompts:**
- App name: Choose unique name (e.g., `whatsapp-memories-yourname`)
- Region: Choose closest to you (`fra` for Europe, `iad` for US East)
- Postgres: **No**
- Redis: **No**
- Deploy now: **No** (we need to create volume first)

### 1.3 Create Persistent Volume

```bash
# Create 1GB volume for SQLite database
# Replace YOUR_REGION with your chosen region (e.g., fra, iad)
fly volumes create whatsapp_memories_data --size 1 --region YOUR_REGION

# Verify volume creation
fly volumes list
```

### 1.4 Set Environment Variables

```bash
# Set Gemini API key (replace with your actual key)
fly secrets set GEMINI_API_KEY="your-actual-gemini-api-key"

# Set CORS origins (will update after Vercel deployment)
fly secrets set ALLOWED_ORIGINS="http://localhost:3000"

# Verify secrets are set
fly secrets list
```

### 1.5 Deploy Backend

```bash
fly deploy
```

**What happens:**
- Builds Docker image from your Dockerfile
- Pushes to Fly.io registry
- Creates VM instance with persistent volume mounted at `/data`
- Starts FastAPI application

**Monitor deployment:**
```bash
fly status
fly logs
```

### 1.6 Test Backend

```bash
# Get your app URL
fly info

# Test health endpoint
curl https://YOUR_APP_NAME.fly.dev/health
```

Expected response: `{"status":"healthy"}`

**Note your backend URL** - you'll need it for frontend configuration: `https://YOUR_APP_NAME.fly.dev`

---

## Phase 2: Deploy Frontend to Vercel

### 2.1 Push Code to GitHub

```bash
# Ensure all changes are committed
git status
git add .
git commit -m "Deploy to production"
git push origin main
```

### 2.2 Deploy via Vercel Web UI

1. Go to [vercel.com/new](https://vercel.com/new)
2. Click **"Import Git Repository"**
3. Select your `whatsapp-memories` repository
4. **Configure project settings:**
   - Framework Preset: **Next.js** (auto-detected)
   - Root Directory: **`frontend`** ← Important!
   - Build Command: `npm run build` (default)
   - Output Directory: `.next` (default)

5. **Set environment variable:**
   - Click **"Environment Variables"**
   - Key: `NEXT_PUBLIC_API_URL`
   - Value: `https://YOUR_FLY_APP_NAME.fly.dev`
   - Environment: All (Production, Preview, Development)

6. Click **"Deploy"**

### 2.3 Alternative: Deploy via CLI

```bash
cd frontend
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name? whatsapp-memories
# - Directory? ./
# - Override settings? No

# Set environment variable
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://YOUR_FLY_APP_NAME.fly.dev

# Deploy to production
vercel --prod
```

### 2.4 Note Your URLs

After deployment completes, you'll have:
- **Frontend URL**: `https://whatsapp-memories.vercel.app` (or custom domain)
- **Backend URL**: `https://YOUR_APP_NAME.fly.dev`

---

## Phase 3: Update CORS Configuration

Now that your frontend is deployed, update the backend CORS settings:

```bash
# Update CORS to allow your Vercel frontend
fly secrets set ALLOWED_ORIGINS="https://your-app.vercel.app,http://localhost:3000"
```

Replace `your-app.vercel.app` with your actual Vercel URL.

The backend will automatically restart after setting secrets (~30 seconds).

**Verify restart:**
```bash
fly status
```

---

## Phase 4: Populate Production Database

You have three options for getting data into production:

### Option A: Process Locally, Copy Database (Recommended)

```bash
# 1. Process your data locally
make start ARGS="--file_in=backend/data_in/your_chat.txt --log_level=INFO"

# 2. Copy database to Fly.io
fly ssh sftp shell
# In SFTP prompt:
put backend_cache.db /data/backend_cache.db
exit
```

### Option B: Process via Fly.io Proxy

```bash
# 1. Create proxy to Fly.io (in one terminal)
fly proxy 8001:8000

# 2. Process data through proxy (in another terminal)
export FASTAPI_BASE_URL=http://localhost:8001
export GEMINI_API_KEY=your-key
make start ARGS="--file_in=backend/data_in/your_chat.txt --log_level=INFO"
```

### Option C: Process on Fly.io Server

```bash
# 1. Copy chat file to server
fly ssh sftp shell
put backend/data_in/your_chat.txt /tmp/your_chat.txt
exit

# 2. SSH into server and process
fly ssh console
cd /app
uv run python -m backend.process_whatsapp_messages --file_in=/tmp/your_chat.txt
exit
```

### Verify Data

```bash
# Test API endpoint
curl https://YOUR_APP_NAME.fly.dev/api/exchanges?page=1&page_size=20

# Or visit frontend
open https://your-app.vercel.app
```

---

## Phase 5: Verification Checklist

Test your production deployment:

### Frontend Checks
- [ ] Visit your Vercel URL
- [ ] Sidebar loads with exchanges
- [ ] Click exchange to view messages
- [ ] Mobile view works (resize browser)
- [ ] No CORS errors in browser console (F12 → Console)

### Backend Checks
```bash
# Health check
curl https://YOUR_APP_NAME.fly.dev/health

# List exchanges
curl https://YOUR_APP_NAME.fly.dev/api/exchanges

# Get specific exchange
curl https://YOUR_APP_NAME.fly.dev/api/exchanges/1
```

### Monitoring
```bash
# Backend logs
fly logs --follow

# Frontend logs
# Visit: Vercel Dashboard → Your Project → Deployments → Latest → Logs
```

---

## Maintenance & Operations

### Adding New Memories

**Recommended: Process Locally + Copy Database**

```bash
# 1. Add new chat export to backend/data_in/
# 2. Process it locally
make start ARGS="--file_in=backend/data_in/new_chat.txt"

# 3. Copy updated database
fly ssh sftp shell
put backend_cache.db /data/backend_cache.db
exit
```

### Backups

**Download database regularly:**

```bash
# Create backup
fly ssh sftp shell
get /data/backend_cache.db ./backup_$(date +%Y%m%d).db
exit
```

**Automate with cron:**

```bash
# Create backup script
cat > backup_db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
fly ssh sftp shell -C "get /data/backend_cache.db ./backups/backup_$DATE.db"
EOF

chmod +x backup_db.sh

# Add to crontab (weekly backups)
crontab -e
# Add: 0 0 * * 0 /path/to/backup_db.sh
```

### Scaling

**Backend (Fly.io):**

```bash
# Increase memory if needed
fly scale memory 512

# Increase CPU
fly scale vm shared-cpu-2x

# Add more instances (for high traffic)
fly scale count 2
```

**Frontend (Vercel):**
- Scales automatically
- Check Analytics in Vercel Dashboard

### Monitoring

```bash
# Fly.io Dashboard
fly dashboard

# View metrics
fly status
fly logs --follow

# SSH into container
fly ssh console
```

---

## Costs & Free Tier Limits

### Fly.io Free Tier

- 3 shared-cpu-1x VMs (256MB RAM each)
- 3GB persistent storage
- 160GB outbound transfer/month

**Expected usage for personal project:** Well within free tier

### Vercel Free Tier

- 100GB bandwidth/month
- Unlimited deployments
- Automatic HTTPS

**Expected usage:** Within free tier for personal use

---

## Troubleshooting

### CORS Errors in Browser

**Symptom:** Console shows "CORS policy" errors

**Fix:**
```bash
# Verify CORS origins
fly secrets list

# Update if needed (include both production and localhost)
fly secrets set ALLOWED_ORIGINS="https://your-app.vercel.app,http://localhost:3000"

# Restart app
fly apps restart
```

### Database Not Persisting

**Symptom:** Data disappears after restart

**Fix:**
```bash
# Verify volume is mounted
fly ssh console
ls -la /data/
exit

# Check logs for mount errors
fly logs | grep -i volume

# If volume not mounted, recreate
fly volumes list
fly volumes destroy vol_xxxxx  # Replace with actual ID
fly volumes create whatsapp_memories_data --size 1 --region YOUR_REGION
fly deploy
```

### Backend Not Starting

**Symptom:** `fly status` shows unhealthy app

**Fix:**
```bash
# Check logs for errors
fly logs

# Common issues:
# 1. Missing env vars - verify: fly secrets list
# 2. Port mismatch - check Dockerfile EXPOSE 8000
# 3. Dependency issues - rebuild: fly deploy --no-cache
```

### Frontend Can't Reach Backend

**Symptom:** Frontend loads but shows no data

**Fix:**
1. Check browser console (F12) for errors
2. Verify env var in Vercel: Settings → Environment Variables
3. Test backend directly: `curl https://YOUR_APP.fly.dev/health`
4. If env var changed, redeploy: Vercel Dashboard → Redeploy

---

## Rollback Procedures

### Rollback Backend (Fly.io)

```bash
# List recent deployments
fly releases

# Rollback to previous version
fly releases rollback
```

### Rollback Frontend (Vercel)

1. Go to Vercel Dashboard → Deployments
2. Find previous working deployment
3. Click **"..."** menu → **"Promote to Production"**

---

## Custom Domain (Optional)

### Add Domain to Vercel

1. Vercel Dashboard → Project → Settings → Domains
2. Add your domain (e.g., `memories.yourdomain.com`)
3. Follow DNS configuration instructions
4. Update CORS on backend with new domain

### Add Domain to Fly.io

```bash
# Add custom domain for API
fly certs add api.yourdomain.com

# Check certificate status
fly certs show api.yourdomain.com
```

Update DNS records as shown in output.

---

## Security Checklist

Before going live:

- [ ] Environment variables stored securely (not in code)
- [ ] CORS configured with specific origins (not `*` wildcard)
- [ ] HTTPS enforced on both frontend and backend
- [ ] Gemini API key not exposed to frontend
- [ ] Regular backups scheduled
- [ ] Fly.io volume encrypted (default)
- [ ] No sensitive data in git history
- [ ] `.env` files in `.gitignore`

---

## Additional Resources

- **Fly.io Documentation**: https://fly.io/docs/
- **Vercel Documentation**: https://vercel.com/docs
- **FastAPI CORS**: https://fastapi.tiangolo.com/tutorial/cors/
- **Next.js Environment Variables**: https://nextjs.org/docs/app/building-your-application/configuring/environment-variables

---

## Next Steps After Deployment

1. Test all functionality in production
2. Set up automated backups
3. Configure monitoring/alerts (optional)
4. Add custom domain (optional)
5. Share with intended audience

**Questions?** Open an issue on GitHub or refer to other documentation in `docs/`.
