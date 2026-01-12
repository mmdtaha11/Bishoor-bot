import os
import logging
import random
import asyncio
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import google.generativeai as genai

# --- تنظیمات توکن‌ها (جایگذاری شده توسط Gemini) ---
TELEGRAM_TOKEN = "8262089518:AAGWW1n48E4HhARzFb1YPVW3eFDBQ8LTbTk"
GEMINI_API_KEY = "AIzaSyCkkiHU9AG9Nv9x53Ws-RA7t-nkObgELl4"

# تنظیم گوگل جمینای
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

logging.basicConfig(level=logging.INFO)

# شخصیت ربات «بیشعور»
SYSTEM_PROMPT = """
تو یک موجود بددهن، رک و بیشعور هستی. 
فحش دادن به خود شخص (احمق، گاو، لجن، کله‌پوک) آزاد است اما فحش ناموسی (مادر، خواهر و...) اکیداً ممنوع.
باید با لحن کوچه بازاری، تند و فارسی عامیانه جواب بدهی. جواب‌ها بسیار کوتاه باشد.
اطلاعات دنیا: Ashen Dunes، Deadwood Marshes، Ironfang Peaks، Blackfen Forest.
"""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user_text = update.message.text
    chat_id = update.effective_chat.id

    # تریگرها: اگر ریپلای شود، یا کلمات خاص بگوید یا شانس ۱۰ درصد
    trigger_words = ["بیشعور", "ربات", "احمق", "تاس", "مپ"]
    is_triggered = any(word in user_text for word in trigger_words)
    is_reply = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id
    
    if is_triggered or is_reply or (random.random() < 0.1):
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        try:
            full_prompt = f"{SYSTEM_PROMPT}\n\nکاربر گفت: {user_text}\nپاسخ تند و کوتاه تو:"
            response = model.generate_content(full_prompt)
            await update.message.reply_text(response.text, reply_to_message_id=update.message.message_id)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()