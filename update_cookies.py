#!/usr/bin/env python3
"""
Helper script to extract cookies from browser headers
Run this when you get 403 errors to update authentication
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
        print("❌ No Cookie header found in the provided text")
        return None, None

    # Extract st-auth-s2 token
    auth_match = re.search(r"st-auth-s2=([^;]+)", cookie_line)
    auth_token = auth_match.group(1) if auth_match else None

    # Extract st-sessionids2
    session_match = re.search(r"st-sessionids2=([^;]+)", cookie_line)
    session_id = session_match.group(1) if session_match else None

    return auth_token, session_id


def main():
    print("🔐 Cookie Extractor for Sportstiming Ticket Checker")
    print("=" * 50)
    print("Paste your browser headers below (Ctrl+D or Ctrl+Z when done):")
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
        print("🎫 Authentication Token (st-auth-s2):")
        print(f"   {auth_token[:50]}...")
        print()

    if session_id:
        print("🆔 Session ID (st-sessionids2):")
        print(f"   {session_id}")
        print()

    print("📋 Commands to update your ticket checker:")

    if auth_token and session_id:
        print(
            f'python ticket_checker.py --auth-token "{auth_token}" --session-id "{session_id}" --single'
        )
    elif auth_token:
        print(f'python ticket_checker.py --auth-token "{auth_token}" --single')
    elif session_id:
        print(f'python ticket_checker.py --session-id "{session_id}" --single')

    print()
    print("💡 Or use the interactive mode:")
    print("python ticket_checker.py --update-cookies")


if __name__ == "__main__":
    main()
