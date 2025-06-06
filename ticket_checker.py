#!/usr/bin/env python3
"""
Sportstiming Ticket Checker Bot
Automatically checks if tickets are available for sale on sportstiming.dk
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import argparse
import json
import os
import sys
import random


class SportstimingTicketChecker:
    def __init__(
        self,
        event_url,
        check_interval=300,
        config_file=None,
        notify_all_statuses=False,
        dry_run=False,
    ):
        """
        Initialize the ticket checker

        Args:
            event_url (str): The URL to check for tickets
            check_interval (int): Time between checks in seconds (default: 5 minutes)
            config_file (str): Path to config file for notifications
            notify_all_statuses (bool): Send notifications for all statuses, not just when tickets are available
            dry_run (bool): Run without sending actual notifications (for testing)
        """
        self.event_url = event_url
        self.check_interval = check_interval
        self.config_file = config_file
        self.config = self.load_config() if config_file else {}
        self.notify_all_statuses = notify_all_statuses
        self.dry_run = dry_run

        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("ticket_checker.log"),
                logging.StreamHandler(
                    sys.stdout
                ),  # Use stdout so Railway doesn't treat INFO as errors
            ],
        )
        self.logger = logging.getLogger(__name__)

        # Enhanced headers to match browser request and bypass 403 errors
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            # Session cookies - you may need to update these periodically
            "Cookie": "cookies_allowed=required; st-lang=da-DK",
        }

        # Automatically load authentication from environment variables
        self.load_auth_from_env()

    def load_auth_from_env(self):
        """
        Load authentication tokens from environment variables
        Environment variables:
        - ST_AUTH_TOKEN: The st-auth-s2 JWT token
        - ST_SESSION_ID: The st-sessionids2 session ID
        """
        auth_token = os.getenv("ST_AUTH_TOKEN")
        session_id = os.getenv("ST_SESSION_ID")

        if auth_token or session_id:
            self.update_cookies(auth_token=auth_token, session_id=session_id)
            self.logger.info("Loaded authentication from environment variables")
            if auth_token:
                self.logger.info("✅ Auth token loaded from ST_AUTH_TOKEN")
            if session_id:
                self.logger.info("✅ Session ID loaded from ST_SESSION_ID")
        else:
            self.logger.debug("No authentication environment variables found")

    def load_config(self):
        """Load configuration from JSON file"""
        if self.config_file and os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                return json.load(f)
        return {}

    def update_cookies(self, auth_token=None, session_id=None):
        """
        Update cookies for authentication

        Args:
            auth_token (str): The st-auth-s2 JWT token from browser
            session_id (str): The st-sessionids2 session ID from browser
        """
        base_cookies = "cookies_allowed=required; st-lang=da-DK"

        if session_id:
            base_cookies += f"; st-sessionids2={session_id}"

        if auth_token:
            base_cookies += f"; st-auth-s2={auth_token}"

        self.headers["Cookie"] = base_cookies
        self.logger.info("Updated authentication cookies")

    def check_tickets_available(self):
        """
        Check if tickets are available for sale

        Returns:
            dict: Dictionary with status and details
        """
        max_retries = 3
        base_delay = 30  # Start with 30 seconds for 429 errors

        for attempt in range(max_retries + 1):
            try:
                # Create a session to maintain cookies
                session = requests.Session()
                session.headers.update(self.headers)

                response = session.get(self.event_url, timeout=30)

                # Handle 429 (Too Many Requests) specifically
                if response.status_code == 429:
                    if attempt < max_retries:
                        delay = base_delay * (
                            2**attempt
                        )  # Exponential backoff: 30s, 60s, 120s
                        self.logger.warning(
                            f"Rate limited (429). Waiting {delay} seconds before retry {attempt + 1}/{max_retries}"
                        )
                        time.sleep(delay)
                        continue
                    else:
                        self.logger.error("Rate limited (429) - max retries exceeded")
                        return {
                            "timestamp": datetime.now().isoformat(),
                            "status": "RATE_LIMITED",
                            "message": "Rate limited by server (429). Try increasing check interval or wait longer.",
                            "ticket_count": 0,
                            "url": self.event_url,
                        }

                # Handle 403 specifically
                if response.status_code == 403:
                    self.logger.warning(
                        "Received 403 Forbidden - authentication may be required"
                    )
                    return {
                        "timestamp": datetime.now().isoformat(),
                        "status": "AUTH_REQUIRED",
                        "message": "Authentication required (403 Forbidden). Please update cookies with --update-cookies command.",
                        "ticket_count": 0,
                        "url": self.event_url,
                    }

                response.raise_for_status()
                break  # Success, exit retry loop

            except requests.RequestException as e:
                if "429" in str(e) and attempt < max_retries:
                    delay = base_delay * (2**attempt)
                    self.logger.warning(
                        f"Rate limited in exception. Waiting {delay} seconds before retry {attempt + 1}/{max_retries}"
                    )
                    time.sleep(delay)
                    continue
                elif attempt < max_retries and "timeout" in str(e).lower():
                    delay = 10 * (attempt + 1)  # 10s, 20s, 30s for timeouts
                    self.logger.warning(
                        f"Request timeout. Waiting {delay} seconds before retry {attempt + 1}/{max_retries}"
                    )
                    time.sleep(delay)
                    continue
                else:
                    error_msg = f"Failed to fetch page: {e}"
                    if "403" in str(e):
                        error_msg += (
                            " - Authentication required. Please update cookies."
                        )
                    elif "429" in str(e):
                        error_msg += " - Rate limited. Increase check interval."
                    self.logger.error(f"Request failed: {e}")
                    return {
                        "timestamp": datetime.now().isoformat(),
                        "status": "ERROR",
                        "message": error_msg,
                        "ticket_count": 0,
                        "url": self.event_url,
                    }
            except Exception as e:
                if attempt < max_retries:
                    delay = 10 * (attempt + 1)
                    self.logger.warning(
                        f"Unexpected error. Waiting {delay} seconds before retry {attempt + 1}/{max_retries}"
                    )
                    time.sleep(delay)
                    continue
                else:
                    self.logger.error(f"Unexpected error: {e}")
                    return {
                        "timestamp": datetime.now().isoformat(),
                        "status": "ERROR",
                        "message": f"Unexpected error: {e}",
                        "ticket_count": 0,
                        "url": self.event_url,
                    }

        # If we get here, the request was successful
        try:
            soup = BeautifulSoup(response.content, "html.parser")

            # Look for the specific "sold out/reserved" message in Danish
            # sold_out_message = "solgt eller reserveret. Hvis en anden kunde afbryder sit køb, kan reservationen muligvis frigives igen."

            # Also check for the general "no tickets" message
            no_tickets_text = "Der findes ingen billetter til salg"
            no_tickets_text_en = "No tickets for sale exists"

            page_text = soup.get_text()

            # Check if tickets are sold out/reserved
            # if sold_out_message in page_text:
            #     status = "NO_TICKETS"
            #     message = "All tickets are sold or reserved"
            if no_tickets_text in page_text:
                status = "NO_TICKETS"
                message = "No tickets available for sale"
            else:
                # If neither "sold out" message is present, tickets might be available
                # Look for ticket listings or sale sections to confirm
                ticket_sections = soup.find_all(
                    ["div", "section"],
                    string=lambda text: text and "billet" in text.lower(),
                )

                # Look for price indicators (DKK, kr, etc.)
                price_indicators = soup.find_all(
                    string=lambda text: text
                    and ("kr" in text.lower() or "dkk" in text.lower())
                )

                if ticket_sections or price_indicators:
                    status = "TICKETS_AVAILABLE"
                    message = "🎫 Tickets are available! Check the website now!"
                else:
                    status = "TICKETS_AVAILABLE"
                    message = (
                        "🎫 No 'sold out' message found - tickets may be available!"
                    )

            # Count any visible ticket listings
            ticket_count = self.count_ticket_listings(soup)

            result = {
                "timestamp": datetime.now().isoformat(),
                "status": status,
                "message": message,
                "ticket_count": ticket_count,
                "url": self.event_url,
            }

            return result

        except Exception as e:
            self.logger.error(f"Error parsing response: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "ERROR",
                "message": f"Error parsing response: {e}",
                "ticket_count": 0,
                "url": self.event_url,
            }

    def count_ticket_listings(self, soup):
        """
        Try to count actual ticket listings on the page

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            int: Number of ticket listings found
        """
        # Look for common patterns that might indicate ticket listings
        ticket_patterns = ["ticket-item", "ticket-listing", "billet-item", "sale-item"]

        count = 0
        for pattern in ticket_patterns:
            elements = soup.find_all(class_=lambda x: x and pattern in x)
            count += len(elements)

        # Also look for table rows that might contain ticket data
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            # Skip header row, count data rows
            if len(rows) > 1:
                count += len(rows) - 1

        return count

    def send_email_notification(self, result):
        """
        Send email notification if configured

        Args:
            result (dict): Result from ticket check
        """
        if not self.config.get("email"):
            return

        try:
            smtp_config = self.config["email"]

            msg = MIMEMultipart()
            msg["From"] = smtp_config["from_email"]
            msg["To"] = smtp_config["to_email"]
            msg["Subject"] = f"Sportstiming Ticket Alert - {result['status']}"

            body = f"""
