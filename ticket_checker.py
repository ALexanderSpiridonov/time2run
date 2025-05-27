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
        ticket_id_range=None,
        specific_ticket_ids=None,
    ):
        """
        Initialize the ticket checker

        Args:
            event_url (str): The URL to check for tickets
            check_interval (int): Time between checks in seconds (default: 5 minutes)
            config_file (str): Path to config file for notifications
            notify_all_statuses (bool): Send notifications for all statuses, not just when tickets are available
            ticket_id_range (tuple): Tuple of (start_id, end_id) for checking specific ticket IDs
            specific_ticket_ids (list): List of specific ticket IDs to check
        """
        self.event_url = event_url
        self.check_interval = check_interval
        self.config_file = config_file
        self.config = self.load_config() if config_file else {}
        self.notify_all_statuses = notify_all_statuses
        self.ticket_id_range = ticket_id_range
        self.specific_ticket_ids = specific_ticket_ids

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

        # User agent to appear as a regular browser
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "da-DK,da;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "DNT": "1",
            "Sec-CH-UA": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"macOS"',
        }

        # Create a session for better connection handling and cookie persistence
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # Initialize session by visiting main page
        self._initialize_session()

    def _initialize_session(self):
        """Initialize session by visiting the main resale page to establish cookies"""
        try:
            main_url = "https://www.sportstiming.dk/event/6583/resale"
            self.logger.debug("Initializing session with main page visit")
            response = self.session.get(main_url, timeout=10)
            if response.status_code == 200:
                self.logger.debug("Session initialized successfully")
            else:
                self.logger.warning(
                    f"Session initialization returned status {response.status_code}"
                )
        except Exception as e:
            self.logger.warning(f"Failed to initialize session: {e}")

    def load_config(self):
        """Load configuration from JSON file"""
        if self.config_file and os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                return json.load(f)
        return {}

    def check_individual_ticket(self, ticket_id):
        """
        Check if a specific ticket ID is available for purchase

        Args:
            ticket_id (int): The ticket ID to check

        Returns:
            dict: Dictionary with status and details for this specific ticket
        """
        base_url = "https://www.sportstiming.dk/event/6583/resale/ticket"
        ticket_url = f"{base_url}/{ticket_id}"

        # Try multiple strategies to avoid 403 errors
        strategies = [
            {"timeout": 10, "delay": 0},  # First try - normal
            {"timeout": 15, "delay": 2},  # Second try - with delay
            {"timeout": 20, "delay": 5},  # Third try - longer delay
        ]

        for attempt, strategy in enumerate(strategies, 1):
            try:
                if strategy["delay"] > 0:
                    self.logger.debug(
                        f"Waiting {strategy['delay']} seconds before retry {attempt}"
                    )
                    time.sleep(strategy["delay"])

                response = self.session.get(
                    ticket_url,
                    timeout=strategy["timeout"],
                    allow_redirects=True,
                )

                # Handle 403 Forbidden specifically
                if response.status_code == 403:
                    self.logger.warning(
                        f"403 Forbidden for ticket {ticket_id} (attempt {attempt})"
                    )
                    if attempt < len(strategies):
                        continue  # Try next strategy
                    else:
                        # After all attempts, treat 403 as "not available"
                        return {
                            "timestamp": datetime.now().isoformat(),
                            "status": "NO_TICKETS",
                            "message": f"Ticket {ticket_id} access forbidden (likely not available or protected)",
                            "ticket_id": ticket_id,
                            "url": ticket_url,
                        }

                # Handle other HTTP errors
                if response.status_code == 404:
                    return {
                        "timestamp": datetime.now().isoformat(),
                        "status": "NO_TICKETS",
                        "message": f"Ticket {ticket_id} not found (404)",
                        "ticket_id": ticket_id,
                        "url": ticket_url,
                    }

                response.raise_for_status()  # Raise for other HTTP errors

                # Success - parse the content
                soup = BeautifulSoup(response.content, "html.parser")
                page_text = soup.get_text()

                # The specific Danish message indicating ticket is not available
                unavailable_message = "Det er p.t. ikke muligt at foretage dette valg, da alt enten er solgt eller reserveret. Hvis en anden kunde afbryder sit køb, kan reservationen muligvis frigives igen."

                # Also check for English version
                unavailable_message_en = "It is currently not possible to make this choice, as everything is either sold or reserved. If another customer cancels their purchase, the reservation may possibly be released again."

                # Check for expired/cancelled tickets
                expired_messages = [
                    "completed or has been cancelled",
                    "expired",
                    "cancelled",
                    "afsluttet",
                    "annulleret",
                ]

                # Debug logging
                if self.logger.isEnabledFor(logging.DEBUG):
                    self.logger.debug(
                        f"Page content for ticket {ticket_id}: {page_text[:500]}..."
                    )
                    self.logger.debug(f"Looking for unavailable message in content...")
                    if unavailable_message in page_text:
                        self.logger.debug("Found Danish unavailable message")
                    if unavailable_message_en in page_text:
                        self.logger.debug("Found English unavailable message")

                # Check if ticket is expired/cancelled
                is_expired = any(
                    exp_msg.lower() in page_text.lower() for exp_msg in expired_messages
                )

                if (
                    unavailable_message in page_text
                    or unavailable_message_en in page_text
                ):
                    status = "NO_TICKETS"
                    message = f"Ticket {ticket_id} is sold or reserved"
                elif is_expired:
                    status = "NO_TICKETS"
                    message = f"Ticket {ticket_id} is expired or cancelled"
                elif (
                    len(page_text.strip()) < 2000
                ):  # Very short pages are likely invalid/expired
                    status = "NO_TICKETS"
                    message = (
                        f"Ticket {ticket_id} appears to be invalid (page too short)"
                    )
                else:
                    # Look for the buy button "Køb" to confirm ticket is available
                    buy_button = soup.find(
                        string=lambda text: text and "køb" in text.lower()
                    )

                    # Also look for price information to confirm it's a valid ticket page
                    price_elements = soup.find_all(
                        string=lambda text: text
                        and (
                            "sek" in text.lower()
                            or "kr" in text.lower()
                            or "dkk" in text.lower()
                        )
                    )

                    if buy_button or price_elements:
                        status = "TICKETS_AVAILABLE"
                        message = (
                            f"🎫 Ticket {ticket_id} is AVAILABLE for purchase! Buy now!"
                        )
                    else:
                        # Might be available but unclear
                        status = "TICKETS_AVAILABLE"
                        message = f"🎫 Ticket {ticket_id} may be available (no unavailable message found)"

                result = {
                    "timestamp": datetime.now().isoformat(),
                    "status": status,
                    "message": message,
                    "ticket_id": ticket_id,
                    "url": ticket_url,
                }

                return result

            except requests.exceptions.Timeout:
                self.logger.warning(
                    f"Timeout for ticket {ticket_id} (attempt {attempt})"
                )
                if attempt < len(strategies):
                    continue
                else:
                    return {
                        "timestamp": datetime.now().isoformat(),
                        "status": "ERROR",
                        "message": f"Timeout checking ticket {ticket_id} after {len(strategies)} attempts",
                        "ticket_id": ticket_id,
                        "url": ticket_url,
                    }
            except requests.RequestException as e:
                self.logger.warning(
                    f"Request failed for ticket {ticket_id} (attempt {attempt}): {e}"
                )
                if attempt < len(strategies):
                    continue
                else:
                    return {
                        "timestamp": datetime.now().isoformat(),
                        "status": "ERROR",
                        "message": f"Failed to fetch ticket {ticket_id} after {len(strategies)} attempts: {e}",
                        "ticket_id": ticket_id,
                        "url": ticket_url,
                    }
            except Exception as e:
                self.logger.error(f"Unexpected error for ticket {ticket_id}: {e}")
                return {
                    "timestamp": datetime.now().isoformat(),
                    "status": "ERROR",
                    "message": f"Unexpected error for ticket {ticket_id}: {e}",
                    "ticket_id": ticket_id,
                    "url": ticket_url,
                }

    def check_ticket_range(self):
        """
        Check a range of ticket IDs for availability

        Returns:
            dict: Summary of results for all checked tickets
        """
        # Determine which tickets to check
        if self.specific_ticket_ids:
            # Check specific individual ticket IDs
            tickets_to_check = self.specific_ticket_ids
            range_description = (
                f"individual tickets: {','.join(map(str, tickets_to_check))}"
            )
        elif self.ticket_id_range:
            # Check range of ticket IDs
            start_id, end_id = self.ticket_id_range
            tickets_to_check = list(range(start_id, end_id + 1))
            range_description = f"{start_id} to {end_id}"
        else:
            # Default range
            self.ticket_id_range = (54310, 54360)
            start_id, end_id = self.ticket_id_range
            tickets_to_check = list(range(start_id, end_id + 1))
            range_description = f"{start_id} to {end_id} (default)"
            self.logger.info(
                "No ticket range specified, using default range: 54310-54360"
            )

        available_tickets = []
        total_checked = 0

        self.logger.info(f"Checking ticket IDs: {range_description}")

        for ticket_id in tickets_to_check:
            total_checked += 1
            self.logger.debug(f"Checking ticket {ticket_id}")

            result = self.check_individual_ticket(ticket_id)

            if result["status"] == "TICKETS_AVAILABLE":
                available_tickets.append(result)
                self.logger.info(f"✅ Found available ticket: {ticket_id}")

                # Send notification immediately for this specific ticket
                immediate_notification = {
                    "timestamp": result["timestamp"],
                    "status": "TICKETS_AVAILABLE",
                    "message": f"🎫 URGENT: Ticket {ticket_id} is AVAILABLE NOW!",
                    "available_tickets": [result],
                    "checked_count": 1,
                    "range": f"{ticket_id}",
                    "url": result["url"],
                }

                self.logger.info(f"🚨 SENDING IMMEDIATE ALERT for ticket {ticket_id}!")
                self.send_notifications(immediate_notification, force=True)

            elif result["status"] == "ERROR":
                self.logger.warning(
                    f"❌ Error checking ticket {ticket_id}: {result['message']}"
                )
            else:
                self.logger.debug(f"❌ Ticket {ticket_id} not available")

            # Add a small delay between requests to be respectful
            time.sleep(random.uniform(2.0, 5.0))

        # Prepare summary result (this won't trigger additional notifications)
        if available_tickets:
            status = "TICKETS_AVAILABLE"
            message = f"🎫 Found {len(available_tickets)} available tickets out of {total_checked} checked!"
            ticket_ids = [ticket["ticket_id"] for ticket in available_tickets]
            message += f" Ticket IDs: {ticket_ids}"
        else:
            status = "NO_TICKETS"
            if self.specific_ticket_ids:
                message = f"No available tickets found in specified IDs: {','.join(map(str, self.specific_ticket_ids))} ({total_checked} tickets checked)"
                range_info = (
                    f"individual: {','.join(map(str, self.specific_ticket_ids))}"
                )
            else:
                start_id, end_id = (
                    self.ticket_id_range if self.ticket_id_range else (54310, 54360)
                )
                message = f"No available tickets found in range {start_id}-{end_id} ({total_checked} tickets checked)"
                range_info = f"{start_id}-{end_id}"

        result = {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "message": message,
            "available_tickets": available_tickets,
            "checked_count": total_checked,
            "range": (
                range_info
                if "range_info" in locals()
                else (
                    f"{self.ticket_id_range[0]}-{self.ticket_id_range[1]}"
                    if self.ticket_id_range
                    else "54310-54360"
                )
            ),
        }

        return result

    def check_tickets_available(self):
        """
        Check if tickets are available for sale

        Returns:
            dict: Dictionary with status and details
        """
        try:
            response = self.session.get(self.event_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Look for the specific "sold out/reserved" message in Danish
            sold_out_message = "solgt eller reserveret. Hvis en anden kunde afbryder sit køb, kan reservationen muligvis frigives igen."

            # Also check for the general "no tickets" message
            no_tickets_text = "Der findes ingen billetter til salg"
            no_tickets_text_en = "No tickets for sale exists"

            page_text = soup.get_text()
            # print("**** PAGE TEXT ****")
            # print(page_text)
            # print("**** END PAGE TEXT ****")

            # Check if tickets are sold out/reserved
            if sold_out_message in page_text:
                status = "NO_TICKETS"
                message = "All tickets are sold or reserved"
            elif no_tickets_text or no_tickets_text_en in page_text:
                print("**** NO TICKETS TEXT IS FOUND ****")
                status = "NO_TICKETS"
                message = "No tickets available for sale"

            # if no_tickets_text in page_text:
            #     status = "NO_TICKETS"
            #     message = "No tickets available for sale"
            else:
                # If neither "sold out" message is present, tickets might be available
                # Look for ticket listings or sale sections to confirm
                ticket_sections = soup.find_all(
                    ["div", "section"],
                    text=lambda text: text and "billet" in text.lower(),
                )

                # Look for price indicators (DKK, kr, etc.)
                price_indicators = soup.find_all(
                    text=lambda text: text
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

        except requests.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "ERROR",
                "message": f"Failed to fetch page: {e}",
                "ticket_count": 0,
                "url": self.event_url,
            }
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "ERROR",
                "message": f"Unexpected error: {e}",
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

            # Handle different result types
            if "available_tickets" in result and result["available_tickets"]:
                # This is a ticket range check with individual tickets
                ticket_details = ""
                for ticket in result["available_tickets"][
                    :5
                ]:  # Limit to first 5 tickets
                    ticket_id = ticket["ticket_id"]
                    ticket_url = ticket["url"]
                    ticket_details += f"\n🎫 [Ticket {ticket_id}]({ticket_url})"

                if len(result["available_tickets"]) > 5:
                    ticket_details += f"\n\\.\\.\\. and {len(result['available_tickets']) - 5} more tickets"

                message_text = f"""🎫 *Sportstiming Ticket Alert*

*Status:* {status}
*Message:* {message}
*Range:* {escape_markdown(result.get('range', 'N/A'))}
*Checked:* {result.get('checked_count', 0)} tickets
*Time:* {timestamp}

*Available Tickets:*{ticket_details}

[Check Main Page]({escape_markdown(self.event_url)})"""
            else:
                # Regular ticket check or single ticket
                ticket_count = result.get(
                    "ticket_count", result.get("checked_count", 0)
                )
                url_to_show = result.get("url", self.event_url)

                message_text = f"""🎫 *Sportstiming Ticket Alert*

*Status:* {status}
*Message:* {message}
*Ticket Count:* {ticket_count}
*Time:* {timestamp}

[Check Website]({escape_markdown(url_to_show)})"""

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

    def test_all_notifications(self, force=False):
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
        self.send_notifications(test_result, force=force)
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

    def send_notifications(self, result, force=False):
        """
        Send all configured notifications

        Args:
            result (dict): Result from ticket check
            force (bool): Force sending notifications regardless of status
        """
        should_send = (
            force or result["status"] == "TICKETS_AVAILABLE" or self.notify_all_statuses
        )

        if should_send:
            # Send email if configured
            self.send_email_notification(result)

            # Send SMS if configured
            self.send_sms_notification(result)

            # Send Telegram if configured
            self.send_telegram_notification(result)

            # Send Pushover if configured
            self.send_pushover_notification(result)
        else:
            self.logger.debug(
                f"Not sending notifications for status: {result['status']}"
            )

    def run_single_check(self):
        """Run a single check and return the result"""
        # If no ticket configuration specified, use the default range 54310-54360
        if not self.ticket_id_range and not self.specific_ticket_ids:
            self.ticket_id_range = (54310, 54360)
            self.logger.info(
                "No ticket range specified, using default range: 54310-54360"
            )

        if self.ticket_id_range or self.specific_ticket_ids:
            # Check specific ticket ID range or individual IDs (notifications sent immediately per ticket)
            if self.specific_ticket_ids:
                self.logger.info(
                    f"Checking individual ticket IDs: {','.join(map(str, self.specific_ticket_ids))}"
                )
            else:
                self.logger.info(
                    f"Checking ticket ID range {self.ticket_id_range[0]}-{self.ticket_id_range[1]}..."
                )
            result = self.check_ticket_range()

            self.logger.info(f"Status: {result['status']} - {result['message']}")
            if result.get("available_tickets"):
                self.logger.info(
                    f"Found {len(result['available_tickets'])} available tickets!"
                )
                for ticket in result["available_tickets"]:
                    self.logger.info(
                        f"  🎫 Ticket {ticket['ticket_id']}: {ticket['url']}"
                    )
        else:
            # Regular check of the main resale page (this should not happen anymore)
            self.logger.info("Checking for available tickets...")
            result = self.check_tickets_available()

            self.logger.info(f"Status: {result['status']} - {result['message']}")
            if result.get("ticket_count", 0) > 0:
                self.logger.info(
                    f"Found {result['ticket_count']} potential ticket listings"
                )

            # Only send notifications for regular checks (not ticket range checks)
            if result["status"] == "TICKETS_AVAILABLE":
                self.send_notifications(result)

        return result

    def run_continuous_monitoring(self):
        """Run continuous monitoring with specified interval"""
        self.logger.info(
            f"Starting continuous ticket monitoring every {self.check_interval} seconds"
        )

        # The ticket range will be set by run_single_check if not already specified
        if self.ticket_id_range:
            self.logger.info(
                f"Monitoring ticket range: {self.ticket_id_range[0]}-{self.ticket_id_range[1]}"
            )
        elif self.specific_ticket_ids:
            self.logger.info(
                f"Monitoring specific ticket IDs: {','.join(map(str, self.specific_ticket_ids))}"
            )
        else:
            self.logger.info("Will use default ticket range: 54310-54360")

        if self.notify_all_statuses:
            self.logger.info("📢 Notifications enabled for ALL statuses")
        else:
            self.logger.info("📢 Notifications only for TICKETS_AVAILABLE status")

        last_status = None
        last_available_count = 0

        try:
            while True:
                result = self.run_single_check()

                current_available_count = len(result.get("available_tickets", []))

                # Individual tickets already sent notifications immediately
                # Just log the summary here
                if current_available_count > 0:
                    self.logger.info(
                        f"✅ Summary: {current_available_count} tickets currently available"
                    )
                    for ticket in result.get("available_tickets", []):
                        self.logger.info(
                            f"  📍 Ticket {ticket['ticket_id']}: {ticket['url']}"
                        )
                else:
                    self.logger.info(
                        f"❌ No tickets available in range {self.ticket_id_range[0]}-{self.ticket_id_range[1]}"
                    )

                # Only send summary notifications if notify_all_statuses is enabled AND status changed
                if self.notify_all_statuses and last_status != result["status"]:
                    # Send a summary notification for status changes
                    summary_notification = {
                        "timestamp": result["timestamp"],
                        "status": result["status"],
                        "message": f"Status update: {result['message']}",
                        "available_tickets": result.get("available_tickets", []),
                        "checked_count": result.get("checked_count", 0),
                        "range": result.get("range", ""),
                    }
                    self.send_notifications(summary_notification)
                    self.logger.info(
                        f"📊 Summary notification sent for status change: {last_status} → {result['status']}"
                    )

                last_status = result["status"]
                last_available_count = current_available_count

                self.logger.info(f"Next check in {self.check_interval} seconds...")
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")

    # Troubleshooting functions
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

    def debug_ticket_content(self, ticket_id):
        """
        Debug method to see the actual content of a ticket page

        Args:
            ticket_id (int): The ticket ID to debug
        """
        base_url = "https://www.sportstiming.dk/event/6583/resale/ticket"
        ticket_url = f"{base_url}/{ticket_id}"

        try:
            response = self.session.get(ticket_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            page_text = soup.get_text()

            print(f"🔍 DEBUG: Ticket {ticket_id} page content analysis")
            print("=" * 60)
            print(f"URL: {ticket_url}")
            print(f"Status Code: {response.status_code}")
            print(f"Content Length: {len(page_text)} characters")
            print(f"HTML Content Length: {len(response.content)} bytes")

            print("\n📄 Raw HTML (first 1500 characters):")
            print("-" * 40)
            print(response.content.decode("utf-8", errors="ignore")[:1500])
            print("-" * 40)

            print("\n📄 Text content (first 1000 characters):")
            print("-" * 40)
            print(page_text[:1000])
            print("-" * 40)

            # Check for specific strings
            unavailable_message = "Det er p.t. ikke muligt at foretage dette valg, da alt enten er solgt eller reserveret. Hvis en anden kunde afbryder sit køb, kan reservationen muligvis frigives igen."
            unavailable_message_en = "It is currently not possible to make this choice, as everything is either sold or reserved. If another customer cancels their purchase, the reservation may possibly be released again."

            # Also check for partial messages that might appear
            partial_messages = [
                "ikke muligt at foretage dette valg",
                "solgt eller reserveret",
                "reserveret",
                "currently not possible",
                "sold or reserved",
                "reserved",
            ]

            print(f"\n🔍 String analysis:")
            print(
                f"Contains full Danish 'unavailable' message: {'✅ YES' if unavailable_message in page_text else '❌ NO'}"
            )
            print(
                f"Contains full English 'unavailable' message: {'✅ YES' if unavailable_message_en in page_text else '❌ NO'}"
            )

            print(f"\n🔍 Partial message analysis:")
            for partial in partial_messages:
                found = partial.lower() in page_text.lower()
                print(f"Contains '{partial}': {'✅ YES' if found else '❌ NO'}")

            # Also check in raw HTML
            raw_html = response.content.decode("utf-8", errors="ignore").lower()
            print(f"\n🔍 Raw HTML analysis:")
            for partial in partial_messages:
                found = partial.lower() in raw_html
                print(f"HTML contains '{partial}': {'✅ YES' if found else '❌ NO'}")

            # Look for buy button
            buy_button = soup.find(string=lambda text: text and "køb" in text.lower())
            print(f"Contains 'køb' button text: {'✅ YES' if buy_button else '❌ NO'}")
            if buy_button:
                print(f"Buy button text: '{buy_button.strip()}'")

            # Look for price
            price_elements = soup.find_all(
                string=lambda text: text
                and (
                    "sek" in text.lower()
                    or "kr" in text.lower()
                    or "dkk" in text.lower()
                )
            )
            print(
                f"Contains price information: {'✅ YES' if price_elements else '❌ NO'}"
            )
            if price_elements:
                print(
                    f"Price elements found: {[elem.strip() for elem in price_elements[:3]]}"
                )

            # Look for specific keywords that might indicate availability
            keywords = ["reserveret", "solgt", "køb", "billet", "pris", "sek", "kr"]
            print(f"\n🏷️ Keyword analysis:")
            for keyword in keywords:
                count = page_text.lower().count(keyword)
                print(f"'{keyword}': {count} occurrences")

        except Exception as e:
            print(f"❌ Error checking ticket {ticket_id}: {e}")


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
        default=120,
        help="Check interval in seconds (default: 120)",
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
        "--ticket-range",
        type=str,
        help="Check specific ticket ID range, format: start-end (e.g., 54296-54305)",
    )
    parser.add_argument(
        "--ticket-ids",
        type=str,
        help="Check specific individual ticket IDs, comma-separated (e.g., 54302,54315,54328)",
    )
    parser.add_argument(
        "--check-ticket",
        type=int,
        help="Check a single specific ticket ID",
    )
    parser.add_argument(
        "--debug-ticket",
        type=int,
        help="Debug the content of a specific ticket ID to see what the page contains",
    )

    args = parser.parse_args()

    if args.create_config:
        create_sample_config()
        return

    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Parse ticket range if provided
    ticket_id_range = None
    specific_ticket_ids = None

    if args.ticket_range:
        try:
            start_str, end_str = args.ticket_range.split("-")
            start_id = int(start_str.strip())
            end_id = int(end_str.strip())
            if start_id > end_id:
                print("❌ Error: Start ID must be less than or equal to end ID")
                return
            ticket_id_range = (start_id, end_id)
            print(f"🎯 Will check ticket ID range: {start_id} to {end_id}")
        except ValueError:
            print(
                "❌ Error: Invalid ticket range format. Use: start-end (e.g., 54296-54305)"
            )
            return
    elif args.ticket_ids:
        # Parse individual ticket IDs (comma-separated)
        try:
            specific_ticket_ids = [int(id.strip()) for id in args.ticket_ids.split(",")]
            if not specific_ticket_ids:
                print("❌ Error: No ticket IDs provided")
                return
            print(f"🎯 Will check individual ticket IDs: {args.ticket_ids}")
        except ValueError:
            print(
                "❌ Error: Invalid ticket IDs format. Use comma-separated numbers (e.g., 54302,54315,54328)"
            )
            return
    elif args.check_ticket:
        # Single ticket check - convert to specific IDs list
        specific_ticket_ids = [args.check_ticket]
        print(f"🎯 Will check single ticket ID: {args.check_ticket}")

    checker = SportstimingTicketChecker(
        event_url=args.url,
        check_interval=args.interval,
        config_file=args.config,
        notify_all_statuses=args.notify_all,
        ticket_id_range=ticket_id_range,
        specific_ticket_ids=specific_ticket_ids,
    )

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

    if args.debug_ticket:
        checker.debug_ticket_content(args.debug_ticket)
        return

    if args.single:
        result = checker.run_single_check()
        print(json.dumps(result, indent=2))
    else:
        checker.run_continuous_monitoring()


if __name__ == "__main__":
    main()
