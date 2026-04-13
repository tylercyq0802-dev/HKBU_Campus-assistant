import os
from dotenv import load_dotenv

# Extract the real secret key from the .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

required_envs = {
    "DATABASE_URL": DATABASE_URL,
    "TG_BOT_TOKEN": BOT_TOKEN,
    "OPENAI_API_KEY": OPENAI_API_KEY
}

for env_name, env_value in required_envs.items():
    if not env_value:
        raise ValueError(f"🚨 Fatal error: Missing required environment variable '{env_name}'! Please check your .env file or system configuration.")

print("✅ All core environment secret keys loaded successfully. Bot is starting up...")


"""
Database Operation Module - Connect to Supabase PostgreSQL
"""
import os
import json
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

def get_connection():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """Initialize the database: create tables (only need to run once)"""
    conn = get_connection()
    cur = conn.cursor()
    # Dialogue Log Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            user_message TEXT,
            bot_response TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    # User Context Table (Stores remembered information)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_context (
            user_id BIGINT PRIMARY KEY,
            context_data JSONB,
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized (tables created).")

def save_chat_log(user_id: int, user_message: str, bot_response: str):
    """Save a conversation record"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO chat_logs (user_id, user_message, bot_response) VALUES (%s, %s, %s)",
        (user_id, user_message, bot_response)
    )
    conn.commit()
    cur.close()
    conn.close()

def get_user_context(user_id: int) -> dict:
    """Get the information remembered by the user (returns a dictionary)"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT context_data FROM user_context WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row and row[0]:
        return row[0]
    return {}

def update_user_context(user_id: int, key: str, value: str):
    """Update or add a user's specific memory (key-value)"""
    conn = get_connection()
    cur = conn.cursor()
   # First, obtain the existing data
    cur.execute("SELECT context_data FROM user_context WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    if row:
        context = row[0] or {}
        context[key] = value
        cur.execute(
            "UPDATE user_context SET context_data = %s, updated_at = NOW() WHERE user_id = %s",
            (Json(context), user_id)
        )
    else:
        context = {key: value}
        cur.execute(
            "INSERT INTO user_context (user_id, context_data) VALUES (%s, %s)",
            (user_id, Json(context))
        )
    conn.commit()
    cur.close()
    conn.close()