Ticket Check Results:

Status: {result['status']}
Message: {result['message']}
Ticket Count: {result['ticket_count']}
Time: {result['timestamp']}
URL: {result['url']}

This is an automated message from your Sportstiming ticket checker.
            """

            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(smtp_config["smtp_server"], smtp_config["smtp_port"])
            server.starttls()
            server.login(smtp_config["username"], smtp_config["password"])
            text = msg.as_string()
            server.sendmail(smtp_config["from_email"], smtp_config["to_email"], text)
            server.quit()

            self.logger.info("Email notification sent successfully")

        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")

    def send_sms_notification(self, result):
        """
        Send SMS notification using Twilio

        Args:
            result (dict): Result from ticket check
        """
        if not self.config.get("sms"):
            return

        try:
            from twilio.rest import Client

            sms_config = self.config["sms"]
            client = Client(sms_config["account_sid"], sms_config["auth_token"])

            message_body = f"""🎫 Sportstiming Alert!

Status: {result['status']}
{result['message']}

Check: {result['url']}
Time: {result['timestamp'][:19]}"""

            message = client.messages.create(
                body=message_body,
                from_=sms_config["from_number"],
                to=sms_config["to_number"],
            )

            self.logger.info(f"SMS notification sent successfully (SID: {message.sid})")

        except ImportError:
            self.logger.error("Twilio library not installed. Run: pip install twilio")
        except Exception as e:
            self.logger.error(f"Failed to send SMS notification: {e}")

    def send_telegram_notification(self, result):
        """
        Send Telegram notification

        Args:
            result (dict): Result from ticket check
        """
        if not self.config.get("telegram"):
            self.logger.warning("Telegram configuration not found in config")
            return

        try:
            telegram_config = self.config["telegram"]
            bot_token = telegram_config.get("bot_token")
            chat_ids = telegram_config.get("chat_id")

            if not bot_token:
                self.logger.error("Telegram bot_token not found in config")
                return

            if not chat_ids:
                self.logger.error("Telegram chat_id not found in config")
                return

            # Support both single chat_id and multiple chat_ids
            if isinstance(chat_ids, str) or isinstance(chat_ids, int):
                chat_ids = [str(chat_ids)]
            elif isinstance(chat_ids, list):
                chat_ids = [str(chat_id) for chat_id in chat_ids]
            else:
                self.logger.error("Telegram chat_id must be a string, number, or list")
                return

            self.logger.info(
                f"Sending Telegram notification to {len(chat_ids)} chat(s)"
            )

            # Escape special characters for Markdown
            def escape_markdown(text):
                """Escape special characters for Telegram Markdown"""
                special_chars = [
                    "_",
                    "*",
                    "[",
                    "]",
                    "(",
                    ")",
                    "~",
                    "`",
                    ">",
                    "#",
                    "+",
                    "-",
                    "=",
                    "|",
                    "{",
                    "}",
                    ".",
                    "!",
                ]
                for char in special_chars:
                    text = text.replace(char, f"\\{char}")
                return text

            # Create the message with proper escaping
            status = escape_markdown(result["status"])
            message = escape_markdown(result["message"])
            timestamp = escape_markdown(result["timestamp"][:19])

            message_text = f"""🎫 *Sportstiming Ticket Alert*

