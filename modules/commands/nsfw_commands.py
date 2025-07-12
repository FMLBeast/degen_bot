"""
NSFW commands with safety checks and topic support
⚠️ WARNING: These commands contain adult content
"""
import json
import random
import sqlite3
import urllib.parse
import http.client
import aiohttp
from modules.auth.authorization import check_chat_authorization
from modules.auth.rate_limiting import require_rate_limit
from modules.database.models import DATABASE_FILE
from utils.reply_helper import reply_to_message, reply_photo
from config.logging_config import logger

# 18+ AGE VERIFICATION REQUIRED
ADULT_WARNING = (
    "🔞 **18+ CONTENT WARNING** 🔞\n\n"
    "This command contains adult content. By using this command, you confirm that you are 18+ years old."
)

def truncate_caption(caption, max_length=1024):
    """Truncate caption to Telegram's limit"""
    if len(caption) > max_length:
        return caption[:max_length-3] + '...'
    return caption

async def search_pornstar_command(update, context):
    """Search for adult performer information (18+ only)"""
    if not await check_chat_authorization(update, context):
        return
    
    if not await require_rate_limit(update.effective_user.id, 'show_me', update, context):
        return
    
    # Age verification warning
    await reply_to_message(update, context, ADULT_WARNING, parse_mode='Markdown')
    
    query = ' '.join(context.args)
    if not query:
        await reply_to_message(update, context, "Please provide a name to search for. Usage: /show_me <name>")
        return

    rapidapi_key = context.bot_data.get('rapidapi_key')
    if not rapidapi_key:
        await reply_to_message(update, context, "❌ Adult content API not configured.")
        return

    await reply_to_message(update, context, f"🔍 Searching for performer: {query}...")
    
    try:
        result = search_pornstar(query, rapidapi_key)

        if 'data' in result:
            name = result['data'].get('name', 'Unknown')
            aka = result['data'].get('aka', 'N/A')
            rating = result['data'].get('rating', {}).get('value', 'N/A')
            votes = result['data'].get('rating', {}).get('votes', 'N/A')
            bio = result['data'].get('bio', [])
            profile_img_link = result['data'].get('profileImgLink', 'No image available')

            bio_str = "\n".join([f"{item['name']}: {item['value']}" for item in bio])

            message = (
                f"*Name:* {name}\n"
                f"*AKA:* {aka}\n"
                f"*Rating:* {rating} {votes}\n\n"
                f"*Bio:\n{bio_str}"
            )
            
            truncated_message = truncate_caption(message)
            
            await reply_photo(update, context, photo=profile_img_link, caption=truncated_message, parse_mode='Markdown')
        else:
            await reply_to_message(update, context, "No results found.")
    except Exception as e:
        logger.error(f"Adult search error: {e}")
        await reply_to_message(update, context, "❌ Search failed. Service may be unavailable.")

def search_pornstar(query, rapidapi_key):
    """Search adult performer database"""
    conn = http.client.HTTPSConnection("quality-porn.p.rapidapi.com")

    headers = {
        'X-RapidAPI-Key': rapidapi_key,
        'X-RapidAPI-Host': "quality-porn.p.rapidapi.com"
    }

    encoded_query = urllib.parse.quote(query)
    conn.request("GET", f"/pornstar/search?query={encoded_query}&responseProfileImage=1", headers=headers)

    res = conn.getresponse()
    data = res.read()

    return json.loads(data.decode("utf-8"))

async def random_movie_command(update, context):
    """Get random adult video (18+ only)"""
    if not await check_chat_authorization(update, context):
        return
    
    if not await require_rate_limit(update.effective_user.id, 'show_me', update, context):
        return
    
    # Age verification warning
    await reply_to_message(update, context, ADULT_WARNING, parse_mode='Markdown')
    
    await reply_to_message(update, context, "🔞 Adult video search temporarily disabled for safety.")

async def fetch_image_command(update, context):
    """Fetch adult images (18+ only)"""
    if not await check_chat_authorization(update, context):
        return
    
    if not await require_rate_limit(update.effective_user.id, 'show_me', update, context):
        return
    
    # Age verification warning
    await reply_to_message(update, context, ADULT_WARNING, parse_mode='Markdown')
    
    await reply_to_message(update, context, "🔞 Adult image fetch temporarily disabled for safety.")

async def increment_cunt_counter(update, context):
    """Count usage of certain words (fun feature)"""
    if not await check_chat_authorization(update, context):
        return
    
    chat_id = update.message.chat.id
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Use UPSERT pattern for SQLite
    cursor.execute('''
        INSERT INTO cunt_counter (chat_id, count) VALUES (?, 1) 
        ON CONFLICT(chat_id) DO UPDATE SET count = count + 1
    ''', (chat_id,))
    conn.commit()

    cursor.execute('SELECT count FROM cunt_counter WHERE chat_id = ?', (chat_id,))
    count = cursor.fetchone()[0]
    conn.close()

    message = f"Word counter - that word has been used {count} times in this chat."
    await reply_to_message(update, context, message)
