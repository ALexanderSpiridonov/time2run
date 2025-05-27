# Sportstiming Ticket Checker Bot

This bot automatically monitors the Sportstiming.dk resale page for available tickets and can notify you via **Email**, **SMS**, **Telegram**, or **Push notifications** when tickets become available.

## Features

- ✅ Automatic ticket availability checking
- ✅ Continuous monitoring with customizable intervals
- ✅ **Multiple notification methods:**
  - 📧 Email notifications
  - 📱 SMS notifications (via Twilio)
  - 💬 Telegram notifications
  - 🔔 Push notifications (via Pushover)
- ✅ Detailed logging to file and console
- ✅ Single check mode for testing
- ✅ Danish language support (detects "Der findes ingen billetter til salg")

## ✨ New Features

- **🎯 Individual Ticket Checking**: Checks specific ticket IDs (54310-54360) instead of just the main page
- **⚡ Immediate Notifications**: Sends alerts instantly when any ticket becomes available
- **🔗 Direct Links**: Provides direct purchase links for each available ticket
- **🚀 Smart Detection**: Detects sold, reserved, expired, and available tickets accurately

## 🚀 Quick Railway Deployment

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/VvbG8J?referralCode=ticket-checker)

### 1. Set Environment Variables

In your Railway dashboard, go to **Variables** and set:

**Required:**
```
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_CHAT_ID=your_chat_id
```

**Optional:**
```
CHECK_INTERVAL=120                    # Check every 2 minutes (default)
TICKET_RANGE=54310-54360             # Ticket ID range to check (default: 54310-54360)
NOTIFY_ALL=false                     # Only notify when tickets are available (default)
```

