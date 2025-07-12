"""
Enhanced Mini Bot - Modular Version
Main bot entry point with proper topic group support
"""
import re
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters

# Configuration
from config.settings import validate_config, BOT_TOKEN, RAPIDAPI_KEY, OPENAI_API_KEY, ADMIN_USER_ID
from config.logging_config import logger

# Database
from modules.database.models import init_database

# Handlers
from modules.handlers.message_handler import handle_message, save_enhanced_chat_message
from modules.handlers.callback_handler import handle_callback_query
from modules.handlers.access_handler import request_access

# Commands
from modules.commands.start import start_command
from modules.commands.crypto import convert_crypto
from modules.commands.bet_calculator import calculate_bet
from modules.commands.timezone_commands import (
    set_timezone, show_times,
    timezone_input, timezone_confirm, timezone_cancel,
    TIMEZONE_INPUT, TIMEZONE_CONFIRM
)
from modules.commands.fight import fight_arena
from modules.commands.tip import tip_degencoins
from modules.commands.balance import balance_command
from modules.commands.gpt import ask_gpt

# Image handlers
from modules.commands.image_commands import (
    handle_draw_me_command, handle_draw_multiple_command, 
    handle_edit_image_command, handle_image_variation,
    set_favorite, add_to_collection, add_to_group_collection,
    view_personal_collection, view_group_collection
)

# Mines calculator
from modules.commands.mines import mines_multi_command

# NSFW commands (with safety checks)
from modules.commands.nsfw_commands import (
    search_pornstar_command, random_movie_command, 
    fetch_image_command, increment_cunt_counter
)

def main() -> None:
    """Main function to run the bot"""
    try:
        # Validate configuration
        validate_config()

        # Initialize database
        init_database()

        # Create application
        application = Application.builder().token(BOT_TOKEN).build()

        # Store API keys in bot_data for access in handlers
        application.bot_data['rapidapi_key'] = RAPIDAPI_KEY
        application.bot_data['openai_key'] = OPENAI_API_KEY
        application.bot_data['admin_user_id'] = ADMIN_USER_ID

        # Basic commands
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("request_access", request_access))

        # Feature commands
        application.add_handler(CommandHandler("convert", convert_crypto))
        application.add_handler(CommandHandler("bet", calculate_bet))
        # Conversation for free-form timezone input with AI suggestion
        timezone_conv = ConversationHandler(
            entry_points=[CommandHandler("timezone", set_timezone)],
            states={
                TIMEZONE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, timezone_input)],
                TIMEZONE_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, timezone_confirm)],
            },
            fallbacks=[CommandHandler("cancel", timezone_cancel)],
            allow_reentry=True,
        )
        application.add_handler(timezone_conv)
        application.add_handler(CommandHandler("times", show_times))
        application.add_handler(CommandHandler("fight", fight_arena))
        #application.add_handler(CommandHandler("tip", tip_degencoins))
        #application.add_handler(CommandHandler("balance", balance_command))
        application.add_handler(CommandHandler("ask", ask_gpt))

        # Image commands
        application.add_handler(CommandHandler("draw_me", handle_draw_me_command))
        application.add_handler(CommandHandler("draw_multiple", handle_draw_multiple_command))
        application.add_handler(CommandHandler("edit_image", handle_edit_image_command))
        application.add_handler(CommandHandler("set_favorite", set_favorite))
        application.add_handler(CommandHandler("add_to_collection", add_to_collection))
        application.add_handler(CommandHandler("add_to_group_collection", add_to_group_collection))
        application.add_handler(CommandHandler("view_personal_collection", view_personal_collection))
        application.add_handler(CommandHandler("view_group_collection", view_group_collection))

        # Mines calculator
        application.add_handler(CommandHandler("mines_multi", mines_multi_command))

        # NSFW commands (18+ warning in implementation)
        application.add_handler(CommandHandler("show_me", search_pornstar_command))
        #application.add_handler(CommandHandler("porn", random_movie_command))
        #application.add_handler(CommandHandler("gimme", fetch_image_command))

        # Callback query handler for all button interactions
        application.add_handler(CallbackQueryHandler(handle_callback_query))

        # Message handlers (including cunt counter)
        application.add_handler(MessageHandler(filters.Regex(r'\\bcunt\\b'), increment_cunt_counter))
        application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

        logger.info("Starting Enhanced Mini Bot with modular structure...")
        logger.info(f"Admin user ID: {ADMIN_USER_ID}")
        logger.info("Topic group support: ENABLED")

        application.run_polling()

    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == '__main__':
    main()
