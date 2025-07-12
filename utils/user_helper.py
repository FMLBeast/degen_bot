"""
User helper utilities for automatic database management
"""
from modules.database.models import upsert_user

def ensure_user_in_database(update):
    """
    Ensure the user from the update is in the database
    This should be called at the start of every command handler
    """
    user = update.effective_user
    if user:
        upsert_user(user.id, user.username, user.first_name, user.last_name)