### 2. Get Telegram Bot Token

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy the token (looks like `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 3. Get Chat ID

**Option A - Individual Chat:**
1. Send a message to your bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Look for `"chat":{"id":CHAT_ID_HERE}`

**Option B - Group Chat (Recommended for multiple people):**
1. Create a Telegram group
2. Add your bot to the group (`/invite @your_bot_name`)
3. Send a message in the group mentioning the bot
4. Use the same URL above to find the group chat ID (usually negative number)
5. For multiple chats: `TELEGRAM_CHAT_ID=chat1,chat2,chat3`

## 📱 How It Works

The bot now monitors **individual ticket URLs** instead of the main page:

1. **Checks tickets 54310-54360** (customizable via `TICKET_RANGE`)
2. **Sends immediate alerts** when any ticket becomes available
3. **Provides direct links** like: `https://www.sportstiming.dk/event/6583/resale/ticket/54302`
4. **Continues scanning** after finding tickets (doesn't stop at first available ticket)

## 🔔 Notification Example

When ticket 54302 becomes available, you'll receive:

```
🎫 Sportstiming Ticket Alert

Status: TICKETS_AVAILABLE
Message: 🎫 URGENT: Ticket 54302 is AVAILABLE NOW!

Available Tickets:
🎫 Ticket 54302 (https://www.sportstiming.dk/event/6583/resale/ticket/54302)

Check Main Page (https://www.sportstiming.dk/event/6583/resale)
```

## ⚙️ Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | - | Bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | ✅ | - | Your chat ID or comma-separated list |
| `CHECK_INTERVAL` | ❌ | 120 | Seconds between checks |
| `TICKET_RANGE` | ❌ | 54310-54360 | Range of ticket IDs to check |
| `NOTIFY_ALL` | ❌ | false | Notify for all status changes |

### Optional Notification Methods

**Email:**
```
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO=recipient@gmail.com
```

**SMS (Twilio):**
```
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890
TWILIO_TO_NUMBER=+1987654321
```

**Pushover:**
```
PUSHOVER_APP_TOKEN=your_app_token
PUSHOVER_USER_KEY=your_user_key
```

## 🔧 Local Development

```bash
# Clone repository
git clone <repository-url>
cd time2run

# Install dependencies
pip install -r requirements.txt

# Check single ticket
python ticket_checker.py --check-ticket 54302 --single

# Check ticket range
python ticket_checker.py --ticket-range 54310-54360 --single

# Start monitoring with notifications
python ticket_checker.py --config config.json --interval 120
```

## 🎯 Usage Examples

```bash
# Monitor default range (54310-54360) every 2 minutes
python ticket_checker.py --interval 120

# Monitor custom range
python ticket_checker.py --ticket-range 54300-54320 --interval 60

# Check single ticket
python ticket_checker.py --check-ticket 54302 --single

# Debug ticket content
python ticket_checker.py --debug-ticket 54302
```

## 🚨 Important Notes

- **Immediate Alerts**: Notifications are sent as soon as ANY ticket is found available
- **Multiple Tickets**: If multiple tickets are available, you'll get separate alerts for each
- **Rate Limiting**: Built-in delays between requests to be respectful to the website
- **Smart Detection**: Automatically handles expired, sold, and invalid tickets

## 📊 Monitoring

The bot logs all activity and you can monitor it in Railway's dashboard under **Logs**.

Successful deployment will show:
```
🚂 Starting Sportstiming Ticket Checker on Railway...
✅ Config file created from environment variables
🎯 Starting monitoring:
   Ticket Range: 54310-54360 (default)
   Interval: 120 seconds
   Notify all statuses: false
🏃 Starting application...
```

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install optional dependencies (choose what you need):**
   ```bash
   # For SMS notifications
   pip install twilio
   
   # Telegram and Pushover use requests (already included)
   ```

3. **Make the script executable (optional):**
   ```bash
   chmod +x ticket_checker.py
   ```

## Quick Setup Guide

### 1. Create Configuration File
```bash
python ticket_checker.py --create-config
```

### 2. Choose Your Notification Method(s)

Edit the generated `config.json` and keep only the sections you want to use:

#### 📧 Email Notifications (Gmail)
```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "your_email@gmail.com",
    "password": "your_app_password",
    "from_email": "your_email@gmail.com",
    "to_email": "notification_recipient@gmail.com"
  }
}
```

**Gmail Setup:**
1. Enable 2-factor authentication
2. Generate an "App Password" (not your regular password)
3. Use the app password in the config

#### 📱 SMS Notifications (Twilio)
```json
{
  "sms": {
    "account_sid": "your_twilio_account_sid",
    "auth_token": "your_twilio_auth_token",
    "from_number": "+1234567890",
    "to_number": "+1987654321"
  }
}
```

**Twilio Setup:**
1. Sign up for [Twilio](https://www.twilio.com/)
2. Get a phone number (free trial gives you $15 credit)
3. Find your Account SID and Auth Token in the dashboard
4. Install Twilio: `pip install twilio`

#### 💬 Telegram Notifications
```json
{
  "telegram": {
    "bot_token": "your_bot_token_from_botfather",
    "chat_id": "your_chat_id"
  }
}
```

**Telegram Setup:**
1. Create a bot:
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Send `/newbot` and follow instructions
   - Save the bot token
2. Get your chat ID:
   - Message your bot or add it to a group
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your chat ID in the response

#### 🔔 Push Notifications (Pushover)
```json
{
  "pushover": {
    "app_token": "your_pushover_app_token",
    "user_key": "your_pushover_user_key"
  }
}
```

**Pushover Setup:**
1. Sign up for [Pushover](https://pushover.net/) ($5 one-time fee after trial)
2. Create an application to get the app token
3. Find your user key in your account dashboard

### 3. Mix and Match Notifications
You can use multiple notification methods simultaneously! Just include multiple sections in your config.json:

```json
{
  "telegram": {
    "bot_token": "your_bot_token",
    "chat_id": "your_chat_id"
  },
  "sms": {
    "account_sid": "your_twilio_sid",
    "auth_token": "your_twilio_token",
    "from_number": "+1234567890",
    "to_number": "+1987654321"
  }
}
```

## Usage

### Quick Start - Single Check
```bash
python ticket_checker.py --single
```

### Continuous Monitoring (Default: every 5 minutes)
```bash
python ticket_checker.py --config config.json
```

### Custom Check Interval (every 2 minutes)
```bash
python ticket_checker.py --config config.json --interval 120
```

### Monitor Different Event
```bash
python ticket_checker.py --url "https://www.sportstiming.dk/event/OTHER_EVENT_ID/resale" --config config.json
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--url` | URL to monitor | https://www.sportstiming.dk/event/6583/resale |
| `--interval` | Check interval in seconds | 300 (5 minutes) |
| `--config` | Path to configuration file | None |
| `--single` | Run single check instead of continuous monitoring | False |
| `--create-config` | Create sample configuration file | False |

## Notification Examples

### 📱 SMS Message
```
🎫 Sportstiming Alert!

Status: TICKETS_AVAILABLE
Tickets may be available! Manual check recommended.

Check: https://www.sportstiming.dk/event/6583/resale
Time: 2024-01-15T10:30:00
```

### 💬 Telegram Message
```
🎫 Sportstiming Ticket Alert

Status: TICKETS_AVAILABLE
Message: Tickets may be available! Manual check recommended.
Ticket Count: 3
Time: 2024-01-15T10:30:00

[Check Website](https://www.sportstiming.dk/event/6583/resale)
```

### 🔔 Push Notification
- **Title:** 🎫 Sportstiming Alert - TICKETS_AVAILABLE
- **Message:** Tickets may be available! Manual check recommended.
- **Link:** Direct link to the resale page

## How It Works

The bot works by:

1. **Fetching the webpage** using HTTP requests with a browser-like user agent
2. **Parsing the HTML** using BeautifulSoup to extract text content
3. **Looking for Danish text** "Der findes ingen billetter til salg" (No tickets for sale)
4. **Detecting ticket availability** by absence of the "no tickets" message
5. **Counting potential listings** by looking for common ticket-related HTML patterns
6. **Logging results** to both console and `ticket_checker.log` file
7. **Sending notifications** via your chosen method(s) when tickets become available

## Running in Background

### macOS/Linux
```bash
# Run in background
nohup python ticket_checker.py --config config.json &

# Check if running
ps aux | grep ticket_checker

# Stop background process
kill [PID]
```

### Using screen/tmux
```bash
# Using screen
screen -S ticket_checker
python ticket_checker.py --config config.json
# Ctrl+A, D to detach

# Reattach later
screen -r ticket_checker
```

## Cost Comparison

| Method | Cost | Reliability | Setup Difficulty |
|--------|------|-------------|------------------|
| **Email** | Free | High | Easy |
| **Telegram** | Free | High | Easy |
| **Pushover** | $5 one-time | Very High | Easy |
| **SMS (Twilio)** | ~$0.02/SMS | Very High | Medium |

**Recommendations:**
- **Free & Reliable**: Telegram + Email
- **Most Reliable**: Pushover ($5 one-time)
- **Instant Mobile**: SMS (if you don't mind the cost)

## Troubleshooting

### Common Issues

1. **Connection Errors**: Check your internet connection
2. **Notifications Not Sending**: 
   - Verify credentials in config.json
   - Check logs for specific error messages
3. **Telegram Bot Not Responding**: 
   - Make sure you've sent at least one message to your bot
   - Verify the bot token and chat ID
4. **SMS Not Sending**: 
   - Check Twilio account balance
   - Verify phone numbers are in correct format (+1234567890)

### Testing Notifications

You can test your notifications by temporarily changing the detection logic or using a different URL that you know has tickets available.

## Rate Limiting & Best Practices

- Default check interval is 5 minutes to be respectful to the website
- Don't set intervals too low (< 60 seconds) to avoid being blocked
- The bot includes proper delays and error handling
- Consider using multiple notification methods for redundancy

## Legal Notice

This bot is for personal use only. Based on the website content from [Sportstiming.dk](https://www.sportstiming.dk/event/6583/resale), this bot helps monitor the official resale platform where participants can sell tickets they can no longer use. Please be respectful of the website's resources. 