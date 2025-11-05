# Troubleshooting Guide

> Quick solutions to common issues with WhatsApp Memories

## Quick Diagnosis Table

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| Frontend loads but no data | Database empty or not uploaded | Upload database to Fly.io |
| CORS error in browser console | Vercel URL not in ALLOWED_ORIGINS | Update Fly.io secrets |
| Backend returns 500 errors | Database issue or missing secrets | Check logs: `fly logs` |
| Slow API responses | Cold start after inactivity | Wait 10-15 seconds, retry |
| "fly" command not found | CLI not installed | Install: `brew install flyctl` |
| Frontend shows old data | Cache not cleared after update | Hard refresh: Ctrl+Shift+R |
| Can't SSH into Fly.io | Auth issue | Run: `fly auth login` |
| Merge button grayed out | Different source files selected | Select same-source exchanges only |
| Mobile view broken | CSS or viewport issue | Check browser console, clear cache |

---

## Frontend Issues

### 1. Frontend Loads But Shows No Data

**Symptoms:**
- App loads successfully at https://whatsapp-memories.vercel.app
- Sidebar is empty
- No error messages in UI
- Browser console shows no errors

**Diagnosis:**
```bash
# Test backend API directly
curl https://whatsapp-memories-api.fly.dev/api/exchanges

# If returns empty items array, database is empty
```

**Solutions:**

**Option A: Database Never Uploaded**
```bash
# Upload your local database
fly ssh sftp shell
put backend_cache.db /data/backend_cache.db
exit
fly apps restart
```

**Option B: Database Was Cleared**
```bash
# Re-process your data
make start ARGS="--file_in=backend/data_in/your_chat.txt"

# Then upload (Option A above)
```

**Option C: Wrong API URL**
```bash
# Verify frontend environment variable
cd frontend
vercel env ls

# Should show: NEXT_PUBLIC_API_URL = https://whatsapp-memories-api.fly.dev
# If missing or wrong:
vercel env add NEXT_PUBLIC_API_URL production
# Enter correct URL, then redeploy:
vercel --prod
```

---

### 2. CORS Error in Browser Console

**Symptoms:**
- Browser console shows: `Access to fetch at 'https://whatsapp-memories-api.fly.dev/api/exchanges' from origin 'https://whatsapp-memories.vercel.app' has been blocked by CORS policy`
- Frontend makes requests but they fail
- Network tab shows (failed) requests

**Diagnosis:**
```bash
# Check current CORS settings
fly secrets list | grep ALLOWED_ORIGINS
```

**Solution:**
```bash
# Update CORS to include your Vercel domain
fly secrets set ALLOWED_ORIGINS="https://whatsapp-memories.vercel.app,http://localhost:3000"

# If you have custom domain:
fly secrets set ALLOWED_ORIGINS="https://whatsapp-memories.vercel.app,https://your-domain.com,http://localhost:3000"

# Wait 30 seconds for restart, then test
curl -I https://whatsapp-memories-api.fly.dev/health
```

**Verify Fix:**
- Refresh frontend
- Check browser console - CORS error should be gone
- Data should load

---

### 3. Frontend Shows Stale Data

**Symptoms:**
- Made changes (delete/merge) but old data still shows
- Backend API returns updated data
- Frontend doesn't reflect changes

**Solutions:**

**Option A: Hard Refresh**
- Chrome/Firefox: `Ctrl + Shift + R` (Windows/Linux) or `Cmd + Shift + R` (Mac)
- Safari: `Cmd + Option + R`

**Option B: Clear Cache**
```bash
# In browser DevTools (F12):
# 1. Right-click refresh button
# 2. Select "Empty Cache and Hard Reload"
```

**Option C: Redeploy Frontend**
```bash
cd frontend
vercel --prod
```

---

### 4. Mobile View Not Working

**Symptoms:**
- Horizontal scroll on mobile
- UI elements overlap
- Both sidebar and chat visible at once

**Solutions:**

**Check Viewport:**
- Browser width should be < 768px for mobile view
- Try actual mobile device vs. browser DevTools

**Clear Browser Cache:**
- On mobile browser, go to Settings → Clear cache
- Reload page

