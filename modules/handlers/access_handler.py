"""
Access request handler
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest, Forbidden
from modules.auth.authorization import save_access_request
from modules.database.models import DATABASE_FILE
from utils.reply_helper import reply_to_message
from config.logging_config import logger
import sqlite3

async def request_access(update, context):
    """Handle access requests for chats"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type == 'private':
        await reply_to_message(update, context, "❌ This command is only for group chats.")
        return
    
    # Check if bot is admin
    try:
        bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            await reply_to_message(update, context,
                "❌ I need to be an **administrator** in this chat first!\n\n"
                "Please make me an admin with these permissions:\n"
                "• Read messages\n"
                "• Send messages\n"
                "• Delete messages",
                parse_mode='Markdown'
            )
            return
    except (BadRequest, Forbidden):
        await reply_to_message(update, context, "❌ Cannot check my permissions in this chat.")
        return
    
    # Save access request
    request_message = ' '.join(context.args) if context.args else "Access request"
    save_access_request(
        chat.id, 
        chat.title or "Unknown Chat", 
        chat.type, 
        user.id, 
        user.username or "Unknown", 
        request_message
    )
    
    # Get the latest request ID
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM chat_access_requests ORDER BY id DESC LIMIT 1')
    request_id = cursor.fetchone()[0]
    conn.close()
    
    admin_user_id = context.bot_data.get('admin_user_id')
    if not admin_user_id:
        await reply_to_message(update, context, "❌ Admin not configured.")
        return
    
    # Send approval request to admin
    keyboard = [
        [InlineKeyboardButton("✅ Approve", callback_data=f'approve_access_{request_id}')],
        [InlineKeyboardButton("❌ Deny", callback_data=f'deny_access_{request_id}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    admin_message = (
        f"🔐 **Access Request** 🔐\n\n"
        f"**Chat:** {chat.title or 'Unknown'} (`{chat.id}`)\n"
        f"**Type:** {chat.type}\n"
        f"**Requested by:** {user.first_name or 'Unknown'} (@{user.username or 'no_username'})\n"
        f"**User ID:** `{user.id}`\n"
        f"**Message:** {request_message}\n\n"
        f"**Note:** Bot is admin in this chat ✅"
    )
    
    try:
        await context.bot.send_message(
            chat_id=admin_user_id,
            text=admin_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        await reply_to_message(update, context,
            "📨 **Access request sent!**\n\n"
            "Your request has been forwarded to the admin.\n"
            "You'll be notified once it's processed.",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Failed to send access request to admin: {e}")
        await reply_to_message(update, context,
            "❌ Failed to send access request. Please try again later."
        )