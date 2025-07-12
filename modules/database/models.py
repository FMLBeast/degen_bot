"""
Database models and initialization
"""
import sqlite3
import json
from typing import Dict, Optional

DATABASE_FILE = 'bot_database.db'

def init_database():
    """Initialize SQLite database with all required tables"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Users table with enhanced fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            timezone TEXT,
            degencoins INTEGER DEFAULT 1000,
            daily_streak INTEGER DEFAULT 0,
            last_daily_claim TEXT,
            total_fights INTEGER DEFAULT 0,
            fights_won INTEGER DEFAULT 0,
            total_tips_sent INTEGER DEFAULT 0,
            total_tips_received INTEGER DEFAULT 0,
            achievements TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Authorized chats table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS authorized_chats (
            chat_id INTEGER PRIMARY KEY,
            chat_title TEXT,
            chat_type TEXT,
            approved_by INTEGER,
            approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # Chat access requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_access_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            chat_title TEXT,
            chat_type TEXT,
            requested_by INTEGER,
            requested_by_username TEXT,
            request_message TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            processed_by INTEGER
        )
    ''')
    
    # Enhanced chat history table with full auditing
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            user_id INTEGER,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            chat_id INTEGER,
            chat_title TEXT,
            chat_type TEXT,
            message_text TEXT,
            message_type TEXT,
            media_file_id TEXT,
            media_file_path TEXT,
            reply_to_message_id INTEGER,
            forward_from_user_id INTEGER,
            edit_date INTEGER,
            message_thread_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Fight history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fight_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fight_type TEXT,
            chat_id INTEGER,
            participants TEXT,
            winner_id INTEGER,
            winner_name TEXT,
            bet_amount INTEGER,
            total_pot INTEGER,
            turns_taken INTEGER,
            fight_scenario TEXT,
            fight_log TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (winner_id) REFERENCES users (user_id)
        )
    ''')
    
    # Transaction history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id INTEGER,
            to_user_id INTEGER,
            amount INTEGER,
            transaction_type TEXT,
            description TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Images table for image handlers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User images table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_images (
            user_id INTEGER,
            image_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (image_id) REFERENCES images (id),
            PRIMARY KEY (user_id, image_id)
        )
    ''')
    
    # Group images table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_images (
            channel_id INTEGER,
            image_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (image_id) REFERENCES images (id),
            PRIMARY KEY (channel_id, image_id)
        )
    ''')
    
    # Draw requests table for rate limiting
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS draw_requests (
            user_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Cunt counter table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cunt_counter (
            chat_id INTEGER PRIMARY KEY,
            count INTEGER DEFAULT 0
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_history_chat_id ON chat_history(chat_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_history_timestamp ON chat_history(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_history_thread_id ON chat_history(message_thread_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_from_user ON transactions(from_user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_to_user ON transactions(to_user_id)')
    
    conn.commit()
    conn.close()

def get_user_data(user_id: int) -> Optional[Dict]:
    """Get user data from database"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'user_id': row[0],
            'username': row[1],
            'first_name': row[2],
            'last_name': row[3],
            'timezone': row[4],
            'degencoins': row[5],
            'daily_streak': row[6],
            'last_daily_claim': row[7],
            'total_fights': row[8],
            'fights_won': row[9],
            'total_tips_sent': row[10],
            'total_tips_received': row[11],
            'achievements': row[12],
            'created_at': row[13],
            'updated_at': row[14]
        }
    return None

def upsert_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """Insert or update user in database"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, degencoins, updated_at)
        VALUES (?, ?, ?, ?, COALESCE((SELECT degencoins FROM users WHERE user_id = ?), 1000), CURRENT_TIMESTAMP)
    ''', (user_id, username, first_name, last_name, user_id))
    
    conn.commit()
    conn.close()

def update_user_degencoins(user_id: int, amount: int):
    """Update user degencoins in database"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET degencoins = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def update_user_timezone(user_id: int, timezone: str):
    """Update user timezone in database"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET timezone = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?', (timezone, user_id))
    conn.commit()
    conn.close()

def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user data by username from database"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? OR first_name = ?', (username, username))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'user_id': row[0],
            'username': row[1],
            'first_name': row[2],
            'last_name': row[3],
            'timezone': row[4],
            'degencoins': row[5],
            'daily_streak': row[6],
            'last_daily_claim': row[7],
            'total_fights': row[8],
            'fights_won': row[9],
            'total_tips_sent': row[10],
            'total_tips_received': row[11],
            'achievements': row[12],
            'created_at': row[13],
            'updated_at': row[14]
        }
    return None

def get_all_user_timezones():
    """Get all users with timezones from database"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, first_name, last_name, timezone FROM users WHERE timezone IS NOT NULL ORDER BY first_name, username')
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_chat_user_timezones(chat_id: int):
    """Get users with timezones who have been active in the specific chat"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT u.user_id, u.username, u.first_name, u.last_name, u.timezone 
        FROM users u
        INNER JOIN chat_history ch ON u.user_id = ch.user_id
        WHERE u.timezone IS NOT NULL 
        AND ch.chat_id = ?
        ORDER BY u.first_name, u.username
    ''', (chat_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def log_transaction(from_user_id: int, to_user_id: int, amount: int, transaction_type: str, description: str):
    """Log transaction to database"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (from_user_id, to_user_id, amount, transaction_type, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (from_user_id, to_user_id, amount, transaction_type, description))
    conn.commit()
    conn.close()