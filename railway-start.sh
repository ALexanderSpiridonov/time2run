#!/bin/bash

# Railway startup script for Sportstiming Ticket Checker

echo "🚀 Starting Sportstiming Ticket Checker on Railway..."

# Check if config file exists, if not create from environment variables
if [ ! -f "config.json" ]; then
    echo "📝 Creating config.json from environment variables..."
    
    cat > config.json << EOF
{
  "telegram": {
    "bot_token": "${TELEGRAM_BOT_TOKEN}",
    "chat_id": "${TELEGRAM_CHAT_ID}"
  }
}
EOF
    
    echo "✅ Config file created"
fi

# Validate configuration
echo "🔍 Testing Telegram configuration..."
python ticket_checker.py --test-telegram --config config.json

if [ $? -eq 0 ]; then
    echo "✅ Configuration validated successfully"
    echo "🎯 Starting continuous monitoring..."
    
    # Start the main application
    exec python ticket_checker.py \
        --config config.json \
        --notify-all \
        --interval ${CHECK_INTERVAL:-300} \
        --url "${TICKET_URL:-https://www.sportstiming.dk/event/6583/resale}"
else
    echo "❌ Configuration validation failed"
    echo "Please check your environment variables:"
    echo "- TELEGRAM_BOT_TOKEN"
    echo "- TELEGRAM_CHAT_ID"
    exit 1
fi 