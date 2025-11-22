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

**🚨 CRITICAL:** The host `db.pjgtzblqhtpdtojgbzpe.supabase.co` is **NOT resolvable via DNS**!

This is why you're getting `[Errno 101] Network is unreachable`. The DNS cannot resolve this hostname.

**✅ SOLUTION:** You **MUST** use Supabase's **Connection Pooler** URL:

```
# Get this from Supabase Dashboard → Project Settings → Database → Connection Pooling
# Select "Session" mode and copy the connection string
# Format: postgresql+asyncpg://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres

DATABASE_URL=postgresql+asyncpg://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres

SUPABASE_URL=https://pjgtzblqhtpdtojgbzpe.supabase.co
SUPABASE_KEY=<your-supabase-service-role-key>
```

**How to get the Connection Pooler URL:**
1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project: `pjgtzblqhtpdtojgbzpe`
3. Navigate to **Settings** → **Database**
4. Scroll down to **"Connection Pooling"** section
5. Select **"Session"** mode (not Transaction mode)
6. Copy the **"Connection string"**
7. Replace `postgresql://` with `postgresql+asyncpg://`
8. Update this in Railway: `railway variables --set DATABASE_URL='<your-pooler-url>' --service ExamAI`

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

**Root Cause (Verified via Railway CLI):**
The hostname `db.pjgtzblqhtpdtojgbzpe.supabase.co` **cannot be resolved by DNS**. 

When we tested with `railway run --service ExamAI -- nslookup db.pjgtzblqhtpdtojgbzpe.supabase.co`, it returned:
```
*** Can't find db.pjgtzblqhtpdtojgbzpe.supabase.co: No answer
```

This is NOT a Railway networking issue - the hostname simply doesn't exist in DNS!

**✅ SOLUTION:**

Use Supabase's Connection Pooler URL instead:

1. Go to [Supabase Dashboard](https://supabase.com/dashboard) → Your Project
2. Settings → Database → Connection Pooling
3. Select **"Session"** mode
4. Copy the connection string (format: `postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres`)
5. Replace `postgresql://` with `postgresql+asyncpg://`
6. Update in Railway:
   ```bash
   railway variables --set DATABASE_URL='postgresql+asyncpg://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres' --service ExamAI
   ```

The pooler hostname (e.g., `aws-0-eu-central-1.pooler.supabase.com`) **IS resolvable** and will work correctly.

### Redis connection errors
- If Redis is not critical, the app will still work
- Rate limiting will fall back to in-memory (not recommended for production)

## Recent Changes

- ✅ Fixed Dockerfile to work with Railway's build context
- ✅ Made database initialization non-blocking for healthcheck
- ✅ Made Redis optional in production (app starts even if Redis is down)
