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

# لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

genai.configure(api_key=GEMINI_API_KEY)

# --- تنظیمات ضد سانسور (خیلی مهم) ---
# این تنظیمات میگه به هیچ چیزی گیر نده
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

# --- شخصیت ربات ---
# یکم دستورش رو نرم‌تر کردم که گوگل بلاک نکنه، ولی هنوز پرروئه
ROASTER_INSTRUCTION = """
تو شخصیتی به نام «بیشعور» هستی.
ویژگی‌ها: شوخ، حاضرجواب، کنایه‌زن و کمی بی‌ادب.
وظیفه: با جملات کوتاه و خنده‌دار، کاربر را ضایع کن.
نکته: اگر کسی گفت "بیشعور"، بگو "جانم؟".
قانون: جملات کوتاه (زیر ۲۰ کلمه) بگو.
"""

model = genai.GenerativeModel(
    'gemini-1.5-flash',
    system_instruction=ROASTER_INSTRUCTION,
    safety_settings=safety_settings
)

chat_histories = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    chat_id = update.effective_chat.id
    
    # هندل کردن تاپیک‌ها
    message_thread_id = update.message.message_thread_id

    trigger_words = ["بیشعور", "ربات", "احمق", "خر", "نفهم", "بات", "چرا", "ساکت", "مشکل"]
    
    # همیشه ۲۰ درصد شانس جواب دادن داره
    should_reply = any(word in user_text for word in trigger_words) or (random.random() < 0.20)

    if should_reply:
        try:
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING, message_thread_id=message_thread_id)
            await asyncio.sleep(1) # مکث کوتاه

            if chat_id not in chat_histories:
                chat_histories[chat_id] = model.start_chat(history=[])
            
            chat_session = chat_histories[chat_id]
            
            # درخواست به گوگل
            response = await chat_session.send_message_async(user_text)
            
            # --- بخش مهم: چاپ ارور اگر گوگل جواب نداد ---
            if response.text:
                await update.message.reply_text(response.text, reply_to_message_id=update.message.message_id)
            else:
                await update.message.reply_text("گوگل جواب رو فرستاد ولی متنش خالی بود!", reply_to_message_id=update.message.message_id)

        except ValueError:
            # این ارور یعنی گوگل کلاً بلاک کرده (سانسور)
            await update.message.reply_text("⛔️ گوگل حرفم رو سانسور کرد! (Safety Block)", reply_to_message_id=update.message.message_id)
            
        except Exception as e:
            # نمایش ارور واقعی به تو
            error_message = f"⚠️ ارور سیستم:\n{str(e)}"
            await update.message.reply_text(error_message, reply_to_message_id=update.message.message_id)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
