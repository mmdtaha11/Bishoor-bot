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

# --- تنظیمات ضد سانسور ---
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

# --- تابعی برای پیدا کردن مدل سالم ---
def get_working_model():
    try:
        # اول سعی میکنیم لیست مدل‌های موجود برای این کلید رو بگیریم
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        print(f"Available models: {available_models}")
        
        # اولویت با مدل‌های جدیدتر است
        priority_list = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro', 'models/gemini-1.0-pro']
        
        for model_name in priority_list:
            if model_name in available_models:
                print(f"✅ Selected Model: {model_name}")
                return genai.GenerativeModel(model_name, safety_settings=safety_settings)
        
        # اگر هیچکدوم توی لیست نبود، شانسی gemini-pro رو انتخاب میکنیم
        return genai.GenerativeModel('gemini-pro', safety_settings=safety_settings)
    except Exception as e:
        print(f"Error listing models: {e}")
        # حالت اضطراری
        return genai.GenerativeModel('gemini-pro', safety_settings=safety_settings)

# انتخاب مدل
model = get_working_model()

chat_histories = {}

# دستورالعمل سیستم (اگر مدل ساپورت نکنه، توی پیام میفرستیم)
ROASTER_SYS_PROMPT = """
تو شخصیتی به نام «بیشعور» هستی.
ویژگی‌ها: شوخ، حاضرجواب، کنایه‌زن و کمی بی‌ادب.
نکته: اگر کسی گفت "بیشعور"، بگو "جانم؟".
قانون: جملات کوتاه (زیر ۲۰ کلمه) بگو.
"""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    chat_id = update.effective_chat.id
    message_thread_id = update.message.message_thread_id

    trigger_words = ["بیشعور", "ربات", "احمق", "خر", "نفهم", "بات", "چرا", "ساکت", "مشکل"]
    should_reply = any(word in user_text for word in trigger_words) or (random.random() < 0.25)

    if should_reply:
        try:
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING, message_thread_id=message_thread_id)
            await asyncio.sleep(1)

            if chat_id not in chat_histories:
                chat_histories[chat_id] = model.start_chat(history=[])
            
            chat_session = chat_histories[chat_id]
            
            # ارسال دستورالعمل همراه با پیام (برای محکم کاری)
            full_prompt = f"{ROASTER_SYS_PROMPT}\n\nکاربر گفت: {user_text}\n(جواب بده:)"
            
            response = await chat_session.send_message_async(full_prompt)
            
            if response.text:
                await update.message.reply_text(response.text, reply_to_message_id=update.message.message_id)
            else:
                await update.message.reply_text("...", reply_to_message_id=update.message.message_id)

        except Exception as e:
            # اگر باز هم ارور داد، دقیقاً میگه چه مدل‌هایی در دسترسه
            error_msg = str(e)
            if "404" in error_msg:
                 await update.message.reply_text("❌ کلید جدید هم مدل‌ها رو پیدا نکرد. لیست مدل‌ها خالیه!", reply_to_message_id=update.message.message_id)
            else:
                 await update.message.reply_text(f"⚠️ ارور: {error_msg}", reply_to_message_id=update.message.message_id)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