**Check for JavaScript Errors:**
- On desktop, open DevTools mobile emulator
- Check console for errors
- Look for hydration warnings

**Code Fix (If Issue Persists):**
Check `frontend/app/page.tsx` for view state logic around line 424-518.

---

## Backend Issues

### 5. Backend Not Starting

**Symptoms:**
- `fly status` shows app as "stopped" or "unhealthy"
- Health check returns timeout
- Logs show startup errors

**Diagnosis:**
```bash
# Check app status
fly status

# Check recent logs for errors
fly logs

# Common error patterns to look for:
# - "ModuleNotFoundError" → Dependency issue
# - "PRAGMA foreign_keys" → Database issue
# - "Port already in use" → Configuration issue
# - "Out of memory" → Resource issue
```

**Solutions:**

**Solution A: Missing Environment Variables**
```bash
# Verify all secrets are set
fly secrets list

# Should see:
# - GEMINI_API_KEY
# - ALLOWED_ORIGINS

# If missing:
fly secrets set GEMINI_API_KEY="your-key"
fly secrets set ALLOWED_ORIGINS="https://whatsapp-memories.vercel.app,http://localhost:3000"
```

**Solution B: Volume Not Mounted**
```bash
# Check volume exists
fly volumes list

# Should show: whatsapp_memories_data

# If missing:
fly volumes create whatsapp_memories_data --size 1 --region fra

# Then redeploy:
fly deploy
```

**Solution C: Rebuild from Scratch**
```bash
# Force rebuild without cache
fly deploy --no-cache
```

**Solution D: Scale Up Resources**
```bash
# If OOM (Out of Memory) errors
fly scale memory 512

# Then restart
fly apps restart
```

---

### 6. Backend Returns 500 Errors

**Symptoms:**
- Frontend shows error or empty data
- Backend logs show Python exceptions
- `/health` endpoint returns 500

**Diagnosis:**
```bash
# Check logs for Python traceback
fly logs | grep -A 20 "Traceback\|Error\|Exception"
```

**Common Causes & Solutions:**

**Database Corruption:**
```bash
# SSH and check database
fly ssh console
sqlite3 /data/backend_cache.db "PRAGMA integrity_check;"

# If corrupted, restore from backup or reprocess data
exit
```

**Database Locked:**
```bash
# Restart usually fixes
fly apps restart
```

**Missing Database File:**
```bash
# Check if database exists
fly ssh console
ls -la /data/backend_cache.db

# If missing, upload it
exit
fly ssh sftp shell
put backend_cache.db /data/backend_cache.db
exit
fly apps restart
```

---

### 7. Slow API Response Times

**Symptoms:**
- First request takes 10-20 seconds
- Subsequent requests are fast
- Health check times out initially

**Explanation:**
- Fly.io auto-stops machines after 5 minutes of inactivity
- First request wakes machine up ("cold start")
- This is **normal behavior** on free tier

**Solutions:**

**Option A: Accept Cold Starts (Recommended for Free Tier)**
- No action needed
- Machines wake in 10-15 seconds
- Saves on resource usage

**Option B: Keep Minimum Machines Running**
Edit `fly.toml`:
```toml
[http_service]
  min_machines_running = 1  # Changed from 0
```

Then redeploy:
```bash
fly deploy
```

**Cost Impact:** May push you over free tier limits with sustained traffic.

---

### 8. Backend Listening Address Warning

**Symptoms:**
After `fly deploy` or secret updates:
```
WARNING The app is not listening on the expected address
You can fix this by configuring your app to listen on:
  - 0.0.0.0:8000
```

**Explanation:**
- This is a **false positive** if app works correctly
- FastAPI is correctly configured to listen on 0.0.0.0:8000
- Fly.io proxy detection can be flaky

**Verify It's Actually Working:**
```bash
curl https://whatsapp-memories-api.fly.dev/health
# If returns {"status":"healthy"}, ignore the warning
```

**If Health Check Fails:**
Check `Dockerfile` has correct CMD:
```dockerfile
CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Database Issues

### 9. Empty Database After Upload

**Symptoms:**
- Uploaded `backend_cache.db` but API returns empty
- File size shows correctly on volume
- No errors in logs

**Diagnosis:**
```bash
# SSH and check database content
fly ssh console
sqlite3 /data/backend_cache.db "SELECT COUNT(*) FROM exchanges;"

