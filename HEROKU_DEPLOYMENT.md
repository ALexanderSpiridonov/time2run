# 🚀 Heroku Deployment Guide

This guide will help you deploy your Sportstiming Ticket Checker to Heroku.

## 📋 Prerequisites

1. **Heroku Account**: Sign up at [heroku.com](https://heroku.com)
2. **Heroku CLI**: Install from [devcenter.heroku.com/articles/heroku-cli](https://devcenter.heroku.com/articles/heroku-cli)
3. **Git**: Make sure Git is installed
4. **Telegram Bot**: You need a bot token and chat ID

## 🎯 Quick Deploy (Recommended)

### Option 1: Deploy Button (Easiest)

1. Click this button (after pushing to GitHub):
   
   [![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

2. Fill in your environment variables:
   - `TELEGRAM_BOT_TOKEN`: Your bot token from @BotFather
   - `TELEGRAM_CHAT_ID`: Your chat ID (or comma-separated for multiple)

3. Click "Deploy app"

### Option 2: Manual Deploy

1. **Clone/Create your repository**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Create Heroku app**:
   ```bash
   heroku create your-app-name
   ```

3. **Set environment variables**:
   ```bash
   heroku config:set TELEGRAM_BOT_TOKEN="your_bot_token_here"
   heroku config:set TELEGRAM_CHAT_ID="your_chat_id_here"
   
   # Optional settings
   heroku config:set CHECK_INTERVAL=300
   heroku config:set NOTIFY_ALL=true
   heroku config:set TZ=Europe/Copenhagen
   ```

4. **Deploy**:
   ```bash
   git push heroku main
   ```

5. **Scale the worker**:
   ```bash
   heroku ps:scale worker=1
   ```

## ⚙️ Environment Variables

### Required:
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `TELEGRAM_CHAT_ID`: Your chat ID (single or comma-separated)

### Optional:
- `CHECK_INTERVAL`: Check frequency in seconds (default: 300)
- `TICKET_URL`: URL to monitor (default: sportstiming event)
- `NOTIFY_ALL`: Send all notifications (default: true)
- `TZ`: Timezone (default: Europe/Copenhagen)

### Multiple Chat IDs:
```bash
heroku config:set TELEGRAM_CHAT_ID="123456789,987654321,-100123456789"
```

## 📱 Getting Your Telegram Info

1. **Get Bot Token**:
   - Message @BotFather on Telegram
   - Create a new bot with `/newbot`
   - Save the token

2. **Get Chat ID**:
   ```bash
   # Test locally first
   python ticket_checker.py --find-chat-ids --config config.json
   ```

## 🔧 Heroku Commands

```bash
# View logs
heroku logs --tail

# Check app status
heroku ps

# Scale workers
heroku ps:scale worker=1

# Stop the app
heroku ps:scale worker=0

# Restart the app
heroku restart

# Open Heroku dashboard
heroku open

# Set config variables
heroku config:set VARIABLE_NAME="value"

# View config variables
heroku config
```

## 💰 Costs

- **Eco Dynos**: $5/month (1000 dyno hours)
- **Basic Plan**: $7/month (unlimited hours)
- **Free Tier**: 550 hours/month (enough for ~18 days)

## 🔍 Monitoring

### Check Logs:
```bash
heroku logs --tail
```

### Expected Output:
```
🚀 Starting Sportstiming Ticket Checker on Heroku...
✅ Config file created from environment variables
🔍 Testing configuration...
✅ Configuration test passed
🎯 Starting monitoring:
   URL: https://www.sportstiming.dk/event/6583/resale
   Interval: 300 seconds
   Notify all statuses: true
```

## 🛠 Troubleshooting

### Common Issues:

1. **App not starting**:
   ```bash
   heroku logs --tail
   # Check for missing environment variables
   ```

2. **No notifications**:
   ```bash
   # Test Telegram config
   heroku run python ticket_checker.py --test-telegram --config config.json
   ```

3. **Wrong timezone**:
   ```bash
   heroku config:set TZ=Europe/Copenhagen
   ```

4. **Too frequent/infrequent checks**:
   ```bash
   heroku config:set CHECK_INTERVAL=120  # 2 minutes
   ```

### Debug Commands:
```bash
# Run one-time check
heroku run python ticket_checker.py --single --notify-all --config config.json

# Test notifications
heroku run python ticket_checker.py --test-notifications --config config.json

# Troubleshoot Telegram
heroku run python ticket_checker.py --troubleshoot-telegram --config config.json
```

## 📊 Usage Examples

### Different Configurations:

1. **Silent mode** (only when tickets available):
   ```bash
   heroku config:set NOTIFY_ALL=false
   ```

2. **Frequent checking** (every minute):
   ```bash
   heroku config:set CHECK_INTERVAL=60
   ```

3. **Multiple recipients**:
   ```bash
   heroku config:set TELEGRAM_CHAT_ID="your_id,friend_id,group_id"
   ```

4. **Different event**:
   ```bash
   heroku config:set TICKET_URL="https://www.sportstiming.dk/event/XXXX/resale"
   ```

## 🎉 Success!

Once deployed, your bot will:
- ✅ Run 24/7 on Heroku
- ✅ Send notifications to Telegram
- ✅ Automatically restart if it crashes
- ✅ Scale up/down as needed

## 📞 Support

If you have issues:
1. Check the logs: `heroku logs --tail`
2. Verify environment variables: `heroku config`
3. Test locally first
4. Check Heroku status: [status.heroku.com](https://status.heroku.com)

Happy monitoring! 🎫 