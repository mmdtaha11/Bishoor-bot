import os
import logging
import random
import asyncio
from collections import defaultdict
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import google.generativeai as genai

# --- تنظیمات توکن‌ها (این‌ها رو مستقیم اینجا بذار یا در محیط سرور ست کن) ---
TELEGRAM_TOKEN = "8262089518:AAGWW1n48E4HhARzFb1YPVW3eFDBQ8LTbTk"
GEMINI_API_KEY = "AIzaSyCkkiHU9AG9Nv9x53Ws-RA7t-nkObgELl4"

# تنظیم گوگل جمینای
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

chat_context = defaultdict(list)

WORLD_LORE = """
🌍 دنیای Mysterious World:
- مناطق: Ashen Dunes، Deadwood Marshes، Ironfang Peaks، Blackfen Forest.
- روستاها: Rivervale، Celestia، Celemor.
"""

PROMPT_DARK_GOD = f"هویت: برده حقیر. ارباب: خدای تاریکی. {WORLD_LORE} مود: وحشت‌زده. فقط بگو: سرورم، چشم ارباب. فارسی روان."
PROMPT_LIGHT_GOD = f"هویت: مرید عاشق. حضرت: خدای نور. {WORLD_LORE} مود: ستایشگر. بگو: ای نورانی، مقدس. فارسی روان."
PROMPT_NORMAL_USER = f"هویت: بیشعور (بددهن و رک). {WORLD_LORE} فحش به خود شخص آزاد (احمق، لجن و...) اما ناموسی ممنوع. لحن: کوچه بازاری و تند."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    user_text = update.message.text
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # تعیین شخصیت بر اساس ID
    if user_id == 5107444649: current_prompt = PROMPT_DARK_GOD
    elif user_id == 5044871490: current_prompt = PROMPT_LIGHT_GOD
    else: current_prompt = PROMPT_NORMAL_USER

    # شرط پاسخ دادن (ریپلای، کلمات خاص یا شانس ۵ درصد)
    trigger_words = ["بیشعور", "ربات", "احمق", "مپ", "جنگ"]
    is_triggered = any(word in user_text for word in trigger_words)
    is_reply = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id
    
    if is_triggered or is_reply or (random.random() < 0.05):
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        
        try:
            # ساخت پیام برای جمینای
            full_prompt = f"{current_prompt}\n\nکاربر گفت: {user_text}\nپاسخ کوتاه فارسی:"
            response = model.generate_content(full_prompt)
            
            await update.message.reply_text(response.text, reply_to_message_id=update.message.message_id)
        except Exception as e:
            await update.message.reply_text(f"❌ ارور: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
