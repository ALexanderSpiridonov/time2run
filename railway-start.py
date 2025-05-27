#!/usr/bin/env python3
"""
Railway startup script for Sportstiming Ticket Checker
Creates config from environment variables and starts the application
"""

import os
import json
import sys
import subprocess
import time


def create_config_from_env():
    """Create config.json from environment variables"""
    config = {}

    # Telegram configuration
    if os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

        # Handle multiple chat IDs (comma-separated)
        if "," in telegram_chat_id:
            chat_ids = [id.strip() for id in telegram_chat_id.split(",")]
        else:
            chat_ids = telegram_chat_id.strip()

        config["telegram"] = {
            "bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
            "chat_id": chat_ids,
        }

    # Email configuration (optional)
    if all(
        [
            os.getenv("EMAIL_SMTP_SERVER"),
            os.getenv("EMAIL_USERNAME"),
            os.getenv("EMAIL_PASSWORD"),
            os.getenv("EMAIL_TO"),
        ]
    ):
        config["email"] = {
            "smtp_server": os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("EMAIL_SMTP_PORT", "587")),
            "username": os.getenv("EMAIL_USERNAME"),
            "password": os.getenv("EMAIL_PASSWORD"),
            "from_email": os.getenv("EMAIL_FROM", os.getenv("EMAIL_USERNAME")),
            "to_email": os.getenv("EMAIL_TO"),
        }

    # SMS/Twilio configuration (optional)
    if all(
        [
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN"),
            os.getenv("TWILIO_FROM_NUMBER"),
            os.getenv("TWILIO_TO_NUMBER"),
        ]
    ):
        config["sms"] = {
            "account_sid": os.getenv("TWILIO_ACCOUNT_SID"),
            "auth_token": os.getenv("TWILIO_AUTH_TOKEN"),
            "from_number": os.getenv("TWILIO_FROM_NUMBER"),
            "to_number": os.getenv("TWILIO_TO_NUMBER"),
        }

    # Pushover configuration (optional)
    if all([os.getenv("PUSHOVER_APP_TOKEN"), os.getenv("PUSHOVER_USER_KEY")]):
        config["pushover"] = {
            "app_token": os.getenv("PUSHOVER_APP_TOKEN"),
            "user_key": os.getenv("PUSHOVER_USER_KEY"),
        }

    return config


def main():
    print("🚂 Starting Sportstiming Ticket Checker on Railway...")

    # Debug: Print environment variables
    print("🔍 Debug - Environment variables:")
    print(
        f"   TELEGRAM_BOT_TOKEN: {'SET' if os.getenv('TELEGRAM_BOT_TOKEN') else 'NOT SET'}"
    )
    print(
        f"   TELEGRAM_CHAT_ID: {'SET' if os.getenv('TELEGRAM_CHAT_ID') else 'NOT SET'}"
    )
    print(f"   CHECK_INTERVAL: {os.getenv('CHECK_INTERVAL', 'NOT SET')}")
    print(f"   NOTIFY_ALL: {os.getenv('NOTIFY_ALL', 'NOT SET')}")
    print(f"   TICKET_RANGE: {os.getenv('TICKET_RANGE', 'NOT SET')}")
    print(f"   TICKET_START_ID: {os.getenv('TICKET_START_ID', 'NOT SET')}")
    print(f"   TICKET_END_ID: {os.getenv('TICKET_END_ID', 'NOT SET')}")
    print(f"   TICKET_IDS: {os.getenv('TICKET_IDS', 'NOT SET')}")

    # Show first few characters of bot token if set (for debugging)
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if bot_token:
        print(f"   Bot token starts with: {bot_token[:10]}...")

    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if chat_id:
        print(f"   Chat ID: {chat_id}")

    # Create config from environment variables
    config = create_config_from_env()

    if not config:
        print("❌ No notification configuration found in environment variables")
        print("Please set at least TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        print("💡 Check Railway dashboard → Variables tab")
        print("⏳ Waiting 30 seconds before exit to prevent restart loop...")
        time.sleep(30)
        sys.exit(1)

    # Write config file
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)

    print("✅ Config file created from environment variables")

    # Get configuration from environment
    check_interval = int(
        os.getenv("CHECK_INTERVAL", "120")
    )  # Default 2 minutes for checking 50+ tickets
    ticket_url = os.getenv(
        "TICKET_URL", "https://www.sportstiming.dk/event/6583/resale"
    )
    notify_all = (
        os.getenv("NOTIFY_ALL", "false").lower() == "true"
    )  # Default to false for cleaner notifications

    # Flexible ticket range configuration
    ticket_range = None

    # Option 1: TICKET_RANGE (e.g., "54310-54360")
    if os.getenv("TICKET_RANGE"):
        ticket_range = os.getenv("TICKET_RANGE")
        print(f"   Using TICKET_RANGE: {ticket_range}")

    # Option 2: Separate start and end IDs
    elif os.getenv("TICKET_START_ID") and os.getenv("TICKET_END_ID"):
        start_id = os.getenv("TICKET_START_ID")
        end_id = os.getenv("TICKET_END_ID")
        ticket_range = f"{start_id}-{end_id}"
        print(f"   Using TICKET_START_ID and TICKET_END_ID: {ticket_range}")

    # Option 3: Individual ticket IDs (comma-separated)
    elif os.getenv("TICKET_IDS"):
        ticket_ids = os.getenv("TICKET_IDS")
        print(f"   Using individual TICKET_IDS: {ticket_ids}")
        # For individual IDs, we'll pass them differently

    print(f"🎯 Starting monitoring:")
    if ticket_range:
        print(f"   Ticket Range: {ticket_range}")
    elif os.getenv("TICKET_IDS"):
        print(f"   Individual Tickets: {os.getenv('TICKET_IDS')}")
    else:
        print(f"   Ticket Range: 54310-54360 (default)")
    print(f"   Interval: {check_interval} seconds")
    print(f"   Notify all statuses: {notify_all}")
    print(f"   Mode: CONTINUOUS MONITORING (not single check)")

    # Build command
    cmd = [
        "python",
        "ticket_checker.py",
        "--config",
        "config.json",
        "--interval",
        str(check_interval),
    ]

    # Add ticket configuration
    if ticket_range:
        cmd.extend(["--ticket-range", ticket_range])
    elif os.getenv("TICKET_IDS"):
        # For individual tickets, use the new --ticket-ids argument
        ticket_ids = os.getenv("TICKET_IDS")
        cmd.extend(["--ticket-ids", ticket_ids])

    # Add notify all if enabled
    if notify_all:
        cmd.append("--notify-all")

    # Explicitly ensure we're NOT in single mode (continuous is default)
    print(f"🏃 Starting application with command: {' '.join(cmd)}")
    print(
        "🔄 This will run CONTINUOUSLY, checking every {} seconds".format(
            check_interval
        )
    )

    # Start the application
    os.execvp("python", cmd)


if __name__ == "__main__":
    main()
