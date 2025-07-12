# 🚀 Quick Start Guide

## First Time Setup

### 1. Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials:
# - BOT_TOKEN: Get from @BotFather on Telegram
# - OPENAI_API_KEY: Get from OpenAI platform
# - RAPIDAPI_KEY: Get from RapidAPI
# - ADMIN_USER_ID: Your Telegram user ID
```

### 3. Run the Bot
```bash
python main_bot.py
```

## ✅ What You Get

### **Core Features:**
- 💱 Crypto conversion
- 🎲 Bet calculator  
- 🕐 Timezone management
- ⚔️ Fight arena with AI
- 💰 Tip system
- 🤖 Ask GPT anything
- 🎨 AI image generation
- 💎 Mines calculator
- 📊 User statistics

### **Enterprise Features:**
- 🔐 Chat authorization system
- ⏳ Rate limiting
- 📝 Full message auditing
- 🏆 Achievement system
- 💪 Topic group support
- 🛡️ Security controls

## 🎯 First Commands to Try

1. **Start the bot**: `/start`
2. **Ask AI**: `/ask What is the meaning of life?`
3. **Convert crypto**: `/convert 1 BTC USD`
4. **Generate art**: `/draw_me a futuristic city`
5. **Calculate bets**: `/bet 10 2.0 15`

## 🔧 Admin Features

As admin, you'll receive access requests with one-click approve/deny buttons when groups want to use the bot.

## 📁 Clean Architecture

- `main_bot.py` - Start here
- `modules/` - All features organized by category
- `config/` - Settings and logging
- `utils/` - Helper functions

Ready to launch! 🎉