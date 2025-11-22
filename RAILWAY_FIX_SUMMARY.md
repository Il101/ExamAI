# Railway Deployment Fix - Summary

## Issue Diagnosed
**Date:** 2025-11-22
**Error:** `[Errno 101] Network is unreachable` when connecting to Supabase database

## Root Cause
The hostname `db.pjgtzblqhtpdtojgbzpe.supabase.co` **does not exist in DNS**.

### Investigation Steps:
1. Connected to Railway via CLI: `railway link`
2. Tested DNS resolution inside Railway container:
   ```bash
   railway run --service ExamAI -- nslookup db.pjgtzblqhtpdtojgbzpe.supabase.co
   ```
   Result: `*** Can't find db.pjgtzblqhtpdtojgbzpe.supabase.co: No answer`

3. Verified that DNS works for other hosts:
   ```bash
   railway run --service ExamAI -- nslookup google.com
   ```
   Result: ✅ Success

4. Tested local DNS resolution:
   ```bash
   nslookup db.pjgtzblqhtpdtojgbzpe.supabase.co
   ```
   Result: Same error - hostname doesn't exist!

## Solution Applied

### 1. Obtained Supabase Connection Pooler URL
From Supabase Dashboard → Settings → Database → Connection Pooling (Session mode):
```
postgresql://postgres.pjgtzblqhtpdtojgbzpe:JGUf3TEEcLf45GBg@aws-1-eu-west-2.pooler.supabase.com:5432/postgres
```

### 2. Verified DNS Resolution
```bash
nslookup aws-1-eu-west-2.pooler.supabase.com
```
Result: ✅ Resolves to AWS ELB IPs (13.41.127.111, 13.43.174.140)

### 3. Updated Railway Environment Variable
```bash
railway variables --set DATABASE_URL='postgresql+asyncpg://postgres.pjgtzblqhtpdtojgbzpe:JGUf3TEEcLf45GBg@aws-1-eu-west-2.pooler.supabase.com:5432/postgres' --service ExamAI
```

### 4. Updated Local .env File
Updated `backend/.env` to use the same Connection Pooler URL for consistency.

## Expected Result
After Railway redeploys (automatic after variable change), the logs should show:
```
✅ Database initialized
```

Instead of:
```
⚠️  Database initialization failed: [Errno 101] Network is unreachable
```

## Files Updated
- ✅ Railway environment variable `DATABASE_URL`
- ✅ `backend/.env` - local development environment
- ✅ `RAILWAY_SETUP.md` - comprehensive deployment guide
- ✅ `scripts/fix_railway_database_url.sh` - helper script

## Next Steps
1. Monitor Railway deployment logs to confirm successful database connection
2. Test the `/health` endpoint to verify the application is fully operational
3. If successful, proceed with adding other required environment variables (Redis, Stripe, etc.)

## Key Learnings
- Supabase no longer uses `db.*.supabase.co` format for direct connections
- Always use Connection Pooler URLs for containerized/serverless environments
- Railway CLI is excellent for debugging container networking issues
- DNS resolution should be tested before assuming network connectivity problems
