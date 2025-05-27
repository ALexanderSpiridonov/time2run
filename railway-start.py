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
        os.getenv("CHECK_INTERVAL", "60")
    )  # Default 2 minutes for faster checking
    ticket_url = os.getenv(
        "TICKET_URL", "https://www.sportstiming.dk/event/6583/resale"
    )
    notify_all = (
        os.getenv("NOTIFY_ALL", "false").lower() == "true"
    )  # Default to false for cleaner notifications
    ticket_range = os.getenv("TICKET_RANGE")  # e.g., "54296-54310"

    print(f"🎯 Starting monitoring:")
    if ticket_range:
        print(f"   Ticket Range: {ticket_range}")
    else:
        print(f"   Ticket Range: 54296-54310 (default)")
    print(f"   Interval: {check_interval} seconds")
    print(f"   Notify all statuses: {notify_all}")

    # Build command
    cmd = [
        "python",
        "ticket_checker.py",
        "--config",
        "config.json",
        "--interval",
        str(check_interval),
    ]

    # Add ticket range if specified
    if ticket_range:
        cmd.extend(["--ticket-range", ticket_range])

    # Add notify all if enabled
    if notify_all:
        cmd.append("--notify-all")

    print(f"🏃 Starting application with command: {' '.join(cmd)}")

    # Start the application
    os.execvp("python", cmd)


if __name__ == "__main__":
    main()
