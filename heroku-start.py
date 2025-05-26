#!/usr/bin/env python3
"""
Heroku startup script for Sportstiming Ticket Checker
Creates config from environment variables and starts the application
"""

import os
import json
import sys
import subprocess


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

    # SMS configuration (optional)
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
    print("🚀 Starting Sportstiming Ticket Checker on Heroku...")

    # Create config from environment variables
    config = create_config_from_env()

    if not config:
        print("❌ No notification configuration found in environment variables")
        print("Please set at least TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        sys.exit(1)

    # Write config file
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)

    print("✅ Config file created from environment variables")

    # Test configuration
    print("🔍 Testing configuration...")
    try:
        result = subprocess.run(
            [
                "python",
                "ticket_checker.py",
                "--test-telegram",
                "--config",
                "config.json",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print("✅ Configuration test passed")
        else:
            print("⚠️ Configuration test failed, but continuing...")
            print(f"Error: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("⚠️ Configuration test timed out, but continuing...")
    except Exception as e:
        print(f"⚠️ Could not test configuration: {e}")

    # Get configuration from environment
    check_interval = int(os.getenv("CHECK_INTERVAL", "300"))
    ticket_url = os.getenv(
        "TICKET_URL", "https://www.sportstiming.dk/event/6583/resale"
    )
    notify_all = os.getenv("NOTIFY_ALL", "true").lower() == "true"

    print(f"🎯 Starting monitoring:")
    print(f"   URL: {ticket_url}")
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
        "--url",
        ticket_url,
    ]

    if notify_all:
        cmd.append("--notify-all")

    # Start the application
    print("🏃 Starting application...")
    os.execvp("python", cmd)


if __name__ == "__main__":
    main()
