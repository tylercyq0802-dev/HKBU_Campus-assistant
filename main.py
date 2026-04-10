"""
Telegram 校园助手机器人 - 英文对话，支持记忆功能
"""
import os   # 用于获取脚本所在目录
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

    # 初始化数据库表（只需运行一次）
    logging.info('Initializing database...')
    init_db()

    # 加载配置（修改开始：使用绝对路径读取 config.ini）
    logging.info('Loading config...')
    config = configparser.ConfigParser()
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.ini')
    config.read(config_path)
    # 修改结束
    print("配置文件中的节(sections):", config.sections())

    global gpt
    gpt = ChatGPT(config)

    logging.info('Connecting to Telegram...')
    app = ApplicationBuilder().token(config['TELEGRAM']['ACCESS_TOKEN']).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, callback))

    logging.info('Bot started!')
    app.run_polling()

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    # 处理 "remember" 命令（优化版）
    if user_message.lower().startswith("remember "):
        content = user_message[9:].strip()
        
        # 特殊模式匹配
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
        save_chat_log(user_id, user_message, reply)
        return

    # 获取用户的记忆信息
    context_data = get_user_context(user_id)
    context_str = ""
    if context_data:
        context_str = f"User known info: {json.dumps(context_data)}\n"

    # 构造校园助手的 prompt
    prompt = f"""You are a campus assistant helping with course questions, campus life, events, etc.
{context_str}
User question: {user_message}
Please answer briefly and helpfully in English."""

    # 发送 "thinking" 提示
    loading_msg = await update.message.reply_text("🤔 Thinking...")

    # 调用 LLM
    response = gpt.submit(prompt)

    # 编辑消息，回复结果
    await loading_msg.edit_text(response)

    # 保存对话记录到数据库
    save_chat_log(user_id, user_message, response)

if __name__ == '__main__':
    main()