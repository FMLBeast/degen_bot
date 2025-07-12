"""
Bot configuration settings
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot credentials
BOT_TOKEN = os.getenv('BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '0'))

# Validate required settings
def validate_config():
    """Validate that all required configuration is present"""
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is required")
    
    if not ADMIN_USER_ID:
        raise ValueError("ADMIN_USER_ID environment variable is required")
    
    return True