# Should return number > 0
```

**Solutions:**

**Database File Didn't Upload Properly:**
```bash
# Remove and re-upload
fly ssh console
rm /data/backend_cache.db
exit

fly ssh sftp shell
put backend_cache.db /data/backend_cache.db
exit

fly apps restart
```

**Uploaded Wrong Database File:**
```bash
# Check local database first
sqlite3 backend_cache.db "SELECT COUNT(*) FROM exchanges;"

# If 0, you need to process data first:
make start ARGS="--file_in=backend/data_in/your_chat.txt"

# Then upload the newly created backend_cache.db
```

---

### 10. Database Corruption

**Symptoms:**
- Backend crashes on queries
- Logs show SQLite errors
- `PRAGMA integrity_check` fails

**Diagnosis:**
```bash
fly ssh console
sqlite3 /data/backend_cache.db "PRAGMA integrity_check;"
# Should return: ok
# If returns errors, database is corrupted
exit
```

**Solutions:**

**Restore from Backup:**
```bash
# If you have backups
fly ssh console
rm /data/backend_cache.db
exit

fly ssh sftp shell
put backups/backup_YYYYMMDD.db /data/backend_cache.db
exit

fly apps restart
```

**Rebuild from Source Data:**
```bash
# Reprocess WhatsApp exports
make start ARGS="--file_in=backend/data_in/your_chat.txt"

# Upload fresh database
fly ssh sftp shell
put backend_cache.db /data/backend_cache.db
exit

fly apps restart
```

---

## Development Issues

### 11. Local Development: "Connection Refused"

**Symptoms:**
- Frontend can't connect to local backend
- Error: `fetch failed` or `ECONNREFUSED`
- Running `make run-backend` but frontend doesn't connect

**Solutions:**

**Verify Backend Running:**
```bash
# Check if process is running
lsof -i :8000

# Should show Python/uvicorn process
```

**Check Backend URL:**
```bash
# In frontend, check API route files
# Should have: const FASTAPI_BASE_URL = ... "http://localhost:8000"

# Test directly:
curl http://localhost:8000/health
```

**Restart Backend:**
```bash
# Stop current backend (Ctrl+C)
# Then restart:
make run-backend
```

---

### 12. "fly" Command Not Found

**Symptoms:**
```bash
$ fly status
zsh: command not found: fly
```

**Solutions:**

**Install Fly.io CLI:**

**macOS:**
```bash
brew install flyctl
```

**Linux/WSL:**
```bash
curl -L https://fly.io/install.sh | sh
```

**Windows:**
```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

**Verify Installation:**
```bash
fly version
# Should show version number
```

**Login:**
```bash
fly auth login
```

---

### 13. SSH/SFTP Authentication Failed

**Symptoms:**
```
Error: ssh: handshake failed: ssh: unable to authenticate
```

**Solutions:**

**Re-authenticate:**
```bash
fly auth login
```

**Issue New SSH Certificate:**
```bash
# This usually happens automatically, but force if needed:
fly ssh issue --agent
```

**Check Organization Access:**
```bash
fly orgs show personal
# Verify you have access to the org
```

**Try Alternative SSH Method:**
```bash
# Instead of sftp shell -C "command"
# Use interactive session:
fly ssh sftp shell
# Then manually enter commands
```

---

## Deployment Issues

### 14. Vercel Deployment Fails

**Symptoms:**
- `vercel --prod` returns errors
- Build fails on Vercel
- Deployment stuck in "Building"

**Solutions:**

**Check Build Logs:**
- Vercel Dashboard → Deployments → Failed deployment → View logs

**Common Build Errors:**

**Missing Dependencies:**
```bash
cd frontend
pnpm install
# Commit package-lock.json
git add package-lock.json
git commit -m "Update dependencies"
git push
```

**Environment Variable Missing:**
- Vercel Dashboard → Settings → Environment Variables
- Add: `NEXT_PUBLIC_API_URL` = `https://whatsapp-memories-api.fly.dev`
- Redeploy

