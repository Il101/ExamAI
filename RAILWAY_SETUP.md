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
```
DATABASE_URL=postgresql+asyncpg://postgres:<password>@db.pjgtzblqhtpdtojgbzpe.supabase.co:5432/postgres
SUPABASE_URL=https://pjgtzblqhtpdtojgbzpe.supabase.co
SUPABASE_KEY=<your-supabase-service-role-key>
```

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

### Database connection errors
- Supabase might need to whitelist Railway's IP ranges
- Or use Supabase's connection pooler URL

### Redis connection errors
- If Redis is not critical, the app will still work
- Rate limiting will fall back to in-memory (not recommended for production)

## Recent Changes

- ✅ Fixed Dockerfile to work with Railway's build context
- ✅ Made database initialization non-blocking for healthcheck
- ✅ Made Redis optional in production (app starts even if Redis is down)
