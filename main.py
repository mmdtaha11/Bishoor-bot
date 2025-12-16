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

# --- بررسی اولیه کلید ---
client = None
if not GROQ_API_KEY:
    print("❌ کلید GROQ پیدا نشد!")
else:
    try:
        client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"❌ ارور در ساخت کلاینت: {e}")

SYSTEM_PROMPT = """
تو «بیشعور» هستی.
ویژگی‌ها: شوخ، حاضرجواب، کنایه‌زن و پررو.
وظیفه: مسخره کردن کاربر.
جواب کوتاه بده.
"""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    # اگر کلید نبود، همون اول بگو
    if not client:
        await update.message.reply_text("❌ کلید Groq توی تنظیمات Railway نیست!", reply_to_message_id=update.message.message_id)
        return

    user_text = update.message.text
    chat_id = update.effective_chat.id
    message_thread_id = update.message.message_thread_id
    user_name = update.effective_user.first_name

    trigger_words = ["بیشعور", "ربات", "احمق", "خر", "نفهم", "بات", "چرا", "ساکت", "مشکل"]
    should_reply = any(word in user_text for word in trigger_words) or (random.random() < 0.30)

    if should_reply:
        # اینجا شروع میکنه به تایپ کردن
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING, message_thread_id=message_thread_id)
        await asyncio.sleep(1)

        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"کاربر {user_name} گفت: '{user_text}'. (جوابش رو بده)"}
            ]

            # درخواست به Groq
            chat_completion = client.chat.completions.create(
                messages=messages,
                model="llama3-8b-8192", # مدل سبک و سریع
                temperature=0.7,
            )

            reply_text = chat_completion.choices[0].message.content
            
            # ارسال جواب
            await update.message.reply_text(reply_text, reply_to_message_id=update.message.message_id)

        except Exception as e:
            # 🚨 اینجا مهم‌ترین بخشه: ارسال متن ارور به تلگرام
            error_msg = str(e)
            await update.message.reply_text(f"⚠️ ارور فنی:\n{error_msg}", reply_to_message_id=update.message.message_id)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
