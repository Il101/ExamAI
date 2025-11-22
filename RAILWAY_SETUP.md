# Railway Deployment Setup

## Required Environment Variables

Configure these in Railway Dashboard → Your Service → Variables:

### Application Settings
```
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<your-secret-key-from-env>
FRONTEND_URL=<your-frontend-url>
ALLOWED_ORIGINS=["<your-frontend-url>"]
```

### Database (Supabase)

**IMPORTANT:** Use Supabase's **Connection Pooler** URL for Railway (more reliable for containerized environments):

```
# Get this from Supabase Dashboard → Project Settings → Database → Connection Pooling
# Format: postgresql+asyncpg://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
DATABASE_URL=postgresql+asyncpg://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres

# Or if pooler doesn't work, try the direct connection with IPv4 preference:
# DATABASE_URL=postgresql+asyncpg://postgres:<password>@db.pjgtzblqhtpdtojgbzpe.supabase.co:5432/postgres

SUPABASE_URL=https://pjgtzblqhtpdtojgbzpe.supabase.co
SUPABASE_KEY=<your-supabase-service-role-key>
```

To get the Connection Pooler URL:
1. Go to Supabase Dashboard → Your Project
2. Settings → Database
3. Scroll to "Connection Pooling"
4. Copy the "Connection string" (Session mode)
5. Replace `postgresql://` with `postgresql+asyncpg://`

### AI Provider
```
GEMINI_API_KEY=<your-gemini-api-key>
GEMINI_MODEL=gemini-2.0-flash-exp
LLM_PROVIDER=gemini
```

### Redis (Optional - add Redis service in Railway)
```
REDIS_URL=redis://default:<password>@<railway-redis-host>:6379
```

If you don't have Redis yet, the app will still work but rate limiting will be disabled.

### Sentry (Optional)
```
SENTRY_DSN=<your-sentry-dsn>
```

### Stripe (Required for payments)
```
STRIPE_SECRET_KEY=<your-stripe-secret-key>
STRIPE_PUBLISHABLE_KEY=<your-stripe-publishable-key>
STRIPE_WEBHOOK_SECRET=<your-stripe-webhook-secret>
STRIPE_PRICE_ID_PRO=<price-id-from-stripe>
STRIPE_PRICE_ID_PREMIUM=<price-id-from-stripe>
```

### Email/Notifications
```
NOTIFICATION_PROVIDER=sendgrid
SENDGRID_API_KEY=<your-sendgrid-api-key>
SENDGRID_FROM_EMAIL=noreply@examai.pro
```

## Deployment Steps

1. **Push code to GitHub** (already done)

2. **Add Redis service** (recommended):
   - In Railway dashboard, click "New"
   - Select "Database" → "Add Redis"
   - Copy the `REDIS_URL` from the Redis service variables
   - Add it to your backend service variables

3. **Configure environment variables**:
   - Go to your backend service → Variables
   - Add all required variables from above
   - Make sure `ENVIRONMENT=production`

4. **Redeploy**:
   - Railway will automatically redeploy after you save variables
   - Or manually trigger: Settings → Redeploy

## Troubleshooting

### Healthcheck fails
- Check that `DATABASE_URL` is correct and accessible
- Verify Supabase allows connections from Railway IPs
- Check deployment logs for specific errors

### Database connection errors: "[Errno 101] Network is unreachable"

This error means Railway container cannot reach Supabase. Try these solutions **in order**:

**Solution 1: Use Supabase Connection Pooler (RECOMMENDED)**
1. Go to Supabase Dashboard → Your Project → Settings → Database
2. Scroll to "Connection Pooling" section
3. Copy the "Connection string" under "Session mode"
4. Replace `postgresql://` with `postgresql+asyncpg://`
5. Update `DATABASE_URL` in Railway with this pooler URL
6. Example: `postgresql+asyncpg://postgres.abc123:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres`

**Solution 2: Check Supabase Network Restrictions**
1. Go to Supabase Dashboard → Settings → Database → Connection Pooling
2. Make sure "Restrict connections to IPv4" is **disabled** (or enable if Railway uses IPv6)
3. Check if there are any IP restrictions that might block Railway

**Solution 3: Use Supabase Direct Connection with SSL**
Try adding SSL parameters to the connection string:
```
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.pjgtzblqhtpdtojgbzpe.supabase.co:5432/postgres?ssl=require
```

**Solution 4: Verify Railway can reach external services**
Railway should allow outbound connections by default, but verify:
- Check Railway service logs for DNS resolution errors
- Try deploying a simple test that pings Supabase host

### Redis connection errors
- If Redis is not critical, the app will still work
- Rate limiting will fall back to in-memory (not recommended for production)

## Recent Changes

- ✅ Fixed Dockerfile to work with Railway's build context
- ✅ Made database initialization non-blocking for healthcheck
- ✅ Made Redis optional in production (app starts even if Redis is down)
