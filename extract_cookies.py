#!/usr/bin/env python3
"""
Cookie extraction helper for Sportstiming Ticket Checker
Helps format browser cookies for use with the bot
"""

import json
import sys


def parse_cookie_string(cookie_string):
    """Parse cookie string from browser into dictionary"""
    # Remove "Cookie:" prefix if present
    if cookie_string.startswith("Cookie:"):
        cookie_string = cookie_string[7:].strip()

    cookies = {}
    for cookie_pair in cookie_string.split(";"):
        if "=" in cookie_pair:
            name, value = cookie_pair.strip().split("=", 1)
            # Skip empty names
            if name.strip():
                cookies[name.strip()] = value.strip()
    return cookies


def main():
    print("🍪 Sportstiming Cookie Extractor")
    print("=" * 40)
    print()
    print("Instructions:")
    print(
        "1. Open your browser and go to: https://www.sportstiming.dk/event/6583/resale"
    )
    print("2. Log in to your account")
    print("3. Open Developer Tools (F12)")
    print("4. Go to Network tab")
    print(
        "5. Visit any ticket page (e.g., https://www.sportstiming.dk/event/6583/resale/ticket/54392)"
    )
    print("6. Find the request in Network tab and copy the Cookie header")
    print()
    print("Paste your Cookie header here (or press Enter to use example):")

    cookie_input = input().strip()

    if not cookie_input:
        # Use the example from the user
        cookie_input = "cookies_allowed=required; st-lang=da-DK; st-sessionids2=1cce6b2e-584c-457a-952d-43147392fe90; st-auth-s2=eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjE1Mjg5IiwibmFtZSI6IkFsZXhhbmRyIFNwaXJpZG9ub3YiLCJnaXZlbl9uYW1lIjoiQWxleGFuZHIiLCJmYW1pbHlfbmFtZSI6IlNwaXJpZG9ub3YiLCJlbWFpbCI6InNwaXJpZG9ub3YuYWxleGFuZHJAZ21haWwuY29tIiwibmJmIjoxNzQ4Mzg0ODExLCJleHAiOjE3NDgzOTIwMTEsImF1ZCI6InN0d2ViX3MyIn0.u-JgRSTXAM3WDqgaQh__-jQkCrnRxUjxizJPZSBWpMuS3u93gWsJYDbenI4aRoEuF_K24_NJmW0W7kyeiD6ehg"
        print("Using example cookies...")

    try:
        cookies = parse_cookie_string(cookie_input)

        print(f"\n✅ Parsed {len(cookies)} cookies:")
        for name, value in cookies.items():
            print(f"   {name}: {value[:50]}{'...' if len(value) > 50 else ''}")

        # Save to file
        with open("auth_cookies.json", "w") as f:
            json.dump(cookies, f, indent=2)

        print(f"\n💾 Saved cookies to auth_cookies.json")

        # Show usage examples
        print("\n📋 Usage Examples:")
        print("\n1. Test with cookies:")
        print(
            f"   python ticket_checker.py --check-ticket 54392 --single --cookies-file auth_cookies.json"
        )

        print("\n2. For Railway deployment, set environment variable:")
        cookie_env = "; ".join([f"{name}={value}" for name, value in cookies.items()])
        print(f'   AUTH_COOKIES="{cookie_env}"')

        print("\n3. Command line usage:")
        print(
            f'   python ticket_checker.py --cookies "{cookie_env}" --check-ticket 54392 --single'
        )

        print("\n⚠️  Important Notes:")
        print("   - These cookies will expire (JWT token expires in ~2 hours)")
        print("   - You'll need to refresh them periodically")
        print("   - Keep them secure - they contain your authentication token")

    except Exception as e:
        print(f"❌ Error parsing cookies: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
