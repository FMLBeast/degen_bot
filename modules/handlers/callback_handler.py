"""
Callback query handler for button interactions
"""
from modules.auth.authorization import get_access_request, update_access_request_status, add_authorized_chat
from utils.reply_helper import send_message_to_chat
from utils.user_helper import ensure_user_in_database
from config.logging_config import logger

async def handle_callback_query(update, context):
    """Handle button callbacks with user isolation and access approvals"""
    query = update.callback_query
    await query.answer()
    
    # Ensure user exists in database
    ensure_user_in_database(update)
    
    callback_data = query.data
    admin_user_id = context.bot_data.get('admin_user_id')
    
    # Handle fight-related callbacks
    if callback_data.startswith(('fight_join_', 'fight_start_', 'fight_cancel_')):
        from modules.commands.fight import handle_fight_callback
        await handle_fight_callback(update, context)
        return
    
    # Handle access approval/denial (admin only)
    if callback_data.startswith('approve_access_') or callback_data.startswith('deny_access_'):
        if query.from_user.id != admin_user_id:
            await query.answer("❌ Only admin can approve/deny access requests.", show_alert=True)
            return
        
        action, request_id = callback_data.rsplit('_', 1)
        request_id = int(request_id)
        
        # Get request details
        request_data = get_access_request(request_id)
        if not request_data:
            await query.edit_message_text("❌ Request not found or already processed.")
            return
        
        chat_id, chat_title, chat_type = request_data[1], request_data[2], request_data[3]
        
        if action == 'approve_access':
            # Approve the chat
            add_authorized_chat(chat_id, chat_title, chat_type, admin_user_id)
            update_access_request_status(request_id, 'approved', admin_user_id)
            
            # Notify the chat
            try:
                await send_message_to_chat(context, chat_id, 
                    "✅ **Access Approved!**\n\nYour chat has been authorized to use this bot.\nUse /start to begin!",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to notify approved chat {chat_id}: {e}")
            
            await query.edit_message_text(
                f"✅ **Access Approved**\n\n"
                f"Chat: {chat_title} ({chat_id})\n"
                f"Status: Authorized ✅",
                parse_mode='Markdown'
            )
        
        elif action == 'deny_access':
            update_access_request_status(request_id, 'denied', admin_user_id)
            
            # Notify the chat
            try:
                await send_message_to_chat(context, chat_id,
                    "❌ **Access Denied**\n\nYour access request has been denied.\nContact the bot admin for more information.",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to notify denied chat {chat_id}: {e}")
            
            await query.edit_message_text(
                f"❌ **Access Denied**\n\n"
                f"Chat: {chat_title} ({chat_id})\n"
                f"Status: Denied ❌",
                parse_mode='Markdown'
            )
        
        return
    
    # Regular button handling with user isolation
    if '_' not in callback_data:
        await query.edit_message_text("❌ Invalid button data.")
        return
    
    action, button_user_id = callback_data.rsplit('_', 1)
    try:
        button_user_id = int(button_user_id)
    except ValueError:
        await query.edit_message_text("❌ Invalid button data format.")
        return
    
    current_user_id = query.from_user.id
    
    # Check if the user clicking the button is the same as the user who triggered it
    if current_user_id != button_user_id:
        await query.answer(
            "❌ This button is not for you! Use /start to get your own menu.",
            show_alert=True
        )
        return
    
    # Handle different actions
    action_responses = {
        'crypto': "💱 **Crypto Converter**\n\nUse `/convert <amount> <from> [to]` to convert currencies.",
        'bet': "🎲 **Bet Calculator**\n\nUse `/bet <base_bet> <multiplier> <increase_%>` to calculate betting progression.",
        'timezone': "🕐 **Timezone Settings**\n\nUse `/timezone <timezone>` to set your timezone.",
        'times': "⏰ **Show Times**\n\nUse `/times` to see current times for all users.",
        'fight': "⚔️ **Fight Arena**\n\nUse `/fight <opponent> <bet_amount>` to challenge someone.",
        'tip': "💰 **Tip Degencoins**\n\nUse `/tip <username> <amount>` to tip degencoins.",
        'askgpt': "🤖 **Ask GPT**\n\nUse `/ask <question>` to ask GPT anything!",
        'draw': "🎨 **AI Art**\n\nUse `/draw_me <prompt>` to generate AI images.",
        'stats': "📊 **Statistics**\n\nComing soon!"
    }
    
    if action in action_responses:
        await query.edit_message_text(action_responses[action], parse_mode='Markdown')
    else:
        await query.edit_message_text("❌ Unknown action.")