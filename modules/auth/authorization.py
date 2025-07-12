"""
Chat authorization and access control
"""
import sqlite3
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest, Forbidden
from modules.database.models import DATABASE_FILE
from utils.reply_helper import reply_to_message

def is_chat_authorized(chat_id: int) -> bool:
    """Check if chat is authorized to use the bot"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT chat_id FROM authorized_chats WHERE chat_id = ? AND is_active = 1', (chat_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_authorized_chat(chat_id: int, chat_title: str, chat_type: str, approved_by: int):
    """Add chat to authorized list"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO authorized_chats (chat_id, chat_title, chat_type, approved_by)
        VALUES (?, ?, ?, ?)
    ''', (chat_id, chat_title, chat_type, approved_by))
    conn.commit()
    conn.close()

def save_access_request(chat_id: int, chat_title: str, chat_type: str, requested_by: int, username: str, message: str):
    """Save chat access request to database"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chat_access_requests (chat_id, chat_title, chat_type, requested_by, requested_by_username, request_message)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (chat_id, chat_title, chat_type, requested_by, username, message))
    conn.commit()
    conn.close()

def update_access_request_status(request_id: int, status: str, processed_by: int):
    """Update access request status"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE chat_access_requests 
        SET status = ?, processed_at = CURRENT_TIMESTAMP, processed_by = ?
        WHERE id = ?
    ''', (status, processed_by, request_id))
    conn.commit()
    conn.close()

def get_access_request(request_id: int):
    """Get access request by ID"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM chat_access_requests WHERE id = ?', (request_id,))
    result = cursor.fetchone()
    conn.close()
    return result

async def check_chat_authorization(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the current chat is authorized to use the bot"""
    chat = update.effective_chat
    if not chat:
        return False
    
    # Allow private chats always
    if chat.type == 'private':
        return True
    
    # Check if chat is authorized
    if not is_chat_authorized(chat.id):
        # Check if bot is admin (required for group usage)
        try:
            bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
            if bot_member.status not in ['administrator', 'creator']:
                await reply_to_message(update, context,
                    "❌ **Bot Access Required**\n\n"
                    "I need to be an **administrator** in this chat to function properly.\n"
                    "Please make me an admin with the following permissions:\n"
                    "• Read messages\n"
                    "• Send messages\n"
                    "• Delete messages\n\n"
                    "After making me admin, use `/request_access` to request authorization.",
                    parse_mode='Markdown'
                )
                return False
        except (BadRequest, Forbidden):
            pass
        
        await reply_to_message(update, context,
            "🚫 **Unauthorized Chat**\n\n"
            "This chat is not authorized to use this bot.\n\n"
            "📝 To request access:\n"
            "1. Make sure I'm an admin in this chat\n"
            "2. Use `/request_access` command\n"
            "3. Wait for admin approval\n\n"
            "💡 **Note**: I need admin permissions to read and log all messages for audit purposes.",
            parse_mode='Markdown'
        )
        return False
    
    return True