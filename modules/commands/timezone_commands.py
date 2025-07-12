"""
Timezone commands with topic support
"""
import pytz
from datetime import datetime
import openai
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ConversationHandler
from modules.auth.authorization import check_chat_authorization
from modules.database.models import update_user_timezone, get_all_user_timezones, get_chat_user_timezones, get_user_data
from utils.reply_helper import reply_to_message
from utils.user_helper import ensure_user_in_database
from config.logging_config import logger

# Common country/city to timezone mapping
TIMEZONE_MAPPING = {
    'belgium': 'Europe/Brussels',
    'netherlands': 'Europe/Amsterdam',
    'germany': 'Europe/Berlin',
    'france': 'Europe/Paris',
    'uk': 'Europe/London',
    'united kingdom': 'Europe/London',
    'spain': 'Europe/Madrid',
    'italy': 'Europe/Rome',
    'usa': 'America/New_York',
    'united states': 'America/New_York',
    'canada': 'America/Toronto',
    'australia': 'Australia/Sydney',
    'japan': 'Asia/Tokyo',
    'china': 'Asia/Shanghai',
    'india': 'Asia/Kolkata',
    'russia': 'Europe/Moscow',
    'brazil': 'America/Sao_Paulo',
    'florida': 'America/New_York',
    'california': 'America/Los_Angeles',
    'new york': 'America/New_York',
    'texas': 'America/Chicago',
}

