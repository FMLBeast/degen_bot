"""
Achievement system for degencoins economy
"""
import json
import sqlite3
from modules.database.models import get_user_data, update_user_degencoins, log_transaction, DATABASE_FILE

def check_and_award_achievements(user_id: int, achievement_type: str, count: int = 1):
    """Check and award achievements to users"""
    user_data = get_user_data(user_id)
    if not user_data:
        return []
    
    current_achievements = json.loads(user_data.get('achievements', '[]'))
    new_achievements = []
    
    achievement_thresholds = {
        'first_fight': {'total_fights': 1, 'reward': 100, 'title': '🥊 First Blood'},
        'fighter': {'total_fights': 10, 'reward': 500, 'title': '⚔️ Warrior'},
        'champion': {'total_fights': 50, 'reward': 1000, 'title': '👑 Champion'},
        'tipper': {'total_tips_sent': 5, 'reward': 200, 'title': '💰 Generous Soul'},
        'popular': {'total_tips_received': 10, 'reward': 300, 'title': '⭐ Popular'},
        'streak_3': {'daily_streak': 3, 'reward': 150, 'title': '🔥 On Fire'},
        'streak_7': {'daily_streak': 7, 'reward': 500, 'title': '💪 Dedicated'},
        'artist': {'images_generated': 25, 'reward': 250, 'title': '🎨 Digital Artist'},
    }
    
    for achievement_id, requirements in achievement_thresholds.items():
        if achievement_id not in current_achievements:
            requirements_met = True
            for req, threshold in requirements.items():
                if req in ['reward', 'title']:
                    continue
                if user_data.get(req, 0) < threshold:
                    requirements_met = False
                    break
            
            if requirements_met:
                current_achievements.append(achievement_id)
                new_achievements.append(requirements)
                
                # Award achievement reward
                new_balance = user_data['degencoins'] + requirements['reward']
                update_user_degencoins(user_id, new_balance)
                log_transaction(0, user_id, requirements['reward'], 'achievement', f"Achievement: {requirements['title']}")
    
    # Update achievements in database
    if new_achievements:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET achievements = ? WHERE user_id = ?', 
                      (json.dumps(current_achievements), user_id))
        conn.commit()
        conn.close()
    
    return new_achievements

def get_user_achievements(user_id: int):
    """Get user's unlocked achievements"""
    user_data = get_user_data(user_id)
    if not user_data:
        return []
    
    achievements = json.loads(user_data.get('achievements', '[]'))
    
    achievement_titles = {
        'first_fight': '🥊 First Blood',
        'fighter': '⚔️ Warrior', 
        'champion': '👑 Champion',
        'tipper': '💰 Generous Soul',
        'popular': '⭐ Popular',
        'streak_3': '🔥 On Fire',
        'streak_7': '💪 Dedicated',
        'artist': '🎨 Digital Artist'
    }
    
    return [achievement_titles.get(ach, ach) for ach in achievements]