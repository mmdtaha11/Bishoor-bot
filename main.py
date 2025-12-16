import os
import logging
import random
import asyncio
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# --- دریافت توکن‌ها ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

genai.configure(api_key=GEMINI_API_KEY)

# --- تنظیمات حساسیت ربات ---
ROAST_CHANCE = 0.35

# --- خاموش کردن فیلترهای اخلاقی گوگل (مهم) ---
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

ROASTER_INSTRUCTION = """
تو شخصیتی به نام «بیشعور» هستی.
1. حاضر جواب، شوخ و کنایه‌زن باش.
2. با اسم «بیشعور» مشکلی نداری و با افتخار جواب میدی.
3. وظیفه: مسخره کردن سوتی‌ها و حرف‌های بی‌مزه کاربران.
4. لحن: فارسی عامیانه، کوچه بازاری.
5. جواب کوتاه (حداکثر ۲ جمله).
"""

model = genai.GenerativeModel(
    'gemini-1.5-flash',
    system_instruction=ROASTER_INSTRUCTION,
    safety_settings=safety_settings  # اعمال تنظیمات ضد سانسور
)

chat_histories = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # چک کردن اینکه پیام متنی هست یا نه
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    chat_id = update.effective_chat.id
    
    # برای گروه‌های دارای تاپیک (Topics)
    message_thread_id = update.message.message_thread_id

    trigger_words = ["بیشعور", "ربات", "احمق", "خر", "نفهم", "بات", "چرا", "ساکت"]
    
    called_by_name = any(word in user_text for word in trigger_words)
    random_attack = random.random() < ROAST_CHANCE

    if called_by_name or random_attack:
        try:
            # اکشن تایپینگ
            await context.bot.send_chat_action(
                chat_id=chat_id, 
                action=ChatAction.TYPING,
                message_thread_id=message_thread_id # مهم برای گروه‌های تاپیک‌دار
            )
            
            await asyncio.sleep(random.randint(1, 2))

            if chat_id not in chat_histories:
                chat_histories[chat_id] = model.start_chat(history=[])
            
            chat_session = chat_histories[chat_id]
            
            prompt = f"کاربر گفت: '{user_text}'. (یک جواب دندان‌شکن و شوخ بهش بده. خیلی کوتاه)"
            
            # ارسال به هوش مصنوعی
            response = await chat_session.send_message_async(prompt)
            
            # ارسال جواب به کاربر
            await update.message.reply_text(
                response.text, 
                reply_to_message_id=update.message.message_id
            )
            
        except Exception as e:
            # اگر ارور داد، متن ارور رو بفرسته تا بفهمیم مشکل چیه
            error_msg = f"❌ ارور: {str(e)}"
            print(error_msg)
            # این خط پایین رو بعد از رفع مشکل می‌تونی پاک کنی که به کاربر ارور نشون نده
            await update.message.reply_text("زبونم بند اومد! (یک خطایی رخ داد)", reply_to_message_id=update.message.message_id)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
