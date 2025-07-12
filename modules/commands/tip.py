"""
Tip commands - placeholder
"""
from modules.auth.authorization import check_chat_authorization
from utils.reply_helper import reply_to_message

async def tip_degencoins(update, context):
    """Tip degencoins command - coming soon"""
    if not await check_chat_authorization(update, context):
        return
    
    await reply_to_message(update, context,
        "💰 **Tip Degencoins** 💰\n\n"
        "Use `/tip <username> <amount>` to tip degencoins to another user.\n\n"
        "Examples:\n"
        "• `/tip @john 50`\n"
        "• `/tip alice 25`\n\n"
        "Check your balance with `/balance`\n\n"
        "🚧 Full implementation coming soon!",
        parse_mode='Markdown'
    )