*Status:* {status}
*Message:* {message}
*Ticket Count:* {result['ticket_count']}
*Time:* {timestamp}

[Check Website]({result['url']})"""

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

            success_count = 0
            failed_chats = []

            # Send to each chat ID
            for chat_id in chat_ids:
                try:
                    payload = {
                        "chat_id": chat_id,
                        "text": message_text,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": False,
                    }

                    self.logger.debug(f"Sending to chat_id: {chat_id}")
                    response = requests.post(url, json=payload, timeout=10)

                    self.logger.debug(f"Response for {chat_id}: {response.status_code}")

                    response.raise_for_status()
                    response_data = response.json()

                    if response_data.get("ok"):
                        self.logger.info(
                            f"✅ Message sent successfully to chat {chat_id}"
                        )
                        success_count += 1
                    else:
                        self.logger.error(
                            f"❌ Telegram API error for chat {chat_id}: {response_data}"
                        )
                        failed_chats.append(chat_id)

                except requests.exceptions.RequestException as e:
                    self.logger.error(
                        f"❌ Network error sending to chat {chat_id}: {e}"
                    )
                    failed_chats.append(chat_id)
                except Exception as e:
                    self.logger.error(f"❌ Error sending to chat {chat_id}: {e}")
                    failed_chats.append(chat_id)

            # Summary
            if success_count > 0:
                self.logger.info(
                    f"Telegram notifications sent successfully to {success_count}/{len(chat_ids)} chats"
                )

            if failed_chats:
                self.logger.warning(f"Failed to send to chats: {failed_chats}")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error sending Telegram notification: {e}")
        except KeyError as e:
            self.logger.error(f"Missing Telegram configuration key: {e}")
        except Exception as e:
            self.logger.error(f"Failed to send Telegram notification: {e}")

    def test_telegram_notification(self):
        """
        Test Telegram notification with a sample message
        """
        if not self.config.get("telegram"):
            self.logger.error(
                "Telegram configuration not found. Please check your config file."
            )
            return False

        test_result = {
            "timestamp": datetime.now().isoformat(),
            "status": "TEST",
            "message": "This is a test notification from your ticket checker",
            "ticket_count": 0,
            "url": self.event_url,
        }

        self.logger.info("Sending test Telegram notification...")
        self.send_telegram_notification(test_result)
        return True

    def test_all_notifications(self):
        """
        Test all configured notification methods
        """
        test_result = {
            "timestamp": datetime.now().isoformat(),
            "status": "TEST",
            "message": "This is a test notification from your ticket checker",
            "ticket_count": 0,
            "url": self.event_url,
        }

        self.logger.info("Sending test notifications...")
        self.send_notifications(test_result, force=True)
        return True

    def get_telegram_bot_info(self):
        """
        Get information about the Telegram bot to verify configuration
        """
        if not self.config.get("telegram"):
            self.logger.error("Telegram configuration not found")
            return None

        try:
            telegram_config = self.config["telegram"]
            bot_token = telegram_config.get("bot_token")

            if not bot_token:
                self.logger.error("Bot token not found in config")
                return None

            url = f"https://api.telegram.org/bot{bot_token}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            bot_info = response.json()
            if bot_info.get("ok"):
                bot_data = bot_info["result"]
                self.logger.info(
                    f"Bot info: {bot_data['first_name']} (@{bot_data.get('username', 'N/A')})"
                )
                return bot_data
            else:
                self.logger.error(f"Failed to get bot info: {bot_info}")
                return None

        except Exception as e:
            self.logger.error(f"Error getting bot info: {e}")
            return None

    def get_telegram_chat_info(self):
        """
        Get information about the Telegram chat to verify chat_id
        """
        if not self.config.get("telegram"):
            self.logger.error("Telegram configuration not found")
            return None

        try:
            telegram_config = self.config["telegram"]
            bot_token = telegram_config.get("bot_token")
            chat_id = telegram_config.get("chat_id")

            if not bot_token or not chat_id:
                self.logger.error("Bot token or chat_id not found in config")
                return None

            url = f"https://api.telegram.org/bot{bot_token}/getChat"
            payload = {"chat_id": chat_id}
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            chat_info = response.json()
            if chat_info.get("ok"):
                chat_data = chat_info["result"]
                self.logger.info(
                    f"Chat info: {chat_data.get('title', chat_data.get('first_name', 'Private chat'))}"
                )
                return chat_data
            else:
                self.logger.error(f"Failed to get chat info: {chat_info}")
                return None

        except Exception as e:
            self.logger.error(f"Error getting chat info: {e}")
            return None

    def send_pushover_notification(self, result):
        """
        Send Pushover notification (popular push notification service)

        Args:
            result (dict): Result from ticket check
        """
        if not self.config.get("pushover"):
            return

        try:
            pushover_config = self.config["pushover"]

            payload = {
                "token": pushover_config["app_token"],
                "user": pushover_config["user_key"],
                "title": f"🎫 Sportstiming Alert - {result['status']}",
                "message": f"{result['message']}\n\nTickets: {result['ticket_count']}\nTime: {result['timestamp'][:19]}",
                "url": result["url"],
                "url_title": "Check Website",
                "priority": 1 if result["status"] == "TICKETS_AVAILABLE" else 0,
            }

            response = requests.post(
                "https://api.pushover.net/1/messages.json", data=payload, timeout=10
            )
            response.raise_for_status()

            self.logger.info("Pushover notification sent successfully")

        except Exception as e:
            self.logger.error(f"Failed to send Pushover notification: {e}")

    def send_notifications(self, result, force=False, dry_run=False):
        """
        Send all configured notifications

        Args:
            result (dict): Result from ticket check
            force (bool): Force sending notifications regardless of status
            dry_run (bool): Log what would be sent without actually sending
        """
        should_send = (
            force or result["status"] == "TICKETS_AVAILABLE" or self.notify_all_statuses
        )

        if should_send:
            if dry_run:
                self.logger.info("🧪 DRY RUN - Would send notifications:")
                if self.config.get("email"):
                    self.logger.info("   📧 Email notification (configured)")
                if self.config.get("sms"):
                    self.logger.info("   📱 SMS notification (configured)")
                if self.config.get("telegram"):
                    self.logger.info("   💬 Telegram notification (configured)")
                if self.config.get("pushover"):
                    self.logger.info("   📲 Pushover notification (configured)")
                return

            # Send email if configured
            self.send_email_notification(result)

            # Send SMS if configured
            self.send_sms_notification(result)

            # Send Telegram if configured
            self.send_telegram_notification(result)

            # Send Pushover if configured
            self.send_pushover_notification(result)
        else:
            if dry_run:
                self.logger.debug(
                    f"🧪 DRY RUN - No notifications would be sent for status: {result['status']}"
                )
            else:
                self.logger.debug(
                    f"Not sending notifications for status: {result['status']}"
                )

    def run_single_check(self):
        """Run a single check and return the result"""
        self.logger.info("Checking for available tickets...")
        result = self.check_tickets_available()

        self.logger.info(f"Status: {result['status']} - {result['message']}")
        if result["ticket_count"] > 0:
            self.logger.info(
                f"Found {result['ticket_count']} potential ticket listings"
            )

        # Note: Notifications are handled by the calling method (run_continuous_monitoring)
        # Only send notifications here if explicitly called from command line with --single
        return result

    def run_continuous_monitoring(self):
        """Run continuous monitoring with specified interval"""
        self.logger.info(
            f"Starting continuous monitoring every {self.check_interval} seconds"
        )
        self.logger.info(f"Monitoring URL: {self.event_url}")

        if self.notify_all_statuses:
            self.logger.info("📢 Notifications enabled for ALL statuses")
        else:
            self.logger.info("📢 Notifications only for TICKETS_AVAILABLE status")

        if self.dry_run:
            self.logger.info(
                "🧪 DRY RUN MODE - Notifications will be logged but not actually sent"
            )

        # Add rate limiting protection
        if self.check_interval < 60:
            self.logger.warning(
                f"⚠️  Check interval ({self.check_interval}s) is quite frequent. Consider using 60s+ to avoid rate limiting."
            )

        last_status = None
        consecutive_same_status = 0  # Track how many times we've seen the same status

        try:
            while True:
                result = self.run_single_check()
                current_status = result["status"]

                # Track consecutive status occurrences
                if current_status == last_status:
                    consecutive_same_status += 1
                else:
                    consecutive_same_status = 1

                # Handle rate limiting
                if current_status == "RATE_LIMITED":
                    self.logger.warning(
                        "🚨 Rate limited! Increasing delay to avoid further rate limiting..."
                    )
                    # Temporarily increase interval for rate limited responses
                    extended_delay = max(
                        self.check_interval * 2, 300
                    )  # At least 5 minutes
                    self.logger.info(
                        f"Using extended delay of {extended_delay} seconds due to rate limiting"
                    )

                    # Add random component to avoid synchronized requests
                    jitter = random.randint(30, 120)  # 30-120 second random delay
                    total_delay = extended_delay + jitter

                    self.logger.info(
                        f"Next check in {total_delay} seconds (extended + {jitter}s jitter)"
                    )
                    time.sleep(total_delay)
                    continue

                # Determine if we should send a notification
                should_send_notification = False
                notification_reason = ""

                if self.notify_all_statuses:
                    # Send notification only when status changes (not for repeated same status)
                    if current_status != last_status:
                        should_send_notification = True
                        notification_reason = (
                            f"Status changed: {last_status} → {current_status}"
                        )
                    else:
                        self.logger.debug(
                            f"Status unchanged: {current_status} (seen {consecutive_same_status} times)"
                        )
                else:
                    # Simple logic: Only notify for TICKETS_AVAILABLE if previous status was NOT TICKETS_AVAILABLE
                    if (
                        current_status == "TICKETS_AVAILABLE"
                        and last_status != "TICKETS_AVAILABLE"
                    ):
                        should_send_notification = True
                        notification_reason = (
                            f"🎫 Tickets became available! (was: {last_status})"
                        )
                    else:
                        self.logger.debug(
                            f"No notification needed: {current_status} (previous: {last_status})"
                        )

                # Send notification if needed
                if should_send_notification:
                    self.logger.info(notification_reason)
                    self.send_notifications(result, dry_run=self.dry_run)
                    notification_type = "DRY RUN" if self.dry_run else "ACTUAL"
                    self.logger.info(
                        f"📤 {notification_type} notification sent for status: {current_status}"
                    )
                else:
                    self.logger.debug(
                        f"🔇 No notification sent - status: {current_status} (consecutive: {consecutive_same_status})"
                    )

                last_status = current_status

                # Add some jitter to prevent synchronized requests
                base_interval = self.check_interval
                jitter = random.randint(-30, 30)  # ±30 seconds random variation
                actual_interval = max(base_interval + jitter, 30)  # Minimum 30 seconds

                self.logger.info(f"Next check in {actual_interval} seconds...")
                time.sleep(actual_interval)

        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")

    def troubleshoot_telegram(self):
        """
        Comprehensive Telegram troubleshooting guide
        """
        print("🔧 Telegram Troubleshooting Guide")
        print("=" * 40)

        # Check if config exists
        if not self.config:
            print("❌ No configuration file loaded")
            print("   Please specify a config file with --config path/to/config.json")
            print("   Or create one with --create-config")
            return False

        # Check if telegram section exists
        if not self.config.get("telegram"):
            print("❌ No Telegram configuration found in config file")
            print("   Please add a 'telegram' section to your config.json:")
            print('   "telegram": {')
            print('     "bot_token": "your_bot_token_here",')
            print('     "chat_id": "your_chat_id_here"')
            print("   }")
            return False

        telegram_config = self.config["telegram"]

        # Check bot token
        bot_token = telegram_config.get("bot_token")
        if not bot_token:
            print("❌ Bot token not found in config")
            print("   Please add your bot token to the config file")
            print("   Get a bot token from @BotFather on Telegram")
            return False

        if bot_token == "your_bot_token_from_botfather":
            print("❌ Bot token is still the placeholder value")
            print("   Please replace with your actual bot token from @BotFather")
            return False

        print("✅ Bot token found in config")

        # Test bot token
        print("\n📡 Testing bot token...")
        bot_info = self.get_telegram_bot_info()
        if not bot_info:
            print("❌ Bot token is invalid or bot is not accessible")
            print("   Please check your bot token with @BotFather")
            return False

        print(
            f"✅ Bot is valid: {bot_info['first_name']} (@{bot_info.get('username', 'N/A')})"
        )

        # Check chat ID
        chat_id = telegram_config.get("chat_id")
        if not chat_id:
            print("❌ Chat ID not found in config")
            print("   Please add your chat ID to the config file")
            print("   To find your chat ID:")
            print("   1. Send a message to your bot")
            print(
                "   2. Visit: https://api.telegram.org/bot{}/getUpdates".format(
                    bot_token
                )
            )
            print("   3. Look for 'id' in the 'chat' section")
            print("\n   💡 For multiple people, you can use:")
            print('   "chat_id": ["your_chat_id", "friend_chat_id"]')
            print("   Or create a group and add the bot to it")
            return False

        if chat_id == "your_chat_id_or_channel_id":
            print("❌ Chat ID is still the placeholder value")
            print("   Please replace with your actual chat ID")
            return False

        # Handle multiple chat IDs
        if isinstance(chat_id, list):
            print(f"✅ Found {len(chat_id)} chat IDs in config")
            chat_ids_to_test = chat_id
        else:
            print("✅ Chat ID found in config")
            chat_ids_to_test = [chat_id]

        # Test each chat ID
        print("\n📡 Testing chat access...")
        accessible_chats = []
        failed_chats = []

        for idx, test_chat_id in enumerate(chat_ids_to_test):
            print(f"   Testing chat {idx + 1}/{len(chat_ids_to_test)}: {test_chat_id}")

            # Temporarily set single chat ID for testing
            original_chat_id = telegram_config["chat_id"]
            telegram_config["chat_id"] = test_chat_id

            chat_info = self.get_telegram_chat_info()

            if chat_info:
                chat_name = chat_info.get(
                    "title", chat_info.get("first_name", "Private chat")
                )
                print(f"   ✅ Chat accessible: {chat_name}")
                accessible_chats.append((test_chat_id, chat_name))
            else:
                print(f"   ❌ Cannot access chat: {test_chat_id}")
                failed_chats.append(test_chat_id)

            # Restore original config
            telegram_config["chat_id"] = original_chat_id

        if failed_chats:
            print(f"\n❌ Cannot access {len(failed_chats)} chat(s)")
            print("   Possible issues:")
            print("   - Chat ID is incorrect")
            print("   - Bot is not added to the chat/channel")
            print("   - Bot doesn't have permission to send messages")
            print("   - User hasn't started the bot (for private chats)")
            print(f"   Failed chats: {failed_chats}")

        if not accessible_chats:
            return False

        # Send test message
        print("\n📤 Sending test message...")
        test_success = self.test_telegram_notification()

        if test_success:
            print("✅ Test message sent successfully!")
            print("   Check your Telegram app for the test message")
        else:
            print("❌ Failed to send test message")
            print("   Check the logs above for error details")

        print("\n🎯 Summary:")
        print(f"   Bot: {bot_info['first_name']} (@{bot_info.get('username', 'N/A')})")
        print(f"   Chat: {accessible_chats[0][1]}")
        print(f"   Chat ID: {accessible_chats[0][0]}")
        print(f"   Test message: {'✅ Success' if test_success else '❌ Failed'}")

        if test_success:
            print("\n🎉 Telegram notifications are working correctly!")
        else:
            print("\n⚠️  Please fix the issues above and try again")

        return test_success

    def get_telegram_updates(self):
        """
        Get recent Telegram updates to help find chat IDs
        """
        if not self.config.get("telegram"):
            self.logger.error("Telegram configuration not found")
            return None

        try:
            telegram_config = self.config["telegram"]
            bot_token = telegram_config.get("bot_token")

            if not bot_token:
                self.logger.error("Bot token not found in config")
                return None

            url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            updates = response.json()
            if updates.get("ok"):
                return updates["result"]
            else:
                self.logger.error(f"Failed to get updates: {updates}")
                return None

        except Exception as e:
            self.logger.error(f"Error getting updates: {e}")
            return None

    def find_chat_ids(self):
        """
        Find and display all chat IDs from recent messages
        """
        print("🔍 Finding Chat IDs from Recent Messages")
        print("=" * 45)

        updates = self.get_telegram_updates()
        if not updates:
            print("❌ Could not get updates from Telegram")
            return

        if not updates:
            print("📭 No recent messages found")
            print("💡 Send a message to your bot or in your group, then try again")
            return

        found_chats = {}

        for update in updates:
            if "message" in update:
                message = update["message"]
                chat = message["chat"]
                chat_id = chat["id"]
                chat_type = chat["type"]

                # Get chat name/title
                if chat_type == "private":
                    name = f"{chat.get('first_name', '')} {chat.get('last_name', '')}".strip()
                    if not name:
                        name = chat.get("username", "Unknown User")
                elif chat_type in ["group", "supergroup"]:
                    name = chat.get("title", "Unknown Group")
                elif chat_type == "channel":
                    name = chat.get("title", "Unknown Channel")
                else:
                    name = f"Unknown ({chat_type})"

                found_chats[chat_id] = {
                    "name": name,
                    "type": chat_type,
                    "message_text": (
                        message.get("text", "")[:50] + "..."
                        if len(message.get("text", "")) > 50
                        else message.get("text", "")
                    ),
                    "from_user": message.get("from", {}).get("first_name", "Unknown"),
                }

        if not found_chats:
            print("📭 No chat messages found in recent updates")
            print("💡 Make sure to:")
            print("   1. Add your bot to the group")
            print("   2. Send a message in the group")
            print("   3. Run this command again")
            return

        print(f"📬 Found {len(found_chats)} chat(s) with recent messages:\n")

        for chat_id, info in found_chats.items():
            print(f"💬 Chat ID: {chat_id}")
            print(f"   📛 Name: {info['name']}")
            print(f"   🏷️  Type: {info['type']}")
            print(f"   👤 Last message from: {info['from_user']}")
            if info["message_text"]:
                print(f"   💭 Last message: \"{info['message_text']}\"")
            print()

        # Provide copy-paste ready config
        if len(found_chats) == 1:
            chat_id = list(found_chats.keys())[0]
            print("📋 Copy this to your config.json:")
            print(f'   "chat_id": "{chat_id}"')
        else:
            all_ids = list(found_chats.keys())
            print("📋 Copy this to your config.json:")
            print("   For a single chat:")
            for chat_id in all_ids:
                print(f'     "chat_id": "{chat_id}"  # {found_chats[chat_id]["name"]}')
            print("\n   For all chats:")
            ids_str = ", ".join([f'"{chat_id}"' for chat_id in all_ids])
            print(f'     "chat_id": [{ids_str}]')

        return found_chats


def create_sample_config():
    """Create a sample configuration file with all notification options"""
    config = {
        "email": {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "your_email@gmail.com",
            "password": "your_app_password",
            "from_email": "your_email@gmail.com",
            "to_email": "notification_recipient@gmail.com",
        },
        "sms": {
            "account_sid": "your_twilio_account_sid",
            "auth_token": "your_twilio_auth_token",
            "from_number": "+1234567890",
            "to_number": "+1987654321",
        },
        "telegram": {
            "bot_token": "your_bot_token_from_botfather",
            "chat_id": "your_chat_id_or_channel_id",
            "_note": 'For multiple people, use: "chat_id": ["123456789", "987654321"] or create a group/channel',
        },
        "pushover": {
            "app_token": "your_pushover_app_token",
            "user_key": "your_pushover_user_key",
        },
    }

    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)

    print("Sample config.json created with all notification options.")
    print("\nTelegram Setup Options:")
    print("🔹 Option 1 - Single person:")
    print('   "chat_id": "123456789"')
    print("\n🔹 Option 2 - Multiple people:")
    print('   "chat_id": ["123456789", "987654321", "555555555"]')
    print("\n🔹 Option 3 - Group/Channel (recommended for multiple people):")
    print("   1. Create a Telegram group")
    print("   2. Add your bot to the group")
    print("   3. Send a message in the group")
    print("   4. Visit: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates")
    print("   5. Use the group's chat ID (usually negative number)")
    print("\nSetup instructions:")
    print("1. Choose which notification method(s) you want to use")
    print("2. Remove unused sections from config.json")
    print("3. Fill in your credentials for the chosen method(s)")
    print("4. Run --troubleshoot-telegram to verify setup")


def main():
    parser = argparse.ArgumentParser(description="Sportstiming Ticket Checker Bot")
    parser.add_argument(
        "--url",
        default="https://www.sportstiming.dk/event/6583/resale",
        help="URL to check for tickets",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Check interval in seconds (default: 300, minimum recommended: 60 to avoid rate limiting)",
    )
    parser.add_argument("--config", help="Path to config file for notifications")
    parser.add_argument(
        "--single",
        action="store_true",
        help="Run single check instead of continuous monitoring",
    )
    parser.add_argument(
        "--create-config", action="store_true", help="Create sample configuration file"
    )
    parser.add_argument(
        "--test-telegram",
        action="store_true",
        help="Test Telegram notification configuration",
    )
    parser.add_argument(
        "--test-notifications",
        action="store_true",
        help="Test all configured notification methods",
    )
    parser.add_argument(
        "--telegram-info",
        action="store_true",
        help="Get Telegram bot and chat information",
    )
    parser.add_argument(
        "--troubleshoot-telegram",
        action="store_true",
        help="Run comprehensive Telegram troubleshooting guide",
    )
    parser.add_argument(
        "--find-chat-ids",
        action="store_true",
        help="Find chat IDs from recent Telegram messages",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging for detailed output",
    )
    parser.add_argument(
        "--notify-all",
        action="store_true",
        help="Send notifications for all statuses, not just when tickets are available",
    )
    parser.add_argument(
        "--update-cookies",
        action="store_true",
        help="Update cookies for authentication (interactive)",
    )
    parser.add_argument(
        "--auth-token",
        help="Set the st-auth-s2 authentication token",
    )
    parser.add_argument(
        "--session-id",
        help="Set the st-sessionids2 session ID",
    )
    parser.add_argument(
        "--show-env",
        action="store_true",
        help="Show current environment variables for authentication",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run monitoring without sending actual notifications (for testing)",
    )

    args = parser.parse_args()

    if args.create_config:
        create_sample_config()
        return

    if args.show_env:
        print("🔍 Environment Variables Status")
        print("=" * 35)

        auth_token = os.getenv("ST_AUTH_TOKEN")
        session_id = os.getenv("ST_SESSION_ID")

        if auth_token:
            print(f"✅ ST_AUTH_TOKEN: {auth_token[:30]}...")
            print(f"   Length: {len(auth_token)} characters")
        else:
            print("❌ ST_AUTH_TOKEN: Not set")

        if session_id:
            print(f"✅ ST_SESSION_ID: {session_id}")
        else:
            print("❌ ST_SESSION_ID: Not set")

        if not auth_token and not session_id:
            print("\n💡 To set environment variables:")
            print("   export ST_AUTH_TOKEN='your_token_here'")
            print("   export ST_SESSION_ID='your_session_id_here'")
            print("\n📖 See RAILWAY_SETUP.md for detailed instructions")
        else:
            print(
                f"\n🎯 Authentication: {'✅ Ready' if (auth_token and session_id) else '⚠️ Partial'}"
            )

        return

    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    checker = SportstimingTicketChecker(
        event_url=args.url,
        check_interval=args.interval,
        config_file=args.config,
        notify_all_statuses=args.notify_all,
        dry_run=args.dry_run,
    )

    # Handle cookie updates
    if args.auth_token or args.session_id:
        # Command-line arguments override environment variables
        checker.update_cookies(auth_token=args.auth_token, session_id=args.session_id)
        print("✅ Cookies updated from command line arguments")
        if (
            not args.single
            and not args.find_chat_ids
            and not args.troubleshoot_telegram
        ):
            print("Running single check to test authentication...")
            result = checker.run_single_check()
            # Send notifications for single checks if tickets are available
            if result["status"] == "TICKETS_AVAILABLE":
                checker.send_notifications(result, dry_run=checker.dry_run)
            print(json.dumps(result, indent=2))
            return

    # Check if environment variables are set
    env_auth_token = os.getenv("ST_AUTH_TOKEN")
    env_session_id = os.getenv("ST_SESSION_ID")

    if env_auth_token or env_session_id:
        print("🔐 Using authentication from environment variables:")
        if env_auth_token:
            print(f"   ✅ ST_AUTH_TOKEN: {env_auth_token[:20]}...")
        if env_session_id:
            print(f"   ✅ ST_SESSION_ID: {env_session_id}")
        print()

    if args.update_cookies:
        print("🔐 Interactive Cookie Update")
        print("=" * 30)
        print("To get these values from your browser:")
        print("1. Go to https://www.sportstiming.dk/event/6583/resale")
        print("2. Open Developer Tools (F12)")
        print("3. Go to Network tab")
        print("4. Refresh the page")
        print("5. Click on the first request to the page")
        print("6. Look for 'Cookie' in the Request Headers")
        print("7. Copy the values for st-auth-s2 and st-sessionids2")
        print()

        auth_token = input("Enter st-auth-s2 token (or press Enter to skip): ").strip()
        session_id = input(
            "Enter st-sessionids2 session ID (or press Enter to skip): "
        ).strip()

        if auth_token or session_id:
            checker.update_cookies(
                auth_token=auth_token if auth_token else None,
                session_id=session_id if session_id else None,
            )
            print("✅ Cookies updated successfully")
            print("Running test check...")
            result = checker.run_single_check()
            # Send notifications for single checks if tickets are available
            if result["status"] == "TICKETS_AVAILABLE":
                checker.send_notifications(result, dry_run=checker.dry_run)
            print(json.dumps(result, indent=2))
        else:
            print("❌ No cookies provided")
        return

    if args.test_telegram:
        checker.test_telegram_notification()
        return

    if args.test_notifications:
        checker.test_all_notifications()
        return

    if args.telegram_info:
        print("Getting Telegram bot information...")
        bot_info = checker.get_telegram_bot_info()
        if bot_info:
            print(
                f"✅ Bot found: {bot_info['first_name']} (@{bot_info.get('username', 'N/A')})"
            )

        print("\nGetting Telegram chat information...")
        chat_info = checker.get_telegram_chat_info()
        if chat_info:
            chat_name = chat_info.get(
                "title", chat_info.get("first_name", "Private chat")
            )
            print(f"✅ Chat found: {chat_name}")
            print(f"   Chat ID: {chat_info['id']}")
            print(f"   Chat Type: {chat_info['type']}")

        return

    if args.troubleshoot_telegram:
        checker.troubleshoot_telegram()
        return

    if args.find_chat_ids:
        found_chats = checker.find_chat_ids()
        if found_chats:
            print("\n🎉 Chat IDs found successfully!")
            print("📋 Copy these to your config.json:")
            for chat_id, info in found_chats.items():
                print(f'   "chat_id": "{chat_id}"  # {info["name"]}')
        else:
            print("\n📭 No chat IDs found")
        return

    if args.single:
        result = checker.run_single_check()
        # Send notifications for single checks if tickets are available
        if result["status"] == "TICKETS_AVAILABLE":
            checker.send_notifications(result, dry_run=checker.dry_run)
        print(json.dumps(result, indent=2))
    else:
        checker.run_continuous_monitoring()


if __name__ == "__main__":
    main()
