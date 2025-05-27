# 🚂 Railway Deployment Guide

Complete guide to deploy the Sportstiming Ticket Checker on Railway with the new ticket range functionality.

## 📋 Prerequisites

1. [Railway account](https://railway.app/) (free tier available)
2. Telegram bot token from [@BotFather](https://t.me/botfather)
3. Your Telegram chat ID

## 🚀 Quick Deployment

### Step 1: Fork/Clone Repository

1. Fork this repository or clone it locally
2. Connect it to your Railway account

### Step 2: Deploy on Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

1. Click "Deploy from GitHub repo"
2. Select your forked repository
3. Railway will automatically detect the Python project

### Step 3: Configure Environment Variables

Go to your Railway project → **Variables** tab and add:

#### Required Variables:
```bash
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=your_chat_id_here
```

#### Optional Variables:
```bash
CHECK_INTERVAL=120                    # Check every 2 minutes
TICKET_RANGE=54310-54360             # Ticket IDs to monitor
NOTIFY_ALL=false                     # Only notify when tickets found
```

## 🤖 Setting Up Telegram Bot

### 1. Create Bot with BotFather

1. Open Telegram and message [@BotFather](https://t.me/botfather)
2. Send `/newbot`
3. Choose a name for your bot (e.g., "My Ticket Checker")
4. Choose a username (e.g., "my_ticket_checker_bot")
5. Copy the bot token (looks like `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 2. Get Your Chat ID

**Option A - Personal Chat:**
1. Send any message to your bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Find your chat ID in the response: `"chat":{"id":YOUR_CHAT_ID}`

**Option B - Group Chat (Recommended):**
1. Create a Telegram group
2. Add your bot to the group
3. Send a message mentioning the bot: `@your_bot_name hello`
4. Use the same URL to get the group chat ID (negative number)

**Option C - Multiple Recipients:**
```bash
TELEGRAM_CHAT_ID=chat1,chat2,chat3
```

## 🔧 Environment Variables Explained

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | - | Token from @BotFather |
| `TELEGRAM_CHAT_ID` | ✅ | - | Where to send notifications |
| `CHECK_INTERVAL` | ❌ | 120 | Seconds between checks |
| `TICKET_RANGE` | ❌ | 54310-54360 | Ticket IDs to monitor |
| `NOTIFY_ALL` | ❌ | false | Notify for all status changes |

### Advanced Notification Options

**Email Notifications:**
```bash
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO=alerts@yourdomain.com
```

**SMS via Twilio:**
```bash
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_FROM_NUMBER=+1234567890
TWILIO_TO_NUMBER=+1987654321
```

**Pushover Push Notifications:**
```bash
PUSHOVER_APP_TOKEN=your_app_token
PUSHOVER_USER_KEY=your_user_key
```

## 🎯 How the New System Works

### Individual Ticket Monitoring

Instead of checking the main page, the bot now:

1. **Checks specific ticket URLs**: `https://www.sportstiming.dk/event/6583/resale/ticket/54296`
2. **Scans range 54310-54360** (customizable)
3. **Sends immediate alerts** when any ticket becomes available
4. **Provides direct purchase links**

### Smart Detection

The bot detects:
- ✅ **Available tickets**: No "sold/reserved" message found
- ❌ **Sold/Reserved**: Contains Danish unavailable message
- ❌ **Expired/Cancelled**: Contains "completed or cancelled"
- ❌ **Invalid**: 404 errors or very short pages

## 📱 Notification Examples

### When Ticket Found:
```
🎫 Sportstiming Ticket Alert

Status: TICKETS_AVAILABLE
Message: 🎫 URGENT: Ticket 54302 is AVAILABLE NOW!

Available Tickets:
🎫 Ticket 54302 (https://www.sportstiming.dk/event/6583/resale/ticket/54302)

Check Main Page (https://www.sportstiming.dk/event/6583/resale)
```

### Multiple Tickets Found:
```
🎫 Sportstiming Ticket Alert

Status: TICKETS_AVAILABLE
Message: 🎫 Found 3 available tickets out of 15 checked!

Available Tickets:
🎫 Ticket 54296 (https://www.sportstiming.dk/event/6583/resale/ticket/54296)
🎫 Ticket 54298 (https://www.sportstiming.dk/event/6583/resale/ticket/54298)
🎫 Ticket 54302 (https://www.sportstiming.dk/event/6583/resale/ticket/54302)

Check Main Page (https://www.sportstiming.dk/event/6583/resale)
```

## 🔍 Monitoring Your Deployment

### Railway Dashboard

1. Go to your Railway project
2. Click **Logs** tab
3. Monitor real-time activity

### Successful Startup Logs:
```
🚂 Starting Sportstiming Ticket Checker on Railway...
🔍 Debug - Environment variables:
   TELEGRAM_BOT_TOKEN: SET
   TELEGRAM_CHAT_ID: SET
   CHECK_INTERVAL: 120
   TICKET_RANGE: 54310-54360
✅ Config file created from environment variables
🎯 Starting monitoring:
   Ticket Range: 54310-54360
   Interval: 120 seconds
   Notify all statuses: false
🏃 Starting application...
```

### Monitoring Activity:
```
2025-01-27 10:00:00 - INFO - Checking ticket ID range 54310-54360...
2025-01-27 10:00:15 - INFO - Status: NO_TICKETS - No available tickets found
2025-01-27 10:00:15 - INFO - ❌ No tickets available in range 54310-54360
2025-01-27 10:00:15 - INFO - Next check in 120 seconds...
```

### When Tickets Found:
```
2025-01-27 10:05:00 - INFO - ✅ Found available ticket: 54302
2025-01-27 10:05:00 - INFO - 🚨 SENDING IMMEDIATE ALERT for ticket 54302!
2025-01-27 10:05:01 - INFO - ✅ Message sent successfully to chat 123456789
```

## 🚨 Troubleshooting

### Common Issues:

**1. Bot Not Starting:**
```
❌ No notification configuration found
```
**Solution:** Check that `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set

**2. No Notifications Received:**
```
❌ Telegram API error: Forbidden
```
**Solution:** Make sure you've sent at least one message to your bot

**3. Wrong Chat ID:**
```
❌ Network error sending to chat
```
**Solution:** Verify your chat ID using the `/getUpdates` method

### Testing Your Setup:

Use Railway's built-in testing commands:

```bash
# Test your bot configuration
python ticket_checker.py --test-telegram --config config.json

# Check a specific ticket
python ticket_checker.py --check-ticket 54302 --single

# Debug troubleshooting
python ticket_checker.py --troubleshoot-telegram
```

## 📊 Performance & Costs

### Railway Free Tier:
- ✅ **500 hours/month**: More than enough for continuous monitoring
- ✅ **No sleeping**: Unlike Heroku, your bot runs 24/7
- ✅ **Automatic restarts**: If the process crashes, Railway restarts it

### Resource Usage:
- **CPU**: Very low (mostly waiting between requests)
- **Memory**: ~50MB (minimal Python script)
- **Network**: ~1MB/hour (checking tickets)

## 🔧 Advanced Configuration

### Custom Ticket Ranges:
```bash
TICKET_RANGE=54300-54350    # Check newer tickets
TICKET_RANGE=54000-54100    # Check older tickets
```

### Faster Checking:
```bash
CHECK_INTERVAL=60          # Check every minute (be respectful!)
```

### Multiple Notification Methods:
Set up Telegram + Email + SMS for redundancy:
```bash
# Telegram (primary)
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat

# Email (backup)
EMAIL_USERNAME=your_email
EMAIL_PASSWORD=your_password
EMAIL_TO=backup@email.com

# SMS (urgent alerts)
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_TO_NUMBER=+1234567890
```

## 🎯 Best Practices

1. **Use Group Chats**: Create a Telegram group for multiple people to receive alerts
2. **Set Reasonable Intervals**: Don't check too frequently (respect the website)
3. **Monitor Logs**: Check Railway logs periodically to ensure everything is working
4. **Test First**: Use `--single` mode to test before enabling continuous monitoring
5. **Backup Notifications**: Set up multiple notification methods for reliability

## 📞 Support

If you need help:

1. Check the **Logs** in Railway dashboard
2. Use the troubleshooting commands in the ticket checker
3. Verify your Telegram bot setup
4. Make sure all environment variables are correctly set

The bot will automatically handle most issues and restart if needed! 