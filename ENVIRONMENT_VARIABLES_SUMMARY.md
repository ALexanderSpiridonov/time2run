# Environment Variables Quick Setup

## For Railway Deployment

The ticket checker now automatically loads authentication from environment variables! 🎉

### Required Environment Variables

In your Railway project, set these variables:

| Variable | Description | Where to get it |
|----------|-------------|-----------------|
| `ST_AUTH_TOKEN` | JWT authentication token | Browser Cookie `st-auth-s2=...` |
| `ST_SESSION_ID` | Session identifier | Browser Cookie `st-sessionids2=...` |

### Quick Setup Steps

1. **Get your tokens**: Use the helper script
   ```bash
   python setup_env.py
   ```
   
2. **Copy tokens to Railway**: 
   - Go to your Railway project
   - Click "Variables" tab
   - Add the two environment variables

3. **Deploy**: Your app will automatically use the tokens!

### Helper Commands

```bash
# Check current environment variables
python ticket_checker.py --show-env

# Test with environment variables
python ticket_checker.py --single

# Extract tokens from browser headers  
python setup_env.py

# Manual token setting (overrides env vars)
python ticket_checker.py --auth-token "YOUR_TOKEN" --session-id "YOUR_SESSION"
```

### Priority Order

1. **Command line arguments** (highest priority)
2. **Environment variables** 
3. **Default (no auth)** (lowest priority)

This means you can always override environment variables with command line arguments if needed.

### What You'll See

When environment variables are loaded successfully:
```
✅ Auth token loaded from ST_AUTH_TOKEN
✅ Session ID loaded from ST_SESSION_ID
Loaded authentication from environment variables
🔐 Using authentication from environment variables:
   ✅ ST_AUTH_TOKEN: eyJhbGciOiJIUzUxMiIs...
   ✅ ST_SESSION_ID: 1cce6b2e-584c-457a-952d-43147392fe90
```

### Token Expiration

JWT tokens expire every few hours. When they do:
1. The script will show `AUTH_REQUIRED` status
2. Get fresh tokens from your browser 
3. Update the Railway environment variables
4. Restart your Railway deployment

That's it! Much easier than manual cookie management. 🚀 