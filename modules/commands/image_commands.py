"""
AI Image generation commands with topic support
"""
import os
import io
import sqlite3
from datetime import datetime
from telegram import Update
from PIL import Image, ImageOps
from modules.auth.authorization import check_chat_authorization
from modules.auth.rate_limiting import require_rate_limit
from modules.economy.achievements import check_and_award_achievements
from modules.database.models import DATABASE_FILE
from utils.reply_helper import reply_to_message, reply_photo
from config.logging_config import logger

IMAGE_DIR = "received_images"
GROUP_IMAGE_DIR = "group_images"
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(GROUP_IMAGE_DIR, exist_ok=True)

async def handle_draw_me_command(update: Update, context):
    """Handle AI image generation with DALL-E"""
    if not await check_chat_authorization(update, context):
        return
    
    if not await require_rate_limit(update.effective_user.id, 'draw_me', update, context):
        return
    
    user_id = update.effective_user.id
    user_input = ' '.join(context.args)

    if not user_input:
        await reply_to_message(update, context, "Please provide a prompt. Usage: /draw_me <your prompt>")
        return

    # Check daily limit
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM draw_requests WHERE user_id = ? AND timestamp >= ?', 
                  (user_id, today_start))
    count = cursor.fetchone()[0]

    if count >= 25:
        await reply_to_message(update, context, "You've reached the daily limit of 25 images. Try again tomorrow.")
        conn.close()
        return

    await reply_to_message(update, context, "🎨 Generating image, please wait...")

    try:
        # Get OpenAI client from bot_data
        openai_key = context.bot_data.get('openai_key')
        if not openai_key:
            await reply_to_message(update, context, "❌ AI image generation not configured.")
            conn.close()
            return
        
        import openai
        client = openai.OpenAI(api_key=openai_key)
        
        response = client.images.generate(
            prompt=user_input,
            model="dall-e-3",
            n=1,
            size="1024x1024",
            response_format="url",
            quality="standard",
            style="vivid"
        )

        image_url = response.data[0].url
        cursor.execute('INSERT INTO draw_requests (user_id, timestamp) VALUES (?, ?)', 
                     (user_id, datetime.now()))
        conn.commit()

        # Check for achievements
        new_achievements = check_and_award_achievements(user_id, 'image_generated')
        
        caption = f"🎨 Generated for: {user_input}"
        if new_achievements:
            caption += "\n\n🏅 **New Achievement!**"
            for achievement in new_achievements:
                caption += f"\n• {achievement['title']} (+{achievement['reward']} coins)"

        await reply_photo(update, context, photo=image_url, caption=caption)
        
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        await reply_to_message(update, context, f"Failed to generate image: {e}")
    finally:
        conn.close()

async def handle_draw_multiple_command(update: Update, context):
    """Generate multiple images with DALL-E 2"""
    if not await check_chat_authorization(update, context):
        return
    
    if not await require_rate_limit(update.effective_user.id, 'draw_me', update, context):
        return
    
    user_input = ' '.join(context.args)
    
    if not user_input:
        await reply_to_message(update, context, "Please provide a prompt. Usage: /draw_multiple <your prompt>")
        return

    await reply_to_message(update, context, "🎨 Generating multiple images, please wait...")

    try:
        openai_key = context.bot_data.get('openai_key')
        if not openai_key:
            await reply_to_message(update, context, "❌ AI image generation not configured.")
            return
        
        import requests
        headers = {"Authorization": f"Bearer {openai_key}"}
        data = {
            "prompt": user_input,
            "model": "dall-e-2",
            "n": 3,
            "size": "1024x1024",
            "response_format": "url"
        }

        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            response_data = response.json()
            for i, image_data in enumerate(response_data['data']):
                await reply_photo(update, context, 
                    photo=image_data['url'], 
                    caption=f"🎨 Image {i+1}/3: {user_input}"
                )
            await reply_to_message(update, context, "✅ Images generated successfully!")
        else:
            await reply_to_message(update, context, f"Generation failed: {response.status_code} - {response.text}")
    except Exception as e:
        await reply_to_message(update, context, f"Error occurred: {e}")

# Placeholder functions for other image commands
async def handle_edit_image_command(update: Update, context):
    await reply_to_message(update, context, "🔧 Image editing feature coming soon!")

async def handle_image_variation(update: Update, context):
    await reply_to_message(update, context, "🔄 Image variation feature coming soon!")

async def set_favorite(update: Update, context):
    await reply_to_message(update, context, "❤️ Set favorite feature coming soon!")

async def add_to_collection(update: Update, context):
    await reply_to_message(update, context, "📁 Add to collection feature coming soon!")

async def add_to_group_collection(update: Update, context):
    await reply_to_message(update, context, "📁 Add to group collection feature coming soon!")

async def view_personal_collection(update: Update, context):
    await reply_to_message(update, context, "👤 Personal collection feature coming soon!")

async def view_group_collection(update: Update, context):
    await reply_to_message(update, context, "👥 Group collection feature coming soon!")