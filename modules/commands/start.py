"""
Start command with daily rewards and topic support
"""
import sqlite3
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from modules.auth.authorization import check_chat_authorization
from modules.database.models import upsert_user, get_user_data, log_transaction, DATABASE_FILE
from utils.reply_helper import reply_to_message

async def start_command(update, context):
    """Handle /start command with daily rewards"""
    if not await check_chat_authorization(update, context):
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name
    
    # Upsert user in database
    upsert_user(user_id, username, first_name, last_name)
    user_data = get_user_data(user_id)
    
   
    keyboard = [
        [InlineKeyboardButton("💱 Crypto Convert", callback_data=f'crypto_{user_id}')],
        [InlineKeyboardButton("🎲 Bet Calculator", callback_data=f'bet_{user_id}')],
        [InlineKeyboardButton("🕐 Set Timezone", callback_data=f'timezone_{user_id}')],
        [InlineKeyboardButton("⏰ Show Times", callback_data=f'times_{user_id}')],
        [InlineKeyboardButton("⚔️ Fight Arena", callback_data=f'fight_{user_id}')],
        [InlineKeyboardButton("🤖 Ask GPT", callback_data=f'askgpt_{user_id}')],
        [InlineKeyboardButton("🎨 AI Art", callback_data=f'draw_{user_id}')],
        [InlineKeyboardButton("📊 Statistics", callback_data=f'stats_{user_id}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await reply_to_message(update, context,
        f"Welcome {first_name or username}! 🤖\n"
    #    f"You have {user_data['degencoins']} degencoins 🪙\n\n"
        "Choose a feature:",
        reply_markup=reply_markup
    )