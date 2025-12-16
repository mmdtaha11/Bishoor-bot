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

# اتصال به Groq
client = Groq(api_key=GROQ_API_KEY)

# --- شخصیت ربات ---
SYSTEM_PROMPT = """
تو «بیشعور» هستی. یک ربات تلگرامی با شخصیت خاص.
ویژگی‌ها: شوخ، حاضرجواب، کنایه‌زن، کمی بی‌ادب و پررو.
وظیفه: کاربرها را مسخره کن و به حرف‌هایشان تیکه بنداز.
اگر کسی اسمت را صدا زد (بیشعور)، بگو "جانم؟" یا "ها؟".
قانون: جواب‌هایت حتماً کوتاه (یک یا دو جمله) باشد.
"""

chat_histories = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    chat_id = update.effective_chat.id
    message_thread_id = update.message.message_thread_id
    user_name = update.effective_user.first_name

    trigger_words = ["بیشعور", "ربات", "احمق", "خر", "نفهم", "بات", "چرا", "ساکت", "مشکل"]
    
    # شانس ۳۰ درصدی یا صدا زدن اسم
    should_reply = any(word in user_text for word in trigger_words) or (random.random() < 0.30)

    if should_reply:
        try:
            # اکشن تایپینگ
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING, message_thread_id=message_thread_id)
            await asyncio.sleep(random.randint(1, 2))

            # آماده‌سازی پیام برای Groq (Llama 3)
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"کاربر {user_name} گفت: '{user_text}'. (یه جواب دندون‌شکن و مسخره بهش بده)"}
            ]

            # درخواست به سرور
            chat_completion = client.chat.completions.create(
                messages=messages,
                model="llama3-70b-8192", # مدل قدرتمند و سریع
                temperature=0.8, # خلاقیت بالا
            )

            reply_text = chat_completion.choices[0].message.content

            # ارسال جواب
            await update.message.reply_text(reply_text, reply_to_message_id=update.message.message_id)

        except Exception as e:
            error_msg = str(e)
            print(f"Error: {error_msg}")
            # فقط اگر خیلی واجب بود ارور رو بفرست، وگرنه ساکت بمون
            if "401" in error_msg:
                await update.message.reply_text("❌ کلید Groq اشتباهه!", reply_to_message_id=update.message.message_id)
            # در بقیه موارد هیچی نگو که ضایع نشه

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
