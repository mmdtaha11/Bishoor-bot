import os
import logging
import random
import asyncio
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from groq import Groq

# --- دریافت توکن‌ها ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- جلوگیری از کرش اگر کلید نباشه ---
if not GROQ_API_KEY:
    print("❌❌❌ ارور مهم: کلید GROQ_API_KEY در تنظیمات Railway پیدا نشد! ❌❌❌")
    client = None
else:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        print("✅ اتصال به Groq برقرار شد.")
    except Exception as e:
        print(f"❌ خطا در اتصال به Groq: {e}")
        client = None

SYSTEM_PROMPT = """
تو «بیشعور» هستی. ربات تلگرامی شوخ و کنایه‌زن.
اگر اسمت (بیشعور) آمد، بگو "جانم؟".
وظیفه: مسخره کردن و تیکه انداختن به کاربر.
قانون: جواب کوتاه (حداکثر ۲ جمله).
"""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    # اگر کلاینت ساخته نشده باشه (یعنی کلید نیست)، هیچی نگو که ارور نده
    if not client:
        return

    user_text = update.message.text
    chat_id = update.effective_chat.id
    message_thread_id = update.message.message_thread_id
    user_name = update.effective_user.first_name

    trigger_words = ["بیشعور", "ربات", "احمق", "خر", "نفهم", "بات", "چرا", "ساکت", "مشکل"]
    should_reply = any(word in user_text for word in trigger_words) or (random.random() < 0.30)

    if should_reply:
        try:
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING, message_thread_id=message_thread_id)
            await asyncio.sleep(random.randint(1, 2))

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"کاربر {user_name} گفت: '{user_text}'. (یه جواب دندون‌شکن و مسخره بهش بده)"}
            ]

            chat_completion = client.chat.completions.create(
                messages=messages,
                model="llama3-70b-8192",
                temperature=0.8,
            )

            reply_text = chat_completion.choices[0].message.content
            await update.message.reply_text(reply_text, reply_to_message_id=update.message.message_id)

        except Exception as e:
            print(f"Error: {e}")
            if "401" in str(e):
                 await update.message.reply_text("❌ کلید Groq اشتباه وارد شده!", reply_to_message_id=update.message.message_id)

if __name__ == '__main__':
    if not TELEGRAM_TOKEN:
        print("❌ توکن تلگرام پیدا نشد!")
    else:
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        app.run_polling()
