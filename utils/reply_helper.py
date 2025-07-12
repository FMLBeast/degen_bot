"""
Reply helper utilities for topic groups and general message handling
"""
from telegram import Update
from telegram.ext import ContextTypes

async def reply_to_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, **kwargs):
    """
    Smart reply function that handles topic groups correctly
    """
    if not update.message:
        return None
    
    # Check if this is a topic group (forum)
    if (hasattr(update.message.chat, 'is_forum') and 
        update.message.chat.is_forum and 
        update.message.message_thread_id):
        # Reply in the same topic thread
        kwargs['message_thread_id'] = update.message.message_thread_id
    
    return await update.message.reply_text(text, **kwargs)

async def reply_photo(update: Update, context: ContextTypes.DEFAULT_TYPE, photo, **kwargs):
    """
    Smart photo reply function that handles topic groups correctly
    """
    if not update.message:
        return None
    
    # Check if this is a topic group (forum)
    if (hasattr(update.message.chat, 'is_forum') and 
        update.message.chat.is_forum and 
        update.message.message_thread_id):
        # Reply in the same topic thread
        kwargs['message_thread_id'] = update.message.message_thread_id
    
    return await update.message.reply_photo(photo=photo, **kwargs)

async def send_message_to_chat(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, 
                              message_thread_id: int = None, **kwargs):
    """
    Send message to chat with optional topic thread support
    """
    if message_thread_id:
        kwargs['message_thread_id'] = message_thread_id
    
    return await context.bot.send_message(chat_id=chat_id, text=text, **kwargs)

async def send_photo_to_chat(context: ContextTypes.DEFAULT_TYPE, chat_id: int, photo, 
                            message_thread_id: int = None, **kwargs):
    """
    Send photo to chat with optional topic thread support
    """
    if message_thread_id:
        kwargs['message_thread_id'] = message_thread_id
    
    return await context.bot.send_photo(chat_id=chat_id, photo=photo, **kwargs)