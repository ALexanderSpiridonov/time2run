# Railway Deployment Guide for Sportstiming Ticket Checker

## Setting Up Environment Variables in Railway

The ticket checker now automatically loads authentication tokens from environment variables, making Railway deployment much easier.

### Required Environment Variables

Set these in your Railway project:

| Variable Name | Description | Example |
|---------------|-------------|---------|
| `ST_AUTH_TOKEN` | The `st-auth-s2` JWT token from your browser | `eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9...` |
| `ST_SESSION_ID` | The `st-sessionids2` session ID from your browser | `1cce6b2e-584c-457a-952d-43147392fe90` |

### How to Set Environment Variables in Railway

1. **Login to Railway**: Go to https://railway.app and login
2. **Select your project**: Click on your ticket checker project
3. **Go to Variables tab**: Click on "Variables" in the left sidebar
4. **Add variables**: Click "New Variable" and add:
   - **Name**: `ST_AUTH_TOKEN`
   - **Value**: Your `st-auth-s2` token (the long JWT string)
5. **Add second variable**:
   - **Name**: `ST_SESSION_ID` 
   - **Value**: Your `st-sessionids2` session ID

### How to Get Your Tokens

1. **Go to the website**: https://www.sportstiming.dk/event/6583/resale
2. **Open Developer Tools**: Press F12
3. **Go to Network tab**: Click "Network"
4. **Refresh page**: Press F5
5. **Find the request**: Click on the first request to the page
6. **Copy tokens from Cookie header**:
   - Find the line starting with `Cookie:`
   - Copy the value after `st-auth-s2=` (until the next `;`)
   - Copy the value after `st-sessionids2=` (until the next `;`)

### Example Cookie Line
```
Cookie: cookies_allowed=required; st-lang=da-DK; st-sessionids2=1cce6b2e-584c-457a-952d-43147392fe90; st-auth-s2=eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjE1Mjg5IiwibmFtZSI6IkFsZXhhbmRyIFNwaXJpZG9ub3YiLCJnaXZlbl9uYW1lIjoiQWxleGFuZHIiLCJmYW1pbHlfbmFtZSI6IlNwaXJpZG9ub3YiLCJlbWFpbCI6InNwaXJpZG9ub3YuYWxleGFuZHJAZ21haWwuY29tIiwibmJmIjoxNzQ4Mzg2NDY0LCJleHAiOjE3NDgzOTM2NjQsImF1ZCI6InN0d2ViX3MyIn0.XHs2sBOliS4gMRCdX6RdPZH6kwTi4Qx9h65JoQ1y7YSaPo4BqC-_6dVLh3K49MFeknC7IymAW6UA9owkoxiZOQ
```

From this example:
- `ST_SESSION_ID` = `1cce6b2e-584c-457a-952d-43147392fe90`
- `ST_AUTH_TOKEN` = `eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjE1Mjg5IiwibmFtZSI6IkFsZXhhbmRyIFNwaXJpZG9ub3YiLCJnaXZlbl9uYW1lIjoiQWxleGFuZHIiLCJmYW1pbHlfbmFtZSI6IlNwaXJpZG9ub3YiLCJlbWFpbCI6InNwaXJpZG9ub3YuYWxleGFuZHJAZ21haWwuY29tIiwibmJmIjoxNzQ4Mzg2NDY0LCJleHAiOjE3NDgzOTM2NjQsImF1ZCI6InN0d2ViX3MyIn0.XHs2sBOliS4gMRCdX6RdPZH6kwTi4Qx9h65JoQ1y7YSaPo4BqC-_6dVLh3K49MFeknC7IymAW6UA9owkoxiZOQ`

### Railway Deployment Steps

1. **Set environment variables** (as described above)
2. **Deploy your code** to Railway
3. **The script will automatically**:
   - Load tokens from environment variables on startup
   - Use authentication for all requests
   - Log successful authentication loading

### Testing Locally with Environment Variables

You can test locally by setting environment variables:

```bash
# On macOS/Linux:
export ST_AUTH_TOKEN="your_token_here"
export ST_SESSION_ID="your_session_id_here"
python ticket_checker.py --single

# On Windows:
set ST_AUTH_TOKEN=your_token_here
set ST_SESSION_ID=your_session_id_here
python ticket_checker.py --single
```

### Token Expiration

**Important**: JWT tokens (`ST_AUTH_TOKEN`) typically expire after a few hours. You'll need to:

1. **Monitor your logs**: Look for 403 errors or `AUTH_REQUIRED` status
2. **Update tokens periodically**: Get fresh tokens from your browser
3. **Update Railway variables**: Replace the expired token with a new one

### Optional: Notification Configuration

You can also set up notifications by adding a `config.json` file to your Railway project with your notification settings (Telegram, email, etc.).

### Troubleshooting

**If you get 403 errors on Railway:**
1. Check that environment variables are set correctly
2. Verify your tokens haven't expired
3. Get fresh tokens from your browser
4. Update the Railway environment variables

**Check logs for:**
- `✅ Auth token loaded from ST_AUTH_TOKEN`
- `✅ Session ID loaded from ST_SESSION_ID`
- `Loaded authentication from environment variables`

These messages confirm that authentication is working properly. 