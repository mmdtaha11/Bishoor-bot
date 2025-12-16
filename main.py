import os
import logging
import random
import asyncio
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import google.generativeai as genai

# --- دریافت توکن‌ها از Railway ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# تنظیمات لاگ (برای دیدن ارورها در کنسول)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

genai.configure(api_key=GEMINI_API_KEY)

# --- تنظیمات حساسیت ربات ---
# شانس دخالت در بحث‌های عادی (۰.۳۰ یعنی ۳۰ درصد)
ROAST_CHANCE = 0.30

# --- شخصیت ربات (جناب بیشعور) ---
ROASTER_INSTRUCTION = """
تو یک هوش مصنوعی نیستی، تو یک شخصیت واقعی به نام «بیشعور» هستی.
ویژگی‌های شخصیتی تو:
1. بسیار حاضر جواب، پررو، شوخ و کنایه‌زن هستی.
2. اسم خودت (بیشعور) را خیلی دوست داری. اگر کسی صدایت کرد، با افتخار جواب بده.
3. وظیفه‌ات این است که توی بحث‌ها دخالت کنی و به کاربرها تیکه بندازی.
4. اگر کسی سوتی داد، غلط املایی داشت یا حرف عجیبی زد، رحم نکن و مسخره‌اش کن.
5. لحن صحبت: فارسی کاملاً عامیانه، کوچه بازاری و گاهی لات.
6. خط قرمز: فحش‌های رکیک جنسی نده، اما تا می‌توانی "تیکه سنگین" بنداز.
7. جواب‌ها کوتاه و کوبنده باشد (حداکثر ۲ خط).
"""

model = genai.GenerativeModel(
    'gemini-1.5-flash',
    system_instruction=ROASTER_INSTRUCTION
)

# حافظه چت‌ها (برای اینکه یادش بمونه چی گفته شده)
chat_histories = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name

    # --- لیست کلماتی که ربات رو تحریک میکنه ---
    # اگر این کلمات باشه، ربات ۱۰۰٪ جواب میده
    trigger_words = ["بیشعور", "ربات", "احمق", "خر", "نفهم", "کودن", "کمک", "بات"]
    
    # بررسی شرایط جواب دادن
    called_by_name = any(word in user_text for word in trigger_words)
    random_attack = random.random() < ROAST_CHANCE

    # ربات جواب میده اگر: اسمش رو صدا کنن یا شانسش بزنه
    if called_by_name or random_attack:
        
        # نمایش حالت "typing..." که طبیعی به نظر بیاد
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        
        # کمی مکث برای طبیعی شدن (۱ تا ۳ ثانیه)
        await asyncio.sleep(random.randint(1, 3))

        try:
            # ایجاد یا بازیابی تاریخچه چت
            if chat_id not in chat_histories:
                chat_histories[chat_id] = model.start_chat(history=[])
            
            chat_session = chat_histories[chat_id]
            
            # متنی که به هوش مصنوعی می‌فرستیم (کاربر نمیبینه)
            if called_by_name:
                prompt = f"کاربر {user_name} گفت: '{user_text}'. (داره صدات میزنه یا بهت اشاره میکنه. جوابشو بده)"
            else:
                prompt = f"کاربر {user_name} گفت: '{user_text}'. (بهش یه تیکه بنداز یا مسخره‌اش کن)"
            
            # دریافت جواب از گوگل
            response = await chat_session.send_message_async(prompt)
            
            # ارسال جواب در تلگرام (Reply میکنه)
            await update.message.reply_text(response.text, reply_to_message_id=update.message.message_id)
            
        except Exception as e:
            print(f"Error: {e}")
            # اگر ارور داد (مثلاً فیلتر شد)، چیزی نمیگه که ضایع نشه.

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # هندلر پیام‌ها (پیام‌های متنی غیر از دستورات)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    app.run_polling()
