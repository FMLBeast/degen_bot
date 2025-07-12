"""
Enhanced message handler with full auditing and topic support
"""
import sqlite3
from telegram import Update, MessageOriginUser
from modules.auth.authorization import is_chat_authorized
from modules.database.models import upsert_user, DATABASE_FILE
from config.logging_config import logger

def get_forward_from_user_id(message):
    """Extract user ID from forward_origin for backward compatibility"""
    if not message.forward_origin:
        return None
    
    if isinstance(message.forward_origin, MessageOriginUser):
        return message.forward_origin.sender_user.id
    
    return None

def save_enhanced_chat_message(update: Update):
    """Save comprehensive message data for auditing with topic support"""
    if not update.message:
        return
        
    message = update.message
    user = message.from_user
    chat = message.chat
    
    # Extract media information
    media_file_id = None
    media_type = 'text'
    
    if message.photo:
        media_file_id = message.photo[-1].file_id
        media_type = 'photo'
    elif message.document:
        media_file_id = message.document.file_id
        media_type = 'document'
    elif message.video:
        media_file_id = message.video.file_id
        media_type = 'video'
    elif message.audio:
        media_file_id = message.audio.file_id
        media_type = 'audio'
    elif message.voice:
        media_file_id = message.voice.file_id
        media_type = 'voice'
    elif message.sticker:
        media_file_id = message.sticker.file_id
        media_type = 'sticker'
    elif message.location:
        media_type = 'location'
    elif message.contact:
        media_type = 'contact'
    
    # TOPIC SUPPORT: Extract message thread ID for forums
    message_thread_id = getattr(message, 'message_thread_id', None)
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chat_history (
            message_id, user_id, username, first_name, last_name,
            chat_id, chat_title, chat_type, message_text, message_type,
            media_file_id, reply_to_message_id, forward_from_user_id, 
            edit_date, message_thread_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        message.message_id,
        user.id if user else None,
        user.username if user else None,
        user.first_name if user else None,
        user.last_name if user else None,
        chat.id,
        chat.title if hasattr(chat, 'title') else None,
        chat.type,
        message.text,
        media_type,
        media_file_id,
        message.reply_to_message.message_id if message.reply_to_message else None,
        get_forward_from_user_id(message),
        message.edit_date.timestamp() if message.edit_date else None,
        message_thread_id  # TOPIC SUPPORT: Store thread ID
    ))
    conn.commit()
    conn.close()

async def handle_message(update: Update, context):
    """Handle all incoming messages and save to database with full auditing"""
    if not update.message:
        return
    
    # Check chat authorization for non-private chats
    if update.effective_chat.type != 'private':
        if not is_chat_authorized(update.effective_chat.id):
            return  # Silently ignore messages from unauthorized chats
    
    # Ensure user exists in database
    if update.effective_user:
        upsert_user(
            update.effective_user.id,
            update.effective_user.username,
            update.effective_user.first_name,
            update.effective_user.last_name
        )
    
    # Save comprehensive message data for auditing
    try:
        save_enhanced_chat_message(update)
    except Exception as e:
        logger.error(f"Failed to save message to database: {e}")