**Wrong Root Directory:**
- Vercel Dashboard → Settings → General
- Root Directory should be: `frontend`

---

### 15. Fly.io Deployment Fails

**Symptoms:**
- `fly deploy` fails
- Error during build or deployment
- App won't start after deployment

**Solutions:**

**Check Deployment Logs:**
```bash
fly logs
```

**Common Deployment Errors:**

**Docker Build Fails:**
```bash
# Rebuild without cache
fly deploy --no-cache
```

**Volume Mount Fails:**
```bash
# Verify volume exists
fly volumes list

# Check fly.toml has correct mount config:
[mounts]
  source = "whatsapp_memories_data"
  destination = "/data"
```

**Out of Resources (Free Tier):**
```bash
# Check current usage
fly status

# May need to scale down or upgrade plan
```

---

## API Issues

### 16. 307 Redirect Loops

**Symptoms:**
- API returns 307 redirect
- `curl` times out
- Frontend makes repeated requests

**Explanation:**
- FastAPI redirects `/api/exchanges` → `/api/exchanges/`
- Usually harmless, `curl -L` follows redirects

**Solution:**
- Always use trailing slash in API calls
- Or use `curl -L` to follow redirects automatically

---

### 17. Rate Limiting or Quota Errors

**Symptoms:**
- Gemini API returns 429 or quota errors
- LLM processing fails
- Logs show "quota exceeded"

**Solutions:**

**Check API Quota:**
- Go to https://aistudio.google.com/
- Check your quota/usage

**Wait and Retry:**
- Gemini has generous free tier
- Wait for quota reset (usually daily)

**Upgrade API Tier:**
- Consider paid tier if processing large amounts

---

## Data Issues

### 18. Merge Doesn't Work

**Symptoms:**
- Merge button grayed out
- Can't select certain exchanges
- Merge fails with error

**Diagnosis:**
- Check if selected exchanges have same `sourceFile`
- Only same-source exchanges can merge

**Solution:**
- Select only exchanges from same WhatsApp export
- Exchanges from different files are incompatible
- This is by design to preserve context

---

### 19. Deleted Messages Still Appear

**Symptoms:**
- Deleted messages still visible after refresh
- Frontend shows old data

**Solution:**
```bash
# Hard refresh browser
Ctrl + Shift + R

# Or clear browser cache and reload
```

---

## Getting More Help

### Collect Diagnostic Information

Before asking for help, gather:

**Backend Info:**
```bash
fly status
fly logs > logs.txt
fly secrets list
fly volumes list
```

**Frontend Info:**
```bash
cd frontend
vercel ls
vercel env ls
# Browser console logs (F12 → Console tab)
```

**Database Info:**
```bash
fly ssh console
ls -lh /data/
sqlite3 /data/backend_cache.db "PRAGMA integrity_check;"
sqlite3 /data/backend_cache.db "SELECT COUNT(*) FROM exchanges;"
exit
```

### Where to Get Help

1. **Check This Guide First** - Most issues covered here
2. **Review Logs** - Errors usually show in `fly logs` or browser console
3. **Consult Other Docs:**
   - [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment procedures
   - [OPERATIONS.md](OPERATIONS.md) - Day-to-day maintenance
   - [USER_GUIDE.md](USER_GUIDE.md) - User-facing features
4. **Platform Status:**
   - https://status.fly.io/
   - https://vercel-status.com/
5. **Open GitHub Issue** - Include diagnostic info above

---

## Preventive Measures

### Regular Health Checks

```bash
# Run weekly
fly status
fly volumes list
curl https://whatsapp-memories-api.fly.dev/health
```

### Backup Schedule

```bash
# Backup database weekly
fly ssh sftp shell
get /data/backend_cache.db ./backups/backup_$(date +%Y%m%d).db
exit
```

### Monitor Logs

```bash
# Watch for recurring errors
fly logs | grep -i error
```

### Keep Dependencies Updated

```bash
# Backend
uv sync

# Frontend
cd frontend
pnpm update
```

---

**Still stuck?** Open an issue on GitHub with:
- Symptoms and when they started
- Steps to reproduce
- Logs and error messages
- What you've already tried
