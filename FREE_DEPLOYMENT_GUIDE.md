# 🆓 Free Deployment Guide for Ticket Checker

Since Heroku is having issues, here are the **best free alternatives** to deploy your ticket checker bot!

## 🏆 **Top Recommendations**

### **1. Railway** ⭐ *BEST CHOICE*
- **Free tier**: $5 credit monthly (enough for small apps)
- **Always on**: No sleeping
- **Easy setup**: GitHub integration
- **Great support**: Active community

### **2. Render** ⭐ *GREAT ALTERNATIVE*
- **Free tier**: 750 hours/month
- **Auto-deploy**: From GitHub
- **Limitation**: Sleeps after 15 min inactivity

### **3. GitHub Actions** ⭐ *TOTALLY FREE*
- **Free tier**: 2000 minutes/month
- **Scheduled runs**: Every 5 minutes
- **Always available**: No sleeping

### **4. Fly.io**
- **Free tier**: 3 small VMs
- **Global**: Fast worldwide
- **Docker-based**: Flexible

---

## 🚂 **Railway Deployment (Recommended)**

### **Step 1: Setup**
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"

### **Step 2: Configuration**
Add these environment variables in Railway dashboard:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
CHECK_INTERVAL=300
NOTIFY_ALL=true
```

### **Step 3: Deploy**
Railway will automatically:
- ✅ Detect Python app
- ✅ Install dependencies
- ✅ Start your bot
- ✅ Keep it running 24/7

**Cost**: Uses ~$2-3 of your $5 monthly credit

---

## 🎨 **Render Deployment**

### **Step 1: Setup**
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Click "New" → "Web Service"

### **Step 2: Configuration**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python railway-start.py`

### **Environment Variables**:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### **Limitation**: 
- Sleeps after 15 minutes of inactivity
- Will wake up when a new ticket check is needed

---

## ⚡ **GitHub Actions (100% Free)**

### **Step 1: Push to GitHub**
```bash
git add .
git commit -m "Add ticket checker"
git push origin main
```

### **Step 2: Add Secrets**
In your GitHub repo:
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add these secrets:
   - `TELEGRAM_BOT_TOKEN`: Your bot token
   - `TELEGRAM_CHAT_ID`: Your chat ID

### **Step 3: Enable Actions**
The workflow is already created in `.github/workflows/ticket-checker.yml`

### **How it works**:
- ✅ Runs every 5 minutes
- ✅ Checks for tickets
- ✅ Sends notifications
- ✅ Completely free
- ✅ Very reliable

---

## 🛠 **Quick Setup Commands**

### **For Railway/Render**:
```bash
# Make startup script executable
chmod +x railway-start.py

# Test locally first
python railway-start.py
```

### **For GitHub Actions**:
```bash
# Push to GitHub
git add .
git commit -m "Deploy ticket checker"
git push origin main

# Add secrets in GitHub UI
# Enable Actions in your repo
```

---

## 📊 **Comparison Table**

| Platform | Free Tier | Always On | Setup Difficulty | Best For |
|----------|-----------|-----------|------------------|----------|
| **Railway** | $5 credit/month | ✅ Yes | 🟢 Easy | Small apps |
| **Render** | 750 hours | ❌ Sleeps | 🟢 Easy | Hobby projects |
| **GitHub Actions** | 2000 min/month | ✅ Scheduled | 🟡 Medium | Periodic checks |
| **Fly.io** | 3 small VMs | ✅ Yes | 🔴 Hard | Advanced users |

---

## 🎯 **My Recommendation**

### **For 24/7 monitoring**: Use **Railway**
- Simple setup
- Always running
- $5 credit lasts months for a small bot

### **For budget-conscious**: Use **GitHub Actions**
- Completely free
- Runs every 5 minutes
- Very reliable

### **For hobby projects**: Use **Render**
- Free tier
- Easy setup
- Acceptable for non-critical monitoring

---

## 🚀 **Quick Start with Railway**

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Railway deployment"
   git push origin main
   ```

2. **Deploy on Railway**:
   - Go to [railway.app](https://railway.app)
   - "New Project" → "Deploy from GitHub repo"
   - Add environment variables
   - Deploy!

3. **Monitor**:
   ```bash
   # Check logs in Railway dashboard
   # Get notifications in Telegram
   ```

---

## 🔧 **Files Created for You**

- `railway.json` - Railway configuration
- `railway-start.py` - Startup script
- `nixpacks.toml` - Railway build config
- `render.yaml` - Render configuration
- `.github/workflows/ticket-checker.yml` - GitHub Actions
- `fly.toml` - Fly.io configuration

**Choose your platform and deploy! 🎉** 