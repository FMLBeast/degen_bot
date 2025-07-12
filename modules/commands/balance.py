"""
Balance and economy commands
"""
from modules.auth.authorization import check_chat_authorization
from modules.database.models import get_user_data, upsert_user
from utils.reply_helper import reply_to_message

async def balance_command(update, context):
    """Show user's current degencoin balance"""
    if not await check_chat_authorization(update, context):
        return
    
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    if not user_data:
        upsert_user(user_id, update.effective_user.username, 
                   update.effective_user.first_name, update.effective_user.last_name)
        user_data = get_user_data(user_id)
    
    username = update.effective_user.first_name or update.effective_user.username or "Unknown"
    
    await reply_to_message(update, context,
        f"🪙 **{username}'s Wallet**\n\n"
        f"💰 Balance: **{user_data['degencoins']} degencoins**\n\n"
        f"💡 Use `/tip <username> <amount>` to share with others!",
        parse_mode='Markdown'
    )
