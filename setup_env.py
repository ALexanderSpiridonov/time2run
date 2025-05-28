#!/usr/bin/env python3
"""
Helper script to extract cookies and generate environment variable commands
Perfect for Railway deployment setup
"""

import re
import sys


def extract_cookies_from_headers(headers_text):
    """Extract cookies from browser headers text"""
    cookie_line = None

    for line in headers_text.split("\n"):
        if line.strip().lower().startswith("cookie:"):
            cookie_line = line.strip()
            break

    if not cookie_line:
        return None, None

    # Extract st-auth-s2 token
    auth_match = re.search(r"st-auth-s2=([^;]+)", cookie_line)
    auth_token = auth_match.group(1) if auth_match else None

    # Extract st-sessionids2
    session_match = re.search(r"st-sessionids2=([^;]+)", cookie_line)
    session_id = session_match.group(1) if session_match else None

    return auth_token, session_id


def main():
    print("🚂 Railway Environment Setup Helper")
    print("=" * 40)
    print("This will help you set up environment variables for Railway deployment.")
    print()
    print("Please paste your browser headers below (press Ctrl+D when done):")
    print("(Get these from Developer Tools > Network tab > Request Headers)")
    print()

    try:
        headers_text = sys.stdin.read()
    except KeyboardInterrupt:
        print("\n❌ Cancelled")
        return

    if not headers_text.strip():
        print("❌ No headers provided")
        return

    auth_token, session_id = extract_cookies_from_headers(headers_text)

    if not auth_token and not session_id:
        print("❌ No authentication cookies found")
        print(
            "Make sure your headers include the Cookie line with st-auth-s2 and/or st-sessionids2"
        )
        return

    print("✅ Cookies extracted successfully!")
    print()

    if auth_token:
        print("🎫 Authentication Token Found:")
        print(f"   {auth_token[:50]}...")
        print(f"   Length: {len(auth_token)} characters")
        print()

    if session_id:
        print("🆔 Session ID Found:")
        print(f"   {session_id}")
        print()

    print("📋 RAILWAY SETUP COMMANDS:")
    print("=" * 30)
    print("Add these environment variables in your Railway project:")
    print()

    if auth_token:
        print(f"Variable Name: ST_AUTH_TOKEN")
        print(f"Variable Value: {auth_token}")
        print()

    if session_id:
        print(f"Variable Name: ST_SESSION_ID")
        print(f"Variable Value: {session_id}")
        print()

    print("🖥️  LOCAL TESTING COMMANDS:")
    print("=" * 30)
    print("For testing locally, run these commands:")
    print()

    if auth_token:
        print(f'export ST_AUTH_TOKEN="{auth_token}"')
    if session_id:
        print(f'export ST_SESSION_ID="{session_id}"')

    print()
    print("Then run: python ticket_checker.py --single")
    print()

    print("🔍 VERIFICATION:")
    print("=" * 15)
    print("After setting up, verify with: python ticket_checker.py --show-env")
    print()

    print("⏰ TOKEN EXPIRATION NOTICE:")
    print("=" * 30)
    print("JWT tokens (ST_AUTH_TOKEN) typically expire after a few hours.")
    print("You'll need to update them periodically when you get 403 errors.")
    print("Session IDs (ST_SESSION_ID) last longer but may also need updating.")


if __name__ == "__main__":
    main()
