# Rate Limiting (429 Error) Guide

## What is a 429 Error?

**429 "Too Many Requests"** means the website is blocking you because you're making requests too frequently. This is a common anti-bot protection.

## How the Script Now Handles 429 Errors

### ✅ **Automatic Retry with Exponential Backoff**
- **First retry**: Waits 30 seconds
- **Second retry**: Waits 60 seconds  
- **Third retry**: Waits 120 seconds
- **After 3 failed attempts**: Returns `RATE_LIMITED` status

### ✅ **Smart Continuous Monitoring**
- **Rate limit detection**: Automatically increases delays when rate limited
- **Random jitter**: Adds ±30 seconds randomization to prevent synchronized requests
- **Extended delays**: Uses at least 5 minutes after rate limiting
- **Minimum interval**: Enforces 30+ second minimum between requests

### ✅ **Warning System**
- Warns if check interval is under 60 seconds
- Logs rate limiting attempts and delays
- Shows extended delay calculations

## Recommended Settings

### For Railway Deployment
```bash
# Safe interval - reduces chance of rate limiting
python ticket_checker.py --interval 300  # 5 minutes (default)

# More aggressive (higher chance of rate limiting)
python ticket_checker.py --interval 120  # 2 minutes

# Very aggressive (likely to get rate limited)
python ticket_checker.py --interval 60   # 1 minute
```

### Troubleshooting 429 Errors

**If you're getting frequent 429 errors:**

1. **Increase check interval**:
   ```bash
   python ticket_checker.py --interval 600  # 10 minutes
   ```

2. **Check current environment variables**:
   ```bash
   python ticket_checker.py --show-env
   ```

3. **Use authentication** (reduces rate limiting):
   - Set `ST_AUTH_TOKEN` and `ST_SESSION_ID` in Railway
   - Or use `--update-cookies` locally

4. **Monitor logs** for these messages:
   - `⚠️ Check interval (Xs) is quite frequent`
   - `🚨 Rate limited! Increasing delay`
   - `Using extended delay of X seconds`

## What You'll See in Logs

### Normal Operation
```
INFO - Checking for available tickets...
INFO - Status: NO_TICKETS - No tickets available for sale
INFO - Next check in 315 seconds...  # (300 + random jitter)
```

### Rate Limited (Automatic Recovery)
```
WARNING - Rate limited (429). Waiting 30 seconds before retry 1/3
WARNING - Rate limited (429). Waiting 60 seconds before retry 2/3
INFO - Status: NO_TICKETS - No tickets available for sale
```

### Extended Rate Limiting
```
WARNING - 🚨 Rate limited! Increasing delay to avoid further rate limiting...
INFO - Using extended delay of 600 seconds due to rate limiting
INFO - Next check in 687 seconds (extended + 87s jitter)
```

## Environment Variables for Railway

Set these to reduce rate limiting (authenticated users get better rate limits):

```
ST_AUTH_TOKEN=your_jwt_token_here
ST_SESSION_ID=your_session_id_here
```

## Best Practices

1. **Use 5+ minute intervals** for continuous monitoring
2. **Set authentication tokens** in Railway environment variables
3. **Monitor Railway logs** for rate limiting patterns
4. **Increase intervals** if you see frequent 429 errors
5. **Don't run multiple instances** of the same script simultaneously

## Quick Commands

```bash
# Check current settings
python ticket_checker.py --show-env

# Test single check (with current auth)
python ticket_checker.py --single

# Start monitoring with safe 10-minute interval
python ticket_checker.py --interval 600

# Interactive cookie update for better rate limits
python ticket_checker.py --update-cookies
```

The script is now much more resilient to rate limiting and will automatically recover from 429 errors! 🚀 