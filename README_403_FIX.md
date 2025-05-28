# 403 Forbidden Error Fix for Sportstiming Ticket Checker

## Problem
The ticket checker was getting `403 Client Error: Forbidden` because the website detects automated requests and requires proper browser headers and authentication.

## Solution
The script has been updated with:

1. **Enhanced Browser Headers**: Updated to match modern Chrome browser headers
2. **Authentication Support**: Added ability to use session cookies for authenticated access
3. **Better Error Handling**: Specific handling for 403 errors with helpful messages

## Quick Fix
If you're getting 403 errors, the basic headers should now work:

```bash
python ticket_checker.py --single
```

## For Authenticated Content (Recommended)
For better access and to avoid future 403 errors:

### Method 1: Interactive Cookie Update
```bash
python ticket_checker.py --update-cookies
```

### Method 2: Command Line Cookie Update
```bash
python ticket_checker.py --auth-token "YOUR_TOKEN" --session-id "YOUR_SESSION_ID" --single
```

### Method 3: Using the Cookie Extractor Helper
```bash
python update_cookies.py
# Paste your browser headers when prompted
```

## How to Get Your Browser Cookies

1. Go to https://www.sportstiming.dk/event/6583/resale in your browser
2. Open Developer Tools (F12)
3. Go to the **Network** tab
4. Refresh the page (F5)
5. Click on the first request to the page
6. Look for **Request Headers** section
7. Find the **Cookie** line and copy these values:
   - `st-auth-s2=` (JWT authentication token)
   - `st-sessionids2=` (Session ID)

Example Cookie line:
```
Cookie: cookies_allowed=required; st-lang=da-DK; st-sessionids2=1cce6b2e-584c-457a-952d-43147392fe90; st-auth-s2=eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9...
```

## New Features Added

### Enhanced Headers
- Updated User-Agent to Chrome 136
- Added all necessary browser headers (Accept, Accept-Language, sec-ch-ua, etc.)
- Added basic cookies for language preferences

### Authentication Methods
- `--update-cookies`: Interactive cookie update
- `--auth-token`: Set authentication token directly
- `--session-id`: Set session ID directly

### Better Error Handling
- Specific 403 error detection
- Authentication status in results
- Helpful error messages with next steps

## Usage Examples

### Basic check (should work without authentication):
```bash
python ticket_checker.py --single
```

### With authentication for full access:
```bash
python ticket_checker.py --auth-token "YOUR_JWT_TOKEN" --session-id "YOUR_SESSION_ID" --single
```

### Continuous monitoring with authentication:
```bash
python ticket_checker.py --auth-token "YOUR_JWT_TOKEN" --session-id "YOUR_SESSION_ID" --interval 60
```

### Update cookies interactively:
```bash
python ticket_checker.py --update-cookies
```

## Notes

- **Authentication tokens expire**: You may need to update cookies periodically (JWT tokens typically last a few hours)
- **Session persistence**: The script now uses sessions to maintain cookies across requests
- **Basic access**: Even without authentication, the enhanced headers should prevent most 403 errors
- **Multiple attempts**: If you still get 403 errors, try updating your cookies

## Troubleshooting

If you still get 403 errors:

1. **Update your cookies** using one of the methods above
2. **Check if your authentication token has expired** (JWT tokens in `st-auth-s2` typically expire after a few hours)
3. **Verify you're logged into the website** in your browser
4. **Try the interactive cookie update** with `--update-cookies`

The script will now show `AUTH_REQUIRED` status instead of `ERROR` when authentication is needed, making it easier to identify when you need to update cookies. 