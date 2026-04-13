import os
from dotenv import load_dotenv

# Extract the real secret key from local .env file.
# When running in a cloud container, it will automatically skip and read the system environment variables.
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
    #else:
        #print(f"{env_name}")
print("✅ All core environment secret keys loaded successfully. Bot is starting up...")


"""
Telegram Campus Assistant Bot - English Conversation, Supports Memory Function
"""
import os   # Used to get the directory where the script is located
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
import configparser
import logging
from ChatGPT_HKBU import ChatGPT
import json
from db import init_db, save_chat_log, get_user_context, update_user_context

gpt = None

def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    # Initialize the database tables (only needs to run once)
    logging.info('Initializing database...')
    init_db()

# ================= Load Configuration (Security Enhanced Version) =================
    logging.info('Loading config...')
    config = configparser.ConfigParser()

    # Get the directory of the current script and read the original config(cleaned).ini framework (storage cabinet)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config(cleaned).ini')
    config.read(config_path)

    # ============ Operations to improve robustness ===========
    # [Key Step A] Ensure the storage cabinet drawers exist, and pre-fill non-sensitive information (Default Fallback mechanism)
    if 'TELEGRAM' not in config:
        config['TELEGRAM'] = {}

    if 'CHATGPT' not in config:
        config['CHATGPT'] = {}

    # Fill in the gaps: If these basic details are not written in config.ini, we automatically pad them with the school's default parameters
    if 'BASE_URL' not in config['CHATGPT']:
        config['CHATGPT']['BASE_URL'] = 'https://genai.hkbu.edu.hk/api/v0/rest'
    if 'MODEL' not in config['CHATGPT']:
        config['CHATGPT']['MODEL'] = 'gpt-5-mini'
    if 'API_VER' not in config['CHATGPT']:
        config['CHATGPT']['API_VER'] = '2024-12-01-preview'
    # ==========================================================

    # [Key Step B] Bait and switch: Override local static configurations with cloud environment variables
    config['TELEGRAM']['ACCESS_TOKEN'] = os.getenv("TG_BOT_TOKEN")

    config['CHATGPT']['API_KEY'] = os.getenv("OPENAI_API_KEY")

    print("The security sections from the environment file have been loaded:", config.sections())

# ================= Load Configuration (Security Enhanced Version End) =================    
    global gpt
    gpt = ChatGPT(config)

    logging.info('Connecting to Telegram...')
    app = ApplicationBuilder().token(config['TELEGRAM']['ACCESS_TOKEN']).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, callback))

    logging.info('Bot started!')
  # app.run_polling()
# ---------------- Core modification: Webhook and long polling environment judgment logic ----------------
# Check whether currently in a production environment (cloud). When testing locally, do not write ENV=production in your .env
    if os.getenv("ENV") == "Webhook":
        logging.info("☁️Running in Webhook mode (HKBUbot)...")
        
        # 从环境变量获取云端 ALB 域名配置的回调地址 (例如 https://your-alb-domain.com)
        webhook_url = os.getenv("WEBHOOK_URL")
        if not webhook_url:
            raise ValueError("🚨 Fatal error: WEBHOOK_URL environment variable missing in production environment!")
            
        app.run_webhook(
            listen="0.0.0.0",
            port=8080,
            webhook_url=webhook_url
        )
    else:
        logging.info("💻 Running in Polling mode (HKBUbot)...")
        app.run_polling()

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    # Process the "remember" command (Optimized version)
    if user_message.lower().startswith("remember "):
        content = user_message[9:].strip()
        
        # Special pattern matching
        if content.lower().startswith("that "):
            value = content[5:].strip()
            key = "info"
        elif content.lower().startswith("my name is "):
            value = content[11:].strip()
            key = "name"
        elif content.lower().startswith("i am "):
            value = content[5:].strip()
            key = "status"
        elif content.lower().startswith("i'm "):
            value = content[4:].strip()
            key = "status"
        elif " " in content:
            key, value = content.split(" ", 1)
        else:
            key = "note"
            value = content
        
        update_user_context(user_id, key, value)
        reply = f"✅ I've remembered: {key} = {value}"
        await update.message.reply_text(reply)
        print(f"============= New instructions =============", flush=True)
        print(f"User Request: {user_message}", flush=True)
        print(f"Bot Response: {reply}", flush=True)
        print(f"==================================", flush=True)
        save_chat_log(user_id, user_message, reply)
        return

    # Get the user's memory information
    context_data = get_user_context(user_id)
    context_str = ""
    if context_data:
        context_str = f"User known info: {json.dumps(context_data)}\n"

    # Construct the campus assistant's prompt
    prompt = f"""User known info: {context_str}
User question: {user_message}
Please answer as the HKBU campus assistant."""

    # Send "thinking" prompt
    loading_msg = await update.message.reply_text("🤔 Thinking...")

    # Call LLM
    response = gpt.submit(prompt)

    # Edit message, reply with the result
    await loading_msg.edit_text(response)
    print(f"============= New conversation =============", flush=True)
    print(f"User Request: {user_message}", flush=True)
    print(f"Bot Response: {response}", flush=True)
    print(f"==================================", flush=True)

    # Save the chat log to the database
    save_chat_log(user_id, user_message, response)

if __name__ == '__main__':
    main()