async def set_timezone(update, context):
    """Entry point: ask user for free-form timezone description"""
    if not await check_chat_authorization(update, context):
        return ConversationHandler.END

    # Ensure user exists in database
    ensure_user_in_database(update)

    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    # Check if user already has a timezone set
    if user_data and user_data.get('timezone'):
        current_timezone = user_data['timezone']
        try:
            tz = pytz.timezone(current_timezone)
            current_time = datetime.now(tz).strftime("%H:%M %Z")
            
            keyboard = [['✅ Keep Current', '🔄 Change Timezone']]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            
            await reply_to_message(update, context,
                f"🕐 **Current timezone:** `{current_timezone}`\n"
                f"🕐 **Current time:** {current_time}\n\n"
                f"Would you like to keep your current timezone or change it?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return TIMEZONE_CONFIRM
        except Exception:
            # Invalid timezone, proceed with normal flow
            pass
    
    await reply_to_message(update, context,
        "🕐 Please enter your timezone or location (e.g. 'Brussels', 'GMT+1', 'Florida')."
    )
    return TIMEZONE_INPUT

async def show_times(update, context):
    """Show current times for all users"""
    if not await check_chat_authorization(update, context):
        return
    
    # Ensure user exists in database
    ensure_user_in_database(update)
    
    user_timezones = get_all_user_timezones()
    
    if not user_timezones:
        await reply_to_message(update, context, "❌ No users have set their timezone yet.")
        return
    
    message = "🕐 **Current Times:**\n\n"
    
    for user_id, username, first_name, last_name, timezone_str in user_timezones:
        # Build better display name
        if first_name and last_name:
            display_name = f"{first_name} {last_name}"
        elif first_name:
            display_name = first_name
        elif username:
            display_name = f"@{username}"
        else:
            display_name = f'User {user_id}'
        try:
            tz = pytz.timezone(timezone_str)
            current_time = datetime.now(tz).strftime("%H:%M %Z")
            message += f"• {display_name}: {current_time} ({timezone_str})\n"
        except Exception as e:
            # Try to fix invalid timezone using mapping
            fixed_timezone = try_timezone_mapping(timezone_str)
            if fixed_timezone:
                try:
                    tz = pytz.timezone(fixed_timezone)
                    current_time = datetime.now(tz).strftime("%H:%M %Z")
                    # Update database with fixed timezone
                    update_user_timezone(user_id, fixed_timezone)
                    message += f"• {display_name}: {current_time} ({fixed_timezone}) ✅ Auto-fixed\n"
                    logger.info(f"Fixed timezone for user {user_id}: {timezone_str} -> {fixed_timezone}")
                except Exception:
                    message += f"• {display_name}: ❌ Invalid timezone ({timezone_str})\n"
                    logger.error(f"Timezone error: {e}")
            else:
                message += f"• {display_name}: ❌ Invalid timezone ({timezone_str})\n"
                logger.error(f"Timezone error: {e}")
    
    await reply_to_message(update, context, message, parse_mode='Markdown')

# Conversation states for free-form timezone handling
TIMEZONE_INPUT, TIMEZONE_CONFIRM = range(2)


def try_timezone_mapping(user_input):
    """Try to map user input to a valid timezone using predefined mapping"""
    normalized_input = user_input.lower().strip()
    return TIMEZONE_MAPPING.get(normalized_input)

async def timezone_input(update, context):
    """Handle user's free-form timezone input and suggest IANA timezone"""
    user_text = update.message.text.strip()
    user_id = update.effective_user.id

    # First try predefined mapping
    mapped_timezone = try_timezone_mapping(user_text)
    if mapped_timezone:
        try:
            pytz.timezone(mapped_timezone)  # Validate
            context.user_data['suggested_timezone'] = mapped_timezone
            
            # Show current time for confirmation
            tz = pytz.timezone(mapped_timezone)
            current_time = datetime.now(tz).strftime("%H:%M %Z")
            
            keyboard = [['✅ Confirm', '❌ Cancel']]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            
            await reply_to_message(update, context,
                f"🎯 Detected timezone: `{mapped_timezone}`\n"
                f"🕐 Current time: {current_time}\n\n"
                f"Is this correct?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return TIMEZONE_CONFIRM
        except Exception:
            pass  # Fall back to AI

    # Fall back to AI mapping
    openai_key = context.bot_data.get('openai_key')
    if not openai_key:
        await reply_to_message(update, context, "❌ AI backend not configured and no direct mapping found.")
        return ConversationHandler.END

    prompt = (
        f"You are an expert in mapping locations or timezone descriptions to IANA timezone identifiers. "
        f"User input: '{user_text}'. Return ONLY a valid IANA timezone identifier (e.g., 'Europe/Brussels', 'America/New_York'). "
        f"Do not include any explanation or additional text - just the timezone identifier."
    )
    try:
        client = openai.AsyncOpenAI(api_key=openai_key)
        resp = await client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role':'user','content':prompt}],
            temperature=0
        )
        tz_suggestion = resp.choices[0].message.content.strip().strip('"')
    except Exception as e:
        logger.error(f"Timezone AI error: {e}")
        await reply_to_message(update, context, "❌ Failed to suggest timezone. Please try again.")
        return ConversationHandler.END

    # Validate suggested timezone
    try:
        tz = pytz.timezone(tz_suggestion)
        current_time = datetime.now(tz).strftime('%H:%M %Z')
        context.user_data['suggested_timezone'] = tz_suggestion
        
        keyboard = [['✅ Confirm', '❌ Cancel']]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        
        await reply_to_message(update, context,
            f"🤖 AI suggestion: `{tz_suggestion}`\n"
            f"🕐 Current time: {current_time}\n\n"
            f"Is this correct?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return TIMEZONE_CONFIRM
    except Exception:
        await reply_to_message(update, context,
            f"❌ AI suggested invalid timezone: {tz_suggestion}. Please try again."
        )
        return ConversationHandler.END


async def timezone_confirm(update, context):
    """Handle user confirmation for suggested timezone"""
    text = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Handle existing timezone options
    if text == '✅ Keep Current':
        user_data = get_user_data(user_id)
        if user_data and user_data.get('timezone'):
            tz_str = user_data['timezone']
            try:
                tz = pytz.timezone(tz_str)
                current_time = datetime.now(tz).strftime('%H:%M %Z')
                await reply_to_message(update, context,
                    f"✅ Keeping current timezone: `{tz_str}`\n"
                    f"🕐 Current time: {current_time}",
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode='Markdown'
                )
            except Exception:
                await reply_to_message(update, context, "❌ Error with current timezone. Please set a new one.")
                await reply_to_message(update, context,
                    "🕐 Please enter your timezone or location (e.g. 'Belgium', 'GMT+1', 'Florida')."
                )
                return TIMEZONE_INPUT
        return ConversationHandler.END
    
    elif text == '🔄 Change Timezone':
        await reply_to_message(update, context,
            "🕐 Please enter your timezone or location (e.g. 'Belgium', 'GMT+1', 'Florida').",
            reply_markup=ReplyKeyboardRemove()
        )
        return TIMEZONE_INPUT
    
    elif text == '✅ Confirm':
        tz_str = context.user_data.get('suggested_timezone')
        if not tz_str:
            await reply_to_message(update, context, "❌ No timezone suggestion found. Please start over.")
            return ConversationHandler.END
            
        try:
            # Double-check timezone is valid before saving
            tz = pytz.timezone(tz_str)
            update_user_timezone(user_id, tz_str)
            current_time = datetime.now(tz).strftime('%H:%M %Z')
            
            await reply_to_message(update, context,
                f"✅ Timezone set to `{tz_str}`\n"
                f"🕐 Current time: {current_time}",
                reply_markup=ReplyKeyboardRemove(),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to set timezone {tz_str} for user {user_id}: {e}")
            await reply_to_message(update, context, "❌ Failed to set timezone. Please try again.")
    
    elif text == '❌ Cancel':
        await reply_to_message(update, context,
            "🕐 Let's try again. Enter your timezone or location:",
            reply_markup=ReplyKeyboardRemove()
        )
        return TIMEZONE_INPUT
    
    else:
        # Handle old format for backward compatibility
        if text.lower() in ('yes', 'y'):
            tz_str = context.user_data.get('tz_suggestion') or context.user_data.get('suggested_timezone')
            if tz_str:
                update_user_timezone(user_id, tz_str)
                tz = pytz.timezone(tz_str)
                current_time = datetime.now(tz).strftime('%H:%M %Z')
                await reply_to_message(update, context,
                    f"✅ Timezone set to `{tz_str}`\n"
                    f"🕐 Current time: {current_time}",
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode='Markdown'
                )
            else:
                await reply_to_message(update, context, "❌ No timezone found. Please start over.")
        else:
            await reply_to_message(update, context,
                "🕐 Let's try again. Enter your timezone or location:",
                reply_markup=ReplyKeyboardRemove()
            )
            return TIMEZONE_INPUT
    
    return ConversationHandler.END


async def timezone_cancel(update, context):
    """Cancel timezone conversation"""
    await reply_to_message(update, context,
        "❌ Timezone setup cancelled.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END
