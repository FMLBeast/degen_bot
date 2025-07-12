# Enhanced Mini Bot

A comprehensive Telegram bot with advanced features, security, and full audit capabilities.

## 🚀 Core Features

1. **💱 Crypto Conversion** - Real-time cryptocurrency and fiat currency conversion
2. **🎲 Bet Calculator** - Advanced betting progression calculations
3. **🕐 Timezone Management** - Personal timezone configuration and global time display
4. **⚔️ Fight Arena** - AI-powered combat simulation with wagering
5. **💰 Tip System** - Transfer degencoins between users
6. **🤖 AI Assistant** - Ask GPT any question
7. **🎨 AI Image Generation** - Generate AI images with `/draw_me <prompt>`
8. **🏆 Achievement System** - Unlock rewards and track progress
9. **📊 Statistics** - Comprehensive user analytics

## 🔐 Security & Administration

- **Chat Authorization System** - Admin approval required for group usage
- **Rate Limiting** - Prevents spam and manages API costs
- **Full Message Auditing** - Complete chat history with media tracking
- **User Isolation** - Private interactions, no cross-user interference
- **Admin Controls** - Centralized management via approval system

## 🏆 Degencoins Economy

- **Daily Rewards** - Login bonuses with streak multipliers
- **Achievements** - Unlock titles and earn bonus coins
- **Transaction History** - Full audit trail of all transfers
- **Statistics Tracking** - Monitor fights, tips, and activities

## ⚙️ Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your API keys and admin user ID
```

3. **Run the bot:**
```bash
python main_bot.py
```

## 📋 Commands

### Core Commands
- `/start` - Start bot and receive daily rewards
- `/balance` - Check your degencoin balance
- `/request_access` - Request chat authorization (groups only)

### Features
- `/convert <amount> <from> [to]` - Convert currencies
- `/bet <base_bet> <multiplier> <increase_%>` - Calculate betting progression
- `/timezone <timezone>` - Set your timezone
- `/times` - Show times for all users
- `/fight <opponent> <bet_amount>` - Challenge to combat
- `/tip <username> <amount>` - Send degencoins to others
- `/ask <question>` - Ask AI any question

`/draw_me <prompt>` - Generate an AI image
`/draw_multiple <prompt>` - Generate multiple AI images

## 🔒 Chat Authorization

### For Group Chats:
1. Add bot to your group
2. Make bot an **administrator** with these permissions:
   - Read messages
   - Send messages
   - Delete messages
3. Use `/request_access` to request authorization
4. Admin will receive approval request with buttons
5. Once approved, full bot functionality is available

### Admin Features:
- Receive access requests with chat details
- One-click approve/deny with buttons
- Automatic notification to requesting chat
- Full audit trail of all approvals

## 🗄️ Database Schema

### Comprehensive Data Storage:
- **Users**: Profiles, balances, statistics, achievements
- **Chat History**: Full message audit with media tracking
- **Transactions**: Complete financial history
- **Fight History**: Combat records and outcomes
- **Access Requests**: Authorization workflow tracking
- **Rate Limits**: Spam prevention data

### Audit Features:
- Message content and metadata
- Media file tracking
- User activity patterns
- Transaction trails
- Administrative actions

## 🛡️ Security Features

### Rate Limiting:
- GPT requests: 30 seconds
- Fight challenges: 1 minute  
- Currency conversion: 10 seconds
- Tips: 5 seconds

### Authorization:
- Private chats: Always allowed
- Group chats: Require admin approval
- Bot must be admin for group functionality
- Silent rejection of unauthorized requests

### Data Protection:
- User-bound interactions
- Private button responses
- Secure transaction processing
- Comprehensive error handling

## 🏅 Achievement System

### Available Achievements:
- **🥊 First Blood** - Complete first fight (+100 coins)
- **⚔️ Warrior** - Win 10 fights (+500 coins)
- **👑 Champion** - Win 50 fights (+1000 coins)
- **💰 Generous Soul** - Send 5 tips (+200 coins)
- **⭐ Popular** - Receive 10 tips (+300 coins)
- **🔥 On Fire** - 3-day login streak (+150 coins)
- **💪 Dedicated** - 7-day login streak (+500 coins)

## 📊 Statistics Tracking

### User Metrics:
- Degencoin balance and transactions
- Daily login streaks
- Fight statistics (total/won)
- Tip activity (sent/received)
- Achievement progress
- Activity timestamps

## 🔧 Environment Variables

```env
BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key  
RAPIDAPI_KEY=your_rapidapi_key
ADMIN_USER_ID=your_telegram_user_id
```

## 🏗️ Modular Architecture

### Clean Code Structure:
```
📁 main_bot.py          # Main entry point
📁 config/              # Configuration settings
📁 modules/
  ├── auth/             # Authorization & rate limiting
  ├── commands/         # All bot commands (crypto, gpt, etc.)
  ├── database/         # Database models & operations
  ├── economy/          # Degencoins & achievements
  └── handlers/         # Message & callback handlers
📁 utils/               # Helper utilities
```

### Benefits:
- **Topic Group Support** - Replies in correct forum threads
- **Easy Maintenance** - Modular components
- **Scalable** - Add new features without touching core
- **Testable** - Isolated modules for unit testing
- **Clean Separation** - Auth, commands, database separate

## 📈 Performance Features

- Database indexing for fast queries
- Connection pooling optimization
- Async message processing
- Comprehensive error handling
- Structured logging system
- Topic group thread awareness

## 🛠️ Technical Requirements

- Python 3.8+
- SQLite database
- Telegram Bot Token (@BotFather)
- OpenAI API Key
- RapidAPI Key
- Admin Telegram User ID

## 🎯 Use Cases

- **Community Management** - Secure group chat integration
- **Gaming Communities** - Virtual economy and competitions  
- **Educational Groups** - AI assistance and utilities
- **Trading Communities** - Crypto tools and analytics
- **General Purpose** - Multi-feature utility bot
