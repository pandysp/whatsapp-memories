# Operations Guide

> Day-to-day maintenance and operations for production WhatsApp Memories deployment

## Production Topology

**Architecture:**
- **Frontend**: Next.js on Vercel (https://whatsapp-memories.vercel.app)
- **Backend**: FastAPI on Fly.io (https://whatsapp-memories-api.fly.dev)
- **Database**: SQLite on Fly.io persistent volume (mounted at `/data`)
- **Region**: Frankfurt (fra) for backend
- **CDN**: Vercel Edge Network for frontend

**Resources:**
- Fly.io: 1x shared-cpu-1x VM (256MB RAM)
- Volume: 1GB persistent storage
- Free tier limits: Well within bounds for personal use

---

## Routine Tasks

### Check Application Health

**Backend Status:**
```bash
# Quick health check
curl https://whatsapp-memories-api.fly.dev/health

# Detailed status
fly status

# Check machine metrics
fly dashboard
```

**Frontend Status:**
- Visit: https://whatsapp-memories.vercel.app
- Or check Vercel Dashboard → Your Project → Deployments

### View Logs

**Backend Logs (Fly.io):**
```bash
# Stream live logs
fly logs

# No-tail mode (snapshot)
fly logs -n

# Filter by machine
fly logs --machine MACHINE_ID

# JSON format
fly logs -j
```

**Frontend Logs (Vercel):**
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project
3. Click **Deployments** → Latest deployment
4. Click **View Function Logs**

### Restart Services

**Restart Backend:**
```bash
fly apps restart

# Verify restart
fly status
```

**Redeploy Frontend:**
```bash
cd frontend
vercel --prod

# Or via Vercel Dashboard → Deployments → Latest → ... → Redeploy
```

---

## Database Operations

### Backup Database

**Manual Backup:**
```bash
# Download current production database
fly ssh sftp shell
# In SFTP:
get /data/backend_cache.db ./backups/backup_$(date +%Y%m%d_%H%M%S).db
exit
```

**Automated Backup Script:**

Create `scripts/backup_db.sh`:
```bash
#!/bin/bash
set -e

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.db"

mkdir -p "$BACKUP_DIR"

echo "Starting backup at $DATE..."
fly ssh sftp shell -C "get /data/backend_cache.db $BACKUP_FILE"
echo "Backup saved to: $BACKUP_FILE"

# Optional: Keep only last 7 backups
ls -t "$BACKUP_DIR"/backup_*.db | tail -n +8 | xargs -r rm
echo "Cleanup complete. Kept 7 most recent backups."
```

**Schedule with cron:**
```bash
# Edit crontab
crontab -e

# Add weekly backup (Sunday at 2 AM)
0 2 * * 0 /path/to/whatsapp-memories/scripts/backup_db.sh
```

### Restore Database

**From Backup:**
```bash
# 1. SSH into machine and remove current DB
fly ssh console
rm /data/backend_cache.db
exit

# 2. Upload backup via SFTP
fly ssh sftp shell
put backups/backup_YYYYMMDD_HHMMSS.db /data/backend_cache.db
exit

# 3. Restart app
fly apps restart

# 4. Verify data is restored
curl https://whatsapp-memories-api.fly.dev/api/exchanges?page=1&page_size=5
```

### Check Database Size

```bash
# SSH into container
fly ssh console

# Check database size
ls -lh /data/backend_cache.db

# Check volume usage
df -h /data

# Exit
exit
```

---

## Adding New Data in Production

### Option A: Process Locally, Upload Database (Recommended)

**Best for**: Adding new chat exports after initial deployment

```bash
# 1. Process new data locally
export GEMINI_API_KEY="your-key"
make start ARGS="--file_in=backend/data_in/new_chat.txt --log_level=INFO"

# 2. Backup current production database first (see above)

# 3. Remove old production database
fly ssh console
rm /data/backend_cache.db
exit

# 4. Upload new database
fly ssh sftp shell
put backend_cache.db /data/backend_cache.db
exit

# 5. Restart backend
fly apps restart

# 6. Verify new data appears
curl https://whatsapp-memories-api.fly.dev/api/exchanges
```

**Important Notes:**
- Always backup production DB before replacing it
- Processing locally is faster and cheaper (no fly.io CPU time)
- Database replacement causes ~30 second downtime during restart

### Option B: Process via Proxy (For Small Updates)

**Best for**: Adding just a few new exchanges

```bash
# 1. Start proxy to production
fly proxy 8001:8000 &

# 2. Process through proxy
export FASTAPI_BASE_URL=http://localhost:8001
export GEMINI_API_KEY="your-key"
make start ARGS="--file_in=backend/data_in/new_chat.txt --log_level=INFO"

# 3. Stop proxy
killall fly
```

**Caution**: This processes data directly on the live database. No atomic rollback.

### Option C: Process on Fly.io Server

**Best for**: Emergency situations only (uses Fly.io CPU quota)

```bash
# 1. Upload chat file to temporary location
fly ssh sftp shell
put backend/data_in/new_chat.txt /tmp/new_chat.txt
exit

# 2. SSH into machine and process
fly ssh console
cd /app
uv run python -m backend.process_whatsapp_messages --file_in=/tmp/new_chat.txt --log_level=INFO
exit

# 3. Verify
curl https://whatsapp-memories-api.fly.dev/api/exchanges
```

---

## Environment Variables

### View Current Variables

**Backend (Fly.io):**
```bash
fly secrets list
```

**Frontend (Vercel):**
```bash
cd frontend
vercel env ls

# Or via Vercel Dashboard → Settings → Environment Variables
```

### Update Environment Variables

**Update Backend CORS:**
```bash
# Add new allowed origin
fly secrets set ALLOWED_ORIGINS="https://whatsapp-memories.vercel.app,https://custom-domain.com,http://localhost:3000"

# App automatically restarts after secret change
```

**Update Gemini API Key:**
```bash
fly secrets set GEMINI_API_KEY="new-api-key"
```

**Update Frontend API URL:**
```bash
cd frontend
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://whatsapp-memories-api.fly.dev

# Redeploy for changes to take effect
vercel --prod
```

**Remove a Secret:**
```bash
fly secrets unset SECRET_NAME
```

---

## Scaling

### Scale Backend Resources

**Increase Memory:**
```bash
# Scale to 512MB
fly scale memory 512

# Verify
fly status
```

**Upgrade CPU:**
```bash
# Upgrade to 2x shared CPU
fly scale vm shared-cpu-2x

# Verify
fly status
```

**Add More Instances (Horizontal Scaling):**
```bash
# Scale to 2 instances
fly scale count 2

# Note: With SQLite, all instances share the same volume
# For true horizontal scaling, you'd need to migrate to Postgres
```

**Scale Back to Free Tier:**
```bash
fly scale memory 256
fly scale vm shared-cpu-1x
fly scale count 1
```

### Scale Database Storage

```bash
# Expand volume to 3GB
fly volumes extend whatsapp_memories_data -s 3

# Verify
fly volumes list
```

**Important**: Volumes can only be expanded, not shrunk.

### Frontend Scaling

Vercel scales automatically. No manual intervention needed.

**Monitor Usage:**
- Vercel Dashboard → Analytics
- Check bandwidth, function invocations, build minutes

---

## Monitoring

### Set Up Alerts

**Fly.io Health Checks:**

The app already has health checks configured in `fly.toml`. Monitor in dashboard:
```bash
fly dashboard
```

**Vercel Monitoring:**
1. Go to Vercel Dashboard → Your Project
2. Click **Analytics** tab
3. Monitor:
   - Response times
   - Error rates
   - Bandwidth usage

### Key Metrics to Watch

**Backend:**
- Health endpoint response time (should be <100ms)
- Memory usage (should stay below 200MB normally)
- CPU usage (spikes during LLM processing are normal)
- Volume usage (watch for 80% threshold)

**Frontend:**
- 4xx/5xx error rates
- API latency to backend
- CORS errors in browser console

**Database:**
- File size growth rate
- Query performance (noticeable in API response times)

---

## Security Operations

### Rotate Secrets

**Rotate Gemini API Key:**
```bash
# 1. Generate new key at https://aistudio.google.com/apikey
# 2. Update Fly.io secret
fly secrets set GEMINI_API_KEY="new-key"
# 3. Test health endpoint
curl https://whatsapp-memories-api.fly.dev/health
```

**Update CORS Origins:**
```bash
# When adding custom domain
fly secrets set ALLOWED_ORIGINS="https://whatsapp-memories.vercel.app,https://your-custom-domain.com,http://localhost:3000"
```

### Review Access

**Fly.io Access:**
```bash
# List organization members
fly orgs show personal

# Review who has SSH access
fly auth whoami
```

**Vercel Access:**
- Vercel Dashboard → Settings → Members

### Audit Logs

**Fly.io:**
```bash
# View deployment history
fly releases

# View machine events
fly status
fly logs
```

**Vercel:**
- Vercel Dashboard → Your Project → Activity

---

## Incident Response

### Backend Down

**Quick Checks:**
```bash
# 1. Check status
fly status

# 2. View recent logs
fly logs -n

# 3. Check for OOM (Out of Memory)
fly logs | grep -i "out of memory\|oom"

# 4. Restart if hung
fly apps restart
```

**Common Causes:**
- Volume mount failure → Check `fly volumes list`
- Out of memory → Scale up or optimize queries
- Database lock → Restart resolves most issues
- Missing secrets → Verify with `fly secrets list`

### Frontend Issues

**Checklist:**
1. Check Vercel deployment status
2. Verify `NEXT_PUBLIC_API_URL` is set correctly
3. Test backend API directly
4. Check browser console for CORS errors
5. Redeploy if environment variables changed

### Database Corruption

**Symptoms:**
- Backend returns 500 errors
- Logs show SQLite errors
- Queries hang

**Recovery:**
```bash
# 1. SSH into machine
fly ssh console

# 2. Check database integrity
sqlite3 /data/backend_cache.db "PRAGMA integrity_check;"

# 3. If corrupted, restore from backup
exit
# Follow restore procedure above

# 4. If no backup, recreate from source data
# Process chat exports again (see "Adding New Data")
```

---

## Maintenance Windows

### Scheduled Maintenance

**Best Times:**
- Low traffic periods (late night in your timezone)
- Weekends for major updates

**Announcement:**
- Update README.md with maintenance notice
- Or add banner to frontend (requires code change)

### Zero-Downtime Updates

**Frontend:**
- Vercel deployments are zero-downtime by default
- Old version serves traffic until new one is ready

**Backend:**
- For code changes: `fly deploy` does rolling restart
- For database updates: 30-60 second downtime is unavoidable

**Minimize Downtime:**
1. Process data locally
2. Upload during low-traffic window
3. Use `fly apps restart` (faster than redeploy)

---

## Cost Management

### Monitor Spending

**Fly.io:**
```bash
fly dashboard
# Click "Billing" to see current usage
```

**Free Tier Limits:**
- 3 shared-cpu-1x VMs
- 3GB persistent storage
- 160GB outbound transfer/month

**Expected Usage (Personal Project):**
- VM: 1x 256MB (well within limit)
- Storage: <1GB for typical use
- Transfer: <10GB/month

**Vercel:**
- Dashboard → Usage
- Free tier: 100GB bandwidth, unlimited deployments

### Optimize Costs

**Backend:**
- Enable auto-stop: Already configured in `fly.toml`
  ```toml
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  ```
- Machines stop after 5 minutes of no traffic
- Start automatically on next request

**Frontend:**
- Use Vercel's ISR (Incremental Static Regeneration) where possible
- Already optimized with Next.js App Router

**Database:**
- Compact database periodically:
  ```bash
  fly ssh console
  sqlite3 /data/backend_cache.db "VACUUM;"
  exit
  ```

---

## Disaster Recovery

### Complete Rebuild

If everything fails, rebuild from scratch:

**Prerequisites:**
- Have `backend_cache.db` backup OR original chat exports
- Have Gemini API key
- Have GitHub repo access

**Steps:**
1. Follow [docs/DEPLOYMENT.md](DEPLOYMENT.md) from Phase 1
2. Restore database from backup OR process exports again
3. Update DNS if using custom domain

**Expected Time:** 30-45 minutes

### Rollback Deployments

**Backend Rollback:**
```bash
# List recent releases
fly releases

# Rollback to previous version
fly releases rollback
```

**Frontend Rollback:**
1. Vercel Dashboard → Deployments
2. Find working deployment
3. Click "..." → "Promote to Production"

---

## Useful Commands Reference

**Fly.io Quick Reference:**
```bash
fly status                    # App status
fly logs                      # Stream logs
fly ssh console               # SSH into machine
fly ssh sftp shell            # SFTP for file transfer
fly apps restart              # Restart app
fly volumes list              # List volumes
fly secrets list              # List secrets (values hidden)
fly releases                  # Deployment history
fly dashboard                 # Open web dashboard
```

**Vercel Quick Reference:**
```bash
vercel                        # Deploy preview
vercel --prod                 # Deploy production
vercel ls                     # List deployments
vercel env ls                 # List environment variables
vercel domains ls             # List domains
vercel logs                   # Stream logs
```

---

## Additional Resources

- [Fly.io Documentation](https://fly.io/docs/)
- [Vercel Documentation](https://vercel.com/docs)
- [FastAPI Deployment Best Practices](https://fastapi.tiangolo.com/deployment/)
- [SQLite Performance Tuning](https://www.sqlite.org/performance.html)
- [Next.js Production Checklist](https://nextjs.org/docs/going-to-production)

---

## Support

**For Production Issues:**
1. Check [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md) first
2. Review logs: `fly logs` or Vercel Dashboard
3. Verify environment variables: `fly secrets list` / `vercel env ls`
4. Try restart: `fly apps restart` / redeploy Vercel
5. Restore from backup if data issue

**For Questions:**
- Open an issue on GitHub
- Consult deployment documentation in `docs/`
- Check platform status pages:
  - https://status.fly.io/
  - https://vercel-status.com/
