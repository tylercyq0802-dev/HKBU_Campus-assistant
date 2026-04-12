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
数据库操作模块 - 连接 Supabase PostgreSQL
"""
import os
import json
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

def get_connection():
    """获取数据库连接"""
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """初始化数据库：创建表（只需运行一次）"""
    conn = get_connection()
    cur = conn.cursor()
    # 对话日志表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            user_message TEXT,
            bot_response TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    # 用户上下文表（存储记住的信息）
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
    """保存一条对话记录"""
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
    """获取用户记住的信息（返回字典）"""
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
    """更新或添加用户的某条记忆（key-value）"""
    conn = get_connection()
    cur = conn.cursor()
    # 先获取现有数据
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