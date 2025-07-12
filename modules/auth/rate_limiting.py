"""
Rate limiting functionality
"""
import time
from collections import defaultdict
from telegram import Update
from utils.reply_helper import reply_to_message

# Rate limiting storage
user_rate_limits = defaultdict(lambda: defaultdict(float))
RATE_LIMITS = {
    'ask_gpt': 30,  # 30 seconds between GPT requests
    'fight': 60,    # 1 minute between fights
    'convert': 10,  # 10 seconds between conversions
    'tip': 5,       # 5 seconds between tips
    'draw_me': 20,  # 20 seconds between image generations
    'show_me': 15,  # 15 seconds between NSFW searches
}

def check_rate_limit(user_id: int, action: str) -> bool:
    """Check if user is within rate limit for action"""
    current_time = time.time()
    last_used = user_rate_limits[user_id][action]
    
    if current_time - last_used < RATE_LIMITS.get(action, 0):
        return False
    
    user_rate_limits[user_id][action] = current_time
    return True

def get_rate_limit_remaining(user_id: int, action: str) -> int:
    """Get remaining seconds for rate limit"""
    current_time = time.time()
    last_used = user_rate_limits[user_id][action]
    limit = RATE_LIMITS.get(action, 0)
    remaining = limit - (current_time - last_used)
    return max(0, int(remaining))

async def require_rate_limit(user_id: int, action: str, update: Update, context) -> bool:
    """Check rate limit and show appropriate message"""
    if not check_rate_limit(user_id, action):
        remaining = get_rate_limit_remaining(user_id, action)
        await reply_to_message(update, context,
            f"⏳ **Rate Limit**\n\n"
            f"Please wait **{remaining} seconds** before using `/{action}` again.\n\n"
            f"This helps prevent spam and manages API costs.",
            parse_mode='Markdown'
        )
        return False
    return True